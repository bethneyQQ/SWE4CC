# Qwen & DeepSeek Quick Reference

## 🔑 API Configuration Comparison

### Qwen (DashScope)
```bash
# Environment variables
export DASHSCOPE_API_KEY="sk-xxx"     # Primary
# OR
export QWEN_API_KEY="sk-xxx"          # Alternative

# Optional: Custom endpoint
export QWEN_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
```

**Get API Key:** https://dashscope.console.aliyun.com/

### DeepSeek
```bash
# Environment variables
export DEEPSEEK_API_KEY="sk-xxx"

# Optional: Custom endpoint
export DEEPSEEK_API_BASE="https://api.deepseek.com"
```

**Get API Key:** https://platform.deepseek.com/

## 📊 Key Differences

| Feature | Qwen | DeepSeek |
|---------|------|----------|
| **Provider** | Alibaba Cloud (DashScope) | DeepSeek |
| **API Endpoint** | `dashscope.aliyuncs.com` | `api.deepseek.com` |
| **Key Format** | DashScope API key | DeepSeek API key |
| **Pricing** | Higher for Max models | Very cost-effective |
| **Context Length** | Up to 30K | Up to 128K (Coder V2) |
| **Special Features** | Chinese language优化 | Reasoning mode available |

## 🚀 Side-by-Side Comparison

### Same Task, Different Models

```bash
# Qwen Coder Plus
export DASHSCOPE_API_KEY="your-dashscope-key"
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path qwen-coder-plus \
    --output_dir ./results \
    --model_args "max_instances=10"

# DeepSeek Coder
export DEEPSEEK_API_KEY="your-deepseek-key"
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --model_name_or_path deepseek-coder \
    --output_dir ./results \
    --model_args "max_instances=10"
```

## 💡 Running Both Models Sequentially

```bash
#!/bin/bash

# Set both API keys
export DASHSCOPE_API_KEY="your-dashscope-key"
export DEEPSEEK_API_KEY="your-deepseek-key"

DATASET="princeton-nlp/SWE-bench_Lite_oracle"
OUTPUT_DIR="./results"
INSTANCES=10

# Run Qwen
echo "Running Qwen Coder Plus..."
python -m swebench.inference.run_api \
    --dataset_name_or_path $DATASET \
    --model_name_or_path qwen-coder-plus \
    --output_dir $OUTPUT_DIR \
    --model_args "max_instances=$INSTANCES,timeout=300"

# Run DeepSeek
echo "Running DeepSeek Coder..."
python -m swebench.inference.run_api \
    --dataset_name_or_path $DATASET \
    --model_name_or_path deepseek-coder \
    --output_dir $OUTPUT_DIR \
    --model_args "max_instances=$INSTANCES,timeout=300"

echo "Both models completed!"
```

## 🔧 Using Custom/Local Endpoints

### Qwen with Custom Endpoint
```bash
# If using a local Qwen deployment or proxy
export QWEN_API_KEY="local-key"
export QWEN_API_BASE="http://localhost:8000/v1"

python -m swebench.inference.run_api \
    --model_name_or_path qwen-coder-plus \
    ...
```

### DeepSeek with Custom Endpoint
```bash
# If using a local DeepSeek deployment or proxy
export DEEPSEEK_API_KEY="local-key"
export DEEPSEEK_API_BASE="http://localhost:8001/v1"

python -m swebench.inference.run_api \
    --model_name_or_path deepseek-coder \
    ...
```

## 📝 Configuration File Approach

Create a `.env` file in your project root:

```bash
# .env file
# Qwen Configuration
DASHSCOPE_API_KEY=sk-your-dashscope-key-here
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

# DeepSeek Configuration
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com

# SWE-bench Configuration
MAX_INSTANCES=10
TIMEOUT=300
```

Then load it:
```bash
# Load environment variables
source .env
# Or use python-dotenv (already included in swebench)
```

## ⚠️ Important Notes

### They Are NOT Interchangeable!

1. **Different API Providers**:
   - Qwen uses Alibaba Cloud DashScope
   - DeepSeek uses DeepSeek's own API

2. **Different API Keys**:
   - You need separate accounts and API keys
   - Keys are NOT compatible between providers

3. **Different Endpoints**:
   - Qwen: `https://dashscope.aliyuncs.com/...`
   - DeepSeek: `https://api.deepseek.com/...`

4. **Different Pricing**:
   - Check respective provider pricing pages
   - DeepSeek is generally more cost-effective

### Can I Use One Key for Both?

**NO.** You need:
- ✅ A DashScope/Alibaba Cloud account → Qwen API key
- ✅ A DeepSeek account → DeepSeek API key

## 🎯 Quick Test Script

Test both APIs are working correctly:

```bash
#!/bin/bash
# test_apis.sh

echo "Testing Qwen API..."
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "❌ DASHSCOPE_API_KEY not set"
else
    curl -s -X POST "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" \
      -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"model":"qwen-turbo","messages":[{"role":"user","content":"Hello"}],"max_tokens":10}' \
      | jq '.choices[0].message.content' && echo "✅ Qwen API working" || echo "❌ Qwen API failed"
fi

echo ""
echo "Testing DeepSeek API..."
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "❌ DEEPSEEK_API_KEY not set"
else
    curl -s -X POST "https://api.deepseek.com/v1/chat/completions" \
      -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Hello"}],"max_tokens":10}' \
      | jq '.choices[0].message.content' && echo "✅ DeepSeek API working" || echo "❌ DeepSeek API failed"
fi
```

Run with:
```bash
chmod +x test_apis.sh
./test_apis.sh
```

## 📊 Cost Estimation

Before running full evaluation:

```bash
# Test with 5 instances first
python -m swebench.inference.run_api \
    --model_name_or_path qwen-turbo \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
    --output_dir ./results \
    --model_args "max_instances=5"

# Check cost
jq '.cost' results/qwen-turbo*.jsonl | jq -s 'add'

# Estimate full run
# If 5 instances cost $0.50, then 300 instances ≈ $30
```

## 🔄 Switching Between Models

```bash
# Use shell function for easy switching
run_swebench() {
    local model=$1
    local instances=${2:-10}

    python -m swebench.inference.run_api \
        --dataset_name_or_path princeton-nlp/SWE-bench_Lite_oracle \
        --model_name_or_path $model \
        --output_dir ./results \
        --model_args "max_instances=$instances,timeout=300"
}

# Usage
run_swebench qwen-coder-plus 10
run_swebench deepseek-coder 10
```

## 📚 Additional Resources

- **Qwen Documentation**: https://help.aliyun.com/zh/dashscope/
- **DeepSeek Documentation**: https://platform.deepseek.com/docs
- **SWE-bench Integration Guide**: [qwen_deepseek_integration.md](qwen_deepseek_integration.md)

---

**Last Updated**: 2025-09-29