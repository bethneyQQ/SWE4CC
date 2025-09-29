#!/usr/bin/env python3

"""
Simple backend verification - shows which backend will be used for each model.
"""

def check_model_routing(model_name):
    """Check which backend a model name will route to."""

    # This is the exact logic from run_api.py
    claude_code_models = ["claude-4", "claude-code", "claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]

    if model_name in claude_code_models:
        return "claude_code"
    elif model_name.startswith("claude"):
        return "anthropic_api"
    elif model_name.startswith("gpt"):
        return "openai_api"
    else:
        return "unknown"

def main():
    """Show routing for different model names."""

    print("🔍 SWE-bench Model Backend Routing")
    print("=" * 50)

    test_models = [
        # Claude Code models (new routing)
        "claude-4",
        "claude-code",
        "claude-3.5-sonnet",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",

        # Standard Anthropic API models (legacy routing)
        "claude-2",
        "claude-instant-1",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",

        # Other APIs
        "gpt-4",
        "gpt-3.5-turbo",
    ]

    print(f"{'Model Name':<25} {'Backend':<15} {'Notes'}")
    print("-" * 60)

    for model in test_models:
        backend = check_model_routing(model)

        if backend == "claude_code":
            emoji = "🤖"
            notes = "Uses Claude Code CLI"
        elif backend == "anthropic_api":
            emoji = "🔧"
            notes = "Uses Anthropic HTTP API"
        elif backend == "openai_api":
            emoji = "🌐"
            notes = "Uses OpenAI API"
        else:
            emoji = "❓"
            notes = "Unknown backend"

        print(f"{model:<25} {emoji} {backend:<12} {notes}")

    print("\n" + "=" * 60)
    print("🎯 Key Differences:")
    print()
    print("🤖 Claude Code Backend:")
    print("   - Uses subprocess to call 'claude' CLI")
    print("   - Enhanced coding capabilities")
    print("   - Output includes 'claude_code_meta' field")
    print("   - Logs: 'swebench.inference.run_claude_code'")
    print()
    print("🔧 Anthropic API Backend:")
    print("   - Direct HTTP API calls to Anthropic")
    print("   - Standard chat completion format")
    print("   - No special metadata in output")
    print("   - Logs: 'Using Anthropic key', 'anthropic_inference'")
    print()
    print("💡 To confirm which backend is actually used:")
    print("   1. Check the logs when running inference")
    print("   2. Look for 'claude_code_meta' in the output JSON")
    print("   3. Use --model_name_or_path with the exact names above")

if __name__ == "__main__":
    main()