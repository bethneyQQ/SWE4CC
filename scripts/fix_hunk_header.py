#!/usr/bin/env python3
"""
修复Claude Code CLI生成的patch中hunk header行数错误的问题

问题：CLI生成的@@ -old_start,old_lines +new_start,new_lines @@中的行数
与实际patch内容不匹配，导致patch命令报malformed错误。

修复：重新计算每个hunk的实际行数，更新hunk header。
"""

import json
import sys
import re
from pathlib import Path


def fix_hunk_headers(patch_str):
    """
    修复patch中所有hunk header的行数声明

    规则：
    - 上下文行（以' '开头且非空）：计入旧+新
    - 删除行（以'-'开头）：只计入旧
    - 添加行（以'+'开头）：只计入新
    - 空行（完全空或换行）：不计数
    - 单空格行（表示空行）：计入旧+新
    """
    if not patch_str or not patch_str.strip():
        return patch_str

    lines = patch_str.split('\n')
    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 检查是否是hunk header
        if line.startswith('@@'):
            # 解析hunk header
            match = re.match(r'(@@ -)(\d+)(,\d+)? (\+)(\d+)(,\d+)?( @@.*)', line)
            if match:
                old_start = match.group(2)
                new_start = match.group(5)
                header_suffix = match.group(7)

                # 收集这个hunk的所有内容行
                hunk_lines = []
                j = i + 1
                while j < len(lines):
                    # 遇到下一个hunk header或文件头就停止
                    if lines[j].startswith('@@'):
                        break
                    if lines[j].startswith('---') or lines[j].startswith('+++'):
                        break
                    if lines[j].startswith('diff '):
                        break
                    hunk_lines.append(lines[j])
                    j += 1

                # 计算实际行数
                old_lines = 0
                new_lines = 0

                for hline in hunk_lines:
                    if not hline:  # 完全空行，不计数
                        continue
                    elif hline == ' ':  # 单空格（空行的正确表示），计入旧+新
                        old_lines += 1
                        new_lines += 1
                    elif hline.startswith('+'):
                        new_lines += 1
                    elif hline.startswith('-'):
                        old_lines += 1
                    elif hline.startswith(' '):  # 上下文行
                        old_lines += 1
                        new_lines += 1
                    elif hline.startswith('\\'):  # "\ No newline at end of file"等，不计数
                        continue
                    else:
                        # 其他情况（理论上不应出现），计入上下文
                        old_lines += 1
                        new_lines += 1

                # 生成新的hunk header
                new_header = f"@@ -{old_start},{old_lines} +{new_start},{new_lines}{header_suffix}"
                result_lines.append(new_header)

                # 添加hunk内容
                result_lines.extend(hunk_lines)

                i = j
            else:
                # hunk header格式无法解析，保留原样
                result_lines.append(line)
                i += 1
        else:
            result_lines.append(line)
            i += 1

    return '\n'.join(result_lines)


def fix_predictions_file(input_file, output_file=None):
    """修复predictions文件中所有patch的hunk header"""

    input_path = Path(input_file)
    if output_file is None:
        output_file = input_path.parent / f"{input_path.stem}.hunk_fixed{input_path.suffix}"

    print(f"读取: {input_file}")
    print(f"输出: {output_file}")

    fixed_count = 0
    total_count = 0
    total_hunks_fixed = 0

    with open(input_file, 'r') as fin, open(output_file, 'w') as fout:
        for line_num, line in enumerate(fin, 1):
            try:
                data = json.loads(line)
                total_count += 1

                # 修复model_patch
                if 'model_patch' in data and data['model_patch']:
                    original_patch = data['model_patch']
                    fixed_patch = fix_hunk_headers(original_patch)

                    if original_patch != fixed_patch:
                        data['model_patch'] = fixed_patch
                        fixed_count += 1

                        # 统计修复了多少个hunk
                        hunks_in_patch = original_patch.count('\n@@')
                        total_hunks_fixed += hunks_in_patch

                        # 显示前3个修复的示例
                        if fixed_count <= 3:
                            print(f"\n修复示例 #{fixed_count}: {data['instance_id']}")
                            print(f"  修复了 {hunks_in_patch} 个hunk header")

                # 写入
                fout.write(json.dumps(data) + '\n')

            except json.JSONDecodeError as e:
                print(f"警告: 第{line_num}行JSON解析失败: {e}")
                continue

    print(f"\n{'='*60}")
    print(f"完成!")
    print(f"  总实例数: {total_count}")
    print(f"  修复实例数: {fixed_count} ({fixed_count/total_count*100:.1f}%)")
    print(f"  修复hunk总数: {total_hunks_fixed}")
    print(f"\n新文件: {output_file}")
    print(f"{'='*60}")

    return str(output_file)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 fix_hunk_header.py <input_file> [output_file]")
        print("\n示例:")
        print("  python3 fix_hunk_header.py results/predictions.jsonl")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(input_file).exists():
        print(f"错误: 文件不存在: {input_file}")
        sys.exit(1)

    fixed_file = fix_predictions_file(input_file, output_file)

    print(f"\n✅ Hunk header修复完成!")
    print(f"\n下一步: 使用修复后的文件重新评估")
