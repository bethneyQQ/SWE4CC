# Claude Code Integration Guide

This guide explains how to integrate and use Claude Code with SWE-bench for enhanced AI-powered software engineering tasks.

## ⚠️ Important Notes

> **Dataset Requirement**: You must use the **oracle** datasets (e.g., `princeton-nlp/SWE-bench_Lite_oracle`) which include the required `text` field. The base datasets (e.g., `princeton-nlp/SWE-bench_Lite`) will not work.

> **Model Name Mapping**: The integration automatically maps SWE-bench model names (e.g., `claude-3-haiku`) to Claude Code CLI aliases (e.g., `haiku`). Use the SWE-bench names in your commands.

> **Tested Models**: The integration has been verified to work with `claude-3-haiku`, `claude-3-sonnet`, `claude-3.5-sonnet`, and `claude-3-opus`.

## Overview

Claude Code is Anthropic's specialized CLI tool and SDK designed specifically for software development workflows. Unlike the standard Anthropic API, Claude Code provides:

- **Enhanced Code Understanding**: Better analysis of code structure and patterns
- **Agentic Capabilities**: Can perform autonomous coding tasks
- **Direct Integration**: Works seamlessly with development environments
- **Rich Tool Ecosystem**: Built-in tools for file operations, git, and more

### Architecture

```
SWE-bench → Claude Code CLI → Anthropic API → LLM
```

The integration acts as a bridge between SWE-bench evaluation framework and Claude Code's enhanced capabilities.

## Prerequisites

### 1. Install Claude Code CLI

First, install the Claude Code CLI globally:

```bash
npm install -g @anthropic-ai/claude-code
```

Verify the installation:

```bash
claude --version
```

### 2. Authentication Setup

Claude Code supports multiple authentication methods:

#### Option 1: API Key (Recommended)

Set your Anthropic API key as an environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

#### Option 2: Claude.ai Subscription

If you have a Claude Pro/Team/Enterprise subscription, you can authenticate through the browser:

```bash
claude auth login
```

### 3. Install SWE-bench Dependencies

Install the Claude Code integration dependencies:

```bash
cd /path/to/SWE-bench
pip install -e ".[inference,claude_code]"
```

## Configuration

### Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional Claude Code Configuration
CLAUDE_CODE_MAX_TOKENS=8192
CLAUDE_CODE_MODEL=claude-3.5-sonnet
CLAUDE_CODE_TIMEOUT=300
CLAUDE_CODE_TEMPERATURE=0.1
```

### Model Selection

Claude Code integration supports these models:

| SWE-bench Model Name | Claude Code Alias | Max Output Tokens | Description |
|---------------------|-------------------|-------------------|-------------|
| `claude-3-haiku` | `haiku` | 4096 | Fastest, most cost-effective |
| `claude-3-sonnet` | `sonnet` | 8192 | Good balance of speed and quality |
| `claude-3.5-sonnet` | `sonnet` | 8192 | **Recommended** - Best performance |
| `claude-3-opus` | `opus` | 8192 | Highest capability |
| `claude-code` | `sonnet` | 8192 | Alias for latest coding model |
| `claude-4` | `sonnet` | 8192 | Alias for latest model |

**Note:** The integration automatically maps SWE-bench model names to Claude Code CLI aliases for optimal compatibility.

## Usage

### Basic Inference

Run inference on SWE-bench Lite Oracle using Claude Code:

```bash
# IMPORTANT: Use the oracle dataset which includes the 'text' field
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path claude-3.5-sonnet \
    --output_dir ./results \
    --model_args "max_instances=10,timeout=300"
```

### Quick Test (Single Instance)

Test the integration with a single instance:

```bash
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path claude-3-haiku \
    --output_dir ./test_results \
    --model_args "max_instances=1,timeout=120" \
    --split test
```

### 🔍 Verifying Claude Code Backend Usage

It's important to confirm that you're actually using the Claude Code agent rather than the standard Anthropic API. Here's how to verify:

#### Model Name Routing

SWE-bench automatically routes different model names to different backends:

**✅ Claude Code Agent (Enhanced):**
- `claude-4` - Latest Claude model
- `claude-code` - Specialized coding model
- `claude-3.5-sonnet` - Recommended balanced model
- `claude-3-opus` - Highest capability
- `claude-3-sonnet` - Good balance
- `claude-3-haiku` - Fastest model

**❌ Standard Anthropic API (Legacy):**
- `claude-2` - Legacy model
- `claude-instant-1` - Legacy instant model
- `claude-3-opus-20240229` - Legacy dated model
- `claude-3-sonnet-20240229` - Legacy dated model
- `claude-3-haiku-20240307` - Legacy dated model

#### Runtime Verification Methods

**1. Check Log Output**

When using Claude Code, you'll see logs like:
```
swebench.inference.run_claude_code - INFO - Starting Claude Code inference with model: claude-3.5-sonnet
swebench.inference.run_claude_code - INFO - Calling Claude Code with model: claude-3.5-sonnet
swebench.inference.run_claude_code - INFO - Configuration: timeout=300s, max_tokens=8192
```

When using standard Anthropic API, you'll see:
```
Using Anthropic key *****xxxxx
Using temperature=0.2, top_p=0.95
Filtered to X instances
```

**2. Check Output JSON Format**

Claude Code outputs include special metadata:
```json
{
  "instance_id": "example__test-1",
  "model_name_or_path": "claude-3.5-sonnet",
  "full_output": "...",
  "model_patch": "...",
  "claude_code_meta": {
    "tools_used": ["code_analysis", "diff_generation"],
    "usage": {"input_tokens": 100, "output_tokens": 200},
    "model_info": "claude-3.5-sonnet"
  }
}
```

Standard API outputs lack the `claude_code_meta` field.

**3. Quick Verification Command**

```bash
# Test which backend a model uses
python -c "
model='claude-3.5-sonnet'
claude_code_models = ['claude-4', 'claude-code', 'claude-3.5-sonnet', 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku']
backend = 'Claude Code Agent' if model in claude_code_models else 'Standard Anthropic API'
print(f'Model {model} will use: {backend}')
"
```

**4. Check for Claude Code Metadata in Output**

```bash
# Check if output contains Claude Code metadata
jq '.claude_code_meta' your_output.jsonl

# If it returns non-null values, you're using Claude Code
# If it returns null, you're using standard Anthropic API
```

#### Quick Backend Verification Script

Save this as `check_backend.py` and run it to see all model routing:

```python
#!/usr/bin/env python3

def check_model_routing(model_name):
    claude_code_models = ["claude-4", "claude-code", "claude-3.5-sonnet",
                         "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]

    if model_name in claude_code_models:
        return "🤖 Claude Code Agent"
    elif model_name.startswith("claude"):
        return "🔧 Standard Anthropic API"
    else:
        return "❓ Other Backend"

# Test your model
model = "claude-3.5-sonnet"  # Change this to test different models
print(f"{model} -> {check_model_routing(model)}")
```

### Advanced Configuration

Use custom parameters for specific use cases:

```bash
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --model_name_or_path claude-code \
    --output_dir ./results \
    --model_args "max_tokens=6000,temperature=0.05,timeout=600,max_instances=50"
```

### Direct Claude Code Script

You can also use the Claude Code adapter directly:

```bash
python -m swebench.inference.run_claude_code \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --model_name_or_path claude-3.5-sonnet \
    --output_dir ./results \
    --model_args "max_tokens=8192,temperature=0.1"
```

## Model Arguments

### Supported Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_tokens` | int | 8192 | Maximum tokens in response |
| `temperature` | float | 0.1 | Creativity/randomness (0.0-1.0) |
| `timeout` | int | 300 | Request timeout in seconds |
| `max_instances` | int | None | Limit number of instances (for testing) |

### Example Configurations

**High Quality (Slower)**:
```bash
--model_args "max_tokens=8192,temperature=0.0,timeout=600"
```

**Balanced**:
```bash
--model_args "max_tokens=6000,temperature=0.1,timeout=300"
```

**Fast Testing**:
```bash
--model_args "max_tokens=4096,temperature=0.1,timeout=120,max_instances=10"
```

## Output Format

Claude Code generates enhanced output with additional metadata:

```json
{
  "instance_id": "sympy__sympy-20590",
  "model_name_or_path": "claude-3.5-sonnet",
  "full_output": "Analysis of the issue...\n\n```diff\n...\n```",
  "model_patch": "diff --git a/file.py b/file.py\n...",
  "claude_code_meta": {
    "tools_used": ["code_analysis", "diff_generation"],
    "usage": {
      "input_tokens": 1500,
      "output_tokens": 800
    },
    "model_info": "claude-3.5-sonnet"
  }
}
```

## Evaluation

After generating predictions, evaluate them using the standard SWE-bench harness:

```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path ./results/claude-3.5-sonnet__SWE-bench_Lite__test.jsonl \
    --max_workers 4 \
    --run_id claude_code_evaluation
```

## Performance Optimization

### 1. Model Selection Strategy

- **Development/Testing**: Use `claude-3-haiku` for speed
- **Production**: Use `claude-3.5-sonnet` for balance
- **Complex Issues**: Use `claude-3-opus` for highest quality

### 2. Parallel Processing

Run multiple instances with sharding:

```bash
# Shard 1 of 4
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --model_name_or_path claude-3.5-sonnet \
    --output_dir ./results \
    --shard_id 0 \
    --num_shards 4

# Shard 2 of 4
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --model_name_or_path claude-3.5-sonnet \
    --output_dir ./results \
    --shard_id 1 \
    --num_shards 4
```

### 3. Resource Management

Monitor and adjust timeouts based on instance complexity:

```bash
# For complex instances
--model_args "timeout=900,max_tokens=8192"

# For simple instances
--model_args "timeout=180,max_tokens=4096"
```

## Troubleshooting

### Common Issues

#### 1. Claude Code CLI Not Found

```bash
Error: claude: command not found
```

**Solution**: Install Claude Code CLI:
```bash
npm install -g @anthropic-ai/claude-code
```

#### 2. Authentication Errors

```bash
Error: ANTHROPIC_API_KEY environment variable must be set
```

**Solution**: Set your API key:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

#### 3. Timeout Issues

```bash
Error: Claude Code call timed out after 300 seconds
```

**Solution**: Increase timeout:
```bash
--model_args "timeout=600"
```

#### 4. JSON Parsing Errors

```bash
Error: Failed to parse Claude Code JSON response
```

**Solution**: This usually indicates a CLI output format issue. Check Claude Code version and update if needed.

#### 5. Wrong Backend Being Used

**Problem**: You expected to use Claude Code but it's using the standard Anthropic API instead.

**Diagnosis**:
```bash
# Check your model name routing
python simple_backend_check.py

# Or quickly test:
python -c "
model='YOUR_MODEL_NAME'
claude_code_models = ['claude-4', 'claude-code', 'claude-3.5-sonnet', 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku']
if model in claude_code_models:
    print(f'✅ {model} will use Claude Code')
else:
    print(f'❌ {model} will use Standard Anthropic API')
    print('Use one of:', claude_code_models)
"
```

**Solution**: Use the correct model names:
```bash
# ✅ Correct (uses Claude Code):
--model_name_or_path claude-3.5-sonnet

# ❌ Wrong (uses standard API):
--model_name_or_path claude-3-sonnet-20240229
```

#### 6. No Claude Code Metadata in Output

**Problem**: Output looks like standard API format, missing `claude_code_meta`.

**Diagnosis**:
```bash
# Check if Claude Code metadata exists
jq '.claude_code_meta' your_output.jsonl

# Should return something like:
# {
#   "tools_used": [...],
#   "usage": {...},
#   "model_info": "..."
# }
```

**Solution**: Verify you're using the correct model name and check logs for backend routing.

#### 7. Dataset Missing 'text' Field

```bash
ValueError: Column 'text' doesn't exist.
```

**Problem**: Using the base SWE-bench dataset which doesn't have the required `text` field.

**Solution**: Use the oracle dataset instead:
```bash
# ❌ Wrong:
--dataset_name_or_path princeton-nlp/SWE-bench_Lite

# ✅ Correct:
--dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle
```

#### 8. Model Not Found Error

```bash
API Error: 404 {"type":"error","error":{"type":"not_found_error","message":"model: claude-3-haiku"}}
```

**Problem**: Using incorrect model name format. Claude Code CLI requires specific model aliases or full model names.

**Solution**: The integration now automatically maps model names. Supported names:
- `claude-3-haiku` (mapped to `haiku` alias)
- `claude-3-sonnet` (mapped to `sonnet` alias)
- `claude-3.5-sonnet` (mapped to `sonnet` alias)
- `claude-3-opus` (mapped to `opus` alias)

If you see this error, verify your model name is in the supported list.

#### 9. Max Tokens Exceeded for Haiku

```bash
API Error: 400 {"message":"max_tokens: 8192 > 4096, which is the maximum allowed..."}
```

**Problem**: Haiku model has a 4096 token output limit, but the default is 8192.

**Solution**: The integration now automatically sets the correct max_tokens based on model. No action needed if using the updated code.

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
python -m swebench.inference.run_api ...
```

### Verify Integration

Test the complete SWE-bench → Claude Code → LLM flow:

```bash
# 1. Verify Claude Code CLI is working
claude --version

# 2. Test with a simple prompt
export ANTHROPIC_API_KEY="your-key-here"
claude -p "What is 2+2?" --output-format json --model haiku

# 3. Run single instance test
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path claude-3-haiku \
    --output_dir ./test_results \
    --model_args "max_instances=1,timeout=120" \
    --split test

# 4. Check output file
cat test_results/claude-3-haiku__SWE-bench_Lite_oracle__test.jsonl | python -m json.tool
```

## Advanced Features

### 1. Custom Prompting

The Claude Code adapter includes optimized prompts for patch generation. You can customize the prompting strategy by modifying the `prepare_claude_code_prompt` function in `swebench/inference/run_claude_code.py`.

### 2. Tool Integration

Claude Code can leverage additional tools for enhanced code understanding. Future versions may include:

- Code execution capabilities
- Git integration for better patch context
- Project-wide code analysis

### 3. Context Management

Claude Code maintains better context across requests, which can be beneficial for related issues in the same repository.

## Comparison with Standard Anthropic API

| Feature | Standard Anthropic API | Claude Code Agent |
|---------|------------------------|-------------------|
| **Backend Type** | Direct HTTP API calls | CLI subprocess calls |
| **Code Understanding** | Good | Excellent |
| **Patch Generation** | Basic text completion | Enhanced with coding tools |
| **Tool Integration** | None | Rich ecosystem (file ops, git, etc.) |
| **Context Management** | Stateless requests | Project-aware sessions |
| **Setup Complexity** | Simple (just API key) | Moderate (CLI + API key) |
| **Performance** | Fast HTTP requests | Optimized for code tasks |
| **Output Format** | Standard JSON | Enhanced with metadata |
| **Debugging** | Basic API logs | Detailed tool usage logs |
| **Model Names** | `claude-3-*-20240229` | `claude-3.5-sonnet`, `claude-code` |

### Key Behavioral Differences

**Standard Anthropic API:**
```json
{
  "instance_id": "test__example-1",
  "model_name_or_path": "claude-3-opus-20240229",
  "full_output": "Here's the fix...",
  "model_patch": "diff --git a/file.py..."
}
```

**Claude Code Agent:**
```json
{
  "instance_id": "test__example-1",
  "model_name_or_path": "claude-3.5-sonnet",
  "full_output": "Analysis: The issue is...\n\nSolution:\n```diff\n...",
  "model_patch": "diff --git a/file.py...",
  "claude_code_meta": {
    "tools_used": ["code_analysis", "diff_generation"],
    "usage": {"input_tokens": 150, "output_tokens": 300},
    "model_info": "claude-3.5-sonnet"
  }
}
```

### When to Use Each Backend

**Use Standard Anthropic API when:**
- You need simple, fast text completion
- You want minimal setup complexity
- You're doing bulk processing without enhanced code features
- You need compatibility with existing Anthropic API workflows

**Use Claude Code Agent when:**
- You want enhanced code understanding and generation
- You need better patch quality for complex issues
- You want detailed debugging information
- You're working on software engineering tasks specifically
- You want to leverage Claude's latest coding capabilities

## Best Practices

1. **Start Small**: Test with a few instances before running on the full dataset
2. **Monitor Resources**: Watch memory and CPU usage during large runs
3. **Use Appropriate Models**: Match model capability to problem complexity
4. **Set Reasonable Timeouts**: Balance between waiting for quality and avoiding hangs
5. **Regular Updates**: Keep Claude Code CLI updated for latest features

## Support and Contributing

### Getting Help

- Check the [SWE-bench Documentation](https://github.com/swe-bench/SWE-bench)
- Review [Claude Code Documentation](https://docs.anthropic.com/claude/docs/claude-code)
- File issues on the [SWE-bench GitHub Repository](https://github.com/swe-bench/SWE-bench/issues)

### Contributing

We welcome contributions to improve Claude Code integration:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Quick Reference

### ✅ Ensure Claude Code Usage Checklist

1. **Use correct model names:**
   ```bash
   # ✅ These use Claude Code:
   --model_name_or_path claude-3.5-sonnet
   --model_name_or_path claude-code
   --model_name_or_path claude-4

   # ❌ These use standard API:
   --model_name_or_path claude-3-opus-20240229
   --model_name_or_path claude-2
   ```

2. **Verify in logs:**
   ```bash
   # Look for this in output:
   "swebench.inference.run_claude_code - INFO - Starting Claude Code inference"
   ```

3. **Check output metadata:**
   ```bash
   # Should contain claude_code_meta:
   jq '.claude_code_meta' output.jsonl
   ```

4. **Quick verification:**
   ```bash
   python -c "print('claude-3.5-sonnet' in ['claude-4', 'claude-code', 'claude-3.5-sonnet', 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'])"
   # Should print: True
   ```

### 🚀 Recommended Commands

**For testing:**
```bash
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --model_name_or_path claude-3.5-sonnet \
    --output_dir ./test_results \
    --model_args "max_instances=5,timeout=300"
```

**For production:**
```bash
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --model_name_or_path claude-3.5-sonnet \
    --output_dir ./results \
    --model_args "timeout=450"
```

**For parallel processing:**
```bash
# Shard 1 of 4
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --model_name_or_path claude-3.5-sonnet \
    --output_dir ./results \
    --shard_id 0 \
    --num_shards 4
```

### 🔧 Environment Setup

```bash
# Required
export ANTHROPIC_API_KEY="your-key-here"

# Optional
export CLAUDE_CODE_TIMEOUT=300
export CLAUDE_CODE_MAX_TOKENS=8192
```

### 📊 Backend Verification Script

Save as `verify_backend.py`:
```python
#!/usr/bin/env python3
import sys

def check_backend(model):
    claude_code_models = ["claude-4", "claude-code", "claude-3.5-sonnet",
                         "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]

    if model in claude_code_models:
        print(f"✅ {model} → Claude Code Agent")
        return True
    elif model.startswith("claude"):
        print(f"❌ {model} → Standard Anthropic API")
        print("💡 Use one of:", ", ".join(claude_code_models))
        return False
    else:
        print(f"❓ {model} → Unknown backend")
        return False

if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "claude-3.5-sonnet"
    check_backend(model)
```

Run with: `python verify_backend.py your-model-name`

## Verification Test Results

The integration has been successfully tested with the following configuration:

### Test Configuration
- **Dataset**: `princeton-nlp/SWE-bench_Lite_oracle`
- **Model**: `claude-3-haiku` (mapped to `haiku` alias)
- **Instance**: `django__django-11099`
- **Duration**: ~13 seconds
- **Status**: ✅ Success (1/1 instances)

### Output Sample
```json
{
  "instance_id": "django__django-11099",
  "model_name_or_path": "claude-3-haiku",
  "full_output": "",
  "model_patch": "",
  "claude_code_meta": {
    "tools_used": [],
    "usage": {
      "input_tokens": 4,
      "cache_creation_input_tokens": 11117,
      "cache_read_input_tokens": 5246,
      "output_tokens": 547,
      "service_tier": "standard"
    },
    "model_info": "claude-3-haiku"
  }
}
```

### Key Indicators of Success
1. ✅ Log shows: `swebench.inference.run_claude_code - INFO - Starting Claude Code inference`
2. ✅ Model mapped correctly: `Calling Claude Code with model: haiku`
3. ✅ Output includes `claude_code_meta` field
4. ✅ Token usage tracked (input, output, cache)
5. ✅ Process completed without errors

### Model-Specific Behavior
- **Haiku**: Uses 4096 max_tokens automatically
- **Sonnet/Opus**: Uses 8192 max_tokens automatically
- **All models**: Benefit from prompt caching (see `cache_read_input_tokens`)

## License

This integration follows the same MIT license as the main SWE-bench project.

---

**Last Updated**: 2025-09-29
**Tested with**: Claude Code CLI v2.0.0, SWE-bench Latest