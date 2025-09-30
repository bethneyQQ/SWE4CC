# Loom Agent Integration for SWE-bench

本指南说明如何使用 Loom Agent API 在 SWE-bench 上进行评估。

## 概述

Loom Agent 提供 OpenAI 兼容的 API 接口，可以通过 SWE-bench 进行代码生成和修复任务的评估。

验证链路：**SWE-bench → ADE API Server → Claude Code CLI → Anthropic API**

## 环境配置

### 1. API 端点

默认端点：
```
http://114.112.75.90:5001/api/cline/openai_compatible/v1/chat/completions
```

可以通过环境变量或命令行参数自定义：
```bash
export LOOM_AGENT_BASE_URL="http://your-api-endpoint:port/api/path"
```

### 2. 请求头配置

API 需要以下请求头：
- `x-loom-client`: 客户端标识（默认: "swebench"）
- `x-loom-sessionid`: 会话 ID（默认: "1"）
- `x-loom-workspacepath`: 工作空间路径（默认: "/tmp/swebench"）

## 使用方法

### 基础使用

```bash
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --split test \
    --model_name_or_path loom-agent \
    --output_dir ./results
```

### 高级配置

使用 `--model_args` 参数自定义配置：

```bash
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --split test \
    --model_name_or_path loom-agent-claude \
    --output_dir ./results \
    --model_args "temperature=0.2,timeout=600,max_instances=10,stream=false"
```

### 可用模型

- `loom-agent`: 默认 Loom Agent 模型
- `loom-agent-claude`: 使用 Claude 后端的 Loom Agent

### 配置参数

通过 `--model_args` 可以设置以下参数（格式：`key=value,key=value`）：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `base_url` | string | 见上文 | API 端点 URL |
| `model` | string | `claude-sonnet-4-20250514` | 后端模型名称 |
| `temperature` | float | `0.2` | 采样温度 |
| `timeout` | int | `600` | 请求超时（秒）|
| `stream` | bool | `false` | 是否使用流式响应 |
| `client` | string | `swebench` | 客户端标识 |
| `session_id` | string | `1` | 会话 ID |
| `workspace_path` | string | `/tmp/swebench` | 工作空间路径 |
| `max_instances` | int | `None` | 最大处理实例数 |

### 成本控制

限制最大成本（美元）：

```bash
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --split test \
    --model_name_or_path loom-agent \
    --output_dir ./results \
    --max_cost 10.0
```

## 输出格式

结果保存为 JSONL 格式，每行包含：

```json
{
  "instance_id": "django__django-12345",
  "model_name_or_path": "loom-agent",
  "text": "原始问题描述...",
  "full_output": "模型完整输出...",
  "model_patch": "提取的 git diff 补丁...",
  "cost": 0.0123,
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 567
  }
}
```

## API 请求示例

### cURL 示例

```bash
curl -X POST \
  'http://114.112.75.90:5001/api/cline/openai_compatible/v1/chat/completions' \
  -H 'Content-Type: application/json' \
  -H 'x-loom-client: swebench' \
  -H 'x-loom-sessionid: 1' \
  -H 'x-loom-workspacepath: /tmp/swebench' \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "messages": [
      {
        "role": "user",
        "content": "修复以下代码问题..."
      }
    ],
    "temperature": 0.2,
    "stream": false
  }'
```

### Python 示例

```python
import requests

url = "http://114.112.75.90:5001/api/cline/openai_compatible/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "x-loom-client": "swebench",
    "x-loom-sessionid": "1",
    "x-loom-workspacepath": "/tmp/swebench"
}

payload = {
    "model": "claude-sonnet-4-20250514",
    "messages": [
        {"role": "user", "content": "修复以下代码问题..."}
    ],
    "temperature": 0.2,
    "stream": False
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()
content = result["choices"][0]["message"]["content"]
```

## 直接使用模块

也可以直接调用 Loom Agent 模块：

```bash
python -m swebench.inference.run_loom_agent \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --split test \
    --model_name_or_path loom-agent \
    --output_dir ./results \
    --model_args "temperature=0.2,timeout=600" \
    --base_url "http://your-custom-endpoint:port/api/path"
```

## 评估结果

运行推理后，使用 SWE-bench 评估工具：

```bash
# 评估结果
python -m swebench.metrics.get_resolution_status \
    --predictions results/loom_agent__SWE-bench_Lite__test.jsonl \
    --swe_bench_tasks princeton-nlp/SWE-bench_Lite \
    --output_dir evaluation_results

# 查看统计
python -m swebench.metrics.compute_metrics \
    --results evaluation_results/loom_agent__SWE-bench_Lite__test.json
```

## 故障排查

### 连接超时
- 检查 API 端点是否可访问
- 增加 `timeout` 参数值

### API 错误
- 检查请求头是否正确设置
- 验证后端模型名称是否有效

### 输出格式错误
- 确认 API 返回 OpenAI 兼容格式
- 检查 `choices[0].message.content` 字段是否存在

## 完整示例脚本

```bash
#!/bin/bash

# 设置变量
DATASET="princeton-nlp/SWE-bench_Lite"
MODEL="loom-agent-claude"
OUTPUT_DIR="./loom_agent_results"
MAX_COST=50.0

# 创建输出目录
mkdir -p $OUTPUT_DIR

# 运行推理
python -m swebench.inference.run_api \
    --dataset_name_or_path $DATASET \
    --split test \
    --model_name_or_path $MODEL \
    --output_dir $OUTPUT_DIR \
    --max_cost $MAX_COST \
    --model_args "temperature=0.1,timeout=900,stream=false"

# 评估结果
python -m swebench.metrics.get_resolution_status \
    --predictions $OUTPUT_DIR/loom_agent-claude__SWE-bench_Lite__test.jsonl \
    --swe_bench_tasks $DATASET \
    --output_dir $OUTPUT_DIR/evaluation

echo "评估完成！结果保存在: $OUTPUT_DIR"
```

## 参考资料

- [SWE-bench 官方文档](https://github.com/princeton-nlp/SWE-bench)
- [OpenAI API 兼容规范](https://platform.openai.com/docs/api-reference)
- Loom Agent API 内部文档