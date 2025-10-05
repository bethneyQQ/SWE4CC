#!/usr/bin/env python3
"""
提取和展示Claude Code的活动记录
包括文件访问、工具使用、交互轮数等
"""
import json
import argparse
from pathlib import Path
from typing import Dict, List
import re


def analyze_claude_activity(predictions_file: str):
    """分析Claude Code的活动"""

    print("=" * 80)
    print("Claude Code 活动分析报告")
    print("=" * 80)

    with open(predictions_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            data = json.loads(line)
            instance_id = data['instance_id']

            print(f"\n{'='*80}")
            print(f"📌 Instance: {instance_id}")
            print(f"{'='*80}")

            # 1. 基本信息
            claude_meta = data.get('claude_code_meta', {})
            response = claude_meta.get('response_data', {})

            is_enhanced = claude_meta.get('enhanced', False)
            has_tools = claude_meta.get('tools_available', False)

            print(f"\n📋 模式配置:")
            print(f"  增强模式: {'✅ 是' if is_enhanced else '❌ 否'}")
            print(f"  工具可用: {'✅ 是' if has_tools else '❌ 否'}")

            # 2. 交互统计
            num_turns = response.get('num_turns', 0)
            duration_ms = response.get('duration_ms', 0)
            duration_api_ms = response.get('duration_api_ms', 0)

            print(f"\n🔄 交互统计:")
            print(f"  交互轮数: {num_turns}")
            print(f"  总耗时: {duration_ms/1000:.1f}秒")
            print(f"  API耗时: {duration_api_ms/1000:.1f}秒")
            print(f"  处理耗时: {(duration_ms-duration_api_ms)/1000:.1f}秒")

            # 3. Token使用
            usage = response.get('usage', {})
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            cache_creation = usage.get('cache_creation_input_tokens', 0)
            cache_read = usage.get('cache_read_input_tokens', 0)

            print(f"\n💬 Token使用:")
            print(f"  Input tokens: {input_tokens:,}")
            print(f"  Output tokens: {output_tokens:,}")
            print(f"  Cache creation: {cache_creation:,} (首次读取)")
            print(f"  Cache read: {cache_read:,} (缓存命中)")
            print(f"  总计: {input_tokens + output_tokens + cache_creation + cache_read:,}")

            # 4. 模型使用 (多模型表示使用了工具)
            model_usage = response.get('modelUsage', {})
            if len(model_usage) > 1:
                print(f"\n🤖 多模型使用 (表明使用了工具):")
                for model, usage_data in model_usage.items():
                    model_name = model.split('-')[1] if '-' in model else model
                    print(f"  {model_name}:")
                    print(f"    Input: {usage_data.get('inputTokens', 0):,}")
                    print(f"    Output: {usage_data.get('outputTokens', 0):,}")
                    print(f"    Cost: ${usage_data.get('costUSD', 0):.4f}")

            # 5. 权限拒绝 (显示被拒绝的工具使用)
            denials = response.get('permission_denials', [])
            if denials:
                print(f"\n🚫 被拒绝的工具使用:")
                for denial in denials:
                    tool_name = denial.get('tool_name', 'unknown')
                    tool_input = denial.get('tool_input', {})
                    print(f"  ❌ {tool_name}:")
                    if 'command' in tool_input:
                        print(f"     Command: {tool_input['command']}")
                    if 'file_path' in tool_input:
                        print(f"     File: {tool_input['file_path']}")
            else:
                print(f"\n✅ 所有工具使用均被允许")

            # 6. 从响应内容推断活动
            result = response.get('result', '')
            full_output = data.get('full_output', '')

            print(f"\n🔍 推断的活动 (从响应分析):")

            # 提取提到的文件
            mentioned_files = set()
            file_patterns = [
                r'([a-zA-Z_][a-zA-Z0-9_/]*\.py)',
                r'`([^`]+\.py)`',
                r'"([^"]+\.py)"',
            ]
            for pattern in file_patterns:
                matches = re.findall(pattern, result)
                mentioned_files.update(matches)

            if mentioned_files:
                print(f"\n  📁 提到的文件 ({len(mentioned_files)} 个):")
                for f in sorted(mentioned_files)[:10]:
                    print(f"    - {f}")
                if len(mentioned_files) > 10:
                    print(f"    ... 还有 {len(mentioned_files) - 10} 个")

            # 提取提到的行号
            line_mentions = set()
            line_patterns = [
                r'line (\d+)',
                r'at line (\d+)',
                r'on line (\d+)',
            ]
            for pattern in line_patterns:
                matches = re.findall(pattern, result, re.IGNORECASE)
                line_mentions.update(matches)

            if line_mentions:
                print(f"\n  🔢 提到的行号:")
                lines = sorted([int(l) for l in line_mentions])
                print(f"    {', '.join(map(str, lines[:10]))}")
                if len(lines) > 10:
                    print(f"    ... 还有 {len(lines) - 10} 个")

            # 工具使用迹象
            tool_indicators = {
                'Read': ['reading', 'i read', 'after reading', 'the file contains', 'looking at the'],
                'Bash': ['i ran', 'executing', 'running', 'i executed', 'command output'],
                'Grep': ['i searched', 'searching for', 'grep shows', 'found occurrences'],
                'Edit': ['i modified', 'i edited', 'changing', 'updating'],
            }

            detected_tools = []
            for tool, indicators in tool_indicators.items():
                for indicator in indicators:
                    if indicator in result.lower():
                        detected_tools.append(tool)
                        break

            if detected_tools:
                print(f"\n  🔧 检测到可能使用的工具:")
                print(f"    {', '.join(detected_tools)}")

            # 7. Repo信息
            if 'repo_path' in data:
                print(f"\n📦 仓库信息:")
                print(f"  路径: {data['repo_path']}")

            # 8. 验证信息
            if 'validation_errors' in data and data['validation_errors']:
                print(f"\n⚠️  验证错误 ({len(data['validation_errors'])} 个):")
                for error in data['validation_errors'][:3]:
                    print(f"  - {error[:80]}...")

            # 9. 尝试次数
            attempts = data.get('attempts', 1)
            if attempts > 1:
                print(f"\n🔄 重试信息:")
                print(f"  尝试次数: {attempts}")

            # 10. Patch复杂度
            if 'patch_complexity' in data:
                complexity = data['patch_complexity']
                print(f"\n📊 Patch复杂度:")
                print(f"  文件数: {complexity.get('files_changed', 0)}")
                print(f"  Hunks: {complexity.get('hunks', 0)}")
                print(f"  添加: {complexity.get('lines_added', 0)} 行")
                print(f"  删除: {complexity.get('lines_removed', 0)} 行")

            # 11. 成本
            total_cost = response.get('total_cost_usd', data.get('cost', 0))
            print(f"\n💰 成本:")
            print(f"  本实例: ${total_cost:.4f}")

            # 12. 生成的patch预览
            patch = data.get('model_patch', '')
            if patch:
                print(f"\n📝 生成的Patch (前5行):")
                patch_lines = patch.split('\n')[:5]
                for line in patch_lines:
                    print(f"  {line}")
                if len(patch.split('\n')) > 5:
                    print(f"  ... 还有 {len(patch.split('\n')) - 5} 行")

    print(f"\n{'='*80}")
    print("✅ 分析完成")
    print(f"{'='*80}\n")


def compare_basic_vs_enhanced(basic_file: str, enhanced_file: str):
    """对比基础模式和增强模式"""

    print("\n" + "=" * 80)
    print("基础模式 vs 增强模式 对比")
    print("=" * 80)

    def load_stats(file):
        with open(file, 'r') as f:
            data = json.loads(f.readline())
            resp = data.get('claude_code_meta', {}).get('response_data', {})
            return {
                'turns': resp.get('num_turns', 0),
                'cache_creation': resp.get('usage', {}).get('cache_creation_input_tokens', 0),
                'cache_read': resp.get('usage', {}).get('cache_read_input_tokens', 0),
                'cost': resp.get('total_cost_usd', 0),
                'models': len(resp.get('modelUsage', {})),
            }

    basic = load_stats(basic_file)
    enhanced = load_stats(enhanced_file)

    print(f"\n| 指标 | 基础模式 | 增强模式 | 差异 |")
    print(f"|------|---------|---------|------|")
    print(f"| 交互轮数 | {basic['turns']} | {enhanced['turns']} | +{enhanced['turns']-basic['turns']} |")
    print(f"| Cache创建 | {basic['cache_creation']:,} | {enhanced['cache_creation']:,} | +{enhanced['cache_creation']-basic['cache_creation']:,} |")
    print(f"| Cache读取 | {basic['cache_read']:,} | {enhanced['cache_read']:,} | +{enhanced['cache_read']-basic['cache_read']:,} |")
    print(f"| 使用模型数 | {basic['models']} | {enhanced['models']} | +{enhanced['models']-basic['models']} |")
    print(f"| 成本 | ${basic['cost']:.4f} | ${enhanced['cost']:.4f} | +${enhanced['cost']-basic['cost']:.4f} |")

    print(f"\n💡 解读:")
    if enhanced['cache_creation'] > basic['cache_creation']:
        print(f"  • 增强模式创建了 {enhanced['cache_creation']-basic['cache_creation']:,} tokens的缓存")
        print(f"    → 表明读取了更多文件")
    if enhanced['turns'] > basic['turns']:
        print(f"  • 增强模式多了 {enhanced['turns']-basic['turns']} 轮交互")
        print(f"    → 表明使用了工具进行探索")
    if enhanced['models'] > basic['models']:
        print(f"  • 增强模式使用了 {enhanced['models']} 个模型")
        print(f"    → Haiku用于工具调用，Sonnet用于主要推理")


def main():
    parser = argparse.ArgumentParser(description='提取Claude Code活动记录')
    parser.add_argument('--predictions_file', required=True, help='Predictions文件')
    parser.add_argument('--compare_with', help='对比的基础模式文件')

    args = parser.parse_args()

    # 分析活动
    analyze_claude_activity(args.predictions_file)

    # 对比
    if args.compare_with:
        compare_basic_vs_enhanced(args.compare_with, args.predictions_file)


if __name__ == '__main__':
    main()
