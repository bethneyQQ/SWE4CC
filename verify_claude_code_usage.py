#!/usr/bin/env python3

"""
Verification script to confirm whether Claude Code or standard Anthropic API is being used.
"""

import json
import subprocess
import tempfile
from pathlib import Path

def verify_claude_code_usage(model_name):
    """
    Verify if the specified model uses Claude Code or standard Anthropic API.

    Args:
        model_name: The model name to test

    Returns:
        str: "claude_code", "anthropic_api", or "unknown"
    """

    print(f"🔍 Verifying backend for model: {model_name}")
    print("=" * 50)

    # Create a tiny test dataset
    test_data = {
        "instance_id": "verify__backend-test-1",
        "text": "Fix this simple Python syntax error: def hello( print('hello')"
    }

    # Create temporary dataset file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        f.write(json.dumps(test_data) + '\n')
        dataset_file = f.name

    # Create temporary output directory
    output_dir = Path("/tmp/backend_verification")
    output_dir.mkdir(exist_ok=True)

    try:
        # Run inference
        cmd = [
            "python", "-m", "swebench.inference.run_api",
            "--dataset_name_or_path", dataset_file,
            "--model_name_or_path", model_name,
            "--output_dir", str(output_dir),
            "--model_args", "max_instances=1,timeout=30"
        ]

        print(f"🚀 Running command:")
        print(f"   {' '.join(cmd)}")
        print()

        # Capture both stdout and stderr
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        print(f"📊 Results:")
        print(f"   Return code: {result.returncode}")

        # Analyze logs for backend identification
        combined_output = result.stdout + result.stderr

        backend_detected = "unknown"

        if "swebench.inference.run_claude_code" in combined_output:
            backend_detected = "claude_code"
            print(f"   ✅ Backend: Claude Code Agent")

            # Look for Claude Code specific log patterns
            if "Starting Claude Code inference" in combined_output:
                print(f"   ✅ Claude Code inference started")
            if "Calling Claude Code with model" in combined_output:
                print(f"   ✅ Claude Code CLI called")

        elif "anthropic_inference" in combined_output or "Using Anthropic key" in combined_output:
            backend_detected = "anthropic_api"
            print(f"   ✅ Backend: Standard Anthropic API")

        else:
            print(f"   ❓ Backend: Unknown/Unclear")

        # Check output files for additional confirmation
        output_files = list(output_dir.glob("*.jsonl"))
        if output_files:
            output_file = output_files[0]
            print(f"   📄 Output file: {output_file.name}")

            try:
                with open(output_file) as f:
                    for line in f:
                        if line.strip():
                            result_data = json.loads(line)

                            if "claude_code_meta" in result_data:
                                print(f"   ✅ Found Claude Code metadata in output")
                                backend_detected = "claude_code"

                                meta = result_data["claude_code_meta"]
                                if "tools_used" in meta:
                                    print(f"   🛠️  Tools used: {meta['tools_used']}")
                                if "usage" in meta:
                                    print(f"   📈 Token usage: {meta['usage']}")

                            else:
                                print(f"   📋 Standard API output format (no claude_code_meta)")
                                if backend_detected == "unknown":
                                    backend_detected = "anthropic_api"

                            break

            except (json.JSONDecodeError, IOError) as e:
                print(f"   ⚠️  Could not read output file: {e}")

        # Show relevant log excerpts
        print(f"\n📝 Relevant log excerpts:")
        log_lines = combined_output.split('\n')
        for line in log_lines:
            if any(keyword in line for keyword in [
                "run_claude_code", "Starting Claude Code", "Calling Claude Code",
                "anthropic_inference", "Using Anthropic key", "Using temperature"
            ]):
                print(f"   {line}")

        return backend_detected

    except subprocess.TimeoutExpired:
        print(f"   ⏰ Command timed out")
        return "timeout"
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return "error"
    finally:
        # Cleanup
        Path(dataset_file).unlink(missing_ok=True)

def main():
    """Test different model names to show backend routing."""

    print("🧪 Claude Code vs Anthropic API Backend Verification")
    print("=" * 60)

    test_models = [
        ("claude-3.5-sonnet", "Should use Claude Code"),
        ("claude-code", "Should use Claude Code"),
        ("claude-3-opus", "Should use Claude Code"),
        ("claude-3-haiku", "Should use Claude Code"),
        ("claude-4", "Should use Claude Code"),
        ("claude-3-opus-20240229", "Should use Anthropic API (legacy name)"),
        ("claude-2", "Should use Anthropic API (legacy model)"),
    ]

    results = {}

    for model_name, expected in test_models:
        print(f"\n{'='*60}")
        print(f"Testing: {model_name}")
        print(f"Expected: {expected}")
        print(f"{'='*60}")

        backend = verify_claude_code_usage(model_name)
        results[model_name] = backend

        print(f"\n✅ Result: {model_name} -> {backend}")

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")

    for model_name, backend in results.items():
        emoji = "🤖" if backend == "claude_code" else "🔧" if backend == "anthropic_api" else "❓"
        print(f"   {emoji} {model_name:25} -> {backend}")

    print(f"\n💡 Key Indicators:")
    print(f"   🤖 Claude Code: Look for 'run_claude_code' logs and 'claude_code_meta' in output")
    print(f"   🔧 Anthropic API: Look for 'anthropic_inference' logs and standard output format")
    print(f"   📄 Check output JSON for 'claude_code_meta' field")

if __name__ == "__main__":
    main()