#!/usr/bin/env python3
"""
为指定的实例运行Claude Code inference

用法:
    python3 scripts/run_single_instances.py \
        --instance_ids "id1,id2,id3" \
        --model claude-3.5-sonnet \
        --output_dir results/test
"""

import json
import argparse
from pathlib import Path
from datasets import load_dataset
from tqdm import tqdm
import sys
import os

# 添加swebench到path
sys.path.insert(0, str(Path(__file__).parent.parent))

from swebench.inference.run_claude_code import (
    prepare_claude_code_prompt,
    call_claude_code,
    check_claude_code_availability
)
from swebench.inference.make_datasets.utils import extract_diff


def main():
    parser = argparse.ArgumentParser(description='Run Claude Code inference on specific instances')
    parser.add_argument('--instance_ids', required=True, help='Comma-separated instance IDs')
    parser.add_argument('--model', default='claude-3.5-sonnet', help='Model name')
    parser.add_argument('--output_dir', required=True, help='Output directory')
    parser.add_argument('--dataset', default='princeton-nlp/SWE-bench_Lite', help='Dataset name')
    parser.add_argument('--split', default='test', help='Dataset split')

    args = parser.parse_args()

    # Parse instance IDs
    instance_ids = set(args.instance_ids.split(','))
    print(f"🎯 目标实例: {len(instance_ids)} 个")
    for iid in sorted(instance_ids):
        print(f"  - {iid}")

    # Check Claude Code availability
    if not check_claude_code_availability():
        print("❌ Claude Code CLI不可用")
        return 1

    # Check API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY环境变量未设置")
        return 1

    # Load dataset
    print(f"\n📚 加载数据集: {args.dataset} ({args.split})")
    dataset = load_dataset(args.dataset, split=args.split)

    # Filter to target instances
    filtered_data = [item for item in dataset if item['instance_id'] in instance_ids]
    print(f"✅ 找到 {len(filtered_data)}/{len(instance_ids)} 个实例")

    if len(filtered_data) < len(instance_ids):
        missing = instance_ids - {item['instance_id'] for item in filtered_data}
        print(f"⚠️  未找到的实例: {missing}")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"claude-3.5-sonnet__SWE-bench_Lite__test.jsonl"

    # Map model names
    model_name_mapping = {
        "claude-3-haiku": "haiku",
        "claude-3-sonnet": "sonnet",
        "claude-3-opus": "opus",
        "claude-3.5-sonnet": "sonnet",
        "claude-code": "sonnet",
        "claude-4": "sonnet",
    }
    actual_model_name = model_name_mapping.get(args.model, args.model)

    print(f"\n🚀 开始生成predictions...")
    print(f"   模型: {args.model} → {actual_model_name}")
    print(f"   输出: {output_file}\n")

    total_cost = 0.0
    successful = 0

    with open(output_file, 'w') as f:
        for datum in tqdm(filtered_data, desc="Processing"):
            instance_id = datum['instance_id']

            # Prepare prompt with NEW enhanced version
            prompt = prepare_claude_code_prompt(datum)

            # Call Claude Code
            import time
            start_time = time.time()

            response_data = call_claude_code(
                prompt=prompt,
                model_name=actual_model_name,
                timeout=300,
                max_tokens=8192,
                temperature=0.1
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response_data is None:
                print(f"❌ {instance_id}: Claude Code调用失败")
                # 写入空结果
                result = {
                    'instance_id': instance_id,
                    'model_patch': '',
                    'model_name_or_path': args.model,
                    'full_output': 'ERROR: Claude Code call failed',
                    'cost': 0.0,
                    'latency_ms': latency_ms,
                }
            else:
                # Extract patch from response
                # Claude Code CLI returns content in 'result' field
                full_output = response_data.get('result', response_data.get('content', ''))

                # Extract diff using existing utility
                try:
                    model_patch = extract_diff(full_output)
                except Exception as e:
                    print(f"⚠️  {instance_id}: Patch提取失败: {e}")
                    model_patch = ''

                # Estimate cost (rough approximation)
                input_tokens = len(prompt) // 4  # Rough estimate
                output_tokens = len(full_output) // 4
                cost = (input_tokens * 3 + output_tokens * 15) / 1_000_000  # Claude 3.5 Sonnet pricing

                total_cost += cost

                result = {
                    'instance_id': instance_id,
                    'model_patch': model_patch,
                    'model_name_or_path': args.model,
                    'full_output': full_output,
                    'cost': cost,
                    'latency_ms': latency_ms,
                    'claude_code_meta': {
                        'model': actual_model_name,
                        'response_data': response_data
                    }
                }

                if model_patch:
                    successful += 1
                    print(f"✅ {instance_id}: Patch生成成功 ({len(model_patch)} bytes, ${cost:.4f})")
                else:
                    print(f"⚠️  {instance_id}: Patch为空")

            # Write result
            f.write(json.dumps(result) + '\n')
            f.flush()

    print(f"\n{'='*60}")
    print(f"✅ 完成!")
    print(f"   成功: {successful}/{len(filtered_data)}")
    print(f"   总成本: ${total_cost:.4f}")
    print(f"   输出文件: {output_file}")
    print(f"{'='*60}\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
