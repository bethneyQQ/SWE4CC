#!/usr/bin/env python3
"""
使用标准API模式重新运行空patch实例

不使用Claude Code工具，直接调用Anthropic API
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datasets import load_dataset
from anthropic import Anthropic
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# 简化版prompt - 基于SWE-bench最佳实践
PROMPT_TEMPLATE = """You are an expert software engineer tasked with fixing a bug in a codebase.

**Problem Statement:**
{problem_statement}

**Instructions:**
1. Analyze the problem carefully
2. Generate a patch in unified diff format to fix the issue
3. The patch must follow these format requirements:
   - Use unified diff format (--- a/file.py, +++ b/file.py)
   - Context lines MUST start with a space ` `
   - Deleted lines start with `-`
   - Added lines start with `+`
   - Include at least 3 lines of context before and after changes

**Output Format:**
Provide your analysis and then the complete patch in a code block.

Example patch format:
```diff
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -10,7 +10,8 @@
 def function(value):
     # Context line (note the leading space!)
-    old_code = value
+    new_code = value
+    additional_line = True
     return value
```

Generate the patch now:"""

def load_empty_patch_instances(pred_file):
    """从prediction文件中提取空patch的实例ID"""
    empty_ids = []

    with open(pred_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            if not data.get('model_patch', '').strip():
                empty_ids.append(data['instance_id'])

    return empty_ids

def extract_diff(text):
    """从文本中提取diff patch"""
    # 查找diff块
    lines = text.split('\n')
    diff_lines = []
    in_diff = False

    for line in lines:
        if line.startswith('--- ') or line.startswith('diff --git'):
            in_diff = True
        if in_diff:
            diff_lines.append(line)
        # diff块通常在遇到非diff行时结束（除了上下文）
        if in_diff and line and not any(line.startswith(p) for p in ['---', '+++', '@@', ' ', '+', '-', 'diff', 'index']):
            in_diff = False

    return '\n'.join(diff_lines) if diff_lines else ''

def call_anthropic_api(problem_statement, anthropic_client, model_name, temperature=0.2, max_tokens=8192):
    """调用Anthropic API"""
    prompt = PROMPT_TEMPLATE.format(problem_statement=problem_statement)

    try:
        response = anthropic_client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # 提取响应内容
        full_output = response.content[0].text

        # 计算成本
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Sonnet 4.5定价: $3/$15 per MTok
        cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)

        return full_output, cost

    except Exception as e:
        logger.error(f"API call failed: {e}")
        return None, 0

def main():
    parser = argparse.ArgumentParser(description='使用标准API重试空patch实例')

    parser.add_argument(
        '--predictions',
        default='/home/zqq/SWE4CC/results/claude-sonnet-4-5__SWE-bench_Lite_oracle__test.jsonl',
        help='原始predictions文件'
    )

    parser.add_argument(
        '--output-dir',
        default='/home/zqq/SWE4CC/results/retry_standard_api',
        help='输出目录'
    )

    parser.add_argument(
        '--model',
        default='claude-sonnet-4-5-20250929',
        help='模型名称'
    )

    parser.add_argument(
        '--dataset',
        default='princeton-nlp/SWE-bench_Lite',
        help='数据集名称'
    )

    parser.add_argument(
        '--smoke-test',
        action='store_true',
        help='只测试第一个实例'
    )

    args = parser.parse_args()

    # 检查API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print('❌ ANTHROPIC_API_KEY环境变量未设置')
        return 1

    # 初始化Anthropic客户端
    anthropic = Anthropic(api_key=api_key)
    logger.info(f"Using API key: {'*' * len(api_key[:-5])}{api_key[-5:]}")

    # 加载空patch实例
    print('=' * 70)
    print('加载空patch实例...')
    print('=' * 70)

    empty_ids = load_empty_patch_instances(args.predictions)
    print(f'找到 {len(empty_ids)} 个空patch实例')

    if args.smoke_test:
        empty_ids = empty_ids[:1]
        print(f'Smoke test模式: 只运行 {empty_ids[0]}')

    print()

    # 加载数据集
    print('加载数据集...')
    dataset = load_dataset(args.dataset, split='test')

    # 过滤出需要重试的实例
    filtered = dataset.filter(lambda x: x['instance_id'] in empty_ids)
    print(f'匹配到 {len(filtered)} 个实例')

    if len(filtered) == 0:
        print('❌ 没有匹配的实例')
        return 1

    print()

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f'{args.model}__SWE-bench_Lite__test__standard_api.jsonl'

    # 加载已处理的实例
    existing_ids = set()
    if output_file.exists():
        with open(output_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    existing_ids.add(data['instance_id'])
                except:
                    pass
        print(f'已处理 {len(existing_ids)} 个实例，将跳过')

    # 运行标准API inference
    print('=' * 70)
    print('使用标准API运行inference...')
    print('=' * 70)
    print(f'模型: {args.model}')
    print(f'总实例数: {len(filtered)}')
    print(f'待处理: {len(filtered) - len(existing_ids)}')
    print()

    total_cost = 0
    success_count = 0

    with open(output_file, 'a') as f:
        for datum in tqdm(filtered, desc='Standard API Inference'):
            instance_id = datum['instance_id']

            # 跳过已处理的实例
            if instance_id in existing_ids:
                continue

            problem_statement = datum['problem_statement']

            # 调用API
            full_output, cost = call_anthropic_api(
                problem_statement=problem_statement,
                anthropic_client=anthropic,
                model_name=args.model,
                temperature=0.2,
                max_tokens=8192
            )

            total_cost += cost

            # 提取patch
            model_patch = extract_diff(full_output) if full_output else ''

            if model_patch:
                success_count += 1

            # 保存结果
            output_dict = {
                'instance_id': instance_id,
                'model_name_or_path': args.model,
                'full_output': full_output or '',
                'model_patch': model_patch,
                'cost': cost,
                'mode': 'standard_api'
            }

            f.write(json.dumps(output_dict) + '\n')
            f.flush()

            logger.info(f'{instance_id}: patch={"✓" if model_patch else "✗"}, cost=${cost:.4f}')

    # 输出统计
    print()
    print('=' * 70)
    print('✅ 运行完成')
    print('=' * 70)
    print(f'输出文件: {output_file}')
    print(f'总实例数: {len(filtered)}')
    print(f'成功生成patch: {success_count}/{len(filtered)} ({success_count/len(filtered)*100:.1f}%)')
    print(f'总成本: ${total_cost:.2f}')
    print(f'平均成本: ${total_cost/len(filtered):.4f} per instance')

    if args.smoke_test and len(filtered) > 0:
        # 显示smoke test结果
        with open(output_file, 'r') as f:
            data = json.loads(f.readline())
            print()
            print('Smoke test结果:')
            print(f'  实例: {data["instance_id"]}')
            print(f'  有patch: {"✓" if data.get("model_patch") else "✗"}')
            if data.get('model_patch'):
                print(f'  Patch长度: {len(data["model_patch"])} 字符')
                print(f'  Patch预览:')
                print('  ' + '\n  '.join(data['model_patch'].split('\n')[:10]))

    return 0

if __name__ == '__main__':
    sys.exit(main())
