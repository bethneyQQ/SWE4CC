#!/usr/bin/env python3
"""
重新评估失败的实例

修复了patch格式问题后，重新运行evaluation。
可以选择性地重新评估特定类型的错误实例。
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from argparse import ArgumentParser

def load_error_instances(eval_report_path, log_dir):
    """加载错误实例并按类型分类"""
    with open(eval_report_path) as f:
        eval_data = json.load(f)

    error_ids = eval_data['error_ids']

    # 按错误类型分类
    categorized = {
        'malformed_patch': [],
        'docker_rate_limit': [],
        'patch_apply_failed': [],
        'unknown': []
    }

    for error_id in error_ids:
        log_file = Path(log_dir) / error_id / 'run_instance.log'
        if log_file.exists():
            content = log_file.read_text()

            if 'malformed patch' in content:
                categorized['malformed_patch'].append(error_id)
            elif 'Too Many Requests' in content or 'toomanyrequests' in content:
                categorized['docker_rate_limit'].append(error_id)
            elif 'Patch Apply Failed' in content:
                categorized['patch_apply_failed'].append(error_id)
            else:
                categorized['unknown'].append(error_id)

    return categorized, error_ids

def run_evaluation(predictions_path, instance_ids, output_dir, dataset, timeout=900):
    """运行SWE-bench评估"""

    # 构建命令
    cmd = [
        sys.executable, '-m', 'swebench.harness.run_evaluation',
        '-p', predictions_path,
        '-d', dataset,
        '-id', 'reevaluation',
        '-t', str(timeout),
    ]

    # 添加实例ID
    if instance_ids:
        cmd.extend(['--instance_ids'] + instance_ids)

    print(f"运行命令: {' '.join(cmd)}")
    print(f"评估 {len(instance_ids)} 个实例...")

    # 运行评估
    result = subprocess.run(cmd, capture_output=False, text=True)

    return result.returncode == 0

def generate_report(output_dir, original_errors):
    """生成重新评估报告"""
    eval_dir = Path(output_dir)

    results = {
        'original_error_count': len(original_errors),
        'reevaluated_count': 0,
        'completed': 0,
        'resolved': 0,
        'unresolved': 0,
        'still_failed': 0,
        'resolved_instances': [],
        'still_failed_instances': [],
        'error_types': {}
    }

    for instance_id in original_errors:
        instance_dir = eval_dir / instance_id
        if not instance_dir.exists():
            continue

        results['reevaluated_count'] += 1

        # 检查report.json
        report_file = instance_dir / 'report.json'
        if report_file.exists():
            with open(report_file) as f:
                report = json.load(f)
                if instance_id in report:
                    instance_report = report[instance_id]
                    results['completed'] += 1

                    if instance_report.get('resolved', False):
                        results['resolved'] += 1
                        results['resolved_instances'].append(instance_id)
                    else:
                        results['unresolved'] += 1
        else:
            # 检查是否仍然失败
            log_file = instance_dir / 'run_instance.log'
            if log_file.exists():
                content = log_file.read_text()
                if 'Error' in content or 'Failed' in content:
                    results['still_failed'] += 1
                    results['still_failed_instances'].append(instance_id)

                    # 分类错误类型
                    if 'malformed patch' in content:
                        results['error_types']['malformed_patch'] = \
                            results['error_types'].get('malformed_patch', 0) + 1
                    elif 'Patch Apply Failed' in content:
                        results['error_types']['patch_apply_failed'] = \
                            results['error_types'].get('patch_apply_failed', 0) + 1
                    elif 'Too Many Requests' in content:
                        results['error_types']['docker_rate_limit'] = \
                            results['error_types'].get('docker_rate_limit', 0) + 1

    # 计算改进率
    if results['reevaluated_count'] > 0:
        results['success_rate'] = (results['completed'] / results['reevaluated_count']) * 100
        if results['completed'] > 0:
            results['resolve_rate'] = (results['resolved'] / results['completed']) * 100
        else:
            results['resolve_rate'] = 0
    else:
        results['success_rate'] = 0
        results['resolve_rate'] = 0

    return results

def main():
    parser = ArgumentParser(description='重新评估失败的SWE-bench实例')
    parser.add_argument('--model', default='claude-3.5-sonnet', help='模型名称')
    parser.add_argument('--eval-report', help='原始评估报告路径')
    parser.add_argument('--predictions', help='预测文件路径')
    parser.add_argument('--log-dir', help='原始日志目录')
    parser.add_argument('--output-dir', help='输出目录')
    parser.add_argument('--dataset', default='princeton-nlp/SWE-bench_Lite', help='数据集')
    parser.add_argument('--type', choices=['all', 'malformed', 'docker', 'patch_failed'],
                       default='malformed', help='要重新评估的错误类型')
    parser.add_argument('--timeout', type=int, default=900, help='超时时间(秒)')
    parser.add_argument('--dry-run', action='store_true', help='仅显示将要评估的实例')
    parser.add_argument('-y', '--yes', action='store_true', help='跳过确认，直接开始评估')

    args = parser.parse_args()

    # 设置默认路径
    if not args.eval_report:
        args.eval_report = f'reports/{args.model}.full_eval.json'
    if not args.predictions:
        # 优先使用修复后的文件
        pred_path_fixed = f'results/{args.model}__SWE-bench_Lite_oracle__test.fixed.jsonl'
        pred_path1 = f'predictions/{args.model}.full_eval.jsonl'
        pred_path2 = f'results/{args.model}__SWE-bench_Lite_oracle__test.jsonl'
        if os.path.exists(pred_path_fixed):
            args.predictions = pred_path_fixed
        elif os.path.exists(pred_path1):
            args.predictions = pred_path1
        elif os.path.exists(pred_path2):
            args.predictions = pred_path2
        else:
            args.predictions = pred_path1  # 使用第一个作为默认，稍后会报错
    if not args.log_dir:
        args.log_dir = f'logs/run_evaluation/full_eval/{args.model}'
    if not args.output_dir:
        args.output_dir = f'logs/run_evaluation/reevaluation/{args.model}'

    # 检查文件存在性
    if not os.path.exists(args.eval_report):
        print(f"错误: 评估报告不存在: {args.eval_report}")
        return 1

    if not os.path.exists(args.predictions):
        print(f"错误: 预测文件不存在: {args.predictions}")
        return 1

    # 加载错误实例
    print("加载错误实例...")
    categorized, all_errors = load_error_instances(args.eval_report, args.log_dir)

    print(f"\n错误实例统计:")
    print(f"  总错误数: {len(all_errors)}")
    print(f"  - Malformed Patch: {len(categorized['malformed_patch'])}")
    print(f"  - Docker Rate Limit: {len(categorized['docker_rate_limit'])}")
    print(f"  - Patch Apply Failed: {len(categorized['patch_apply_failed'])}")
    print(f"  - Unknown: {len(categorized['unknown'])}")

    # 选择要重新评估的实例
    if args.type == 'all':
        instances_to_eval = all_errors
    elif args.type == 'malformed':
        instances_to_eval = categorized['malformed_patch']
    elif args.type == 'docker':
        instances_to_eval = categorized['docker_rate_limit']
    elif args.type == 'patch_failed':
        instances_to_eval = categorized['patch_apply_failed']

    print(f"\n将重新评估 {len(instances_to_eval)} 个 '{args.type}' 类型的实例")

    if args.dry_run:
        print("\n实例列表:")
        for i, instance_id in enumerate(instances_to_eval[:20], 1):
            print(f"  {i}. {instance_id}")
        if len(instances_to_eval) > 20:
            print(f"  ... 还有 {len(instances_to_eval) - 20} 个")
        return 0

    # 确认
    if not args.yes:
        response = input(f"\n确认重新评估? (y/n): ")
        if response.lower() != 'y':
            print("取消操作")
            return 0

    # 创建输出目录
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # 运行评估
    print(f"\n开始重新评估...")
    success = run_evaluation(
        args.predictions,
        instances_to_eval,
        args.output_dir,
        args.dataset,
        args.timeout
    )

    if not success:
        print("评估失败")
        return 1

    # 生成报告
    print("\n生成重新评估报告...")
    results = generate_report(args.output_dir, instances_to_eval)

    # 保存报告
    report_path = f'reports/{args.model}.reevaluation_{args.type}.json'
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)

    # 打印结果
    print("\n" + "="*80)
    print("重新评估结果")
    print("="*80)
    print(f"原始错误数: {results['original_error_count']}")
    print(f"实际评估数: {results['reevaluated_count']}")
    print(f"成功完成: {results['completed']} ({results['success_rate']:.1f}%)")
    print(f"  - 已解决: {results['resolved']}")
    print(f"  - 未解决: {results['unresolved']}")
    print(f"仍然失败: {results['still_failed']}")

    if results['error_types']:
        print(f"\n仍然失败的错误类型:")
        for error_type, count in results['error_types'].items():
            print(f"  - {error_type}: {count}")

    print(f"\n改进情况:")
    original_success = (300 - len(all_errors)) / 300 * 100
    new_success = (300 - len(all_errors) + results['completed']) / 300 * 100
    print(f"  原始成功率: {original_success:.1f}% ({300 - len(all_errors)}/300)")
    print(f"  修复后成功率: {new_success:.1f}% ({300 - len(all_errors) + results['completed']}/300)")
    print(f"  成功率提升: +{new_success - original_success:.1f}%")

    print(f"\n详细报告: {report_path}")
    print("="*80)

    return 0

if __name__ == '__main__':
    sys.exit(main())
