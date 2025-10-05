#!/usr/bin/env python3
"""
Comprehensive analysis of SWE-bench predictions and evaluation results.
Combines all available metadata, derived metrics, and agent-specific fields.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
import statistics

def load_jsonl(filepath: Path) -> List[Dict]:
    """Load JSONL file."""
    records = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def load_json(filepath: Path) -> Dict:
    """Load JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def analyze_predictions(predictions: List[Dict]) -> Dict[str, Any]:
    """Extract comprehensive metadata from predictions."""
    analysis = {
        'basic_info': {},
        'field_inventory': {},
        'original_fields': {},
        'derived_metrics': {},
        'agent_metrics': {},
        'quality_metrics': {},
        'resource_metrics': {},
        'per_instance_details': []
    }

    if not predictions:
        return analysis

    # Basic info
    analysis['basic_info'] = {
        'total_instances': len(predictions),
        'dataset': 'SWE-bench_Lite_oracle',
        'model': predictions[0].get('model_name_or_path', 'unknown'),
        'analysis_timestamp': datetime.now().isoformat()
    }

    # Field inventory - categorize all fields found
    all_fields = set()
    for pred in predictions:
        all_fields.update(pred.keys())
        if 'claude_code_meta' in pred and pred['claude_code_meta']:
            meta_fields = pred['claude_code_meta'].keys()
            all_fields.update([f'claude_code_meta.{k}' for k in meta_fields])

    analysis['field_inventory'] = {
        'total_unique_fields': len(all_fields),
        'fields_list': sorted(list(all_fields))
    }

    # Original fields - map to standard schema
    analysis['original_fields'] = {
        'identification': ['instance_id'],
        'model_info': ['model_name_or_path'],
        'output': ['model_patch', 'full_output'],
        'performance': ['latency_ms', 'cost'],
        'enhanced_metadata': ['claude_code_meta']
    }

    # Derived metrics
    costs = []
    latencies = []
    patch_sizes = []
    attempts_list = []
    validation_errors_list = []
    num_turns_list = []

    for pred in predictions:
        if 'cost' in pred and pred['cost'] is not None:
            costs.append(pred['cost'])

        if 'latency_ms' in pred and pred['latency_ms'] is not None:
            latencies.append(pred['latency_ms'])

        if 'model_patch' in pred and pred['model_patch']:
            patch_sizes.append(len(pred['model_patch']))

        # Enhanced metadata
        if 'claude_code_meta' in pred and pred['claude_code_meta']:
            meta = pred['claude_code_meta']

            if 'attempts' in meta:
                attempts_list.append(meta['attempts'])

            if 'validation_errors' in meta:
                validation_errors_list.append(len(meta['validation_errors']))

            if 'response_data' in meta and meta['response_data']:
                resp = meta['response_data']
                if 'num_turns' in resp:
                    num_turns_list.append(resp['num_turns'])

    analysis['derived_metrics'] = {
        'cost_analysis': {
            'total_cost': sum(costs) if costs else 0,
            'avg_cost': statistics.mean(costs) if costs else 0,
            'min_cost': min(costs) if costs else 0,
            'max_cost': max(costs) if costs else 0,
            'median_cost': statistics.median(costs) if costs else 0
        },
        'latency_analysis': {
            'avg_latency_ms': statistics.mean(latencies) if latencies else 0,
            'min_latency_ms': min(latencies) if latencies else 0,
            'max_latency_ms': max(latencies) if latencies else 0,
            'median_latency_ms': statistics.median(latencies) if latencies else 0,
            'p95_latency_ms': statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0)
        },
        'patch_analysis': {
            'avg_patch_size_bytes': statistics.mean(patch_sizes) if patch_sizes else 0,
            'min_patch_size_bytes': min(patch_sizes) if patch_sizes else 0,
            'max_patch_size_bytes': max(patch_sizes) if patch_sizes else 0,
            'patches_generated': len([p for p in predictions if p.get('model_patch')]),
            'empty_patches': len([p for p in predictions if not p.get('model_patch')])
        }
    }

    # Agent-specific metrics
    analysis['agent_metrics'] = {
        'retry_analysis': {
            'avg_attempts': statistics.mean(attempts_list) if attempts_list else 0,
            'max_attempts': max(attempts_list) if attempts_list else 0,
            'first_attempt_success': len([a for a in attempts_list if a == 1]) if attempts_list else 0,
            'required_retry': len([a for a in attempts_list if a > 1]) if attempts_list else 0
        },
        'validation_analysis': {
            'total_validation_errors': sum(validation_errors_list) if validation_errors_list else 0,
            'instances_with_errors': len([v for v in validation_errors_list if v > 0]) if validation_errors_list else 0,
            'clean_validations': len([v for v in validation_errors_list if v == 0]) if validation_errors_list else 0
        },
        'interaction_analysis': {
            'avg_turns': statistics.mean(num_turns_list) if num_turns_list else 0,
            'min_turns': min(num_turns_list) if num_turns_list else 0,
            'max_turns': max(num_turns_list) if num_turns_list else 0,
            'total_turns': sum(num_turns_list) if num_turns_list else 0
        },
        'enhanced_features': {
            'using_enhanced_mode': sum(1 for p in predictions if p.get('claude_code_meta', {}).get('enhanced', False)),
            'using_tools': sum(1 for p in predictions if p.get('claude_code_meta', {}).get('tools_available', False)),
            'repo_access': sum(1 for p in predictions if p.get('claude_code_meta', {}).get('repo_path'))
        }
    }

    # Quality metrics (from token usage)
    cache_creation_tokens = []
    cache_read_tokens = []
    input_tokens = []
    output_tokens = []

    for pred in predictions:
        meta = pred.get('claude_code_meta', {})
        resp = meta.get('response_data', {})
        usage = resp.get('usage', {})

        if 'cache_creation_input_tokens' in usage:
            cache_creation_tokens.append(usage['cache_creation_input_tokens'])
        if 'cache_read_input_tokens' in usage:
            cache_read_tokens.append(usage['cache_read_input_tokens'])
        if 'input_tokens' in usage:
            input_tokens.append(usage['input_tokens'])
        if 'output_tokens' in usage:
            output_tokens.append(usage['output_tokens'])

    analysis['quality_metrics'] = {
        'token_usage': {
            'total_cache_creation': sum(cache_creation_tokens),
            'total_cache_read': sum(cache_read_tokens),
            'total_input': sum(input_tokens),
            'total_output': sum(output_tokens),
            'avg_cache_creation': statistics.mean(cache_creation_tokens) if cache_creation_tokens else 0,
            'avg_cache_read': statistics.mean(cache_read_tokens) if cache_read_tokens else 0,
            'avg_input': statistics.mean(input_tokens) if input_tokens else 0,
            'avg_output': statistics.mean(output_tokens) if output_tokens else 0
        },
        'cache_efficiency': {
            'cache_hit_rate': (sum(cache_read_tokens) / (sum(cache_read_tokens) + sum(input_tokens))) if (sum(cache_read_tokens) + sum(input_tokens)) > 0 else 0,
            'total_tokens_saved': sum(cache_read_tokens)
        }
    }

    # Resource metrics
    analysis['resource_metrics'] = {
        'cost_efficiency': {
            'cost_per_patch': analysis['derived_metrics']['cost_analysis']['total_cost'] / max(1, analysis['derived_metrics']['patch_analysis']['patches_generated']),
            'cost_per_turn': analysis['derived_metrics']['cost_analysis']['total_cost'] / max(1, analysis['agent_metrics']['interaction_analysis']['total_turns'])
        },
        'time_efficiency': {
            'latency_per_turn_ms': analysis['derived_metrics']['latency_analysis']['avg_latency_ms'] / max(1, analysis['agent_metrics']['interaction_analysis']['avg_turns']),
            'total_time_seconds': sum(latencies) / 1000 if latencies else 0
        }
    }

    # Per-instance details
    for pred in predictions:
        instance_detail = {
            'instance_id': pred.get('instance_id'),
            'cost': pred.get('cost'),
            'latency_ms': pred.get('latency_ms'),
            'patch_size': len(pred.get('model_patch', '')),
            'has_patch': bool(pred.get('model_patch')),
            'enhanced': pred.get('claude_code_meta', {}).get('enhanced', False),
            'attempts': pred.get('claude_code_meta', {}).get('attempts', 0),
            'validation_errors': len(pred.get('claude_code_meta', {}).get('validation_errors', [])),
            'num_turns': pred.get('claude_code_meta', {}).get('response_data', {}).get('num_turns', 0),
            'repo_path': pred.get('claude_code_meta', {}).get('repo_path', '')
        }
        analysis['per_instance_details'].append(instance_detail)

    return analysis

def combine_with_evaluation(pred_analysis: Dict, eval_data: Dict) -> Dict[str, Any]:
    """Combine prediction analysis with evaluation results."""
    combined = {
        'summary': {},
        'prediction_analysis': pred_analysis,
        'evaluation_results': {},
        'combined_metrics': {}
    }

    # Extract evaluation results
    combined['evaluation_results'] = {
        'total_instances': eval_data.get('total_instances', 0),
        'submitted': eval_data.get('submitted_instances', 0),
        'completed': eval_data.get('completed_instances', 0),
        'resolved': eval_data.get('resolved_instances', 0),
        'unresolved': eval_data.get('unresolved_instances', 0),
        'empty_patches': eval_data.get('empty_patch_instances', 0),
        'errors': eval_data.get('error_instances', 0),
        'resolved_ids': eval_data.get('resolved_ids', []),
        'unresolved_ids': eval_data.get('unresolved_ids', [])
    }

    # Combined metrics
    submitted = combined['evaluation_results']['submitted']
    resolved = combined['evaluation_results']['resolved']

    combined['combined_metrics'] = {
        'success_rate': (resolved / submitted * 100) if submitted > 0 else 0,
        'completion_rate': (combined['evaluation_results']['completed'] / submitted * 100) if submitted > 0 else 0,
        'error_rate': (combined['evaluation_results']['errors'] / submitted * 100) if submitted > 0 else 0,
        'empty_patch_rate': (combined['evaluation_results']['empty_patches'] / submitted * 100) if submitted > 0 else 0,
        'avg_cost_per_resolved': (pred_analysis['derived_metrics']['cost_analysis']['total_cost'] / resolved) if resolved > 0 else 0,
        'avg_latency_per_resolved_ms': (pred_analysis['derived_metrics']['latency_analysis']['avg_latency_ms']) if resolved > 0 else 0,
        'first_attempt_success_rate': (pred_analysis['agent_metrics']['retry_analysis']['first_attempt_success'] / submitted * 100) if submitted > 0 else 0
    }

    # Summary
    combined['summary'] = {
        'model': pred_analysis['basic_info']['model'],
        'dataset': pred_analysis['basic_info']['dataset'],
        'total_instances': submitted,
        'resolved': resolved,
        'success_rate': f"{combined['combined_metrics']['success_rate']:.1f}%",
        'avg_cost': f"${pred_analysis['derived_metrics']['cost_analysis']['avg_cost']:.4f}",
        'avg_latency': f"{pred_analysis['derived_metrics']['latency_analysis']['avg_latency_ms'] / 1000:.1f}s",
        'enhanced_features_enabled': pred_analysis['agent_metrics']['enhanced_features']['using_enhanced_mode'] > 0,
        'cache_efficiency': f"{pred_analysis['quality_metrics']['cache_efficiency']['cache_hit_rate'] * 100:.1f}%",
        'analysis_timestamp': pred_analysis['basic_info']['analysis_timestamp']
    }

    return combined

def generate_markdown_report(analysis: Dict) -> str:
    """Generate a comprehensive markdown report."""
    md = []

    # Header
    md.append("# SWE-bench Enhanced Prediction Analysis Report")
    md.append("")
    md.append(f"**Generated:** {analysis['summary']['analysis_timestamp']}")
    md.append(f"**Model:** {analysis['summary']['model']}")
    md.append(f"**Dataset:** {analysis['summary']['dataset']}")
    md.append("")

    # Executive Summary
    md.append("## 📊 Executive Summary")
    md.append("")
    md.append(f"- **Total Instances:** {analysis['summary']['total_instances']}")
    md.append(f"- **Resolved:** {analysis['summary']['resolved']}")
    md.append(f"- **Success Rate:** {analysis['summary']['success_rate']}")
    md.append(f"- **Average Cost:** {analysis['summary']['avg_cost']}")
    md.append(f"- **Average Latency:** {analysis['summary']['avg_latency']}")
    md.append(f"- **Enhanced Features:** {'✅ Enabled' if analysis['summary']['enhanced_features_enabled'] else '❌ Disabled'}")
    md.append(f"- **Cache Efficiency:** {analysis['summary']['cache_efficiency']}")
    md.append("")

    # Field Inventory
    md.append("## 📋 Field Inventory")
    md.append("")
    md.append(f"**Total Unique Fields:** {analysis['prediction_analysis']['field_inventory']['total_unique_fields']}")
    md.append("")
    md.append("### Available Fields")
    md.append("")
    for field in analysis['prediction_analysis']['field_inventory']['fields_list']:
        md.append(f"- `{field}`")
    md.append("")

    # Original Fields Mapping
    md.append("## 🗂️ Standard Schema Mapping")
    md.append("")
    for category, fields in analysis['prediction_analysis']['original_fields'].items():
        md.append(f"### {category.replace('_', ' ').title()}")
        for field in fields:
            md.append(f"- `{field}`")
        md.append("")

    # Evaluation Results
    md.append("## ✅ Evaluation Results")
    md.append("")
    eval_results = analysis['evaluation_results']
    md.append(f"- **Total Instances in Dataset:** {eval_results['total_instances']}")
    md.append(f"- **Submitted for Evaluation:** {eval_results['submitted']}")
    md.append(f"- **Completed:** {eval_results['completed']}")
    md.append(f"- **Resolved (Passed Tests):** {eval_results['resolved']}")
    md.append(f"- **Unresolved:** {eval_results['unresolved']}")
    md.append(f"- **Empty Patches:** {eval_results['empty_patches']}")
    md.append(f"- **Errors:** {eval_results['errors']}")
    md.append("")

    if eval_results['resolved_ids']:
        md.append("### Resolved Instances")
        for iid in eval_results['resolved_ids']:
            md.append(f"- ✅ `{iid}`")
        md.append("")

    if eval_results['unresolved_ids']:
        md.append("### Unresolved Instances")
        for iid in eval_results['unresolved_ids']:
            md.append(f"- ❌ `{iid}`")
        md.append("")

    # Combined Metrics
    md.append("## 📈 Combined Metrics")
    md.append("")
    combined = analysis['combined_metrics']
    md.append(f"- **Success Rate:** {combined['success_rate']:.1f}%")
    md.append(f"- **Completion Rate:** {combined['completion_rate']:.1f}%")
    md.append(f"- **Error Rate:** {combined['error_rate']:.1f}%")
    md.append(f"- **Empty Patch Rate:** {combined['empty_patch_rate']:.1f}%")
    md.append(f"- **Average Cost per Resolved:** ${combined['avg_cost_per_resolved']:.4f}")
    md.append(f"- **Average Latency per Resolved:** {combined['avg_latency_per_resolved_ms'] / 1000:.1f}s")
    md.append(f"- **First Attempt Success Rate:** {combined['first_attempt_success_rate']:.1f}%")
    md.append("")

    # Derived Metrics
    md.append("## 💰 Cost Analysis")
    md.append("")
    cost = analysis['prediction_analysis']['derived_metrics']['cost_analysis']
    md.append(f"- **Total Cost:** ${cost['total_cost']:.4f}")
    md.append(f"- **Average Cost:** ${cost['avg_cost']:.4f}")
    md.append(f"- **Min Cost:** ${cost['min_cost']:.4f}")
    md.append(f"- **Max Cost:** ${cost['max_cost']:.4f}")
    md.append(f"- **Median Cost:** ${cost['median_cost']:.4f}")
    md.append("")

    md.append("## ⏱️ Latency Analysis")
    md.append("")
    latency = analysis['prediction_analysis']['derived_metrics']['latency_analysis']
    md.append(f"- **Average Latency:** {latency['avg_latency_ms'] / 1000:.1f}s")
    md.append(f"- **Min Latency:** {latency['min_latency_ms'] / 1000:.1f}s")
    md.append(f"- **Max Latency:** {latency['max_latency_ms'] / 1000:.1f}s")
    md.append(f"- **Median Latency:** {latency['median_latency_ms'] / 1000:.1f}s")
    md.append(f"- **P95 Latency:** {latency['p95_latency_ms'] / 1000:.1f}s")
    md.append("")

    md.append("## 📝 Patch Analysis")
    md.append("")
    patch = analysis['prediction_analysis']['derived_metrics']['patch_analysis']
    md.append(f"- **Patches Generated:** {patch['patches_generated']}")
    md.append(f"- **Empty Patches:** {patch['empty_patches']}")
    md.append(f"- **Average Patch Size:** {patch['avg_patch_size_bytes']:.0f} bytes")
    md.append(f"- **Min Patch Size:** {patch['min_patch_size_bytes']:.0f} bytes")
    md.append(f"- **Max Patch Size:** {patch['max_patch_size_bytes']:.0f} bytes")
    md.append("")

    # Agent Metrics
    md.append("## 🤖 Agent-Specific Metrics")
    md.append("")

    md.append("### Retry Analysis")
    retry = analysis['prediction_analysis']['agent_metrics']['retry_analysis']
    md.append(f"- **Average Attempts:** {retry['avg_attempts']:.1f}")
    md.append(f"- **Max Attempts:** {retry['max_attempts']}")
    md.append(f"- **First Attempt Success:** {retry['first_attempt_success']}")
    md.append(f"- **Required Retry:** {retry['required_retry']}")
    md.append("")

    md.append("### Validation Analysis")
    validation = analysis['prediction_analysis']['agent_metrics']['validation_analysis']
    md.append(f"- **Total Validation Errors:** {validation['total_validation_errors']}")
    md.append(f"- **Instances with Errors:** {validation['instances_with_errors']}")
    md.append(f"- **Clean Validations:** {validation['clean_validations']}")
    md.append("")

    md.append("### Interaction Analysis")
    interaction = analysis['prediction_analysis']['agent_metrics']['interaction_analysis']
    md.append(f"- **Average Turns:** {interaction['avg_turns']:.1f}")
    md.append(f"- **Min Turns:** {interaction['min_turns']}")
    md.append(f"- **Max Turns:** {interaction['max_turns']}")
    md.append(f"- **Total Turns:** {interaction['total_turns']}")
    md.append("")

    md.append("### Enhanced Features")
    enhanced = analysis['prediction_analysis']['agent_metrics']['enhanced_features']
    md.append(f"- **Using Enhanced Mode:** {enhanced['using_enhanced_mode']}")
    md.append(f"- **Using Tools:** {enhanced['using_tools']}")
    md.append(f"- **Repo Access:** {enhanced['repo_access']}")
    md.append("")

    # Quality Metrics
    md.append("## 🎯 Quality Metrics")
    md.append("")

    md.append("### Token Usage")
    tokens = analysis['prediction_analysis']['quality_metrics']['token_usage']
    md.append(f"- **Total Cache Creation:** {tokens['total_cache_creation']:,}")
    md.append(f"- **Total Cache Read:** {tokens['total_cache_read']:,}")
    md.append(f"- **Total Input:** {tokens['total_input']:,}")
    md.append(f"- **Total Output:** {tokens['total_output']:,}")
    md.append(f"- **Avg Cache Creation:** {tokens['avg_cache_creation']:.0f}")
    md.append(f"- **Avg Cache Read:** {tokens['avg_cache_read']:.0f}")
    md.append(f"- **Avg Input:** {tokens['avg_input']:.0f}")
    md.append(f"- **Avg Output:** {tokens['avg_output']:.0f}")
    md.append("")

    md.append("### Cache Efficiency")
    cache = analysis['prediction_analysis']['quality_metrics']['cache_efficiency']
    md.append(f"- **Cache Hit Rate:** {cache['cache_hit_rate'] * 100:.1f}%")
    md.append(f"- **Total Tokens Saved:** {cache['total_tokens_saved']:,}")
    md.append("")

    # Resource Metrics
    md.append("## 💡 Resource Efficiency")
    md.append("")

    md.append("### Cost Efficiency")
    cost_eff = analysis['prediction_analysis']['resource_metrics']['cost_efficiency']
    md.append(f"- **Cost per Patch:** ${cost_eff['cost_per_patch']:.4f}")
    md.append(f"- **Cost per Turn:** ${cost_eff['cost_per_turn']:.4f}")
    md.append("")

    md.append("### Time Efficiency")
    time_eff = analysis['prediction_analysis']['resource_metrics']['time_efficiency']
    md.append(f"- **Latency per Turn:** {time_eff['latency_per_turn_ms']:.0f}ms")
    md.append(f"- **Total Time:** {time_eff['total_time_seconds']:.1f}s")
    md.append("")

    # Per-Instance Details
    md.append("## 📊 Per-Instance Details")
    md.append("")
    md.append("| Instance ID | Cost | Latency | Patch Size | Attempts | Turns | Errors |")
    md.append("|-------------|------|---------|------------|----------|-------|--------|")

    for detail in analysis['prediction_analysis']['per_instance_details']:
        md.append(f"| `{detail['instance_id']}` | ${detail['cost']:.4f} | {detail['latency_ms'] / 1000:.1f}s | {detail['patch_size']} B | {detail['attempts']} | {detail['num_turns']} | {detail['validation_errors']} |")

    md.append("")

    # Quick Commands
    md.append("## 🔧 Quick Analysis Commands")
    md.append("")
    md.append("### Extract Specific Fields")
    md.append("```bash")
    md.append("# Get all instance IDs")
    md.append('jq -r \'.instance_id\' predictions.jsonl')
    md.append("")
    md.append("# Get cost summary")
    md.append('jq -s \'map(.cost) | {total: add, avg: (add/length), min: min, max: max}\' predictions.jsonl')
    md.append("")
    md.append("# Get instances with validation errors")
    md.append('jq -r \'select(.claude_code_meta.validation_errors | length > 0) | .instance_id\' predictions.jsonl')
    md.append("")
    md.append("# Get cache hit rate")
    md.append('jq -s \'map(.claude_code_meta.response_data.usage | {cache_read: .cache_read_input_tokens, input: .input_tokens}) | {total_cache: map(.cache_read) | add, total_input: map(.input) | add} | .total_cache / (.total_cache + .total_input)\' predictions.jsonl')
    md.append("```")
    md.append("")

    # Recommendations
    md.append("## 💡 Recommendations")
    md.append("")

    if analysis['combined_metrics']['success_rate'] == 100:
        md.append("✅ **Excellent performance!** All submitted instances were resolved successfully.")
    elif analysis['combined_metrics']['success_rate'] >= 80:
        md.append("✅ **Good performance.** Most instances were resolved successfully.")
    elif analysis['combined_metrics']['success_rate'] >= 50:
        md.append("⚠️ **Moderate performance.** Consider investigating failed instances.")
    else:
        md.append("❌ **Low success rate.** Significant improvements needed.")

    md.append("")

    if cache['cache_hit_rate'] > 0.8:
        md.append("✅ **Excellent cache utilization!** High cache hit rate reduces costs.")
    elif cache['cache_hit_rate'] > 0.5:
        md.append("✅ **Good cache utilization.**")
    else:
        md.append("⚠️ **Low cache utilization.** Consider enabling prompt caching.")

    md.append("")

    if retry['first_attempt_success'] == analysis['evaluation_results']['submitted']:
        md.append("✅ **Perfect first-attempt success rate!** Validation is working well.")
    elif retry['required_retry'] > 0:
        md.append(f"⚠️ **{retry['required_retry']} instances required retries.** Validation caught errors effectively.")

    md.append("")

    return "\n".join(md)

def main():
    """Main analysis function."""
    # Paths
    predictions_path = Path('results/claude-sonnet-4-5__SWE-bench_Lite_oracle__test.jsonl')
    evaluation_path = Path('reports/claude-sonnet-4-5.claude-sonnet-4-5-test.json')
    output_path = Path('reports/comprehensive_analysis_report.md')
    json_output_path = Path('reports/comprehensive_analysis_report.json')

    # Check files exist
    if not predictions_path.exists():
        print(f"❌ Predictions file not found: {predictions_path}")
        return 1

    if not evaluation_path.exists():
        print(f"❌ Evaluation file not found: {evaluation_path}")
        return 1

    print("📊 Starting comprehensive analysis...")
    print(f"📁 Predictions: {predictions_path}")
    print(f"📁 Evaluation: {evaluation_path}")

    # Load data
    print("\n📥 Loading data...")
    predictions = load_jsonl(predictions_path)
    evaluation = load_json(evaluation_path)

    print(f"✅ Loaded {len(predictions)} predictions")
    print(f"✅ Loaded evaluation with {evaluation.get('submitted_instances', 0)} instances")

    # Analyze
    print("\n🔍 Analyzing predictions...")
    pred_analysis = analyze_predictions(predictions)

    print("\n🔗 Combining with evaluation results...")
    combined_analysis = combine_with_evaluation(pred_analysis, evaluation)

    # Generate reports
    print("\n📝 Generating markdown report...")
    markdown_report = generate_markdown_report(combined_analysis)

    # Save reports
    print(f"\n💾 Saving reports...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(markdown_report)
    print(f"✅ Markdown report: {output_path}")

    with open(json_output_path, 'w') as f:
        json.dump(combined_analysis, f, indent=2)
    print(f"✅ JSON report: {json_output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Model: {combined_analysis['summary']['model']}")
    print(f"Success Rate: {combined_analysis['summary']['success_rate']}")
    print(f"Average Cost: {combined_analysis['summary']['avg_cost']}")
    print(f"Average Latency: {combined_analysis['summary']['avg_latency']}")
    print(f"Cache Efficiency: {combined_analysis['summary']['cache_efficiency']}")
    print("=" * 60)

    return 0

if __name__ == '__main__':
    sys.exit(main())
