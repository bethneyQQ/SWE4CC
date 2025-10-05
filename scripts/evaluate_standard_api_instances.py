#!/usr/bin/env python3
"""
只评估标准API重试的39个实例
"""

import json
import subprocess
import sys
from pathlib import Path
from datasets import load_dataset, DatasetDict

def main():
    # 加载标准API结果，获取instance IDs
    standard_api_file = Path('/home/zqq/SWE4CC/results/retry_standard_api/claude-sonnet-4-5-20250929__SWE-bench_Lite__test__standard_api.jsonl')

    instance_ids = []
    with open(standard_api_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            instance_ids.append(data['instance_id'])

    print(f'找到 {len(instance_ids)} 个标准API实例需要评估')
    print()

    # 创建临时数据集（只包含这39个实例）
    print('加载原始数据集...')
    dataset = load_dataset('princeton-nlp/SWE-bench_Lite', split='test')

    # 过滤
    filtered = dataset.filter(lambda x: x['instance_id'] in instance_ids)
    print(f'匹配到 {len(filtered)} 个实例')

    # 保存为临时数据集
    temp_dir = '/tmp/swebench_standard_api_eval'
    Path(temp_dir).mkdir(parents=True, exist_ok=True)

    dataset_dict = DatasetDict({'test': filtered})
    dataset_dict.save_to_disk(temp_dir)
    print(f'临时数据集保存到: {temp_dir}')
    print()

    # 创建只包含这39个实例的prediction文件
    merged_file = Path('/home/zqq/SWE4CC/results/claude-sonnet-4-5__SWE-bench_Lite_oracle__test.with_standard_api.jsonl')
    temp_pred_file = Path('/tmp/swebench_standard_api_predictions.jsonl')

    with open(merged_file, 'r') as f_in, open(temp_pred_file, 'w') as f_out:
        for line in f_in:
            data = json.loads(line)
            if data['instance_id'] in instance_ids:
                f_out.write(line)

    print(f'临时predictions文件: {temp_pred_file}')
    print()

    # 运行evaluation
    print('=' * 70)
    print('运行SWE-bench evaluation (仅39个标准API实例)...')
    print('=' * 70)
    print()

    cmd = [
        'python', '-m', 'swebench.harness.run_evaluation',
        '--dataset_name', temp_dir,
        '--predictions_path', str(temp_pred_file),
        '--max_workers', '2',
        '--run_id', 'standard-api-retry',
        '--report_dir', '/home/zqq/SWE4CC/reports'
    ]

    print(f'命令: {" ".join(cmd)}')
    print()

    try:
        result = subprocess.run(cmd, check=True)
        print()
        print('=' * 70)
        print('✅ Evaluation完成!')
        print('=' * 70)
        print()
        print('报告目录: /home/zqq/SWE4CC/reports/standard-api-retry/')
        return 0
    except subprocess.CalledProcessError as e:
        print(f'❌ Evaluation失败: {e}')
        return 1

if __name__ == '__main__':
    sys.exit(main())
