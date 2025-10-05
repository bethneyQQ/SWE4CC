#!/usr/bin/env python3
"""
Enhanced Claude Code inference with repository access
This enables: SWE-bench → Claude Code CLI → API → LLM (with tool use)
"""
import json
import argparse
import sys
import os
import time
from pathlib import Path
from datasets import load_dataset
from tqdm import tqdm

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from swebench.inference.run_claude_code import (
    call_claude_code,
    check_claude_code_availability
)
from swebench.inference.make_datasets.utils import extract_diff
from swebench.inference.repo_manager import RepoManager
from swebench.inference.enhanced_prompts import (
    prepare_enhanced_claude_code_prompt,
    prepare_retry_prompt
)
from swebench.inference.patch_validator import (
    validate_patch_format,
    verify_hunk_line_numbers,
    analyze_patch_complexity
)


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Claude Code inference with repo access'
    )
    parser.add_argument('--instance_ids', required=True, help='Comma-separated IDs')
    parser.add_argument('--model', default='claude-3.5-sonnet', help='Model name')
    parser.add_argument('--output_dir', required=True, help='Output directory')
    parser.add_argument('--dataset', default='princeton-nlp/SWE-bench_Lite')
    parser.add_argument('--split', default='test')
    parser.add_argument('--max_retries', type=int, default=2, help='Max retry attempts')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup repos after')
    parser.add_argument('--validate_hunks', action='store_true', help='Validate line numbers')
    parser.add_argument('--use_cache', action='store_true', default=True, help='Use repo cache (default: True)')
    parser.add_argument('--no_cache', action='store_true', help='Disable repo cache')

    args = parser.parse_args()

    # Prerequisites
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
    print(f"📚 Loading dataset: {args.dataset} ({args.split})")
    dataset = load_dataset(args.dataset, split=args.split)
    filtered_data = [item for item in dataset if item['instance_id'] in instance_ids]
    print(f"✅ Found {len(filtered_data)}/{len(instance_ids)} instances\n")

    # Setup
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{args.model}__enhanced__test.jsonl"

    # Determine cache usage
    use_cache = args.use_cache and not args.no_cache
    repo_manager = RepoManager(use_cache=use_cache)

    if use_cache:
        print(f"📁 Using repo cache: {repo_manager.cache_dir}")
        print(f"📂 Worktrees will be in: {repo_manager.base_dir}\n")
    else:
        print(f"📁 Repos will be cloned to: {repo_manager.base_dir}")
        print(f"⚠️  Cache disabled - will clone separately for each instance\n")

    model_map = {
        "claude-3-haiku": "haiku",
        "claude-3-sonnet": "sonnet",
        "claude-3.5-sonnet": "sonnet",
        "claude-code": "sonnet",
    }
    actual_model = model_map.get(args.model, args.model)

    print(f"🚀 Starting ENHANCED inference (Claude Code → API → LLM with tools)...\n")

    stats = {
        'total': 0,
        'successful': 0,
        'format_valid': 0,
        'hunk_valid': 0,
        'retried': 0,
        'total_cost': 0.0
    }

    with open(output_file, 'w') as f:
        for datum in tqdm(filtered_data, desc="Processing"):
            instance_id = datum['instance_id']
            stats['total'] += 1

            try:
                # STEP 1: Setup repository at base_commit
                print(f"\n📦 {instance_id}: Setting up repository...")
                repo_path = repo_manager.setup_repo(datum)

                # STEP 2: Generate enhanced prompt with tool guidance
                prompt = prepare_enhanced_claude_code_prompt(datum, repo_path)

                # STEP 3: Change to repo directory (crucial for Claude Code tool access!)
                original_cwd = os.getcwd()
                os.chdir(repo_path)

                patch = None
                validation_errors = []
                attempts = 0

                # STEP 4: Generation loop with retry
                for attempt in range(args.max_retries + 1):
                    attempts += 1

                    # Use retry prompt if this is a retry
                    if attempt > 0 and validation_errors:
                        current_prompt = prepare_retry_prompt(
                            prompt,
                            validation_errors[-1],
                            attempt
                        )
                        stats['retried'] += 1
                    else:
                        current_prompt = prompt

                    # Call Claude Code (it can now access files in repo_path!)
                    print(f"🤖 {instance_id}: Calling Claude Code (attempt {attempt + 1})...")
                    start_time = time.time()

                    response_data = call_claude_code(
                        prompt=current_prompt,
                        model_name=actual_model,
                        timeout=300,
                        max_tokens=8192,
                        temperature=0.1
                    )

                    latency_ms = int((time.time() - start_time) * 1000)

                    if not response_data:
                        print(f"❌ {instance_id}: Claude Code call failed")
                        break

                    # Extract patch
                    full_output = response_data.get('result', '')
                    try:
                        patch = extract_diff(full_output)
                    except Exception as e:
                        print(f"⚠️  {instance_id}: Patch extraction failed: {e}")
                        patch = ''

                    if not patch:
                        validation_errors.append("No patch extracted from response")
                        continue

                    # STEP 5: Validate format
                    is_format_valid, format_error = validate_patch_format(patch)
                    if not is_format_valid:
                        print(f"⚠️  {instance_id}: Format validation failed: {format_error}")
                        validation_errors.append(f"Format error: {format_error}")
                        if attempt < args.max_retries:
                            continue
                        break

                    stats['format_valid'] += 1

                    # STEP 6: Validate line numbers against actual repo
                    if args.validate_hunks:
                        is_hunk_valid, hunk_error = verify_hunk_line_numbers(patch, repo_path)
                        if not is_hunk_valid:
                            print(f"⚠️  {instance_id}: Hunk validation failed")
                            print(f"   {hunk_error[:200]}")
                            validation_errors.append(f"Line number error: {hunk_error}")
                            if attempt < args.max_retries:
                                continue
                            break

                        stats['hunk_valid'] += 1

                    # Success!
                    print(f"✅ {instance_id}: Valid patch generated ({len(patch)} bytes)")
                    break

                # Restore directory
                os.chdir(original_cwd)

                # Analyze complexity
                complexity = analyze_patch_complexity(patch) if patch else {}

                # Estimate cost
                input_tokens = len(current_prompt) // 4
                output_tokens = len(full_output) // 4 if full_output else 0
                cost = (input_tokens * 3 + output_tokens * 15) / 1_000_000
                stats['total_cost'] += cost * attempts

                # Save result
                result = {
                    'instance_id': instance_id,
                    'model_patch': patch or '',
                    'model_name_or_path': args.model,
                    'full_output': full_output if response_data else 'ERROR',
                    'cost': cost,
                    'attempts': attempts,
                    'validation_errors': validation_errors,
                    'repo_path': repo_path,
                    'patch_complexity': complexity,
                    'claude_code_meta': {
                        'model': actual_model,
                        'enhanced': True,
                        'tools_available': True,
                        'response_data': response_data if response_data else None
                    }
                }

                if patch:
                    stats['successful'] += 1

                f.write(json.dumps(result) + '\n')
                f.flush()

            except Exception as e:
                print(f"❌ {instance_id}: Error: {e}")
                result = {
                    'instance_id': instance_id,
                    'model_patch': '',
                    'error': str(e)
                }
                f.write(json.dumps(result) + '\n')
                f.flush()
            finally:
                os.chdir(original_cwd)

    # Cleanup
    if args.cleanup:
        print("\n🧹 Cleaning up repositories...")
        repo_manager.cleanup_all()

    # Summary
    print(f"\n{'='*60}")
    print(f"✅ ENHANCED INFERENCE COMPLETED")
    print(f"{'='*60}")
    print(f"Total instances:     {stats['total']}")
    print(f"Successful patches:  {stats['successful']}/{stats['total']}")
    print(f"Format validated:    {stats['format_valid']}")
    if args.validate_hunks:
        print(f"Hunk validated:      {stats['hunk_valid']}")
    print(f"Retries triggered:   {stats['retried']}")
    print(f"Total cost:          ${stats['total_cost']:.4f}")
    print(f"\n📁 Output: {output_file}")
    print(f"📁 Repos: {repo_manager.base_dir}")
    print(f"{'='*60}\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
