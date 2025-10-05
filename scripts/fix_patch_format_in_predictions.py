#!/usr/bin/env python3
"""
真正修复predictions文件中的patch格式

在每个patch的上下文行前添加空格（在@@ @@行之后的非+/-开头的行）
"""

import json
import sys
from pathlib import Path

def fix_patch_format(patch_str):
    """
    修复patch字符串，为上下文行添加前导空格

    规则：
    - 在@@ @@行之后
    - 不以+、-、@、\开头的行
    - 不是文件头（---、+++）
    - 添加一个空格前缀
    - 去除开头的空行
    - 确保以换行符结尾
    """
    if not patch_str:
        return patch_str

    # 去除开头的空白，但保留结尾换行符
    patch_str = patch_str.lstrip()

    lines = patch_str.split('\n')
    fixed_lines = []
    in_hunk = False

    for line in lines:
        # 文件头，不修改
        if line.startswith('---') or line.startswith('+++'):
            in_hunk = False
            fixed_lines.append(line)
            continue

        # Hunk开始
        if line.startswith('@@'):
            in_hunk = True
            fixed_lines.append(line)
            continue

        # diff命令行
        if line.startswith('diff '):
            in_hunk = False
            fixed_lines.append(line)
            continue

        # 在hunk中
        if in_hunk:
            if not line:
                # 空行在hunk中也是上下文，需要前导空格
                fixed_lines.append(' ')
            elif line[0] in ['+', '-', ' ', '\\']:
                # 已经有正确前缀
                fixed_lines.append(line)
            else:
                # 上下文行缺少前导空格
                fixed_lines.append(' ' + line)
        else:
            # 不在hunk中，不修改
            fixed_lines.append(line)

    result = '\n'.join(fixed_lines)

    # 确保以换行符结尾（如果原始patch有的话）
    if patch_str.endswith('\n') and not result.endswith('\n'):
        result += '\n'

    return result

def fix_predictions_file(input_file, output_file=None):
    """修复predictions文件"""

    input_path = Path(input_file)
    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}.patched{input_path.suffix}"

    print(f"读取: {input_file}")
    print(f"输出: {output_file}")

    fixed_count = 0
    total_count = 0

    with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
        for line_num, line in enumerate(fin, 1):
            try:
                data = json.loads(line)
                total_count += 1

                # 修复model_patch
                if 'model_patch' in data and data['model_patch']:
                    original_patch = data['model_patch']
                    fixed_patch = fix_patch_format(original_patch)

                    if original_patch != fixed_patch:
                        data['model_patch'] = fixed_patch
                        fixed_count += 1

                        # 显示前3个修复的示例
                        if fixed_count <= 3:
                            print(f"\n修复实例 #{fixed_count}: {data['instance_id']}")
                            print(f"  原patch前5行:")
                            for i, l in enumerate(original_patch.split('\n')[:5], 1):
                                print(f"    {i}: {repr(l)}")
                            print(f"  修复后前5行:")
                            for i, l in enumerate(fixed_patch.split('\n')[:5], 1):
                                print(f"    {i}: {repr(l)}")

                # 写入
                fout.write(json.dumps(data) + '\n')

            except json.JSONDecodeError as e:
                print(f"警告: 第{line_num}行JSON解析失败: {e}")
                continue

    print(f"\n{'='*60}")
    print(f"完成!")
    print(f"  总实例数: {total_count}")
    print(f"  修复数量: {fixed_count}")
    print(f"  修复率: {fixed_count/total_count*100:.1f}%")
    print(f"\n新文件: {output_file}")
    print(f"{'='*60}")

    return str(output_file)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 fix_patch_format_in_predictions.py <input_file> [output_file]")
        print("\n示例:")
        print("  python3 fix_patch_format_in_predictions.py results/claude-3.5-sonnet__SWE-bench_Lite_oracle__test.jsonl")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(input_file).exists():
        print(f"错误: 文件不存在: {input_file}")
        sys.exit(1)

    fixed_file = fix_predictions_file(input_file, output_file)

    print(f"\n✅ Patch格式修复完成!")
    print(f"\n下一步: 使用修复后的文件重新评估")
    print(f"  python3 scripts/reevaluate_failed_instances.py \\")
    print(f"    --predictions {fixed_file} \\")
    print(f"    --type malformed \\")
    print(f"    -y")
