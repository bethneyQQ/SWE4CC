#!/usr/bin/env python3
"""
重新运行空patch的实例

这些实例在第一次运行时产生了空的model_patch，需要重新生成
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datasets import load_dataset

def load_empty_patch_instances(pred_file):
    """从prediction文件中提取空patch的实例ID"""
    empty_ids = []

    with open(pred_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            if not data.get('model_patch', '').strip():
                empty_ids.append(data['instance_id'])

    return empty_ids

def main():
    parser = argparse.ArgumentParser(description='重新运行空patch实例')

    parser.add_argument(
        '--predictions',
        default='/home/zqq/SWE4CC/results/claude-sonnet-4-5__SWE-bench_Lite_oracle__test.jsonl',
        help='原始predictions文件'
    )

    parser.add_argument(
        '--output-dir',
        default='/home/zqq/SWE4CC/results/retry_empty',
        help='输出目录'
    )

    parser.add_argument(
        '--model',
        default='claude-4',
        help='模型名称 (对于Claude Code使用claude-4)'
    )

    parser.add_argument(
        '--dataset',
        default='princeton-nlp/SWE-bench_Lite',
        help='数据集名称'
    )

    parser.add_argument(
        '--max-workers',
        type=int,
        default=4,
        help='并发数'
    )

    parser.add_argument(
        '--smoke-test',
        action='store_true',
        help='只测试第一个实例'
    )

    args = parser.parse_args()

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

    # 创建临时数据集
    print('创建临时数据集...')
    dataset = load_dataset(args.dataset, split='test')

    # 过滤出需要重试的实例
    filtered = dataset.filter(lambda x: x['instance_id'] in empty_ids)

    print(f'匹配到 {len(filtered)} 个实例')

    if len(filtered) == 0:
        print('❌ 没有匹配的实例')
        return 1

    # 保存临时数据集（需要保存为带split的DatasetDict格式）
    temp_dir = '/tmp/swebench_empty_retry'
    Path(temp_dir).mkdir(parents=True, exist_ok=True)

    from datasets import DatasetDict
    dataset_dict = DatasetDict({'test': filtered})
    dataset_dict.save_to_disk(temp_dir)

    print(f'临时数据集保存到: {temp_dir}')
    print()

    # 运行inference
    print('=' * 70)
    print('运行inference...')
    print('=' * 70)

    # 使用run_claude_code.py (直接调用enhanced模式)
    cmd = [
        'python3', '-m', 'swebench.inference.run_claude_code',
        '--dataset_name_or_path', temp_dir,
        '--model_name_or_path', args.model,
        '--output_dir', args.output_dir
    ]

    print(f'命令: {" ".join(cmd)}')
    print()

    try:
        # 运行
        result = subprocess.run(cmd, check=True)

        print()
        print('=' * 70)
        print('✅ 运行完成')
        print('=' * 70)

        # 检查输出
        output_pattern = f'{args.model}__*__test*.jsonl'
        output_files = list(Path(args.output_dir).glob(output_pattern))

        if output_files:
            output_file = output_files[0]
            print(f'输出文件: {output_file}')

            # 统计结果
            with open(output_file, 'r') as f:
                lines = f.readlines()

            success_count = 0
            for line in lines:
                data = json.loads(line)
                if data.get('model_patch', '').strip():
                    success_count += 1

            print(f'成功生成patch: {success_count}/{len(lines)}')

            if args.smoke_test and lines:
                data = json.loads(lines[0])
                print()
                print('Smoke test结果:')
                print(f'  实例: {data["instance_id"]}')
                print(f'  有patch: {"✓" if data.get("model_patch") else "✗"}')
                if data.get('model_patch'):
                    print(f'  Patch长度: {len(data["model_patch"])} 字符')

        return 0

    except subprocess.CalledProcessError as e:
        print(f'❌ 运行失败: {e}')
        return 1
    except KeyboardInterrupt:
        print('⚠️ 用户中断')
        return 1

if __name__ == '__main__':
    sys.exit(main())
