#!/usr/bin/env python3
"""
Final verification test for Loom Agent API.
Tests with the correct parameters that match the working curl command.
"""

import json
import requests
import sys

def test_loom_api():
    """Test the Loom Agent API with correct streaming configuration."""

    base_url = "http://114.112.75.90:5001/api/cline/openai_compatible/v1/chat/completions"

    print("=" * 80)
    print("Loom Agent API Verification Test")
    print("=" * 80)
    print()

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "x-loom-client": "swebench",
        "x-loom-sessionid": "test-001",
        "x-loom-workspacepath": "/home/ade",
    }

    payload = {
        "model": "claude-sonnet-4-20250514",
        "messages": [
            {"role": "user", "content": "Write a Python function to add two numbers"}
        ],
        "temperature": 1,
        "stream": True,
        "stream_options": {}
    }

    try:
        print(f"📡 URL: {base_url}")
        print(f"🤖 Model: {payload['model']}")
        print(f"🌊 Stream: {payload['stream']}")
        print(f"🌡️  Temperature: {payload['temperature']}")
        print()

        response = requests.post(
            base_url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            print("✅ API Response (streaming):")
            print("-" * 80)

            full_content = ""
            chunk_count = 0

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')

                    if line_str.startswith('data: '):
                        data_str = line_str[6:]

                        if data_str.strip() == '[DONE]':
                            print("\n[Stream completed]")
                            break

                        try:
                            chunk = json.loads(data_str)
                            chunk_count += 1

                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                full_content += content

                                # Print first chunk details
                                if chunk_count == 1:
                                    print(f"First chunk: {json.dumps(chunk, indent=2)}")
                                    print()
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}")
                            continue

            print("-" * 80)
            print()
            print(f"📊 Statistics:")
            print(f"   Total chunks: {chunk_count}")
            print(f"   Content length: {len(full_content)} chars")
            print(f"   Estimated tokens: ~{len(full_content) // 4}")
            print()
            print(f"📝 Full Content:")
            print("-" * 80)
            print(full_content)
            print("-" * 80)
            print()
            print("✅ Test PASSED - API is working correctly!")
            return True
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_loom_api()
    sys.exit(0 if success else 1)