#!/usr/bin/env python3

"""
Example usage of Claude Code integration with SWE-bench.
This demonstrates how to use the new Claude Code functionality.
"""

import subprocess
import json
from pathlib import Path

def create_sample_dataset():
    """Create a small sample dataset for testing."""
    sample_data = [
        {
            "instance_id": "example__syntax-fix-1",
            "text": "Fix the following Python function that has a syntax error:\n\n```python\ndef calculate_area(radius\n    pi = 3.14159\n    return pi * radius * radius\n```\n\nPlease provide a patch to fix the syntax error."
        },
        {
            "instance_id": "example__logic-fix-1",
            "text": "The following function is supposed to find the maximum of two numbers, but it has a logical error:\n\n```python\ndef find_max(a, b):\n    if a < b:\n        return a\n    else:\n        return b\n```\n\nPlease fix the logic error and provide a patch."
        }
    ]

    dataset_file = Path("/tmp/sample_dataset.jsonl")
    with open(dataset_file, "w") as f:
        for item in sample_data:
            f.write(json.dumps(item) + "\n")

    return dataset_file

def run_claude_code_inference():
    """Run Claude Code inference on the sample dataset."""

    print("🚀 Claude Code SWE-bench Integration Demo")
    print("=" * 50)

    # Create sample dataset
    print("📝 Creating sample dataset...")
    dataset_file = create_sample_dataset()
    print(f"   ✓ Created: {dataset_file}")

    # Output directory
    output_dir = Path("/tmp/claude_code_results")
    output_dir.mkdir(exist_ok=True)

    print(f"\n🔧 Running Claude Code inference...")
    print(f"   Dataset: {dataset_file}")
    print(f"   Output: {output_dir}")

    # Command to run Claude Code inference
    cmd = [
        "python", "-m", "swebench.inference.run_api",
        "--dataset_name_or_path", str(dataset_file),
        "--model_name_or_path", "claude-3.5-sonnet",
        "--output_dir", str(output_dir),
        "--model_args", "max_instances=2,timeout=30"
    ]

    print(f"   Command: {' '.join(cmd)}")
    print("\n⚠️  Note: This requires ANTHROPIC_API_KEY to be set in your environment")
    print("   Set it with: export ANTHROPIC_API_KEY='your-key-here'")

    # Show what the command would do
    print(f"\n💡 To run this manually:")
    print(f"   {' '.join(cmd)}")

    # Check if we can actually run it
    import os
    if os.environ.get('ANTHROPIC_API_KEY'):
        print(f"\n🎯 API key found! Running inference...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print("   ✅ Inference completed successfully!")

                # Look for output files
                output_files = list(output_dir.glob("*.jsonl"))
                if output_files:
                    output_file = output_files[0]
                    print(f"   📄 Output file: {output_file}")

                    # Show results
                    with open(output_file) as f:
                        results = [json.loads(line) for line in f if line.strip()]

                    print(f"   📊 Processed {len(results)} instances")

                    for i, result in enumerate(results, 1):
                        print(f"\n   Result {i}:")
                        print(f"     Instance: {result['instance_id']}")
                        print(f"     Model: {result['model_name_or_path']}")
                        print(f"     Patch length: {len(result.get('model_patch', ''))} chars")
                        if result.get('model_patch'):
                            print(f"     Patch preview: {result['model_patch'][:100]}...")

                else:
                    print("   ⚠️  No output files found")
            else:
                print(f"   ❌ Command failed with return code {result.returncode}")
                print(f"   Error: {result.stderr}")

        except subprocess.TimeoutExpired:
            print("   ⏰ Command timed out after 2 minutes")
        except Exception as e:
            print(f"   ❌ Error running command: {e}")
    else:
        print(f"\n⚠️  No API key found. Set ANTHROPIC_API_KEY to run the actual inference.")

    print(f"\n📚 For more information, see:")
    print(f"   - docs/guides/claude_code_integration.md")
    print(f"   - swebench/inference/run_claude_code.py")

if __name__ == "__main__":
    run_claude_code_inference()