#!/usr/bin/env python3
"""
合并原始predictions和标准API重试结果

将标准API生成的patch替换到原始predictions文件中
"""

import json
import sys
from pathlib import Path

def main():
    # 文件路径
    original_file = Path('/home/zqq/SWE4CC/results/claude-sonnet-4-5__SWE-bench_Lite_oracle__test.jsonl')
    standard_api_file = Path('/home/zqq/SWE4CC/results/retry_standard_api/claude-sonnet-4-5-20250929__SWE-bench_Lite__test__standard_api.jsonl')
    output_file = Path('/home/zqq/SWE4CC/results/claude-sonnet-4-5__SWE-bench_Lite_oracle__test.with_standard_api.jsonl')

    # 加载标准API结果
    print('加载标准API结果...')
    standard_api_results = {}
    with open(standard_api_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            instance_id = data['instance_id']
            standard_api_results[instance_id] = data

    print(f'找到 {len(standard_api_results)} 个标准API结果')

    # 处理原始文件
    print('处理原始predictions...')
    replaced_count = 0
    total_count = 0

    with open(original_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            data = json.loads(line)
            total_count += 1
            instance_id = data['instance_id']

            # 如果这个实例有标准API结果，替换它
            if instance_id in standard_api_results:
                api_result = standard_api_results[instance_id]

                # 保留原始的一些元数据
                merged = {
                    'instance_id': instance_id,
                    'model_name_or_path': data['model_name_or_path'],
                    'full_output': api_result['full_output'],
                    'model_patch': api_result['model_patch'],
                    'cost': api_result.get('cost', 0),
                    'mode': 'standard_api_retry',
                    'original_mode': 'enhanced_empty',
                    'standard_api_success': bool(api_result['model_patch'])
                }

                # 保留原始的claude_code_meta作为参考
                if 'claude_code_meta' in data:
                    merged['original_enhanced_meta'] = {
                        'enhanced': data['claude_code_meta'].get('enhanced'),
                        'attempts': data['claude_code_meta'].get('attempts'),
                        'num_turns': data['claude_code_meta'].get('response_data', {}).get('num_turns'),
                        'cost': data['claude_code_meta'].get('response_data', {}).get('total_cost_usd'),
                    }

                f_out.write(json.dumps(merged) + '\n')
                replaced_count += 1
                print(f'  ✓ {instance_id}: 替换为标准API结果')
            else:
                # 保留原始结果
                f_out.write(line)

    print()
    print('=' * 70)
    print('合并完成!')
    print('=' * 70)
    print(f'总实例数: {total_count}')
    print(f'替换的实例: {replaced_count}')
    print(f'输出文件: {output_file}')
    print()

    # 统计新文件中的patch情况
    with open(output_file, 'r') as f:
        lines = f.readlines()
        empty_count = 0
        valid_count = 0
        for line in lines:
            data = json.loads(line)
            if data.get('model_patch', '').strip():
                valid_count += 1
            else:
                empty_count += 1

    print('新文件统计:')
    print(f'  有效patch: {valid_count}')
    print(f'  空patch: {empty_count}')
    print(f'  总计: {len(lines)}')

    return 0

if __name__ == '__main__':
    sys.exit(main())
