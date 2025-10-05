#!/usr/bin/env python3
"""
正确的Unified Diff格式修复工具

修复Claude Code CLI生成的patch中的格式问题：
1. 上下文行缺少前导空格
2. 空行格式错误（应该是单个空格）
3. 移除markdown代码块标记
"""

import json
import sys
from pathlib import Path


def fix_unified_diff_format(patch_str):
    """
    修复unified diff格式问题

    Unified diff格式规则：
    - 文件头: --- 和 +++
    - Hunk header: @@ -x,y +a,b @@
    - 上下文行: 以单个空格' '开头
    - 添加行: 以'+'开头
    - 删除行: 以'-'开头
    - 空行: 在hunk中应该是单个空格' '
    - 反斜杠行: 以'\'开头
    """
    if not patch_str or not patch_str.strip():
        return patch_str

    # 1. 移除markdown代码块标记
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

        # 反斜杠行（"\ No newline at end of file"等）
        if line.startswith('\\'):
            cleaned_lines.append(line)
            continue

        # 在hunk中
        if in_hunk:
            # 空行 -> 单个空格
            if not line:
                cleaned_lines.append(' ')
            # 添加行（以+开头）
            elif line.startswith('+'):
                cleaned_lines.append(line)
            # 删除行（以-开头）
            elif line.startswith('-'):
                cleaned_lines.append(line)
            # 其他所有行都是上下文行，需要添加前导空格
            # 注意：不能用line[0] == ' '判断，因为Python代码的缩进空格会被误认为patch前导
            else:
                # CLI生成的上下文行没有patch前导空格，直接以代码内容开头
                cleaned_lines.append(' ' + line)
        else:
            # 不在hunk中，保留原样（如index行等）
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
        output_file = input_path.parent / f"{input_path.stem}.fixed{input_path.suffix}"

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
                    fixed_patch = fix_unified_diff_format(original_patch)

                    if original_patch != fixed_patch:
                        data['model_patch'] = fixed_patch
                        fixed_count += 1

                        # 显示前3个修复的示例
                        if fixed_count <= 3:
                            print(f"\n修复示例 #{fixed_count}: {data['instance_id']}")
                            print(f"  原patch长度: {len(original_patch)} → 修复后: {len(fixed_patch)}")
                            print(f"  长度变化: +{len(fixed_patch) - len(original_patch)} 字符")

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
        print("用法: python3 fix_unified_diff_format.py <input_file> [output_file]")
        print("\n示例:")
        print("  python3 fix_unified_diff_format.py results/predictions.jsonl")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(input_file).exists():
        print(f"错误: 文件不存在: {input_file}")
        sys.exit(1)

    fixed_file = fix_predictions_file(input_file, output_file)

    print(f"\n✅ Patch格式修复完成!")
    print(f"\n下一步: 使用修复后的文件重新评估")
