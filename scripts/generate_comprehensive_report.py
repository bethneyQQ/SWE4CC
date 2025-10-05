#!/usr/bin/env python3
"""
综合报告生成器 - 整合Evaluation结果和Predictions详细信息

可复用的报告生成工具，支持：
1. 从evaluation报告提取统计信息
2. 从predictions文件提取所有可用字段
3. 生成多维度分析报告（markdown格式）
4. 支持自定义分析维度
"""

import json
import sys
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import argparse


class ComprehensiveReportGenerator:
    """综合报告生成器"""

    def __init__(self, predictions_file, eval_report_file=None, log_dir=None):
        self.predictions_file = Path(predictions_file)
        self.eval_report_file = Path(eval_report_file) if eval_report_file else None
        self.log_dir = Path(log_dir) if log_dir else None

        # 数据容器
        self.predictions = []
        self.eval_data = {}
        self.stats = defaultdict(dict)

    def load_data(self):
        """加载所有数据"""
        print(f"加载predictions文件: {self.predictions_file}")
        self._load_predictions()

        if self.eval_report_file and self.eval_report_file.exists():
            print(f"加载evaluation报告: {self.eval_report_file}")
            self._load_eval_report()
        else:
            print("未提供evaluation报告，仅分析predictions")

    def _load_predictions(self):
        """加载predictions文件（JSONL格式）"""
        with open(self.predictions_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    pred = json.loads(line.strip())
                    self.predictions.append(pred)
                except json.JSONDecodeError as e:
                    print(f"警告: 第{line_num}行JSON解析失败: {e}")

        print(f"  已加载 {len(self.predictions)} 条predictions")

    def _load_eval_report(self):
        """加载evaluation报告（JSON格式）"""
        with open(self.eval_report_file, 'r') as f:
            self.eval_data = json.load(f)

        print(f"  已加载evaluation报告")

    def analyze(self):
        """执行全面分析"""
        print("\n开始分析...")

        # 基础统计
        self._analyze_basic_stats()

        # Predictions字段分析
        self._analyze_predictions_fields()

        # 错误分析
        self._analyze_errors()

        # 错误根因分析（从日志）
        if self.log_dir and self.log_dir.exists():
            self._analyze_error_causes()

        # 失败类型分类
        if self.eval_data:
            self._classify_failure_types()

        # 性能分析（如果有相关字段）
        self._analyze_performance()

        # 按维度分组分析
        self._analyze_by_dimensions()

        print("分析完成！\n")

    def _analyze_basic_stats(self):
        """基础统计"""
        stats = {
            'total_samples': len(self.predictions),
            'timestamp': datetime.now().isoformat(),
            'predictions_file': str(self.predictions_file.name),
        }

        # 从evaluation报告获取统计
        if self.eval_data:
            stats.update({
                'eval_total': self.eval_data.get('total_instances', 0),
                'eval_completed': self.eval_data.get('completed_instances', 0),
                'eval_resolved': self.eval_data.get('resolved_instances', 0),
                'eval_unresolved': self.eval_data.get('unresolved_instances', 0),
                'eval_errors': self.eval_data.get('error_instances', 0),
                'eval_empty_patch': self.eval_data.get('empty_patch_instances', 0),
            })

            # 计算通过率
            total = stats['eval_total']
            if total > 0:
                stats['pass_rate'] = stats['eval_resolved'] / total
                stats['completion_rate'] = stats['eval_completed'] / total
                stats['error_rate'] = stats['eval_errors'] / total

        self.stats['basic'] = stats

    def _analyze_predictions_fields(self):
        """分析predictions中的所有字段"""
        if not self.predictions:
            return

        # 收集所有出现的字段
        all_fields = set()
        field_presence = Counter()
        field_types = defaultdict(Counter)

        for pred in self.predictions:
            fields = set(pred.keys())
            all_fields.update(fields)

            for field in fields:
                field_presence[field] += 1
                field_types[field][type(pred[field]).__name__] += 1

        # 统计字段覆盖率
        total = len(self.predictions)
        field_stats = {}

        for field in sorted(all_fields):
            count = field_presence[field]
            types = dict(field_types[field])

            field_stats[field] = {
                'presence': count,
                'coverage': count / total,
                'types': types,
            }

        self.stats['fields'] = {
            'all_fields': sorted(all_fields),
            'field_count': len(all_fields),
            'field_details': field_stats,
        }

    def _analyze_errors(self):
        """错误分析"""
        error_stats = {
            'total_with_errors': 0,
            'error_types': Counter(),
            'error_samples': [],
        }

        for pred in self.predictions:
            # 检查各种错误字段
            has_error = False
            error_info = {}

            if 'error' in pred and pred['error']:
                has_error = True
                error_info['error'] = pred['error']

            if 'exception' in pred and pred['exception']:
                has_error = True
                error_info['exception'] = pred['exception']

            if 'passed' in pred and pred['passed'] == False:
                has_error = True
                error_info['failed_test'] = True

            if has_error:
                error_stats['total_with_errors'] += 1

                # 记录错误类型
                error_type = 'unknown'
                if 'error' in error_info:
                    error_type = str(error_info['error'])[:50]
                elif 'exception' in error_info:
                    error_type = str(error_info['exception'])[:50]
                elif 'failed_test' in error_info:
                    error_type = 'test_failed'

                error_stats['error_types'][error_type] += 1

                # 保存前10个错误样本
                if len(error_stats['error_samples']) < 10:
                    error_stats['error_samples'].append({
                        'instance_id': pred.get('instance_id', pred.get('case_id', 'unknown')),
                        'error_info': error_info,
                    })

        # 转换Counter为dict
        error_stats['error_types'] = dict(error_stats['error_types'].most_common(20))

        self.stats['errors'] = error_stats

    def _analyze_performance(self):
        """性能分析（延迟、成本等）"""
        perf_stats = {
            'has_latency': False,
            'has_cost': False,
            'has_tokens': False,
        }

        latencies = []
        costs = []
        input_tokens = []
        output_tokens = []

        for pred in self.predictions:
            # 延迟
            if 'latency_ms' in pred:
                latencies.append(pred['latency_ms'])
            elif 'duration_s' in pred:
                latencies.append(pred['duration_s'] * 1000)

            # 成本
            if 'cost' in pred:
                costs.append(pred['cost'])
            elif 'billing_cost' in pred:
                costs.append(pred['billing_cost'])

            # Tokens
            if 'input_tokens' in pred:
                input_tokens.append(pred['input_tokens'])
            if 'output_tokens' in pred:
                output_tokens.append(pred['output_tokens'])

        # 计算统计量
        if latencies:
            perf_stats['has_latency'] = True
            perf_stats['latency'] = self._calc_stats(latencies)

        if costs:
            perf_stats['has_cost'] = True
            perf_stats['cost'] = self._calc_stats(costs)
            perf_stats['total_cost'] = sum(costs)

        if input_tokens or output_tokens:
            perf_stats['has_tokens'] = True
            if input_tokens:
                perf_stats['input_tokens'] = self._calc_stats(input_tokens)
            if output_tokens:
                perf_stats['output_tokens'] = self._calc_stats(output_tokens)

        self.stats['performance'] = perf_stats

    def _analyze_by_dimensions(self):
        """按维度分组分析"""
        dimensions = ['dataset', 'model_name', 'split', 'task', 'difficulty']

        by_dim = {}

        for dim in dimensions:
            # 检查是否有这个维度
            has_dim = any(dim in pred for pred in self.predictions)
            if not has_dim:
                continue

            # 按维度分组
            groups = defaultdict(list)
            for pred in self.predictions:
                if dim in pred:
                    key = pred[dim]
                    groups[key].append(pred)

            # 计算每组的统计
            dim_stats = {}
            for key, preds in groups.items():
                dim_stats[str(key)] = {
                    'count': len(preds),
                    'percentage': len(preds) / len(self.predictions),
                }

                # 计算通过率（如果有passed字段）
                if any('passed' in p for p in preds):
                    passed = sum(1 for p in preds if p.get('passed', False))
                    dim_stats[str(key)]['passed'] = passed
                    dim_stats[str(key)]['pass_rate'] = passed / len(preds)

            by_dim[dim] = dim_stats

        self.stats['by_dimension'] = by_dim

    def _analyze_error_causes(self):
        """从日志文件分析错误根因"""
        print("  分析错误根因...")

        error_causes = {
            'malformed_patch': [],
            'docker_rate_limit': [],
            'patch_apply_failed': [],
            'test_failure': [],
            'timeout': [],
            'other': [],
        }

        error_patterns = Counter()
        error_examples = defaultdict(list)

        # 获取所有错误实例的日志
        error_ids = self.eval_data.get('error_ids', [])
        unresolved_ids = self.eval_data.get('unresolved_ids', [])

        for instance_id in error_ids + unresolved_ids:
            log_file = self.log_dir / instance_id / "run_instance.log"

            if not log_file.exists():
                continue

            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()

                # 分类错误原因
                cause = 'other'
                error_detail = ''

                # 检查各种错误模式
                if 'malformed patch' in log_content:
                    cause = 'malformed_patch'
                    # 提取具体错误信息
                    match = re.search(r'malformed patch at line (\d+): (.+)', log_content)
                    if match:
                        line_num, error_msg = match.groups()
                        error_detail = f"Line {line_num}: {error_msg[:50]}"
                        error_patterns[error_msg[:50]] += 1

                elif 'Too Many Requests' in log_content or 'toomanyrequests' in log_content:
                    cause = 'docker_rate_limit'
                    error_detail = "Docker Hub rate limit exceeded"

                elif 'Patch Apply Failed' in log_content:
                    cause = 'patch_apply_failed'
                    # 提取具体错误
                    match = re.search(r'Patch Apply Failed:\n(.+?)(?:\n\n|Check)', log_content, re.DOTALL)
                    if match:
                        error_detail = match.group(1).strip()[:100]
                        # 提取错误模式
                        if 'Hunk' in error_detail:
                            error_patterns['Hunk failed to apply'] += 1
                        elif 'can\'t find file' in error_detail:
                            error_patterns['File not found'] += 1
                        else:
                            error_patterns['Other patch apply error'] += 1

                elif 'resolved: False' in log_content and instance_id in unresolved_ids:
                    cause = 'test_failure'
                    # 提取测试失败信息
                    match = re.search(r"'FAIL_TO_PASS'.*?'failure': \[(.*?)\]", log_content, re.DOTALL)
                    if match:
                        failed_tests = match.group(1)[:100]
                        error_detail = f"Tests failed: {failed_tests}"
                        error_patterns['Test failure'] += 1

                elif 'timeout' in log_content.lower():
                    cause = 'timeout'
                    error_detail = "Execution timeout"
                    error_patterns['Timeout'] += 1

                error_causes[cause].append(instance_id)

                # 保存错误样例（每类最多5个）
                if len(error_examples[cause]) < 5 and error_detail:
                    error_examples[cause].append({
                        'instance_id': instance_id,
                        'detail': error_detail
                    })

            except Exception as e:
                print(f"    警告: 无法读取日志 {log_file}: {e}")
                continue

        # 保存统计结果
        self.stats['error_causes'] = {
            'by_type': {k: len(v) for k, v in error_causes.items() if v},
            'instances': {k: v for k, v in error_causes.items() if v},
            'patterns': dict(error_patterns.most_common(15)),
            'examples': dict(error_examples),
        }

        print(f"    已分析 {sum(len(v) for v in error_causes.values())} 个错误实例")

    def _classify_failure_types(self):
        """对失败实例进行详细分类"""
        print("  分类失败类型...")

        failure_types = {
            'format_errors': {
                'description': 'Patch格式错误（语法问题）',
                'instances': [],
                'subcategories': Counter(),
            },
            'application_errors': {
                'description': 'Patch应用失败（代码不匹配）',
                'instances': [],
                'subcategories': Counter(),
            },
            'test_failures': {
                'description': 'Patch应用成功但测试失败',
                'instances': [],
                'subcategories': Counter(),
            },
            'infrastructure_errors': {
                'description': '基础设施问题（Docker等）',
                'instances': [],
                'subcategories': Counter(),
            },
        }

        # 从error_causes获取分类信息
        if 'error_causes' in self.stats:
            causes = self.stats['error_causes']['instances']

            # 格式错误
            if 'malformed_patch' in causes:
                failure_types['format_errors']['instances'] = causes['malformed_patch']
                # 从patterns获取子分类
                patterns = self.stats['error_causes']['patterns']
                for pattern, count in patterns.items():
                    if any(x in pattern.lower() for x in ['expected', 'trailing', 'unexpected', 'leading']):
                        failure_types['format_errors']['subcategories'][pattern[:40]] = count

            # 应用错误
            if 'patch_apply_failed' in causes:
                failure_types['application_errors']['instances'] = causes['patch_apply_failed']
                patterns = self.stats['error_causes']['patterns']
                for pattern, count in patterns.items():
                    if 'hunk' in pattern.lower() or 'file' in pattern.lower():
                        failure_types['application_errors']['subcategories'][pattern[:40]] = count

            # 测试失败
            if 'test_failure' in causes:
                failure_types['test_failures']['instances'] = causes['test_failure']
                failure_types['test_failures']['subcategories']['Tests did not pass'] = len(causes['test_failure'])

            # 基础设施错误
            if 'docker_rate_limit' in causes:
                failure_types['infrastructure_errors']['instances'] = causes['docker_rate_limit']
                failure_types['infrastructure_errors']['subcategories']['Docker rate limit'] = len(causes['docker_rate_limit'])

            if 'timeout' in causes:
                failure_types['infrastructure_errors']['instances'].extend(causes['timeout'])
                failure_types['infrastructure_errors']['subcategories']['Timeout'] = len(causes['timeout'])

        # 计算统计
        failure_summary = {}
        for ftype, data in failure_types.items():
            if data['instances']:
                failure_summary[ftype] = {
                    'count': len(data['instances']),
                    'percentage': len(data['instances']) / self.stats['basic']['total_samples'] * 100,
                    'description': data['description'],
                    'subcategories': dict(data['subcategories'].most_common(5)),
                    'example_instances': data['instances'][:5],
                }

        self.stats['failure_classification'] = failure_summary

        print(f"    已分类 {sum(v['count'] for v in failure_summary.values())} 个失败实例")

    def _calc_stats(self, values):
        """计算统计量"""
        if not values:
            return {}

        sorted_values = sorted(values)
        n = len(sorted_values)

        return {
            'count': n,
            'min': sorted_values[0],
            'max': sorted_values[-1],
            'mean': sum(values) / n,
            'median': sorted_values[n // 2],
            'p90': sorted_values[int(n * 0.9)],
            'p95': sorted_values[int(n * 0.95)],
            'p99': sorted_values[int(n * 0.99)] if n >= 100 else sorted_values[-1],
        }

    def generate_report(self, output_file=None):
        """生成Markdown报告"""
        if output_file is None:
            output_file = self.predictions_file.parent / f"{self.predictions_file.stem}_comprehensive_report.md"

        output_file = Path(output_file)

        print(f"生成报告: {output_file}")

        with open(output_file, 'w', encoding='utf-8') as f:
            # 标题
            f.write(f"# 综合评估报告\n\n")
            f.write(f"**生成时间**: {self.stats['basic']['timestamp']}\n\n")
            f.write(f"**Predictions文件**: `{self.stats['basic']['predictions_file']}`\n\n")

            if self.eval_report_file:
                f.write(f"**Evaluation报告**: `{self.eval_report_file.name}`\n\n")

            f.write("---\n\n")

            # 1. 执行摘要
            f.write("## 📊 执行摘要\n\n")
            self._write_executive_summary(f)

            # 2. Evaluation结果
            if self.eval_data:
                f.write("\n## ✅ Evaluation结果\n\n")
                self._write_eval_results(f)

            # 3. Predictions字段分析
            f.write("\n## 🔍 Predictions字段分析\n\n")
            self._write_field_analysis(f)

            # 4. 错误分析
            f.write("\n## ❌ 错误分析\n\n")
            self._write_error_analysis(f)

            # 5. 错误根因分析
            if 'error_causes' in self.stats:
                f.write("\n## 🔬 错误根因分析\n\n")
                self._write_error_causes(f)

            # 6. 失败类型分类
            if 'failure_classification' in self.stats:
                f.write("\n## 📋 失败类型分类\n\n")
                self._write_failure_classification(f)

            # 7. 性能分析
            if self.stats['performance']['has_latency'] or self.stats['performance']['has_cost']:
                f.write("\n## ⚡ 性能分析\n\n")
                self._write_performance_analysis(f)

            # 8. 维度分析
            if self.stats.get('by_dimension'):
                f.write("\n## 📈 多维度分析\n\n")
                self._write_dimension_analysis(f)

            # 9. 建议与总结
            f.write("\n## 💡 建议与总结\n\n")
            self._write_recommendations(f)

        print(f"✅ 报告已生成: {output_file}")
        return str(output_file)

    def _write_executive_summary(self, f):
        """执行摘要"""
        basic = self.stats['basic']

        f.write("### 核心指标\n\n")
        f.write(f"- **总样本数**: {basic['total_samples']}\n")

        if 'eval_total' in basic:
            f.write(f"- **评估样本数**: {basic['eval_total']}\n")
            f.write(f"- **成功解决**: {basic['eval_resolved']} ({basic.get('pass_rate', 0)*100:.1f}%)\n")
            f.write(f"- **未解决**: {basic['eval_unresolved']}\n")
            f.write(f"- **错误数**: {basic['eval_errors']} ({basic.get('error_rate', 0)*100:.1f}%)\n")
            f.write(f"- **空补丁**: {basic['eval_empty_patch']}\n")

    def _write_eval_results(self, f):
        """Evaluation结果详情"""
        f.write("### 统计详情\n\n")
        f.write("| 指标 | 数量 | 百分比 |\n")
        f.write("|------|------|--------|\n")

        total = self.eval_data.get('total_instances', 1)
        metrics = [
            ('总实例数', 'total_instances'),
            ('提交实例', 'submitted_instances'),
            ('完成评估', 'completed_instances'),
            ('已解决', 'resolved_instances'),
            ('未解决', 'unresolved_instances'),
            ('错误', 'error_instances'),
            ('空补丁', 'empty_patch_instances'),
        ]

        for label, key in metrics:
            if key in self.eval_data:
                value = self.eval_data[key]
                pct = value / total * 100 if total > 0 else 0
                f.write(f"| {label} | {value} | {pct:.1f}% |\n")

        # 成功/失败的instance IDs
        if 'completed_ids' in self.eval_data:
            completed = self.eval_data['completed_ids']
            f.write(f"\n### 成功实例 ({len(completed)}个)\n\n")
            f.write(f"```\n{', '.join(completed[:20])}\n")
            if len(completed) > 20:
                f.write(f"... 还有 {len(completed)-20} 个\n")
            f.write("```\n")

        if 'error_ids' in self.eval_data:
            errors = self.eval_data['error_ids']
            f.write(f"\n### 错误实例 ({len(errors)}个)\n\n")
            f.write(f"```\n{', '.join(errors[:20])}\n")
            if len(errors) > 20:
                f.write(f"... 还有 {len(errors)-20} 个\n")
            f.write("```\n")

    def _write_field_analysis(self, f):
        """字段分析"""
        fields = self.stats['fields']

        f.write(f"### 字段概览\n\n")
        f.write(f"- **字段总数**: {fields['field_count']}\n")
        f.write(f"- **所有字段**: `{', '.join(fields['all_fields'])}`\n\n")

        f.write("### 字段详情\n\n")
        f.write("| 字段名 | 覆盖率 | 类型 |\n")
        f.write("|--------|--------|------|\n")

        for field, details in sorted(fields['field_details'].items(),
                                     key=lambda x: x[1]['coverage'], reverse=True):
            coverage = details['coverage'] * 100
            types = ', '.join(f"{t}({c})" for t, c in details['types'].items())
            f.write(f"| `{field}` | {coverage:.1f}% | {types} |\n")

    def _write_error_analysis(self, f):
        """错误分析"""
        errors = self.stats['errors']

        f.write(f"### 错误统计\n\n")
        f.write(f"- **错误总数**: {errors['total_with_errors']}\n")
        f.write(f"- **错误率**: {errors['total_with_errors']/len(self.predictions)*100:.1f}%\n\n")

        if errors['error_types']:
            f.write("### Top错误类型\n\n")
            f.write("| 错误类型 | 数量 |\n")
            f.write("|----------|------|\n")

            for error_type, count in list(errors['error_types'].items())[:10]:
                f.write(f"| `{error_type}` | {count} |\n")

        if errors['error_samples']:
            f.write("\n### 错误样本\n\n")
            for i, sample in enumerate(errors['error_samples'][:5], 1):
                f.write(f"{i}. **{sample['instance_id']}**\n")
                f.write(f"   - {sample['error_info']}\n")

    def _write_performance_analysis(self, f):
        """性能分析"""
        perf = self.stats['performance']

        if perf.get('has_latency'):
            lat = perf['latency']
            f.write("### 延迟统计\n\n")
            f.write("| 指标 | 值 (ms) |\n")
            f.write("|------|--------|\n")
            f.write(f"| 平均 | {lat['mean']:.2f} |\n")
            f.write(f"| 中位数 | {lat['median']:.2f} |\n")
            f.write(f"| P90 | {lat['p90']:.2f} |\n")
            f.write(f"| P95 | {lat['p95']:.2f} |\n")
            f.write(f"| 最小 | {lat['min']:.2f} |\n")
            f.write(f"| 最大 | {lat['max']:.2f} |\n")
            f.write("\n")

        if perf.get('has_cost'):
            cost = perf['cost']
            f.write("### 成本统计\n\n")
            f.write(f"- **总成本**: ${perf['total_cost']:.4f}\n")
            f.write(f"- **平均成本**: ${cost['mean']:.6f}\n")
            f.write(f"- **中位成本**: ${cost['median']:.6f}\n")
            f.write("\n")

        if perf.get('has_tokens'):
            f.write("### Token使用\n\n")
            if 'input_tokens' in perf:
                tok = perf['input_tokens']
                f.write(f"- **输入Tokens**: 平均 {tok['mean']:.0f}, 总计 {tok['mean']*tok['count']:.0f}\n")
            if 'output_tokens' in perf:
                tok = perf['output_tokens']
                f.write(f"- **输出Tokens**: 平均 {tok['mean']:.0f}, 总计 {tok['mean']*tok['count']:.0f}\n")
            f.write("\n")

    def _write_dimension_analysis(self, f):
        """维度分析"""
        by_dim = self.stats['by_dimension']

        for dim, groups in by_dim.items():
            f.write(f"### 按 {dim} 分组\n\n")
            f.write("| 值 | 数量 | 占比 | 通过率 |\n")
            f.write("|----|------|------|--------|\n")

            for key, stats in sorted(groups.items(), key=lambda x: x[1]['count'], reverse=True):
                count = stats['count']
                pct = stats['percentage'] * 100
                pass_rate = stats.get('pass_rate', 0) * 100 if 'pass_rate' in stats else 'N/A'

                if isinstance(pass_rate, float):
                    f.write(f"| {key} | {count} | {pct:.1f}% | {pass_rate:.1f}% |\n")
                else:
                    f.write(f"| {key} | {count} | {pct:.1f}% | {pass_rate} |\n")

            f.write("\n")

    def _write_error_causes(self, f):
        """写入错误根因分析"""
        causes = self.stats['error_causes']

        f.write("### 错误类型统计\n\n")
        f.write("| 错误类型 | 数量 | 占比 |\n")
        f.write("|---------|------|------|\n")

        total_errors = sum(causes['by_type'].values())
        for cause_type, count in sorted(causes['by_type'].items(), key=lambda x: x[1], reverse=True):
            pct = count / total_errors * 100 if total_errors > 0 else 0
            # 中文名称映射
            type_names = {
                'malformed_patch': 'Patch格式错误',
                'docker_rate_limit': 'Docker限流',
                'patch_apply_failed': 'Patch应用失败',
                'test_failure': '测试失败',
                'timeout': '执行超时',
                'other': '其他错误',
            }
            f.write(f"| {type_names.get(cause_type, cause_type)} | {count} | {pct:.1f}% |\n")

        # 常见错误模式
        if causes['patterns']:
            f.write("\n### Top错误模式\n\n")
            f.write("| 错误模式 | 次数 |\n")
            f.write("|---------|------|\n")

            for pattern, count in list(causes['patterns'].items())[:10]:
                # 清理和截断模式字符串
                clean_pattern = pattern.replace('|', '\\|').strip()
                f.write(f"| `{clean_pattern}` | {count} |\n")

        # 错误示例
        if causes['examples']:
            f.write("\n### 典型错误示例\n\n")

            for cause_type, examples in causes['examples'].items():
                if not examples:
                    continue

                type_names = {
                    'malformed_patch': 'Patch格式错误',
                    'docker_rate_limit': 'Docker限流',
                    'patch_apply_failed': 'Patch应用失败',
                    'test_failure': '测试失败',
                    'timeout': '执行超时',
                    'other': '其他错误',
                }

                f.write(f"#### {type_names.get(cause_type, cause_type)}\n\n")

                for ex in examples[:3]:
                    f.write(f"- **{ex['instance_id']}**: {ex['detail']}\n")

                f.write("\n")

    def _write_failure_classification(self, f):
        """写入失败类型分类"""
        classification = self.stats['failure_classification']

        f.write("### 失败类型概览\n\n")
        f.write("| 失败类型 | 描述 | 数量 | 占比 |\n")
        f.write("|---------|------|------|------|\n")

        for ftype, data in sorted(classification.items(), key=lambda x: x[1]['count'], reverse=True):
            f.write(f"| {ftype} | {data['description']} | {data['count']} | {data['percentage']:.1f}% |\n")

        # 详细子分类
        f.write("\n### 失败子类型详情\n\n")

        for ftype, data in sorted(classification.items(), key=lambda x: x[1]['count'], reverse=True):
            if not data['subcategories']:
                continue

            # 类型名称映射
            type_display = {
                'format_errors': '📝 格式错误',
                'application_errors': '⚙️ 应用错误',
                'test_failures': '❌ 测试失败',
                'infrastructure_errors': '🏗️ 基础设施错误',
            }

            f.write(f"#### {type_display.get(ftype, ftype)}\n\n")
            f.write(f"**{data['description']}** ({data['count']} 个实例)\n\n")

            if data['subcategories']:
                f.write("| 子类型 | 数量 |\n")
                f.write("|--------|------|\n")

                for subtype, count in data['subcategories'].items():
                    clean_subtype = subtype.replace('|', '\\|')
                    f.write(f"| {clean_subtype} | {count} |\n")

            # 示例实例
            if data['example_instances']:
                f.write(f"\n**示例实例**: `{', '.join(data['example_instances'][:5])}`\n")

            f.write("\n")

    def _write_recommendations(self, f):
        """建议与总结"""
        basic = self.stats['basic']
        errors = self.stats['errors']

        f.write("### 主要发现\n\n")

        # 成功率分析
        if 'pass_rate' in basic:
            pass_rate = basic['pass_rate'] * 100
            if pass_rate < 50:
                f.write(f"⚠️ **通过率较低** ({pass_rate:.1f}%)，需要改进模型或任务设置\n\n")
            elif pass_rate < 80:
                f.write(f"✅ **通过率中等** ({pass_rate:.1f}%)，有提升空间\n\n")
            else:
                f.write(f"🎉 **通过率优秀** ({pass_rate:.1f}%)！\n\n")

        # 错误率分析
        error_rate = errors['total_with_errors'] / len(self.predictions) * 100
        if error_rate > 30:
            f.write(f"⚠️ **错误率较高** ({error_rate:.1f}%)，建议优先修复top错误类型\n\n")

        f.write("### 改进建议\n\n")

        recommendation_num = 1

        # 基于失败分类的建议
        if 'failure_classification' in self.stats:
            classification = self.stats['failure_classification']

            # 按影响排序
            sorted_failures = sorted(classification.items(), key=lambda x: x[1]['count'], reverse=True)

            for ftype, data in sorted_failures[:3]:  # 只显示前3类
                f.write(f"{recommendation_num}. **{data['description']}** ({data['count']}个, {data['percentage']:.1f}%)\n")

                if ftype == 'format_errors':
                    f.write("   - 建议改进Patch生成器，确保符合unified diff格式规范\n")
                    f.write("   - 使用patch格式验证工具检查生成的patches\n")
                elif ftype == 'application_errors':
                    f.write("   - 改进代码上下文理解，确保patch能匹配实际代码\n")
                    f.write("   - 增加代码变更前的验证步骤\n")
                elif ftype == 'test_failures':
                    f.write("   - 分析测试失败原因，可能是patch逻辑不正确\n")
                    f.write("   - 考虑在生成patch前运行相关测试\n")
                elif ftype == 'infrastructure_errors':
                    f.write("   - 配置Docker认证以避免rate limit\n")
                    f.write("   - 增加重试机制和超时处理\n")

                f.write("\n")
                recommendation_num += 1

        # 基于错误类型的建议（如果没有分类数据）
        elif errors['error_types']:
            top_error = list(errors['error_types'].keys())[0]
            f.write(f"{recommendation_num}. **优先修复**: `{top_error}` (占错误的 {list(errors['error_types'].values())[0]/errors['total_with_errors']*100:.1f}%)\n\n")
            recommendation_num += 1

        # 基于字段的建议
        fields = self.stats['fields']
        missing_important = []
        for field in ['model_name', 'model_args', 'cost', 'latency_ms']:
            if field not in fields['all_fields']:
                missing_important.append(field)

        if missing_important:
            f.write(f"{recommendation_num}. **建议添加字段**: `{', '.join(missing_important)}` 以便更全面的分析\n\n")
            recommendation_num += 1

        # 基于成本和性能的建议
        if 'performance' in self.stats and self.stats['performance'].get('has_cost'):
            total_cost = self.stats['performance']['total_cost']
            avg_cost = self.stats['performance']['cost']['mean']
            if avg_cost > 0.15:  # 平均成本较高
                f.write(f"{recommendation_num}. **成本优化**: 当前平均成本 ${avg_cost:.4f}/实例，考虑使用更小的模型或优化提示词\n\n")

        f.write("\n---\n\n")
        f.write("*报告由 `generate_comprehensive_report.py` 自动生成*\n")


def main():
    parser = argparse.ArgumentParser(
        description='生成综合评估报告 - 整合Evaluation结果和Predictions详细信息'
    )
    parser.add_argument(
        '--predictions',
        required=True,
        help='Predictions文件路径 (JSONL格式)'
    )
    parser.add_argument(
        '--eval-report',
        help='Evaluation报告文件路径 (JSON格式)'
    )
    parser.add_argument(
        '--log-dir',
        help='评估日志目录 (用于错误根因分析)'
    )
    parser.add_argument(
        '--output',
        help='输出报告文件路径 (默认: predictions文件同目录下的 *_comprehensive_report.md)'
    )

    args = parser.parse_args()

    # 验证文件存在
    if not Path(args.predictions).exists():
        print(f"错误: Predictions文件不存在: {args.predictions}")
        sys.exit(1)

    if args.eval_report and not Path(args.eval_report).exists():
        print(f"错误: Evaluation报告不存在: {args.eval_report}")
        sys.exit(1)

    if args.log_dir and not Path(args.log_dir).exists():
        print(f"警告: 日志目录不存在: {args.log_dir}，将跳过错误根因分析")
        args.log_dir = None

    # 生成报告
    generator = ComprehensiveReportGenerator(
        predictions_file=args.predictions,
        eval_report_file=args.eval_report,
        log_dir=args.log_dir
    )

    generator.load_data()
    generator.analyze()
    report_file = generator.generate_report(output_file=args.output)

    print(f"\n✅ 综合报告生成完成: {report_file}")


if __name__ == '__main__':
    main()
