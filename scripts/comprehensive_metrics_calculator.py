#!/usr/bin/env python3
"""
Claude Code CLI 综合评估指标计算脚本
整合原始评估和修复后评估的数据
"""

import json
import numpy as np
from pathlib import Path
from collections import defaultdict

class ComprehensiveMetricsCalculator:
    def __init__(self, prediction_file, original_eval_file, fixed_eval_file):
        """
        初始化计算器

        Args:
            prediction_file: prediction.jsonl文件路径
            original_eval_file: 原始evaluation.json
            fixed_eval_file: 71个修复实例的evaluation.json
        """
        print(f"加载数据...")
        self.predictions = self._load_jsonl(prediction_file)
        print(f"  - Predictions: {len(self.predictions)} 个实例")

        self.original_eval = self._load_json(original_eval_file)
        print(f"  - 原始评估: {self.original_eval['resolved_instances']} resolved")

        self.fixed_eval = self._load_json(fixed_eval_file)
        print(f"  - 修复后评估: {self.fixed_eval['resolved_instances']} resolved (71个实例)")

        # 计算合并后的evaluation结果
        self.merged_eval = self._merge_evaluations()
        print(f"  - 合并后评估: {self.merged_eval['resolved_instances']} resolved\n")

    def _load_jsonl(self, file_path):
        data = []
        with open(file_path) as f:
            for line in f:
                data.append(json.loads(line))
        return data

    def _load_json(self, file_path):
        with open(file_path) as f:
            return json.load(f)

    def _merge_evaluations(self):
        """合并原始评估和修复后评估的结果"""
        # 从原始评估中移除71个malformed,加入修复后的结果
        original_resolved = set(self.original_eval['resolved_ids'])
        original_unresolved = set(self.original_eval['unresolved_ids'])
        original_error = set(self.original_eval['error_ids'])

        fixed_resolved = set(self.fixed_eval['resolved_ids'])
        fixed_unresolved = set(self.fixed_eval['unresolved_ids'])
        fixed_error = set(self.fixed_eval['error_ids'])

        # 所有修复的实例ID
        all_fixed_ids = fixed_resolved | fixed_unresolved | fixed_error

        # 从原始error中移除这71个
        new_error = original_error - all_fixed_ids

        # 合并
        merged_resolved = original_resolved | fixed_resolved
        merged_unresolved = original_unresolved | fixed_unresolved
        merged_error = new_error | fixed_error

        return {
            'total_instances': self.original_eval['total_instances'],
            'resolved_instances': len(merged_resolved),
            'unresolved_instances': len(merged_unresolved),
            'error_instances': len(merged_error),
            'empty_patch_instances': self.original_eval['empty_patch_instances'],
            'completed_instances': len(merged_resolved) + len(merged_unresolved),
            'resolved_ids': list(sorted(merged_resolved)),
            'unresolved_ids': list(sorted(merged_unresolved)),
            'error_ids': list(sorted(merged_error)),
            'empty_patch_ids': self.original_eval['empty_patch_ids']
        }

    def _format_eval_summary(self, eval_data):
        total = eval_data['total_instances']
        return {
            'total': total,
            'resolved': eval_data['resolved_instances'],
            'unresolved': eval_data['unresolved_instances'],
            'error': eval_data['error_instances'],
            'empty': eval_data['empty_patch_instances'],
            'resolved_rate': f"{eval_data['resolved_instances']/total*100:.1f}%"
        }

    def _calculate_improvement(self):
        orig_resolved = self.original_eval['resolved_instances']
        new_resolved = self.merged_eval['resolved_instances']
        total = self.original_eval['total_instances']

        return {
            'resolved增加': new_resolved - orig_resolved,
            'success_rate提升': f"{(new_resolved - orig_resolved)/total*100:.1f}%",
            '原始success_rate': f"{orig_resolved/total*100:.1f}%",
            '修复后success_rate': f"{new_resolved/total*100:.1f}%"
        }

    # ===== 1. 核心成功率指标 =====
    def _calculate_success_metrics(self):
        """计算核心成功率指标"""
        eval_data = self.merged_eval
        total = eval_data['total_instances']
        empty = eval_data['empty_patch_instances']
        resolved = eval_data['resolved_instances']
        completed = eval_data['completed_instances']
        error = eval_data['error_instances']

        # 对比原始数据
        orig = self.original_eval

        return {
            '1.1_整体解决率': {
                '原始': f"{orig['resolved_instances']}/{total} = {orig['resolved_instances']/total*100:.2f}%",
                '修复后': f"{resolved}/{total} = {resolved/total*100:.2f}%",
                '提升': f"+{(resolved - orig['resolved_instances'])/total*100:.1f}%"
            },
            '1.2_有效解决率': {
                '说明': '排除空patch后的成功率',
                '原始': f"{orig['resolved_instances']}/{total - empty} = {orig['resolved_instances']/(total-empty)*100:.2f}%",
                '修复后': f"{resolved}/{total - empty} = {resolved/(total-empty)*100:.2f}%"
            },
            '1.3_Patch有效性': {
                '说明': '生成非空patch的比例',
                '值': f"{total - empty}/{total} = {(total-empty)/total*100:.2f}%"
            },
            '1.4_Patch应用成功率': {
                '说明': 'Patch能成功应用的比例',
                '原始': f"{orig['completed_instances']}/{total - empty} = {orig['completed_instances']/(total-empty)*100:.2f}%",
                '修复后': f"{completed}/{total - empty} = {completed/(total-empty)*100:.2f}%",
                '提升': f"+{(completed - orig['completed_instances'])/(total-empty)*100:.1f}%"
            },
            '1.5_Patch格式错误率': {
                '说明': 'Error占有效patch的比例',
                '原始': f"{orig['error_instances']}/{total - empty} = {orig['error_instances']/(total-empty)*100:.2f}%",
                '修复后': f"{error}/{total - empty} = {error/(total-empty)*100:.2f}%",
                '改善': f"-{(orig['error_instances'] - error)/(total-empty)*100:.1f}%"
            }
        }

    # ===== 2. 成本效率指标 =====
    def _calculate_cost_metrics(self):
        """计算成本效率指标"""
        costs = []
        for pred in self.predictions:
            if 'claude_code_meta' in pred and 'response_data' in pred['claude_code_meta']:
                cost = pred['claude_code_meta']['response_data'].get('total_cost_usd', 0)
                costs.append(cost)

        total_cost = sum(costs)
        total_instances = self.merged_eval['total_instances']
        resolved = self.merged_eval['resolved_instances']

        return {
            '2.1_总成本': f"${total_cost:.2f}",
            '2.2_平均成本': f"${total_cost/total_instances:.4f}/instance",
            '2.3_成功实例成本': f"${total_cost/resolved:.4f}/resolved" if resolved > 0 else "N/A",
            '2.4_成本效率': f"{resolved/total_cost:.2f} resolved/$" if total_cost > 0 else "N/A",
            '2.5_成本分布': {
                'P50中位数': f"${np.median(costs):.4f}",
                'P90': f"${np.percentile(costs, 90):.4f}",
                'P99': f"${np.percentile(costs, 99):.4f}",
                'Max': f"${max(costs):.4f}",
                'Min': f"${min(costs):.4f}",
                'Std': f"${np.std(costs):.4f}"
            }
        }

    # ===== 3. 性能效率指标 =====
    def _calculate_performance_metrics(self):
        """计算性能效率指标"""
        latencies = []
        for pred in self.predictions:
            if 'claude_code_meta' in pred and 'response_data' in pred['claude_code_meta']:
                # 字段名是duration_ms不是latency_ms
                duration_ms = pred['claude_code_meta']['response_data'].get('duration_ms', 0)
                latencies.append(duration_ms / 1000)  # 转换为秒

        avg_latency = np.mean(latencies) if latencies else 0

        if not latencies:
            return {'说明': '无耗时数据'}

        return {
            '3.1_平均耗时': f"{avg_latency:.1f}秒/instance",
            '3.2_中位数耗时': f"{np.median(latencies):.1f}秒",
            '3.3_吞吐量': f"{60/avg_latency:.2f} instances/min" if avg_latency > 0 else "N/A",
            '3.4_耗时分布': {
                'P90': f"{np.percentile(latencies, 90):.1f}秒",
                'P99': f"{np.percentile(latencies, 99):.1f}秒",
                'Max': f"{max(latencies):.1f}秒",
                'Min': f"{min(latencies):.1f}秒"
            }
        }

    # ===== 4. Token使用效率指标 =====
    def _calculate_token_metrics(self):
        """计算Token使用效率指标"""
        input_tokens = []
        output_tokens = []
        cache_read = []
        cache_creation = []

        for pred in self.predictions:
            if 'claude_code_meta' in pred and 'response_data' in pred['claude_code_meta']:
                usage = pred['claude_code_meta']['response_data'].get('usage', {})
                input_tokens.append(usage.get('input_tokens', 0))
                output_tokens.append(usage.get('output_tokens', 0))
                cache_read.append(usage.get('cache_read_input_tokens', 0))
                cache_creation.append(usage.get('cache_creation_input_tokens', 0))

        total_cache_read = sum(cache_read)
        total_cache_creation = sum(cache_creation)
        total_input = sum(input_tokens)
        total_tokens = total_cache_read + total_cache_creation + total_input

        cache_hit_rate = total_cache_read / total_tokens * 100 if total_tokens > 0 else 0

        return {
            '4.1_平均Token使用': {
                'Input': f"{np.mean(input_tokens):.0f} tokens",
                'Output': f"{np.mean(output_tokens):.0f} tokens",
                'Cache_Read': f"{np.mean(cache_read):.0f} tokens"
            },
            '4.2_总Token使用': {
                'Total_Input': f"{total_input:,} tokens",
                'Total_Output': f"{sum(output_tokens):,} tokens",
                'Total_Cache_Read': f"{total_cache_read:,} tokens",
                'Total_Cache_Creation': f"{total_cache_creation:,} tokens"
            },
            '4.3_Cache效率': {
                'Cache_Hit_Rate': f"{cache_hit_rate:.1f}%",
                '说明': 'cache_read / (cache_read + cache_creation + input)'
            },
            '4.4_Cache节省成本': {
                '说明': 'cache按10%价格计算,节省90%成本',
                '估算节省': f"${total_cache_read * 0.003 * 0.9 / 1000:.2f}"
            }
        }

    # ===== 5. Agent交互质量指标 =====
    def _calculate_interaction_metrics(self):
        """计算Agent交互质量指标"""
        turns_data = defaultdict(list)

        for pred in self.predictions:
            if 'claude_code_meta' not in pred:
                continue

            instance_id = pred['instance_id']
            num_turns = pred['claude_code_meta']['response_data'].get('num_turns', 0)

            if instance_id in self.merged_eval['resolved_ids']:
                turns_data['resolved'].append(num_turns)
            elif instance_id in self.merged_eval['unresolved_ids']:
                turns_data['unresolved'].append(num_turns)
            elif instance_id in self.merged_eval['error_ids']:
                turns_data['error'].append(num_turns)
            elif instance_id in self.merged_eval['empty_patch_ids']:
                turns_data['empty'].append(num_turns)

        return {
            '5.1_总体平均对话轮数': f"{np.mean([t for ts in turns_data.values() for t in ts]):.1f}轮",
            '5.2_按结果分类的对话轮数': {
                'Resolved': f"{np.mean(turns_data['resolved']):.1f}轮 (n={len(turns_data['resolved'])})" if turns_data['resolved'] else "N/A",
                'Unresolved': f"{np.mean(turns_data['unresolved']):.1f}轮 (n={len(turns_data['unresolved'])})" if turns_data['unresolved'] else "N/A",
                'Error': f"{np.mean(turns_data['error']):.1f}轮 (n={len(turns_data['error'])})" if turns_data['error'] else "N/A",
                'Empty_Patch': f"{np.mean(turns_data['empty']):.1f}轮 (n={len(turns_data['empty'])})" if turns_data['empty'] else "N/A"
            },
            '5.3_关键观察': {
                '空Patch轮数异常': "是" if (turns_data['empty'] and turns_data['resolved'] and np.mean(turns_data['empty']) > np.mean(turns_data['resolved'])) else "否"
            }
        }

    # ===== 6. Patch质量指标 =====
    def _calculate_patch_quality_metrics(self):
        """计算Patch质量指标"""
        complexities = []

        for pred in self.predictions:
            patch = pred.get('model_patch', '')
            if patch and patch.strip():
                complexity = {
                    'files_modified': patch.count('--- a/'),
                    'hunks': patch.count('\n@@'),
                    'lines_added': patch.count('\n+') - patch.count('\n+++'),
                    'lines_removed': patch.count('\n-') - patch.count('\n---')
                }
                complexities.append(complexity)

        if not complexities:
            return {'说明': '无有效patch数据'}

        return {
            '6.1_Patch复杂度': {
                '平均修改文件数': f"{np.mean([c['files_modified'] for c in complexities]):.1f}",
                '平均hunk数': f"{np.mean([c['hunks'] for c in complexities]):.1f}",
                '平均添加行数': f"{np.mean([c['lines_added'] for c in complexities]):.1f}",
                '平均删除行数': f"{np.mean([c['lines_removed'] for c in complexities]):.1f}",
                '平均总修改行数': f"{np.mean([c['lines_added'] + c['lines_removed'] for c in complexities]):.1f}"
            },
            '6.2_样本数': len(complexities)
        }

    # ===== 7. 错误分析指标 =====
    def _calculate_error_analysis(self):
        """计算错误分析指标"""

        # 原始评估的错误分布
        original_errors = self.original_eval['error_instances']

        # 修复后的错误分布
        merged_errors = self.merged_eval['error_instances']

        # 71个修复实例的分布
        fixed_resolved = len(self.fixed_eval['resolved_ids'])
        fixed_unresolved = len(self.fixed_eval['unresolved_ids'])
        fixed_error = len(self.fixed_eval['error_ids'])

        return {
            '7.1_错误类型变化': {
                '原始Error总数': original_errors,
                '其中Malformed(工具bug)': 71,
                'Malformed占比': f"{71/original_errors*100:.1f}%",
                '修复后Error总数': merged_errors,
                '修复后Error占比': f"{merged_errors/(self.merged_eval['total_instances'] - self.merged_eval['empty_patch_instances'])*100:.1f}%"
            },
            '7.2_71个Malformed实例修复后归属': {
                '总数': 71,
                'Resolved(代码完全正确)': f"{fixed_resolved} ({fixed_resolved/71*100:.1f}%)",
                'Unresolved(代码不完全正确)': f"{fixed_unresolved} ({fixed_unresolved/71*100:.1f}%)",
                'Error(仍失败)': f"{fixed_error} ({fixed_error/71*100:.1f}%)",
                '说明': 'Error是Reversed/Hunk Failed等真实代码错误'
            },
            '7.3_关键发现': {
                '工具bug掩盖的成功案例': fixed_resolved,
                '占总实例比例': f"{fixed_resolved/300*100:.1f}%"
            }
        }

    # ===== 10. 综合评分指标 =====
    def _calculate_composite_scores(self):
        """计算综合评分指标"""
        eval_data = self.merged_eval
        total = eval_data['total_instances']
        empty = eval_data['empty_patch_instances']

        resolution_rate = eval_data['resolved_instances'] / total * 100
        application_rate = eval_data['completed_instances'] / (total - empty) * 100
        malformed_rate = eval_data['error_instances'] / (total - empty) * 100

        # Token指标
        token_metrics = self._calculate_token_metrics()
        cache_hit_str = token_metrics['4.3_Cache效率']['Cache_Hit_Rate']
        cache_hit_rate = float(cache_hit_str.replace('%', ''))

        empty_rate = empty / total * 100

        # AQS计算
        aqs = (
            0.40 * resolution_rate +
            0.20 * application_rate +
            0.15 * (100 - malformed_rate) +
            0.15 * cache_hit_rate +
            0.10 * (100 - empty_rate)
        )

        # 成本指标
        cost_metrics = self._calculate_cost_metrics()
        avg_cost_str = cost_metrics['2.2_平均成本']
        avg_cost = float(avg_cost_str.replace('$', '').split('/')[0])

        value_score = aqs / avg_cost if avg_cost > 0 else 0

        # 对比原始评估的AQS
        orig_resolution_rate = self.original_eval['resolved_instances'] / total * 100
        orig_application_rate = self.original_eval['completed_instances'] / (total - empty) * 100
        orig_malformed_rate = self.original_eval['error_instances'] / (total - empty) * 100

        orig_aqs = (
            0.40 * orig_resolution_rate +
            0.20 * orig_application_rate +
            0.15 * (100 - orig_malformed_rate) +
            0.15 * cache_hit_rate +
            0.10 * (100 - empty_rate)
        )

        return {
            '10.1_Agent质量评分AQS': {
                '说明': '综合评分0-100分',
                '计算公式': '0.4×成功率 + 0.2×应用率 + 0.15×(100-错误率) + 0.15×cache + 0.1×(100-空率)',
                '原始AQS': f"{orig_aqs:.2f}/100",
                '修复后AQS': f"{aqs:.2f}/100",
                '提升': f"+{aqs - orig_aqs:.2f}分"
            },
            '10.2_性价比评分': {
                '说明': 'AQS / 平均成本',
                '原始Value_Score': f"{orig_aqs/avg_cost:.2f} points/$",
                '修复后Value_Score': f"{value_score:.2f} points/$",
                '提升': f"+{value_score - orig_aqs/avg_cost:.2f} points/$"
            }
        }

    def generate_full_report(self):
        """生成完整的评估报告"""

        print("="*70)
        print("开始计算综合评估指标...")
        print("="*70)

        report = {
            "评估概览": {
                "原始评估": self._format_eval_summary(self.original_eval),
                "修复后评估": self._format_eval_summary(self.merged_eval),
                "改进": self._calculate_improvement()
            },

            "1_核心成功率指标": self._calculate_success_metrics(),
            "2_成本效率指标": self._calculate_cost_metrics(),
            "3_性能效率指标": self._calculate_performance_metrics(),
            "4_Token使用效率指标": self._calculate_token_metrics(),
            "5_Agent交互质量指标": self._calculate_interaction_metrics(),
            "6_Patch质量指标": self._calculate_patch_quality_metrics(),
            "7_错误分析指标": self._calculate_error_analysis(),
            "10_综合评分指标": self._calculate_composite_scores()
        }

        return report


if __name__ == "__main__":
    # 文件路径
    prediction_file = "/home/zqq/SWE4CC/results/claude-sonnet-4-5__SWE-bench_Lite_oracle__test.jsonl"
    original_eval_file = "/home/zqq/SWE4CC/reports/claude-sonnet-4-5.claude-4.5-sonnet-evaluation.json"
    fixed_eval_file = "/home/zqq/claude-sonnet-4-5.malformed-hunk-fixed.json"

    # 创建计算器
    calculator = ComprehensiveMetricsCalculator(
        prediction_file,
        original_eval_file,
        fixed_eval_file
    )

    # 生成报告
    report = calculator.generate_full_report()

    # 输出JSON格式
    output_file = "/home/zqq/SWE4CC/reports/comprehensive_metrics_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n完整报告已保存到: {output_file}")

    # 同时输出可读格式
    print("\n" + "="*70)
    print("综合评估报告摘要")
    print("="*70)
    print(json.dumps(report, indent=2, ensure_ascii=False))
