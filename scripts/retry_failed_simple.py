#!/usr/bin/env python3
"""
简化版重试脚本 - 直接调用run_api.py处理特定实例

创建临时数据集文件，只包含失败的实例
"""

import argparse
import json
import sys
import subprocess
from pathlib import Path
from datasets import Dataset, DatasetDict

def create_temp_dataset(failed_instances, original_dataset_name, temp_path):
    """创建只包含失败实例的临时数据集"""
    from datasets import load_dataset

    print(f"加载原始数据集: {original_dataset_name}")
    dataset = load_dataset(original_dataset_name, split="test")

    # 过滤出失败的实例
    filtered = dataset.filter(lambda x: x['instance_id'] in failed_instances)

    print(f"原始数据集: {len(dataset)} 实例")
    print(f"失败实例: {len(failed_instances)} 个")
    print(f"匹配到: {len(filtered)} 实例")

    # 保存为临时数据集
    temp_path = Path(temp_path)
    temp_path.mkdir(parents=True, exist_ok=True)

    filtered.save_to_disk(str(temp_path))
    print(f"临时数据集已保存到: {temp_path}")

    return len(filtered)

def main():
    parser = argparse.ArgumentParser(description='重试失败实例 - 简化版')

    parser.add_argument('--failed-file',
                       default='/home/zqq/SWE4CC/failed_instances.txt',
                       help='失败实例ID列表文件')

    parser.add_argument('--smoke-test', action='store_true',
                       help='只测试第一个实例')

    parser.add_argument('--output-dir',
                       default='/home/zqq/SWE4CC/results/retry',
                       help='输出目录')

    parser.add_argument('--model',
                       default='claude-sonnet-4-5',
                       help='模型名称')

    args = parser.parse_args()

    # 加载失败实例列表
    with open(args.failed_file, 'r') as f:
        failed_instances = [line.strip() for line in f if line.strip()]

    if args.smoke_test:
        print("=" * 70)
        print("🧪 SMOKE TEST MODE")
        print("=" * 70)
        failed_instances = failed_instances[:1]
        print(f"只测试第一个实例: {failed_instances[0]}\n")
    else:
        print(f"将重试 {len(failed_instances)} 个失败实例\n")

    # 创建临时数据集
    temp_dataset_path = '/tmp/swebench_retry_dataset'
    count = create_temp_dataset(
        set(failed_instances),
        'princeton-nlp/SWE-bench_Lite',
        temp_dataset_path
    )

    if count == 0:
        print("❌ 没有找到匹配的实例")
        return 1

    # 运行run_api.py
    print("\n" + "=" * 70)
    print("运行inference...")
    print("=" * 70)

    cmd = [
        'python3', '-m', 'swebench.inference.run_api',
        '--dataset_name_or_path', temp_dataset_path,
        '--model_name_or_path', args.model,
        '--output_dir', args.output_dir
    ]

    print(f"命令: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True)

        print("\n" + "=" * 70)
        print("✅ 完成!")
        print("=" * 70)

        # 检查输出
        output_file = Path(args.output_dir) / f"{args.model}__SWE-bench_Lite__test__default.jsonl"
        if output_file.exists():
            with open(output_file, 'r') as f:
                lines = f.readlines()
            print(f"\n生成了 {len(lines)} 个结果")
            print(f"输出文件: {output_file}")

            # 如果是smoke test，显示结果
            if args.smoke_test and lines:
                data = json.loads(lines[0])
                has_patch = bool(data.get('model_patch', '').strip())
                print(f"\nSmoke test结果:")
                print(f"  instance_id: {data['instance_id']}")
                print(f"  有patch: {'✓' if has_patch else '✗'}")
                if has_patch:
                    print(f"  patch长度: {len(data['model_patch'])} 字符")

        return 0

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 运行失败: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
        return 1

if __name__ == '__main__':
    sys.exit(main())
