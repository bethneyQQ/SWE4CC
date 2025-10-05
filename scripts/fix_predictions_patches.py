#!/usr/bin/env python3
"""
修复predictions文件中的patch格式

读取现有的predictions文件，应用patch格式修复，生成新文件
"""

import json
import sys
from pathlib import Path
from swebench.inference.make_datasets.utils import fix_patch_context_lines

def fix_predictions_file(input_file, output_file=None):
    """修复predictions文件中所有的patch"""

    if output_file is None:
        # 创建新文件名：original_name.fixed.jsonl
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}.fixed{input_path.suffix}"

    print(f"读取: {input_file}")
    print(f"输出: {output_file}")

    fixed_count = 0
    total_count = 0

    with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
        for line in fin:
            total_count += 1
            data = json.loads(line)

            # 修复model_patch
            if 'model_patch' in data and data['model_patch']:
                original_patch = data['model_patch']
                fixed_patch = fix_patch_context_lines(original_patch)

                # 检查是否有变化
                if original_patch != fixed_patch:
                    data['model_patch'] = fixed_patch
                    fixed_count += 1
                    if fixed_count <= 3:
                        print(f"  修复实例: {data['instance_id']}")

            # 写入修复后的数据
            fout.write(json.dumps(data) + '\n')

    print(f"\n完成!")
    print(f"  总实例数: {total_count}")
    print(f"  修复数量: {fixed_count}")
    print(f"  修复率: {fixed_count/total_count*100:.1f}%")
    print(f"\n新文件: {output_file}")

    return str(output_file)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 fix_predictions_patches.py <input_file> [output_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    fixed_file = fix_predictions_file(input_file, output_file)

    print(f"\n下一步:")
    print(f"  使用修复后的文件重新评估:")
    print(f"  python3 -m swebench.harness.run_evaluation \\")
    print(f"    -p {fixed_file} \\")
    print(f"    -d princeton-nlp/SWE-bench_Lite \\")
    print(f"    -id reevaluation_fixed \\")
    print(f"    -i <instance_ids>")
