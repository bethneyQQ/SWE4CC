# Loom Agent 启动清单

等拿到 API key 后，按以下步骤操作即可开始测试。

## 📋 前置准备

### 1. 确认 API 信息

- [ ] API Endpoint: `http://114.112.75.90:5001/api/cline/openai_compatible/v1/chat/completions`
- [ ] API Key: (待获取)
- [ ] 后端模型: `claude-sonnet-4-20250514` (或其他可用模型)

### 2. 检查依赖

```bash
cd /home/shared/zqq/SWE4CC

# 检查必要的 Python 包
python3 -c "import requests; print('✅ requests installed')"
python3 -c "import datasets; print('✅ datasets installed')"
python3 -c "import tqdm; print('✅ tqdm installed')"
```

如果有缺失，安装：
```bash
pip install requests datasets tqdm tenacity
```

---

## 🚀 测试步骤

### Step 1: API 连接测试 (约 1 分钟)

```bash
# 如果 API 需要 key，先设置环境变量
export LOOM_AGENT_API_KEY="your-api-key-here"

# 运行连接测试
python3 test_loom_agent_connection.py
```

**预期结果**：
- ✅ 看到 "SUCCESS! API is reachable"
- ✅ 看到 API 返回的响应内容
- ✅ 看到 token 使用统计

**如果失败**：
- 检查 API endpoint 是否正确
- 检查网络连接
- 确认 API 是否需要在请求头中添加 API key

---

### Step 2: 完整集成验证 (约 2-3 分钟)

```bash
./verify_loom_integration.sh
```

**预期结果**：
```
✅ All Verification Steps Passed!
Your Loom Agent integration is working correctly!
```

**如果失败**：
- 查看具体是哪一步失败
- 检查错误日志
- 可能需要调整代码以适配你的 API key 认证方式

---

### Step 3: 小规模测试 (测试 5 个实例，约 5-10 分钟)

```bash
# 设置只测试 5 个实例
export MAX_INSTANCES=5
export OUTPUT_DIR="./results/test_run"

./example_loom_agent.sh
```

**预期输出**：
```
================================================================================
🚀 Starting Loom Agent inference
================================================================================
📍 API Endpoint: http://114.112.75.90:5001/...
🤖 Backend Model: claude-sonnet-4-20250514
...

Processing: 100%|████████████| 5/5
✅ Loom Agent inference completed!
   Success rate: 5/5 instances
```

**查看结果**：
```bash
# 查看生成的预测文件
ls -lh results/test_run/*.jsonl

# 查看前几行结果
head -n 1 results/test_run/*.jsonl | jq .
```

---

### Step 4: 完整评估 (可选，数小时)

如果小规模测试成功，可以运行完整评估：

```bash
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --split test \
    --model_name_or_path loom-agent \
    --output_dir ./results/full_eval \
    --model_args "temperature=0.2,timeout=600"
```

**SWE-bench Lite 规模**：
- 约 300 个实例
- 预计耗时：3-6 小时（取决于 API 速度）
- 预计成本：$10-30（取决于定价）

---

## 🔧 API Key 集成方式

如果你的 API 需要 key 认证，有以下几种方式：

### 方式 1: 环境变量（推荐）

```bash
export LOOM_AGENT_API_KEY="your-api-key"
```

然后修改代码读取：
```python
# 在 run_loom_agent.py 的 call_loom_agent 函数中
api_key = os.environ.get("LOOM_AGENT_API_KEY")
if api_key:
    headers["Authorization"] = f"Bearer {api_key}"
    # 或者其他格式，如：
    # headers["X-API-Key"] = api_key
```

### 方式 2: 通过 model_args 传递

```bash
python -m swebench.inference.run_api \
    --model_name_or_path loom-agent \
    --model_args "api_key=your-key,temperature=0.2" \
    ...
```

### 方式 3: 写入配置文件

创建 `.env` 文件：
```bash
echo "LOOM_AGENT_API_KEY=your-api-key" > .env
```

---

## 📝 根据你的 API 需求调整

### 如果 API key 在请求头中

编辑 `swebench/inference/run_loom_agent.py` 第 93-99 行：

```python
def call_loom_agent(
    base_url: str,
    messages: List[Dict],
    model: str = "claude-sonnet-4-20250514",
    temperature: float = 0.2,
    api_key: str = None,  # ← 添加这个参数
    ...
):
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "x-loom-client": client,
        "x-loom-sessionid": session_id,
        "x-loom-workspacepath": workspace_path,
    }

    # 添加 API key（根据你的 API 要求调整）
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        # 或者： headers["X-API-Key"] = api_key
        # 或者： headers["api-key"] = api_key
```

### 如果 API key 在 URL 参数中

```python
if api_key:
    base_url = f"{base_url}?api_key={api_key}"
```

### 如果 API key 在请求体中

```python
payload = {
    "model": model,
    "messages": messages,
    "temperature": temperature,
    "stream": stream,
    "api_key": api_key,  # ← 添加到 payload
}
```

---

## 🐛 常见问题

### Q: 如何确认用的是 Loom Agent？
**A**: 查看日志中的 `🚀 Starting Loom Agent inference` 和 API endpoint URL

### Q: 超时怎么办？
**A**: 增加 timeout：`--model_args "timeout=1200"`（20分钟）

### Q: 成本如何估算？
**A**:
- 每个实例平均 ~5K tokens 输入，~2K tokens 输出
- 300 个实例 ≈ 1.5M input + 600K output tokens
- 成本取决于你的定价

### Q: 如何暂停和恢复？
**A**:
- 脚本支持断点续传
- 按 Ctrl+C 暂停
- 再次运行相同命令会自动跳过已完成的实例

### Q: 输出文件在哪里？
**A**: `./results/loom_agent__<dataset>__<split>.jsonl`

---

## 📞 需要帮助时

1. **查看日志**：运行时的详细日志会显示每一步
2. **检查输出文件**：`cat results/*.jsonl | jq .` 查看 JSON 格式
3. **测试单个请求**：用 `test_loom_agent_connection.py` 隔离测试
4. **检查 API 日志**：在你的服务器上查找对应的 session ID

---

## ✅ 准备好了吗？

拿到 API key 后，执行：

```bash
# 1. 快速测试（必做）
python3 test_loom_agent_connection.py

# 2. 小规模测试（推荐）
MAX_INSTANCES=5 ./example_loom_agent.sh

# 3. 完整评估（可选）
python -m swebench.inference.run_api \
    --dataset_name_or_path princeton-nlp/SWE-bench_Lite \
    --split test \
    --model_name_or_path loom-agent \
    --output_dir ./results
```

祝测试顺利！🚀