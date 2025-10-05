#!/usr/bin/env python3
"""
测试新Prompt在失败实例上的效果

用法:
    python3 scripts/test_new_prompt.py --sample-size 10 --error-type all
"""

import json
import argparse
import random
from pathlib import Path
from collections import defaultdict


def load_error_instances(eval_report_path):
    """加载错误实例并按类型分类"""
    with open(eval_report_path) as f:
        eval_data = json.load(f)

    # 从日志目录分析错误类型
    log_dir = Path("logs/run_evaluation/full_eval/claude-3.5-sonnet")

    error_types = {
        'format_errors': [],
        'application_errors': [],
        'test_failures': [],
        'docker_errors': [],
    }

    for instance_id in eval_data.get('error_ids', []):
        log_file = log_dir / instance_id / "run_instance.log"
        if not log_file.exists():
            continue

        log_content = log_file.read_text(errors='ignore')

        if 'malformed patch' in log_content:
            error_types['format_errors'].append(instance_id)
        elif 'Patch Apply Failed' in log_content:
            error_types['application_errors'].append(instance_id)
        elif 'Too Many Requests' in log_content or 'toomanyrequests' in log_content:
            error_types['docker_errors'].append(instance_id)

    # 测试失败
    for instance_id in eval_data.get('unresolved_ids', []):
        log_file = log_dir / instance_id / "run_instance.log"
        if log_file.exists() and 'resolved: False' in log_file.read_text(errors='ignore'):
            error_types['test_failures'].append(instance_id)

    return error_types


def select_test_instances(error_types, sample_size, error_type='all'):
    """选择测试实例"""

    if error_type == 'all':
        # 从每个类型按比例采样
        samples = []

        # 格式错误 (最多，采样40%)
        n_format = min(len(error_types['format_errors']), int(sample_size * 0.4))
        samples.extend(random.sample(error_types['format_errors'], n_format))

        # 应用失败 (采样20%)
        n_app = min(len(error_types['application_errors']), int(sample_size * 0.2))
        samples.extend(random.sample(error_types['application_errors'], n_app))

        # 测试失败 (采样40%)
        n_test = min(len(error_types['test_failures']), int(sample_size * 0.4))
        samples.extend(random.sample(error_types['test_failures'], n_test))

        # 填充到目标数量
        remaining = sample_size - len(samples)
        if remaining > 0:
            all_errors = []
            for instances in error_types.values():
                all_errors.extend([i for i in instances if i not in samples])
            if all_errors:
                samples.extend(random.sample(all_errors, min(remaining, len(all_errors))))

        return samples[:sample_size]
    else:
        # 从特定类型采样
        instances = error_types.get(error_type, [])
        return random.sample(instances, min(sample_size, len(instances)))


def create_test_dataset(instances, output_path):
    """创建测试数据集文件"""
    dataset_path = Path("princeton-nlp/SWE-bench_Lite")

    # 查找原始数据集
    possible_paths = [
        dataset_path / "test.json",
        Path("data/SWE-bench_Lite/test.json"),
    ]

    original_data = None
    for path in possible_paths:
        if path.exists():
            with open(path) as f:
                original_data = json.load(f)
            break

    if original_data is None:
        print("警告: 找不到原始数据集，将只创建instance_id列表")
        output_path.write_text('\n'.join(instances))
        return

    # 提取测试实例
    test_data = [item for item in original_data if item['instance_id'] in instances]

    with open(output_path, 'w') as f:
        json.dump(test_data, f, indent=2)

    print(f"✅ 测试数据集已创建: {output_path} ({len(test_data)} 个实例)")


def generate_test_report(error_types, selected_instances):
    """生成测试报告"""

    # 统计选中的实例类型分布
    type_counts = defaultdict(int)
    for etype, instances in error_types.items():
        for instance in selected_instances:
            if instance in instances:
                type_counts[etype] += 1

    report = f"""
# 新Prompt测试方案

## 测试样本分布

总测试实例: {len(selected_instances)}

"""

    for etype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(selected_instances) * 100
        report += f"- {etype}: {count} ({pct:.1f}%)\n"

    report += f"""

## 测试实例列表

```
{chr(10).join(selected_instances)}
```

## 执行步骤

### 1. 用新prompt重新生成predictions

```bash
python3 swebench/inference/run_claude_code.py \\
  --dataset_name princeton-nlp/SWE-bench_Lite \\
  --split test \\
  --instance_ids {','.join(selected_instances[:5])}... \\
  --model_name_or_path claude-3.5-sonnet \\
  --output_dir results/test_new_prompt \\
  --max_workers 4
```

### 2. 评估新结果

```bash
python3 swebench/harness/run_evaluation.py \\
  --predictions_path results/test_new_prompt/claude-3.5-sonnet__SWE-bench_Lite__test.jsonl \\
  --run_id test_new_prompt \\
  --max_workers 4
```

### 3. 生成对比报告

```bash
python3 scripts/generate_comprehensive_report.py \\
  --predictions results/test_new_prompt/claude-3.5-sonnet__SWE-bench_Lite__test.jsonl \\
  --eval-report reports/test_new_prompt.json \\
  --log-dir logs/run_evaluation/test_new_prompt \\
  --output reports/test_new_prompt_comprehensive.md
```

## 预期结果

### 当前表现 (旧prompt)

- 格式错误率: {type_counts['format_errors']/len(selected_instances)*100:.1f}%
- 应用失败率: {type_counts['application_errors']/len(selected_instances)*100:.1f}%
- 测试失败率: {type_counts['test_failures']/len(selected_instances)*100:.1f}%

### 目标表现 (新prompt)

- 格式错误率: < 10% (降低 {type_counts['format_errors']/len(selected_instances)*100 - 10:.1f} 个百分点)
- 应用失败率: < 5% (降低 {type_counts['application_errors']/len(selected_instances)*100 - 5:.1f} 个百分点)
- 总通过率: > 50% (提升约 30 个百分点)

## 成本估算

- 预计成本: {len(selected_instances)} × $0.15 = ${len(selected_instances) * 0.15:.2f}
- 预计时间: {len(selected_instances)} × 30秒 = {len(selected_instances) * 30 / 60:.1f} 分钟
"""

    return report


def main():
    parser = argparse.ArgumentParser(description='测试新Prompt效果')
    parser.add_argument(
        '--sample-size',
        type=int,
        default=20,
        help='测试样本数量 (默认: 20)'
    )
    parser.add_argument(
        '--error-type',
        choices=['all', 'format_errors', 'application_errors', 'test_failures', 'docker_errors'],
        default='all',
        help='错误类型筛选 (默认: all)'
    )
    parser.add_argument(
        '--eval-report',
        default='reports/claude-3.5-sonnet.full_eval.json',
        help='评估报告路径'
    )
    parser.add_argument(
        '--output-dir',
        default='test_data',
        help='输出目录'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='随机种子'
    )

    args = parser.parse_args()

    # 设置随机种子
    random.seed(args.seed)

    print(f"📊 加载错误实例分析...")
    error_types = load_error_instances(args.eval_report)

    # 打印统计
    print(f"\n错误类型分布:")
    for etype, instances in error_types.items():
        print(f"  - {etype}: {len(instances)}")

    print(f"\n🎯 选择测试样本 (类型: {args.error_type}, 数量: {args.sample_size})...")
    selected = select_test_instances(error_types, args.sample_size, args.error_type)

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # 保存实例列表
    instances_file = output_dir / "test_instances.txt"
    instances_file.write_text('\n'.join(selected))
    print(f"✅ 实例列表已保存: {instances_file}")

    # 创建测试数据集
    dataset_file = output_dir / "test_dataset.json"
    create_test_dataset(selected, dataset_file)

    # 生成测试报告
    report = generate_test_report(error_types, selected)
    report_file = output_dir / "test_plan.md"
    report_file.write_text(report)
    print(f"✅ 测试计划已生成: {report_file}")

    print(f"\n📋 测试概要:")
    print(f"   - 测试实例: {len(selected)}")
    print(f"   - 预计成本: ${len(selected) * 0.15:.2f}")
    print(f"   - 预计时间: {len(selected) * 30 / 60:.1f} 分钟")
    print(f"\n💡 下一步: 查看 {report_file} 了解详细执行步骤")


if __name__ == '__main__':
    main()
