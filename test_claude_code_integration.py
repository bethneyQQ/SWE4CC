#!/usr/bin/env python3

"""
Test script for Claude Code integration with SWE-bench.
This script tests the integration without requiring actual API calls.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from swebench.inference.run_claude_code import (
    claude_code_inference,
    prepare_claude_code_prompt,
    parse_claude_code_args,
    check_claude_code_availability
)

def test_integration():
    """Test the complete Claude Code integration workflow."""

    print("🧪 Testing Claude Code Integration")
    print("=" * 50)

    # Test 1: Check Claude Code availability
    print("\n1. Testing Claude Code availability...")
    is_available = check_claude_code_availability()
    print(f"   ✓ Claude Code available: {is_available}")

    # Test 2: Test argument parsing
    print("\n2. Testing argument parsing...")
    args = "max_tokens=8192,temperature=0.1,timeout=300"
    parsed = parse_claude_code_args(args)
    expected = {"max_tokens": 8192, "temperature": 0.1, "timeout": 300}
    assert parsed == expected
    print(f"   ✓ Arguments parsed correctly: {parsed}")

    # Test 3: Test prompt preparation
    print("\n3. Testing prompt preparation...")
    datum = {
        "text": "Fix the following Python function that has a syntax error:\n\ndef add_numbers(a, b\n    return a + b"
    }
    prompt = prepare_claude_code_prompt(datum)
    assert "syntax error" in prompt
    assert "patch" in prompt.lower()
    print("   ✓ Prompt prepared successfully")

    # Test 4: Test the complete inference workflow with mocked Claude Code call
    print("\n4. Testing complete inference workflow...")

    # Create test dataset
    test_instances = [
        {
            "instance_id": "test__example-1",
            "text": "Fix this Python syntax error: def add(a, b return a + b"
        },
        {
            "instance_id": "test__example-2",
            "text": "The function should handle None values gracefully"
        }
    ]

    # Mock dataset class
    class MockDataset:
        def __init__(self, data):
            self.data = data
        def __iter__(self):
            return iter(self.data)

    test_dataset = MockDataset(test_instances)

    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        output_file = f.name

    try:
        # Mock the Claude Code call to return a successful response
        mock_response = {
            "content": """The issue is a missing closing parenthesis in the function definition.

Here's the fix:

```diff
--- a/example.py
+++ b/example.py
@@ -1,2 +1,2 @@
-def add_numbers(a, b
+def add_numbers(a, b):
     return a + b
```

This adds the missing closing parenthesis and colon to make the function definition syntactically correct.""",
            "usage": {
                "input_tokens": 50,
                "output_tokens": 120
            },
            "model": "claude-3.5-sonnet"
        }

        with patch('swebench.inference.run_claude_code.call_claude_code') as mock_call, \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            mock_call.return_value = mock_response

            # Run inference
            claude_code_inference(
                test_dataset=test_dataset,
                model_name_or_path="claude-3.5-sonnet",
                output_file=output_file,
                model_args={"max_instances": 2},
                existing_ids=set()
            )

        # Check output
        results = []
        with open(output_file, 'r') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))

        assert len(results) == 2

        for result in results:
            assert "instance_id" in result
            assert "model_name_or_path" in result
            assert "full_output" in result
            assert "model_patch" in result
            assert "claude_code_meta" in result

        print(f"   ✓ Processed {len(results)} instances successfully")
        print(f"   ✓ Output written to {output_file}")

        # Show sample result
        sample_result = results[0]
        print(f"   ✓ Sample instance ID: {sample_result['instance_id']}")
        print(f"   ✓ Generated patch length: {len(sample_result['model_patch'])} chars")

    finally:
        # Cleanup
        Path(output_file).unlink(missing_ok=True)

    print("\n🎉 All tests passed! Claude Code integration is working correctly.")
    print("\n📝 Next steps:")
    print("   1. Set your ANTHROPIC_API_KEY environment variable")
    print("   2. Run: python -m swebench.inference.run_api --model_name_or_path claude-3.5-sonnet ...")
    print("   3. Or use the direct adapter: python -m swebench.inference.run_claude_code ...")

if __name__ == "__main__":
    test_integration()