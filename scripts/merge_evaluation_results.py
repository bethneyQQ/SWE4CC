#!/usr/bin/env python3
"""
合并原始评估结果和重新评估结果

将重新评估中成功的实例更新到原始评估报告中
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def merge_results(original_report, reevaluation_report, output_file=None):
    """
    合并评估结果

    Args:
        original_report: 原始完整评估报告路径
        reevaluation_report: 重新评估报告路径
        output_file: 输出文件路径（可选）
    """

    print(f"读取原始报告: {original_report}")
    with open(original_report, 'r') as f:
        original = json.load(f)

    print(f"读取重新评估报告: {reevaluation_report}")
    with open(reevaluation_report, 'r') as f:
        reevaluation = json.load(f)

    # 创建实例ID到结果的映射
    instance_results = {}

    # 先加载原始结果
    for instance_id, result in original.items():
        if instance_id not in ['total_instances', 'completed_instances', 'resolved_instances',
                                'unresolved_instances', 'error_instances', 'empty_patch_instances',
                                'incomplete_instances', 'report_file']:
            instance_results[instance_id] = result

    # 用重新评估的结果覆盖（如果更好的话）
    updated_count = 0
    newly_resolved = []

    for instance_id, result in reevaluation.items():
        if instance_id in ['total_instances', 'completed_instances', 'resolved_instances',
                          'unresolved_instances', 'error_instances', 'empty_patch_instances',
                          'incomplete_instances', 'report_file']:
            continue

        if instance_id in instance_results:
            old_result = instance_results[instance_id]

            # 检查是否从错误变为成功
            old_status = old_result.get('status', 'error')
            new_status = result.get('status', 'error')

            # 如果新结果更好（从error变为resolved/unresolved），则更新
            if old_status == 'error' and new_status in ['resolved', 'unresolved']:
                instance_results[instance_id] = result
                updated_count += 1
                if new_status == 'resolved':
                    newly_resolved.append(instance_id)
                print(f"  ✓ {instance_id}: {old_status} -> {new_status}")
            # 如果新结果从unresolved变为resolved，也更新
            elif old_status == 'unresolved' and new_status == 'resolved':
                instance_results[instance_id] = result
                updated_count += 1
                newly_resolved.append(instance_id)
                print(f"  ✓ {instance_id}: {old_status} -> {new_status}")

    # 统计合并后的结果
    stats = defaultdict(int)
    for instance_id, result in instance_results.items():
        status = result.get('status', 'error')
        stats[status] += 1

    # 构建合并后的报告
    merged = instance_results.copy()
    merged['total_instances'] = len(instance_results)
    merged['completed_instances'] = stats['resolved'] + stats['unresolved']
    merged['resolved_instances'] = stats['resolved']
    merged['unresolved_instances'] = stats['unresolved']
    merged['error_instances'] = stats['error']
    merged['empty_patch_instances'] = stats.get('empty_patch', 0)
    merged['incomplete_instances'] = stats.get('incomplete', 0)

    # 输出文件
    if output_file is None:
        original_path = Path(original_report)
        output_file = original_path.parent / f"{original_path.stem}.merged{original_path.suffix}"

    merged['report_file'] = str(output_file)

    with open(output_file, 'w') as f:
        json.dump(merged, f, indent=2)

    # 打印统计信息
    print("\n" + "="*80)
    print("合并结果统计")
    print("="*80)
    print(f"总实例数: {merged['total_instances']}")
    print(f"完成评估: {merged['completed_instances']} ({merged['completed_instances']/merged['total_instances']*100:.1f}%)")
    print(f"  - 已解决: {merged['resolved_instances']}")
    print(f"  - 未解决: {merged['unresolved_instances']}")
    print(f"错误实例: {merged['error_instances']}")
    print(f"空patch: {merged['empty_patch_instances']}")
    print(f"\n从重新评估中更新了 {updated_count} 个实例")
    if newly_resolved:
        print(f"新解决的实例数: {len(newly_resolved)}")
        print(f"  {', '.join(newly_resolved[:10])}")
        if len(newly_resolved) > 10:
            print(f"  ... 还有 {len(newly_resolved)-10} 个")

    print(f"\n合并后的报告: {output_file}")
    print("="*80)

    return str(output_file)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 merge_evaluation_results.py <original_report> <reevaluation_report> [output_file]")
        print("\n示例:")
        print("  python3 merge_evaluation_results.py \\")
        print("    reports/claude-3.5-sonnet.full_eval.json \\")
        print("    reports/claude-3.5-sonnet.reevaluation_malformed.json")
        sys.exit(1)

    original = sys.argv[1]
    reevaluation = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else None

    if not Path(original).exists():
        print(f"错误: 原始报告不存在: {original}")
        sys.exit(1)

    if not Path(reevaluation).exists():
        print(f"错误: 重新评估报告不存在: {reevaluation}")
        sys.exit(1)

    merged_file = merge_results(original, reevaluation, output)
    print(f"\n✅ 合并完成: {merged_file}")
