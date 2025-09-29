#!/usr/bin/env python3
"""
Comprehensive statistics analyzer for SWE-bench predictions
Extracts detailed metrics from predictions.jsonl and evaluation results
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter
from datetime import datetime


class PredictionAnalyzer:
    """Analyze predictions and evaluation results with detailed statistics"""

    def __init__(self, predictions_path: str, evaluation_path: str = None):
        self.predictions_path = Path(predictions_path)
        self.evaluation_path = Path(evaluation_path) if evaluation_path else None
        self.predictions = []
        self.evaluation_data = {}

    def load_data(self):
        """Load predictions and evaluation data"""
        # Load predictions
        with open(self.predictions_path, 'r') as f:
            for line in f:
                if line.strip():
                    self.predictions.append(json.loads(line))

        # Load evaluation results if available
        if self.evaluation_path and self.evaluation_path.exists():
            with open(self.evaluation_path, 'r') as f:
                self.evaluation_data = json.loads(f.read())

    def compute_basic_stats(self) -> Dict[str, Any]:
        """Compute basic statistics"""
        n_samples = len(self.predictions)

        stats = {
            "total_samples": n_samples,
            "predictions_file": str(self.predictions_path),
            "analysis_timestamp": datetime.now().isoformat()
        }

        # Add evaluation stats if available
        if self.evaluation_data:
            stats.update({
                "total_instances": self.evaluation_data.get("total_instances", 0),
                "submitted_instances": self.evaluation_data.get("submitted_instances", 0),
                "completed_instances": self.evaluation_data.get("completed_instances", 0),
                "resolved_instances": self.evaluation_data.get("resolved_instances", 0),
                "unresolved_instances": self.evaluation_data.get("unresolved_instances", 0),
                "empty_patch_instances": self.evaluation_data.get("empty_patch_instances", 0),
                "error_instances": self.evaluation_data.get("error_instances", 0),
                "pass_rate": (
                    self.evaluation_data.get("resolved_instances", 0) /
                    self.evaluation_data.get("submitted_instances", 1)
                    if self.evaluation_data.get("submitted_instances", 0) > 0 else 0
                )
            })

        return stats

    def compute_performance_metrics(self) -> Dict[str, Any]:
        """Compute performance metrics (latency, cost, tokens)"""
        latencies = []
        costs = []
        input_tokens = []
        output_tokens = []
        total_tokens = []
        cache_creation_tokens = []
        cache_read_tokens = []

        for pred in self.predictions:
            # Latency
            if "latency_ms" in pred:
                latencies.append(pred["latency_ms"])

            # Cost
            if "cost" in pred:
                costs.append(pred["cost"])

            # Token usage from claude_code_meta
            if "claude_code_meta" in pred and "usage" in pred["claude_code_meta"]:
                usage = pred["claude_code_meta"]["usage"]
                if "input_tokens" in usage:
                    input_tokens.append(usage["input_tokens"])
                if "output_tokens" in usage:
                    output_tokens.append(usage["output_tokens"])
                if "cache_creation_input_tokens" in usage:
                    cache_creation_tokens.append(usage["cache_creation_input_tokens"])
                if "cache_read_input_tokens" in usage:
                    cache_read_tokens.append(usage["cache_read_input_tokens"])

                total = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                if total > 0:
                    total_tokens.append(total)

        metrics = {}

        # Latency stats
        if latencies:
            metrics["latency"] = {
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "mean_ms": statistics.mean(latencies),
                "median_ms": statistics.median(latencies),
                "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "p95_ms": self._percentile(latencies, 95),
                "p99_ms": self._percentile(latencies, 99),
                "total_seconds": sum(latencies) / 1000
            }

        # Cost stats
        if costs:
            metrics["cost"] = {
                "total": sum(costs),
                "mean": statistics.mean(costs),
                "median": statistics.median(costs),
                "min": min(costs),
                "max": max(costs),
                "cost_per_success": (
                    sum(costs) / self.evaluation_data.get("resolved_instances", 1)
                    if self.evaluation_data and self.evaluation_data.get("resolved_instances", 0) > 0
                    else sum(costs) / len(costs) if costs else 0
                )
            }

        # Token usage stats
        if input_tokens:
            metrics["tokens"] = {
                "input": {
                    "total": sum(input_tokens),
                    "mean": statistics.mean(input_tokens),
                    "median": statistics.median(input_tokens),
                    "max": max(input_tokens)
                },
                "output": {
                    "total": sum(output_tokens) if output_tokens else 0,
                    "mean": statistics.mean(output_tokens) if output_tokens else 0,
                    "median": statistics.median(output_tokens) if output_tokens else 0,
                    "max": max(output_tokens) if output_tokens else 0
                },
                "total": {
                    "total": sum(total_tokens) if total_tokens else 0,
                    "mean": statistics.mean(total_tokens) if total_tokens else 0
                },
                "cache": {
                    "creation_total": sum(cache_creation_tokens) if cache_creation_tokens else 0,
                    "read_total": sum(cache_read_tokens) if cache_read_tokens else 0,
                    "creation_mean": statistics.mean(cache_creation_tokens) if cache_creation_tokens else 0,
                    "read_mean": statistics.mean(cache_read_tokens) if cache_read_tokens else 0
                }
            }

        return metrics

    def compute_model_info(self) -> Dict[str, Any]:
        """Extract model configuration and usage info"""
        model_info = {
            "model_names": Counter(),
            "tools_used": Counter(),
            "service_tiers": Counter()
        }

        for pred in self.predictions:
            # Model name
            if "model_name_or_path" in pred:
                model_info["model_names"][pred["model_name_or_path"]] += 1

            # Tools used
            if "claude_code_meta" in pred:
                meta = pred["claude_code_meta"]
                if "tools_used" in meta:
                    for tool in meta["tools_used"]:
                        model_info["tools_used"][tool] += 1

                # Service tier
                if "usage" in meta and "service_tier" in meta["usage"]:
                    model_info["service_tiers"][meta["usage"]["service_tier"]] += 1

                # Model info
                if "model_info" in meta:
                    if "model_versions" not in model_info:
                        model_info["model_versions"] = Counter()
                    model_info["model_versions"][meta["model_info"]] += 1

        return model_info

    def compute_patch_stats(self) -> Dict[str, Any]:
        """Compute statistics about generated patches"""
        patch_stats = {
            "has_patch": 0,
            "empty_patch": 0,
            "patch_sizes": [],
            "files_modified": Counter()
        }

        for pred in self.predictions:
            if "model_patch" in pred:
                patch = pred["model_patch"].strip()
                if patch:
                    patch_stats["has_patch"] += 1
                    patch_stats["patch_sizes"].append(len(patch))

                    # Count modified files (lines starting with --- or +++)
                    for line in patch.split('\n'):
                        if line.startswith('---') or line.startswith('+++'):
                            # Extract file path
                            parts = line.split()
                            if len(parts) >= 2:
                                filepath = parts[1].lstrip('ab/')
                                patch_stats["files_modified"][filepath] += 1
                else:
                    patch_stats["empty_patch"] += 1

        if patch_stats["patch_sizes"]:
            patch_stats["patch_size_stats"] = {
                "mean": statistics.mean(patch_stats["patch_sizes"]),
                "median": statistics.median(patch_stats["patch_sizes"]),
                "min": min(patch_stats["patch_sizes"]),
                "max": max(patch_stats["patch_sizes"])
            }

        return patch_stats

    def compute_instance_details(self) -> Dict[str, Any]:
        """Get detailed information about each instance"""
        instances = []

        resolved_ids = set(self.evaluation_data.get("resolved_ids", []))

        for pred in self.predictions:
            instance = {
                "instance_id": pred.get("instance_id", "unknown"),
                "model": pred.get("model_name_or_path", "unknown"),
                "passed": pred.get("instance_id") in resolved_ids,
                "latency_ms": pred.get("latency_ms", 0),
                "cost": pred.get("cost", 0),
                "has_patch": bool(pred.get("model_patch", "").strip()),
                "patch_size": len(pred.get("model_patch", "")),
            }

            # Token info
            if "claude_code_meta" in pred and "usage" in pred["claude_code_meta"]:
                usage = pred["claude_code_meta"]["usage"]
                instance["input_tokens"] = usage.get("input_tokens", 0)
                instance["output_tokens"] = usage.get("output_tokens", 0)
                instance["cache_read_tokens"] = usage.get("cache_read_input_tokens", 0)

            instances.append(instance)

        return {"instances": instances}

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (len(sorted_data) - 1) * percentile / 100
        floor = int(index)
        ceil = floor + 1
        if ceil >= len(sorted_data):
            return sorted_data[floor]
        return sorted_data[floor] + (sorted_data[ceil] - sorted_data[floor]) * (index - floor)

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive report"""
        report = {
            "basic_stats": self.compute_basic_stats(),
            "performance_metrics": self.compute_performance_metrics(),
            "model_info": self.compute_model_info(),
            "patch_stats": self.compute_patch_stats(),
            "instance_details": self.compute_instance_details()
        }

        return report

    def print_summary(self):
        """Print human-readable summary"""
        report = self.generate_report()

        print("\n" + "="*80)
        print("SWE-BENCH PREDICTIONS ANALYSIS REPORT")
        print("="*80)

        # Basic stats
        print("\n📊 BASIC STATISTICS")
        print("-" * 80)
        basic = report["basic_stats"]
        print(f"Total Samples: {basic['total_samples']}")
        if "submitted_instances" in basic:
            print(f"Submitted: {basic['submitted_instances']}")
            print(f"Completed: {basic['completed_instances']}")
            print(f"Resolved: {basic['resolved_instances']} ({basic['pass_rate']*100:.1f}%)")
            print(f"Unresolved: {basic['unresolved_instances']}")
            print(f"Errors: {basic['error_instances']}")
            print(f"Empty Patches: {basic['empty_patch_instances']}")

        # Performance metrics
        if "performance_metrics" in report and report["performance_metrics"]:
            print("\n⚡ PERFORMANCE METRICS")
            print("-" * 80)
            perf = report["performance_metrics"]

            if "latency" in perf:
                lat = perf["latency"]
                print(f"\nLatency:")
                print(f"  Mean: {lat['mean_ms']:.0f}ms | Median: {lat['median_ms']:.0f}ms")
                print(f"  Min: {lat['min_ms']:.0f}ms | Max: {lat['max_ms']:.0f}ms")
                print(f"  P95: {lat['p95_ms']:.0f}ms | P99: {lat['p99_ms']:.0f}ms")
                print(f"  Total Time: {lat['total_seconds']:.1f}s")

            if "cost" in perf:
                cost = perf["cost"]
                print(f"\nCost:")
                print(f"  Total: ${cost['total']:.4f}")
                print(f"  Mean: ${cost['mean']:.4f} | Median: ${cost['median']:.4f}")
                print(f"  Min: ${cost['min']:.4f} | Max: ${cost['max']:.4f}")
                print(f"  Cost per Success: ${cost['cost_per_success']:.4f}")

            if "tokens" in perf:
                tok = perf["tokens"]
                print(f"\nToken Usage:")
                print(f"  Input: {tok['input']['total']:,} (mean: {tok['input']['mean']:.0f})")
                print(f"  Output: {tok['output']['total']:,} (mean: {tok['output']['mean']:.0f})")
                print(f"  Total: {tok['total']['total']:,} (mean: {tok['total']['mean']:.0f})")
                if tok['cache']['creation_total'] > 0 or tok['cache']['read_total'] > 0:
                    print(f"  Cache Creation: {tok['cache']['creation_total']:,}")
                    print(f"  Cache Reads: {tok['cache']['read_total']:,}")

        # Model info
        if "model_info" in report:
            print("\n🤖 MODEL INFORMATION")
            print("-" * 80)
            model = report["model_info"]
            print(f"Models: {dict(model['model_names'])}")
            if model["tools_used"]:
                print(f"Tools Used: {dict(model['tools_used'])}")
            if model["service_tiers"]:
                print(f"Service Tiers: {dict(model['service_tiers'])}")

        # Patch stats
        if "patch_stats" in report:
            print("\n📝 PATCH STATISTICS")
            print("-" * 80)
            patch = report["patch_stats"]
            print(f"Patches Generated: {patch['has_patch']}")
            print(f"Empty Patches: {patch['empty_patch']}")
            if "patch_size_stats" in patch:
                ps = patch["patch_size_stats"]
                print(f"Patch Size: mean={ps['mean']:.0f}, median={ps['median']:.0f}, "
                      f"min={ps['min']}, max={ps['max']}")
            if patch["files_modified"]:
                print(f"\nMost Modified Files:")
                for filepath, count in patch["files_modified"].most_common(10):
                    print(f"  {filepath}: {count} times")

        # Instance details
        if "instance_details" in report and report["instance_details"]["instances"]:
            print("\n📋 INSTANCE DETAILS")
            print("-" * 80)
            instances = report["instance_details"]["instances"]
            print(f"{'Instance ID':<40} {'Pass':<6} {'Latency':<10} {'Cost':<10} {'Tokens':<10}")
            print("-" * 80)
            for inst in instances:
                passed = "✓" if inst["passed"] else "✗"
                tokens = inst.get("input_tokens", 0) + inst.get("output_tokens", 0)
                print(f"{inst['instance_id']:<40} {passed:<6} "
                      f"{inst['latency_ms']:>8.0f}ms ${inst['cost']:>8.4f} {tokens:>8,}t")

        print("\n" + "="*80)
        print(f"Analysis completed at: {basic['analysis_timestamp']}")
        print("="*80 + "\n")

    def save_report(self, output_path: str):
        """Save detailed report to JSON file"""
        report = self.generate_report()
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✅ Detailed report saved to: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze SWE-bench predictions with detailed statistics")
    parser.add_argument("predictions_path", help="Path to predictions.jsonl file")
    parser.add_argument("--evaluation", "-e", help="Path to evaluation results JSON file")
    parser.add_argument("--output", "-o", help="Path to save detailed report JSON")
    parser.add_argument("--quiet", "-q", action="store_true", help="Don't print summary to console")

    args = parser.parse_args()

    analyzer = PredictionAnalyzer(args.predictions_path, args.evaluation)
    analyzer.load_data()

    if not args.quiet:
        analyzer.print_summary()

    if args.output:
        analyzer.save_report(args.output)
    elif not args.quiet:
        # Auto-generate output filename
        output_path = Path(args.predictions_path).with_suffix('.analysis.json')
        analyzer.save_report(str(output_path))


if __name__ == "__main__":
    main()