# SWE-bench Enhanced Prediction Analysis Report

**Generated:** 2025-10-04T07:38:34.236182
**Model:** claude-sonnet-4-5
**Dataset:** SWE-bench_Lite_oracle

## 📊 Executive Summary

- **Total Instances:** 1
- **Resolved:** 1
- **Success Rate:** 100.0%
- **Average Cost:** $0.0890
- **Average Latency:** 22.3s
- **Enhanced Features:** ✅ Enabled
- **Cache Efficiency:** 100.0%

## 📋 Field Inventory

**Total Unique Fields:** 13

### Available Fields

- `claude_code_meta`
- `claude_code_meta.attempts`
- `claude_code_meta.enhanced`
- `claude_code_meta.repo_path`
- `claude_code_meta.response_data`
- `claude_code_meta.tools_available`
- `claude_code_meta.validation_errors`
- `cost`
- `full_output`
- `instance_id`
- `latency_ms`
- `model_name_or_path`
- `model_patch`

## 🗂️ Standard Schema Mapping

### Identification
- `instance_id`

### Model Info
- `model_name_or_path`

### Output
- `model_patch`
- `full_output`

### Performance
- `latency_ms`
- `cost`

### Enhanced Metadata
- `claude_code_meta`

## ✅ Evaluation Results

- **Total Instances in Dataset:** 300
- **Submitted for Evaluation:** 1
- **Completed:** 1
- **Resolved (Passed Tests):** 1
- **Unresolved:** 0
- **Empty Patches:** 0
- **Errors:** 0

### Resolved Instances
- ✅ `django__django-11099`

## 📈 Combined Metrics

- **Success Rate:** 100.0%
- **Completion Rate:** 100.0%
- **Error Rate:** 0.0%
- **Empty Patch Rate:** 0.0%
- **Average Cost per Resolved:** $0.0890
- **Average Latency per Resolved:** 22.3s
- **First Attempt Success Rate:** 100.0%

## 💰 Cost Analysis

- **Total Cost:** $0.0890
- **Average Cost:** $0.0890
- **Min Cost:** $0.0890
- **Max Cost:** $0.0890
- **Median Cost:** $0.0890

## ⏱️ Latency Analysis

- **Average Latency:** 22.3s
- **Min Latency:** 22.3s
- **Max Latency:** 22.3s
- **Median Latency:** 22.3s
- **P95 Latency:** 22.3s

## 📝 Patch Analysis

- **Patches Generated:** 1
- **Empty Patches:** 0
- **Average Patch Size:** 784 bytes
- **Min Patch Size:** 784 bytes
- **Max Patch Size:** 784 bytes

## 🤖 Agent-Specific Metrics

### Retry Analysis
- **Average Attempts:** 1.0
- **Max Attempts:** 1
- **First Attempt Success:** 1
- **Required Retry:** 0

### Validation Analysis
- **Total Validation Errors:** 0
- **Instances with Errors:** 0
- **Clean Validations:** 1

### Interaction Analysis
- **Average Turns:** 12.0
- **Min Turns:** 12
- **Max Turns:** 12
- **Total Turns:** 12

### Enhanced Features
- **Using Enhanced Mode:** 1
- **Using Tools:** 1
- **Repo Access:** 1

## 🎯 Quality Metrics

### Token Usage
- **Total Cache Creation:** 15,668
- **Total Cache Read:** 54,427
- **Total Input:** 26
- **Total Output:** 872
- **Avg Cache Creation:** 15668
- **Avg Cache Read:** 54427
- **Avg Input:** 26
- **Avg Output:** 872

### Cache Efficiency
- **Cache Hit Rate:** 100.0%
- **Total Tokens Saved:** 54,427

## 💡 Resource Efficiency

### Cost Efficiency
- **Cost per Patch:** $0.0890
- **Cost per Turn:** $0.0074

### Time Efficiency
- **Latency per Turn:** 1860ms
- **Total Time:** 22.3s

## 📊 Per-Instance Details

| Instance ID | Cost | Latency | Patch Size | Attempts | Turns | Errors |
|-------------|------|---------|------------|----------|-------|--------|
| `django__django-11099` | $0.0890 | 22.3s | 784 B | 1 | 12 | 0 |

## 🔧 Quick Analysis Commands

### Extract Specific Fields
```bash
# Get all instance IDs
jq -r '.instance_id' predictions.jsonl

# Get cost summary
jq -s 'map(.cost) | {total: add, avg: (add/length), min: min, max: max}' predictions.jsonl

# Get instances with validation errors
jq -r 'select(.claude_code_meta.validation_errors | length > 0) | .instance_id' predictions.jsonl

# Get cache hit rate
jq -s 'map(.claude_code_meta.response_data.usage | {cache_read: .cache_read_input_tokens, input: .input_tokens}) | {total_cache: map(.cache_read) | add, total_input: map(.input) | add} | .total_cache / (.total_cache + .total_input)' predictions.jsonl
```

## 💡 Recommendations

✅ **Excellent performance!** All submitted instances were resolved successfully.

✅ **Excellent cache utilization!** High cache hit rate reduces costs.

✅ **Perfect first-attempt success rate!** Validation is working well.
