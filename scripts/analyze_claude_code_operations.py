#!/usr/bin/env python3
"""
分析Claude Code在inference过程中的所有操作
从response metadata中提取工具使用记录
"""
import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


def extract_tool_usage(response_data: Dict) -> List[Dict]:
    """
    从Claude Code响应中提取工具使用记录

    Claude Code的response结构:
    {
        "type": "result",
        "usage": {...},
        "modelUsage": {...},
        "tool_uses": [...]  # 可能的工具使用记录
    }
    """
    tool_uses = []

    # 方法1: 检查tool_uses字段
    if 'tool_uses' in response_data:
        tool_uses.extend(response_data['tool_uses'])

    # 方法2: 从usage中提取 (如果有server_tool_use)
    if 'usage' in response_data:
        usage = response_data['usage']
        if 'server_tool_use' in usage:
            # 这里可能包含工具使用统计
            pass

    # 方法3: 从完整响应中搜索工具调用模式
    # Claude可能在result文本中记录了工具使用

    return tool_uses


def analyze_predictions_file(predictions_file: str) -> Dict:
    """
    分析predictions文件中的Claude Code操作
    """
    stats = {
        'total_instances': 0,
        'instances_with_tools': 0,
        'tool_usage_by_type': defaultdict(int),
        'file_operations': defaultdict(list),
        'instances_details': []
    }

    with open(predictions_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            instance_id = data['instance_id']
            stats['total_instances'] += 1

            # 提取Claude Code metadata
            claude_meta = data.get('claude_code_meta', {})
            response_data = claude_meta.get('response_data', {})

            # 检查是否使用了增强模式
            is_enhanced = claude_meta.get('enhanced', False)
            has_tools = claude_meta.get('tools_available', False)

            instance_info = {
                'instance_id': instance_id,
                'enhanced': is_enhanced,
                'tools_available': has_tools,
                'tools_used': [],
                'files_accessed': [],
                'operations': []
            }

            # 提取工具使用
            tool_uses = extract_tool_usage(response_data)
            if tool_uses:
                stats['instances_with_tools'] += 1
                for tool_use in tool_uses:
                    tool_name = tool_use.get('name', 'unknown')
                    stats['tool_usage_by_type'][tool_name] += 1
                    instance_info['tools_used'].append(tool_use)

            # 尝试从full_output中提取操作信息
            full_output = data.get('full_output', '')
            if full_output:
                # 查找Read操作的痕迹
                import re

                # 模式1: "Reading file: path/to/file.py"
                read_patterns = [
                    r'Reading (?:file )?[\'"]?([^\'"\\n]+\.py)[\'"]?',
                    r'Read\([\'"]([^\'"\\n]+)[\'"\)]',
                    r'examining ([^\\s]+\.py)',
                    r'looking at ([^\\s]+\.py)',
                ]

                for pattern in read_patterns:
                    matches = re.findall(pattern, full_output, re.IGNORECASE)
                    for match in matches:
                        if match not in instance_info['files_accessed']:
                            instance_info['files_accessed'].append(match)
                            stats['file_operations'][match].append(instance_id)

                # 模式2: Bash操作
                bash_patterns = [
                    r'(?:Running|Executing) bash: (.+)',
                    r'`([^`]+)`',  # 代码块中的命令
                ]

                for pattern in bash_patterns:
                    matches = re.findall(pattern, full_output)
                    for match in matches[:5]:  # 限制数量
                        if any(cmd in match.lower() for cmd in ['ls', 'find', 'grep', 'cd', 'pwd']):
                            instance_info['operations'].append({
                                'type': 'bash',
                                'command': match
                            })

            # 从repo_path获取访问的仓库
            if 'repo_path' in data:
                instance_info['repo_path'] = data['repo_path']

            stats['instances_details'].append(instance_info)

    return stats


def print_summary(stats: Dict):
    """打印统计摘要"""
    print("=" * 80)
    print("Claude Code操作分析报告")
    print("=" * 80)

    print(f"\n📊 总体统计:")
    print(f"  总实例数: {stats['total_instances']}")
    print(f"  使用工具的实例: {stats['instances_with_tools']}")
    print(f"  工具使用率: {stats['instances_with_tools']/stats['total_instances']*100:.1f}%")

    print(f"\n🔧 工具使用统计:")
    if stats['tool_usage_by_type']:
        for tool, count in sorted(stats['tool_usage_by_type'].items(), key=lambda x: -x[1]):
            print(f"  {tool}: {count} 次")
    else:
        print("  (从metadata中未检测到显式的工具使用记录)")

    print(f"\n📁 文件访问统计:")
    if stats['file_operations']:
        print(f"  访问的文件总数: {len(stats['file_operations'])}")
        print(f"\n  热门文件 (Top 10):")
        sorted_files = sorted(stats['file_operations'].items(), key=lambda x: -len(x[1]))
        for file, instances in sorted_files[:10]:
            print(f"    {file}: {len(instances)} 个实例")
    else:
        print("  (从输出中未检测到明确的文件访问记录)")

    print(f"\n📋 实例详情:")
    for instance in stats['instances_details']:
        print(f"\n  🔹 {instance['instance_id']}")
        print(f"    增强模式: {'是' if instance['enhanced'] else '否'}")
        print(f"    工具可用: {'是' if instance['tools_available'] else '否'}")

        if instance['files_accessed']:
            print(f"    访问的文件: {len(instance['files_accessed'])} 个")
            for f in instance['files_accessed'][:3]:
                print(f"      - {f}")
            if len(instance['files_accessed']) > 3:
                print(f"      ... 还有 {len(instance['files_accessed']) - 3} 个")

        if instance['operations']:
            print(f"    执行的操作: {len(instance['operations'])} 个")
            for op in instance['operations'][:2]:
                print(f"      - {op['type']}: {op['command'][:60]}...")

        if 'repo_path' in instance:
            print(f"    仓库路径: {instance['repo_path']}")


def export_detailed_report(stats: Dict, output_file: str):
    """导出详细的JSON报告"""
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"\n💾 详细报告已保存至: {output_file}")


def check_actual_tool_usage(predictions_file: str):
    """
    检查实际的工具使用情况
    通过分析Claude的响应内容来推断工具使用
    """
    print("\n" + "=" * 80)
    print("🔍 深度分析: Claude Code工具使用推断")
    print("=" * 80)

    with open(predictions_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            data = json.loads(line)
            instance_id = data['instance_id']
            full_output = data.get('full_output', '')

            print(f"\n📌 Instance: {instance_id}")
            print("-" * 80)

            # 分析输出内容
            indicators = {
                'read_file': [
                    'I can see', 'Looking at', 'Reading', 'The file contains',
                    'examining the', 'After reading', 'Based on the file'
                ],
                'bash': [
                    'Running', 'Executing', 'Using bash', 'I ran', 'I executed',
                    'found the following', 'located in'
                ],
                'grep': [
                    'Searching for', 'I searched', 'grep shows', 'pattern match',
                    'I found these occurrences'
                ],
                'direct_answer': [
                    'Based on the problem', 'Here\'s the patch', 'The issue is',
                    'I can see you\'ve shared'  # 这个表示没用工具
                ]
            }

            detected_tools = []
            evidence = []

            for tool, patterns in indicators.items():
                for pattern in patterns:
                    if pattern.lower() in full_output.lower():
                        if tool not in detected_tools:
                            detected_tools.append(tool)
                        # 提取上下文
                        idx = full_output.lower().find(pattern.lower())
                        context = full_output[max(0, idx-20):min(len(full_output), idx+80)]
                        evidence.append({
                            'tool': tool,
                            'pattern': pattern,
                            'context': context.replace('\n', ' ')
                        })
                        break  # 找到一个就够了

            if detected_tools:
                print(f"  检测到的工具使用: {', '.join(detected_tools)}")
                print(f"\n  证据:")
                for ev in evidence[:3]:  # 只显示前3个
                    print(f"    [{ev['tool']}] ...{ev['context']}...")
            else:
                print(f"  ⚠️  未检测到明确的工具使用迹象")
                # 显示响应的开头
                preview = full_output[:200].replace('\n', ' ')
                print(f"  响应预览: {preview}...")


def main():
    parser = argparse.ArgumentParser(
        description='分析Claude Code的操作记录'
    )
    parser.add_argument(
        '--predictions_file',
        required=True,
        help='Predictions JSONL文件路径'
    )
    parser.add_argument(
        '--output',
        help='输出详细报告的JSON文件路径'
    )
    parser.add_argument(
        '--deep-analysis',
        action='store_true',
        help='启用深度分析（从响应内容推断工具使用）'
    )

    args = parser.parse_args()

    # 分析文件
    stats = analyze_predictions_file(args.predictions_file)

    # 打印摘要
    print_summary(stats)

    # 深度分析
    if args.deep_analysis:
        check_actual_tool_usage(args.predictions_file)

    # 导出报告
    if args.output:
        export_detailed_report(stats, args.output)

    print("\n" + "=" * 80)
    print("✅ 分析完成")
    print("=" * 80)


if __name__ == '__main__':
    main()
