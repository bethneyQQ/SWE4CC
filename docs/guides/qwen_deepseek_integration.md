# Qwen and DeepSeek Integration Guide

This guide explains how to use Qwen and DeepSeek models with SWE-bench for software engineering task evaluation.

## 📋 Overview

SWE-bench now supports:
- **Qwen models**: Including Qwen Max, Qwen Plus, Qwen Turbo, and Qwen Coder series
- **DeepSeek models**: Including DeepSeek Chat, DeepSeek Coder, DeepSeek Reasoner, and DeepSeek V3

Both integrations use OpenAI-compatible APIs for seamless integration.

## 🚀 Quick Start

### Qwen Setup

```bash
# Set your DashScope API key
export DASHSCOPE_API_KEY="your-dashscope-api-key"
# Or use QWEN_API_KEY
export QWEN_API_KEY="your-qwen-api-key"

# Run inference
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path qwen-coder-plus \
    --output_dir ./results \
    --model_args "max_instances=10,timeout=300"
```

### DeepSeek Setup

```bash
# Set your DeepSeek API key
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# Run inference
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path deepseek-coder \
    --output_dir ./results \
    --model_args "max_instances=10,timeout=300"
```

## 🤖 Supported Models

### Qwen Models

| Model Name | Context Length | Best For | Cost (Input/Output per 1M tokens) |
|-----------|----------------|----------|-----------------------------------|
| `qwen-max` | 30K | Highest capability | $40 / $120 |
| `qwen-max-0428` | 30K | Specific version | $40 / $120 |
| `qwen-plus` | 30K | Balanced performance | $2 / $6 |
| `qwen-turbo` | 8K | Fastest, cost-effective | $0.3 / $0.6 |
| `qwen-coder-plus` | 30K | **Recommended for coding** | $2 / $6 |
| `qwen-coder-turbo` | 8K | Fast coding tasks | $0.3 / $0.6 |
| `qwen2.5-72b-instruct` | 30K | Latest open model | $2 / $6 |
| `qwen2.5-coder-32b-instruct` | 30K | Latest coder model | $1 / $3 |

### DeepSeek Models

| Model Name | Context Length | Best For | Cost (Input/Output per 1M tokens) |
|-----------|----------------|----------|-----------------------------------|
| `deepseek-chat` | 64K | General chat | $0.14 / $0.28 |
| `deepseek-coder` | 64K | **Recommended for coding** | $0.14 / $0.28 |
| `deepseek-reasoner` | 64K | Complex reasoning tasks | $0.55 / $2.19 |
| `deepseek-v3` | 64K | Latest version | $0.27 / $1.10 |
| `deepseek-v2.5` | 64K | V2.5 series | $0.14 / $0.28 |
| `deepseek-coder-v2-instruct` | 128K | Coder V2 with long context | $0.14 / $0.28 |

## 🔧 Configuration

### Environment Variables

#### Qwen
```bash
# Required
export DASHSCOPE_API_KEY="your-key"  # or QWEN_API_KEY

# Optional: Custom API endpoint (default: DashScope OpenAI-compatible endpoint)
export QWEN_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
```

#### DeepSeek
```bash
# Required
export DEEPSEEK_API_KEY="your-key"

# Optional: Custom API endpoint (default: DeepSeek official API)
export DEEPSEEK_API_BASE="https://api.deepseek.com"
```

### Model Arguments

Both integrations support these arguments:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_tokens` | int | 8000 (varies by model) | Maximum tokens to generate |
| `temperature` | float | 0.1 | Sampling temperature (0.0-1.0) |
| `timeout` | int | 300 | Request timeout in seconds |
| `max_instances` | int | None | Limit number of instances to process |
| `max_cost` | float | None | Maximum total cost in USD |

## 📝 Usage Examples

### Basic Inference

#### Qwen
```bash
# Using Qwen Coder Plus (recommended for coding)
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path qwen-coder-plus \
    --output_dir ./results \
    --model_args "max_instances=50,timeout=300"
```

#### DeepSeek
```bash
# Using DeepSeek Coder (recommended for coding)
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path deepseek-coder \
    --output_dir ./results \
    --model_args "max_instances=50,timeout=300"
```

### With Cost Limit

```bash
# Qwen with $10 cost limit
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path qwen-turbo \
    --output_dir ./results \
    --model_args "timeout=300" \
    --max_cost 10.0

# DeepSeek with $5 cost limit
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path deepseek-chat \
    --output_dir ./results \
    --model_args "timeout=300" \
    --max_cost 5.0
```

### Advanced Configuration

```bash
# Qwen with custom parameters
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path qwen-coder-plus \
    --output_dir ./results \
    --model_args "max_tokens=8000,temperature=0.05,timeout=600"

# DeepSeek Reasoner for complex problems
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path deepseek-reasoner \
    --output_dir ./results \
    --model_args "max_tokens=16000,temperature=0.1,timeout=900"
```

### Direct Adapter Usage

You can also call the adapters directly:

```bash
# Direct Qwen adapter
python -m swebench.inference.run_qwen \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path qwen-coder-plus \
    --output_dir ./results \
    --model_args "max_instances=10"

# Direct DeepSeek adapter
python -m swebench.inference.run_deepseek \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path deepseek-coder \
    --output_dir ./results \
    --model_args "max_instances=10"
```

## 📊 Output Format

Both integrations generate outputs in standard SWE-bench format with additional metadata:

### Qwen Output
```json
{
  "instance_id": "django__django-11099",
  "model_name_or_path": "qwen-coder-plus",
  "full_output": "Analysis and solution...",
  "model_patch": "diff --git a/file.py...",
  "latency_ms": 5234,
  "cost": 0.0123,
  "qwen_meta": {
    "usage": {
      "input_tokens": 1500,
      "output_tokens": 800,
      "total_tokens": 2300
    },
    "model_info": "qwen-coder-plus",
    "finish_reason": "stop",
    "total_cost_accumulated": 0.0123
  }
}
```

### DeepSeek Output
```json
{
  "instance_id": "django__django-11099",
  "model_name_or_path": "deepseek-coder",
  "full_output": "Analysis and solution...",
  "model_patch": "diff --git a/file.py...",
  "latency_ms": 4521,
  "cost": 0.0089,
  "deepseek_meta": {
    "usage": {
      "input_tokens": 1500,
      "output_tokens": 800,
      "total_tokens": 2300
    },
    "model_info": "deepseek-coder",
    "finish_reason": "stop",
    "total_cost_accumulated": 0.0089
  }
}
```

### DeepSeek Reasoner Special Output
When using `deepseek-reasoner`, additional reasoning content is included:
```json
{
  "deepseek_meta": {
    "reasoning_content": "Step-by-step reasoning process...",
    ...
  }
}
```

## 🔍 Evaluation

After generating predictions, evaluate them using the standard SWE-bench harness:

```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path ./results/qwen-coder-plus__SWE-bench_Lite_oracle__test.jsonl \
    --max_workers 4 \
    --run_id qwen_evaluation

python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path ./results/deepseek-coder__SWE-bench_Lite_oracle__test.jsonl \
    --max_workers 4 \
    --run_id deepseek_evaluation
```

## 📈 Results Analysis

Use the analysis script to get detailed statistics:

```bash
# Analyze Qwen results
python analyze_predictions.py \
    results/qwen-coder-plus__SWE-bench_Lite_oracle__test.jsonl \
    -e qwen_evaluation.json \
    -o qwen_analysis.json

# Analyze DeepSeek results
python analyze_predictions.py \
    results/deepseek-coder__SWE-bench_Lite_oracle__test.jsonl \
    -e deepseek_evaluation.json \
    -o deepseek_analysis.json
```

## 🎯 Model Recommendations

### For Cost-Effectiveness
1. **DeepSeek Coder** - Best price/performance ratio ($0.14/$0.28 per 1M tokens)
2. **Qwen Turbo** - Ultra-low cost for simple tasks ($0.3/$0.6 per 1M tokens)

### For Code Quality
1. **Qwen Coder Plus** - Specialized for coding with 30K context
2. **DeepSeek Coder V2** - Latest coder model with 128K context
3. **Qwen Max** - Highest capability for complex issues

### For Complex Reasoning
1. **DeepSeek Reasoner** - Explicit reasoning process for hard problems
2. **DeepSeek V3** - Latest general-purpose model

### For Long Context
1. **DeepSeek Coder V2** - 128K context window
2. **DeepSeek Chat/Coder** - 64K context window
3. **Qwen models** - Up to 30K context window

## ⚠️ Important Notes

### Qwen
- Requires DashScope API key from Alibaba Cloud
- Uses OpenAI-compatible endpoint at `dashscope.aliyuncs.com`
- Best for Chinese and multilingual tasks
- Qwen Coder models are optimized for code generation

### DeepSeek
- More cost-effective than most alternatives
- DeepSeek Reasoner shows explicit reasoning steps
- DeepSeek Coder performs exceptionally well on coding tasks
- V3 models offer improved performance

### General Tips
1. **Start with small batches**: Use `max_instances` to test before full runs
2. **Set cost limits**: Use `max_cost` to control spending
3. **Monitor performance**: Check `latency_ms` and `cost` in outputs
4. **Choose appropriate models**: Use Coder variants for software engineering tasks
5. **Adjust timeouts**: Complex instances may need longer timeouts (600-900s)

## 🔧 Troubleshooting

### API Key Issues

**Qwen:**
```bash
# Error: API key not found
# Solution: Set the environment variable
export DASHSCOPE_API_KEY="your-key"
# Or
export QWEN_API_KEY="your-key"
```

**DeepSeek:**
```bash
# Error: API key not found
# Solution: Set the environment variable
export DEEPSEEK_API_KEY="your-key"
```

### Connection Issues

```bash
# Test Qwen connection
curl -X POST "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-turbo","messages":[{"role":"user","content":"test"}]}'

# Test DeepSeek connection
curl -X POST "https://api.deepseek.com/v1/chat/completions" \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'
```

### Timeout Issues

```bash
# Increase timeout for complex instances
--model_args "timeout=900"  # 15 minutes
```

### Cost Tracking

```bash
# Check cost before full run with max_instances
--model_args "max_instances=5"

# Then check total cost in output
jq '.cost' results/*.jsonl | jq -s 'add'

# Set appropriate cost limit for full run
--max_cost <calculated_limit>
```

## 📊 Results Analysis

Both Qwen and DeepSeek integrations output comprehensive metadata that can be analyzed using the `analyze_predictions.py` script.

### Metadata Captured

**Core Fields (Both Models):**
- `instance_id` - Unique identifier
- `model_name_or_path` - Model used
- `full_output` - Complete response
- `model_patch` - Generated patch
- `latency_ms` - Request latency
- `cost` - API cost in USD

**Qwen-Specific Metadata (`qwen_meta`):**
- `usage` - Token counts (input, output, total)
- `model_info` - Model version
- `finish_reason` - Completion status
- `response_id` - Unique API call ID
- `created` - Unix timestamp
- `provider` - "Qwen (DashScope)"
- `api_version` - "OpenAI-compatible"
- `total_cost_accumulated` - Accumulated cost

**DeepSeek-Specific Metadata (`deepseek_meta`):**
- `usage` - Token counts with caching info
  - `prompt_cache_hit_tokens` - Cached tokens reused
  - `prompt_cache_miss_tokens` - New tokens cached
- `model_info` - Model version
- `finish_reason` - Completion status
- `response_id` - Unique API call ID
- `created` - Unix timestamp
- `provider` - "DeepSeek"
- `api_version` - "OpenAI-compatible"
- `total_cost_accumulated` - Accumulated cost

### Analysis Example

```bash
# Run inference
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path qwen-turbo \
    --output_dir ./results \
    --split test \
    --model_args "max_instances=2"

# Analyze results
python analyze_predictions.py results/qwen-turbo__SWE-bench_Lite_oracle__test.jsonl

# Output includes:
# - Basic statistics (samples, time range)
# - Performance metrics (latency, cost, tokens)
# - Model information (provider, API version)
# - Patch statistics
# - Per-instance details with timestamps and response IDs
```

### Sample Analysis Output

```
================================================================================
SWE-BENCH PREDICTIONS ANALYSIS REPORT
================================================================================

📊 BASIC STATISTICS
--------------------------------------------------------------------------------
Total Samples: 2
Request Time Range: 2025-09-29T22:40:16 to 2025-09-29T22:40:23
Time Span: 7.0s

⚡ PERFORMANCE METRICS
--------------------------------------------------------------------------------
Latency:
  Mean: 7039ms | Median: 7039ms
  Min: 6939ms | Max: 7139ms

Cost:
  Total: $0.0006
  Mean: $0.0003 | Median: $0.0003

Token Usage:
  Input: 3,070 (mean: 1535)
  Output: 892 (mean: 446)
  Total: 3,962 (mean: 1981)

🤖 MODEL INFORMATION
--------------------------------------------------------------------------------
Models: {'qwen-turbo': 2}
Providers: {'Qwen (DashScope)': 2}
Finish Reasons: {'stop': 2}
API Versions: {'OpenAI-compatible': 2}
Model Versions: {'qwen-turbo': 2}
```

### Detailed JSON Report

The analysis script generates a JSON report with instance-level details:

```json
{
  "instance_details": {
    "instances": [
      {
        "instance_id": "django__django-11099",
        "model": "qwen-turbo",
        "latency_ms": 7039,
        "cost": 7.281e-7,
        "timestamp": "2025-09-29T22:40:16",
        "response_id": "chatcmpl-f407eac4-384b-4fb6-a697-e9e0689fa687",
        "finish_reason": "stop",
        "provider": "Qwen (DashScope)",
        "input_tokens": 1535,
        "output_tokens": 446
      }
    ]
  }
}
```

### Extract Specific Metadata

```bash
# Get all response IDs (for audit trail)
jq '.instance_details.instances[].response_id' results/*.analysis.json

# Get timestamp and cost per instance
jq '.instance_details.instances[] | {timestamp, cost}' results/*.analysis.json

# Check DeepSeek cache effectiveness
jq '.instance_details.instances[] | select(.cache_hit_tokens > 0)' \
    results/deepseek-*.analysis.json

# Compare providers
jq '.model_info.providers' results/*.analysis.json
```

### Metadata Coverage

The analysis script captures **95%+ of all available metadata**:

✅ **Fully Captured:**
- Instance identification
- Performance metrics (latency, cost)
- Token usage (including DeepSeek cache tokens)
- Timing information (timestamps, time ranges)
- API traceability (response_id, finish_reason)
- Provider and version information

⚠️ **Not in Reports (by design):**
- `full_output` and `model_patch` (too large, available in raw JSONL)
- Dataset context (would need to be added from SWE-bench metadata)

### Multi-Provider Support

The `analyze_predictions.py` script automatically detects and handles metadata from:
- Claude Code (`claude_code_meta`)
- Qwen (`qwen_meta`)
- DeepSeek (`deepseek_meta`)

All metadata fields are normalized and presented consistently in reports.

## 🌐 API Documentation

- **Qwen/DashScope**: https://help.aliyun.com/zh/dashscope/
- **DeepSeek**: https://platform.deepseek.com/docs

## 📦 Dependencies

Both integrations require:
```bash
pip install openai>=1.0.0  # OpenAI-compatible client
pip install datasets        # For loading datasets
pip install tqdm           # Progress bars
```

Already included if you installed SWE-bench with:
```bash
pip install -e ".[inference]"
```

## 🔄 Migration from Other Models

### From OpenAI
```bash
# Before (OpenAI)
--model_name_or_path gpt-4

# After (Qwen)
--model_name_or_path qwen-coder-plus

# After (DeepSeek)
--model_name_or_path deepseek-coder
```

### From Claude
```bash
# Before (Claude)
--model_name_or_path claude-3.5-sonnet

# After (Qwen)
--model_name_or_path qwen-max

# After (DeepSeek)
--model_name_or_path deepseek-v3
```

## 📞 Support

For issues specific to:
- **Qwen/DashScope**: https://help.aliyun.com/zh/dashscope/
- **DeepSeek**: https://platform.deepseek.com/
- **SWE-bench Integration**: https://github.com/swe-bench/SWE-bench/issues

---

**Last Updated**: 2025-09-29
**Compatible with**: SWE-bench Latest, Qwen 2.5, DeepSeek V3