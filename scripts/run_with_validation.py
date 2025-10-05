#!/usr/bin/env python3
"""
Run Claude Code inference with validation and retry logic
"""
import json
import argparse
import sys
import os
from pathlib import Path
from datasets import load_dataset
from tqdm import tqdm

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from swebench.inference.run_claude_code import (
    prepare_claude_code_prompt,
    call_claude_code,
    check_claude_code_availability
)
from swebench.inference.make_datasets.utils import extract_diff
from swebench.inference.patch_validator import (
    validate_patch_format,
    dry_run_patch,
    verify_hunk_line_numbers,
    is_patch_too_complex,
    split_patch_by_file,
    analyze_patch_complexity
)
from swebench.inference.retry_handler import PatchRetryHandler, create_validation_chain


def main():
    parser = argparse.ArgumentParser(description='Run inference with validation')
    parser.add_argument('--instance_ids', required=True, help='Comma-separated instance IDs')
    parser.add_argument('--model', default='claude-3.5-sonnet', help='Model name')
    parser.add_argument('--output_dir', required=True, help='Output directory')
    parser.add_argument('--dataset', default='princeton-nlp/SWE-bench_Lite', help='Dataset')
    parser.add_argument('--split', default='test', help='Split')
    parser.add_argument('--max_retries', type=int, default=2, help='Max retry attempts')
    parser.add_argument('--validate_format', action='store_true', help='Validate patch format')
    parser.add_argument('--validate_hunks', action='store_true', help='Validate hunk line numbers')

    args = parser.parse_args()

    # Check prerequisites
    if not check_claude_code_availability():
        print("❌ Claude Code CLI not available")
        return 1

    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not set")
        return 1

    # Parse instance IDs
    instance_ids = set(args.instance_ids.split(','))
    print(f"🎯 Target instances: {len(instance_ids)}")

    # Load dataset
    print(f"\n📚 Loading dataset: {args.dataset} ({args.split})")
    dataset = load_dataset(args.dataset, split=args.split)
    filtered_data = [item for item in dataset if item['instance_id'] in instance_ids]
    print(f"✅ Found {len(filtered_data)}/{len(instance_ids)} instances\n")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{args.model}__SWE-bench_Lite__test.jsonl"

    # Model name mapping
    model_map = {
        "claude-3-haiku": "haiku",
        "claude-3-sonnet": "sonnet",
        "claude-3.5-sonnet": "sonnet",
        "claude-code": "sonnet",
        "claude-4": "sonnet",
    }
    actual_model = model_map.get(args.model, args.model)

    # Setup validation
    validators = []
    if args.validate_format:
        validators.append(validate_patch_format)
        print("✅ Format validation enabled")

    if args.validate_hunks:
        print("⚠️  Hunk validation requires repo access (skipping for now)")
        # validators.append(lambda p: verify_hunk_line_numbers(p, repo_path))

    validation_func = create_validation_chain(*validators) if validators else None

    # Setup retry handler
    retry_handler = PatchRetryHandler(
        max_retries=args.max_retries,
        validation_func=validation_func,
        delay_seconds=2.0
    )

    print(f"🔄 Retry enabled: max {args.max_retries} attempts\n")
    print(f"🚀 Starting inference...\n")

    total_cost = 0.0
    successful = 0
    validation_stats = {
        'total': 0,
        'valid': 0,
        'invalid': 0,
        'retried': 0
    }

    with open(output_file, 'w') as f:
        for datum in tqdm(filtered_data, desc="Processing"):
            instance_id = datum['instance_id']
            validation_stats['total'] += 1

            # Prepare prompt
            prompt = prepare_claude_code_prompt(datum)

            # Generate function for retry handler
            def generate_patch(prompt=prompt):
                import time
                start = time.time()

                response_data = call_claude_code(
                    prompt=prompt,
                    model_name=actual_model,
                    timeout=300,
                    max_tokens=8192,
                    temperature=0.1
                )

                latency_ms = int((time.time() - start) * 1000)

                if not response_data:
                    return {'model_patch': '', 'full_output': 'ERROR', 'latency_ms': latency_ms}

                full_output = response_data.get('result', response_data.get('content', ''))

                try:
                    model_patch = extract_diff(full_output)
                except Exception as e:
                    print(f"⚠️  {instance_id}: Patch extraction error: {e}")
                    model_patch = ''

                return {
                    'model_patch': model_patch,
                    'full_output': full_output,
                    'latency_ms': latency_ms,
                    'response_data': response_data
                }

            # Use retry handler
            result = retry_handler.generate_with_retry(
                generate_func=generate_patch,
                instance_id=instance_id
            )

            # Track validation stats
            if result.get('validation_status') == 'valid':
                validation_stats['valid'] += 1
            elif result.get('validation_status') == 'invalid':
                validation_stats['invalid'] += 1

            if result.get('attempts', 1) > 1:
                validation_stats['retried'] += 1

            # Analyze complexity
            if result['model_patch']:
                complexity = analyze_patch_complexity(result['model_patch'])
                is_complex, reason = is_patch_too_complex(result['model_patch'])

                if is_complex:
                    print(f"⚠️  {instance_id}: Complex patch - {reason}")

            # Estimate cost
            input_tokens = len(prompt) // 4
            output_tokens = len(result.get('full_output', '')) // 4
            cost = (input_tokens * 3 + output_tokens * 15) / 1_000_000
            total_cost += cost * result.get('attempts', 1)

            # Prepare output
            output = {
                'instance_id': instance_id,
                'model_patch': result['model_patch'],
                'model_name_or_path': args.model,
                'full_output': result.get('full_output', ''),
                'cost': cost,
                'validation_attempts': result.get('attempts', 1),
                'validation_status': result.get('validation_status', 'unknown'),
                'validation_errors': result.get('validation_errors', []),
            }

            # Include response metadata if available
            if 'response_data' in result.get('retry_history', [{}])[-1]:
                output['claude_code_meta'] = {
                    'model': actual_model,
                    'response_data': result['retry_history'][-1].get('response_data', {})
                }

            if result['model_patch']:
                successful += 1
                status = "✅" if result.get('validation_status') == 'valid' else "⚠️ "
                attempts_info = f" ({result.get('attempts', 1)} attempts)" if result.get('attempts', 1) > 1 else ""
                print(f"{status} {instance_id}: {len(result['model_patch'])} bytes{attempts_info}")
            else:
                print(f"❌ {instance_id}: Failed after {result.get('attempts', 1)} attempts")

            f.write(json.dumps(output) + '\n')
            f.flush()

    print(f"\n{'='*60}")
    print(f"✅ Completed!")
    print(f"   Successful: {successful}/{len(filtered_data)}")
    print(f"   Total cost: ${total_cost:.4f}")
    print(f"\n📊 Validation Stats:")
    print(f"   Valid: {validation_stats['valid']}/{validation_stats['total']}")
    print(f"   Invalid: {validation_stats['invalid']}/{validation_stats['total']}")
    print(f"   Retried: {validation_stats['retried']}/{validation_stats['total']}")
    print(f"\n📁 Output: {output_file}")
    print(f"{'='*60}\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
