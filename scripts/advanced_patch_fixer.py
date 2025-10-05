#!/usr/bin/env python3
"""
高级Patch修复工具 - 修复71个malformed patch的格式问题

这个工具能处理更复杂的patch格式错误，包括：
1. 上下文行缺少前导空格
2. 空行缺少空格
3. markdown代码块标记
4. 注释或解释文本混入patch
"""

import json
import sys
import re
from pathlib import Path


def advanced_fix_patch(patch_str):
    """
    高级patch格式修复，处理复杂的格式问题
    """
    if not patch_str or not patch_str.strip():
        return patch_str

    # 1. 移除开头的markdown标记
    patch_str = re.sub(r'^```(?:diff|patch)?\n', '', patch_str, flags=re.MULTILINE)

    # 2. 移除结尾的markdown标记
    patch_str = re.sub(r'\n```\s*$', '', patch_str)

    # 3. 移除任何独立的```行
    lines = patch_str.split('\n')
    cleaned_lines = []

    in_hunk = False
    for line in lines:
        # 跳过markdown标记
        if line.strip() in ['```', '```diff', '```patch']:
            continue

        # 文件头
        if line.startswith('---') or line.startswith('+++'):
            in_hunk = False
            cleaned_lines.append(line)
            continue

        # diff命令行
        if line.startswith('diff '):
            in_hunk = False
            cleaned_lines.append(line)
            continue

        # Hunk header
        if line.startswith('@@'):
            in_hunk = True
            cleaned_lines.append(line)
            continue

        # 反斜杠行
        if line.startswith('\\'):
            cleaned_lines.append(line)
            continue

        # 在hunk中
        if in_hunk:
            if not line:
                # 空行在hunk中应该是' '（一个空格）
                cleaned_lines.append(' ')
            elif line[0] in ['+', '-', ' ']:
                # 已经有正确前导的行
                cleaned_lines.append(line)
            else:
                # 上下文行缺少前导空格
                # 但要排除可能的注释或解释文本
                # 判断：如果是Python缩进的代码，很可能是上下文行
                if line.startswith((' ', '\t')) or re.match(r'^\s*(def|class|import|from|if|for|while|return|#)', line):
                    cleaned_lines.append(' ' + line)
                else:
                    # 可能是注释或解释，跳过
                    continue
        else:
            # 不在hunk中，保留原样
            cleaned_lines.append(line)

    result = '\n'.join(cleaned_lines)

    # 确保以换行符结尾
    if result and not result.endswith('\n'):
        result += '\n'

    return result


def fix_predictions_file(input_file, output_file=None):
    """修复predictions文件中的所有patch"""

    input_path = Path(input_file)
    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}.advanced_fixed{input_path.suffix}"

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
                    fixed_patch = advanced_fix_patch(original_patch)

                    if original_patch != fixed_patch:
                        data['model_patch'] = fixed_patch
                        fixed_count += 1

                        # 显示前3个修复的示例
                        if fixed_count <= 3:
                            print(f"\n修复示例 #{fixed_count}: {data['instance_id']}")
                            print(f"  原patch长度: {len(original_patch)} → 修复后: {len(fixed_patch)}")

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
        print("用法: python3 advanced_patch_fixer.py <input_file> [output_file]")
        print("\n示例:")
        print("  python3 advanced_patch_fixer.py results/claude-sonnet-4-5__SWE-bench_Lite_oracle__test.jsonl")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(input_file).exists():
        print(f"错误: 文件不存在: {input_file}")
        sys.exit(1)

    fixed_file = fix_predictions_file(input_file, output_file)

    print(f"\n✅ Patch格式修复完成!")
    print(f"\n下一步: 使用修复后的文件重新评估")
