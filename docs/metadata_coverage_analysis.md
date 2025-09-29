# SWE-bench Predictions Metadata Coverage Analysis

## 📋 完整字段对比：Claude Code vs Qwen vs DeepSeek

本文档对比三个模型适配器的元数据完整性，基于你提供的完整字段清单。

---

## 一、核心原始字段对比

### ✅ 已实现字段

| 推荐字段 | Claude Code | Qwen | DeepSeek | 说明 |
|---------|-------------|------|----------|------|
| **case_id / id** | ✅ `instance_id` | ✅ `instance_id` | ✅ `instance_id` | 样例唯一标识 |
| **model_name / model_version** | ✅ `model_name_or_path` + `model_info` | ✅ `model_name_or_path` + `model_info` | ✅ `model_name_or_path` + `model_info` | 模型标识 |
| **prediction / output** | ✅ `full_output` | ✅ `full_output` | ✅ `full_output` | 模型生成的主输出 |
| **diff / patch** | ✅ `model_patch` | ✅ `model_patch` | ✅ `model_patch` | 代码修改补丁 |
| **latency_ms** | ✅ | ✅ | ✅ | 请求耗时（毫秒）|
| **cost / billing_cost** | ✅ | ✅ | ✅ | 调用费用估算 |
| **token_usage** | ✅ 详细 | ✅ 完整 | ✅ 完整 | Token 计数 |
| **input_tokens** | ✅ | ✅ | ✅ | 输入 token 数 |
| **output_tokens** | ✅ | ✅ | ✅ | 输出 token 数 |
| **timestamp / created** | ❌ | ✅ `created` | ✅ `created` | 执行时间戳 |

### ❌ 缺失字段（三个模型均未实现）

| 推荐字段 | 说明 | 建议 |
|---------|------|------|
| **dataset** | 数据集名称 | ⚠️ 可从文件名推断但未显式存储 |
| **split** | 数据集拆分（train/val/test）| ⚠️ 可从文件名推断但未显式存储 |
| **prompt / input** | 原始 prompt 文本 | ⚠️ 未存储（为节省空间）|
| **system_message** | system prompt | ❌ 未存储 |
| **gold / reference** | 参考答案 | ❌ 在数据集中，不在 predictions |
| **passed / tests_passed** | 是否通过测试 | ❌ 需要评估后才有（在 evaluation.json） |
| **test_result / tests** | 详细测试结果 | ❌ 需要评估后才有 |
| **error / exception** | 调用出错信息 | ⚠️ 失败时记录在日志，未存 JSON |
| **http_status / http_code** | HTTP 状态码 | ❌ 未存储 |
| **model_args** | temperature 等参数 | ❌ 未存储在输出中 |
| **seed / random_state** | 随机种子 | ❌ 未存储 |
| **run_id / experiment_id** | 评测作业标识 | ❌ 未存储 |
| **worker / host** | 执行机器信息 | ❌ 未存储 |
| **retries** | 重试次数 | ❌ 未实现 |
| **confidence / score** | 置信分 | ❌ API 不返回 |
| **meta / tags** | 任意元信息 | ⚠️ 部分在 `*_meta` 中 |

---

## 二、详细元数据字段对比

### Claude Code 独有字段 ✨

```json
{
  "claude_code_meta": {
    "tools_used": [],                          // ✅ 工具使用列表
    "cache_creation_input_tokens": 11370,      // ✅ 缓存创建 token
    "cache_read_input_tokens": 5291,           // ✅ 缓存读取 token
    "server_tool_use": {                       // ✅ 服务端工具使用
      "web_search_requests": 0
    },
    "service_tier": "standard",                // ✅ 服务等级
    "cache_creation": {                        // ✅ 详细缓存信息
      "ephemeral_1h_input_tokens": 0,
      "ephemeral_5m_input_tokens": 11370
    },
    "duration_api_ms": 7887,                   // ✅ API 调用时长
    "session_id": "4d7797a4-215e..."           // ✅ 会话 ID
  }
}
```

**优势**：
- ✅ 最详细的缓存使用追踪
- ✅ 工具调用信息
- ✅ 服务等级信息
- ✅ 会话追踪

### Qwen 独有字段 ✨

```json
{
  "qwen_meta": {
    "response_id": "chatcmpl-f407eac4...",     // ✅ 响应 ID
    "system_fingerprint": null,                 // ✅ 系统指纹
    "created": 1759185616,                      // ✅ 创建时间戳
    "finish_reason": "stop",                    // ✅ 完成原因
    "provider": "Qwen (DashScope)",             // ✅ 提供商信息
    "api_version": "OpenAI-compatible"          // ✅ API 版本
  }
}
```

**优势**：
- ✅ OpenAI 标准响应 ID
- ✅ 完成原因（stop/length/etc）
- ✅ 明确的提供商标识
- ✅ 创建时间戳

### DeepSeek 独有字段 ✨

```json
{
  "deepseek_meta": {
    "prompt_cache_hit_tokens": 0,              // ✅ 缓存命中 token
    "prompt_cache_miss_tokens": 0,             // ✅ 缓存未命中 token
    "response_id": "chatcmpl-7bac3266...",     // ✅ 响应 ID
    "system_fingerprint": null,                 // ✅ 系统指纹
    "created": 1759186103,                      // ✅ 创建时间戳
    "finish_reason": "stop",                    // ✅ 完成原因
    "provider": "DeepSeek",                     // ✅ 提供商信息
    "api_version": "OpenAI-compatible",         // ✅ API 版本
    "reasoning_content": "..."                  // ✅ 推理内容（仅 deepseek-r1）
  }
}
```

**优势**：
- ✅ Prompt 缓存详细统计
- ✅ 推理模型特殊支持（reasoning_content）
- ✅ 与 Qwen 相同的标准 OpenAI 字段

---

## 三、Token 使用字段对比

### Claude Code Token 字段 📊

```json
{
  "usage": {
    "input_tokens": 4,                         // ✅ 实际输入 token
    "cache_creation_input_tokens": 11370,      // ✅ 缓存创建
    "cache_read_input_tokens": 5291,           // ✅ 缓存读取
    "output_tokens": 494,                      // ✅ 输出 token
    "server_tool_use": {...},                  // ✅ 工具使用统计
    "service_tier": "standard",                // ✅ 服务等级
    "cache_creation": {...}                    // ✅ 缓存详情
  }
}
```

**特点**：
- ✅ 最详细的缓存分类（1h/5m）
- ✅ 实际输入 token 非常少（缓存效果显著）
- ✅ 服务端工具使用统计

### Qwen Token 字段 📊

```json
{
  "usage": {
    "input_tokens": 1535,                      // ✅ 输入 token
    "output_tokens": 446,                      // ✅ 输出 token
    "total_tokens": 1981,                      // ✅ 总 token
    "prompt_tokens": 1535,                     // ✅ prompt token（别名）
    "completion_tokens": 446                   // ✅ completion token（别名）
  }
}
```

**特点**：
- ✅ 标准 OpenAI 格式
- ✅ 提供别名字段兼容性
- ✅ 明确的总 token 计数
- ❌ 无缓存相关信息

### DeepSeek Token 字段 📊

```json
{
  "usage": {
    "input_tokens": 1537,                      // ✅ 输入 token
    "output_tokens": 445,                      // ✅ 输出 token
    "total_tokens": 1982,                      // ✅ 总 token
    "prompt_tokens": 1537,                     // ✅ prompt token（别名）
    "completion_tokens": 445,                  // ✅ completion token（别名）
    "prompt_cache_hit_tokens": 0,              // ✅ 缓存命中
    "prompt_cache_miss_tokens": 0              // ✅ 缓存未命中
  }
}
```

**特点**：
- ✅ 标准 OpenAI 格式
- ✅ Prompt 缓存统计
- ✅ 提供别名字段兼容性

---

## 四、Agent/多步评测字段支持

### ❌ 当前均不支持的 Agent 字段

| 字段 | 说明 | 状态 |
|------|------|------|
| **trajectory** | 按步的交互轨迹 | ❌ 未实现（单步推理）|
| **steps** | 总步数 | ❌ 未实现 |
| **final_patch** | 最终补丁 | ⚠️ 用 `model_patch` 代替 |
| **tools_used** | 工具调用列表 | ⚠️ Claude Code 有，但为空 |
| **sandbox_stdout** | 工具执行输出 | ❌ 未实现 |
| **stop_reason** | 停止原因 | ⚠️ Qwen/DeepSeek 有 `finish_reason` |
| **checkpoint_states** | 每步状态 | ❌ 未实现 |

**说明**：当前实现都是**单步推理**模式，不是 Agent 模式。如果需要 Agent 支持，需要：
1. 实现多轮对话
2. 添加工具调用框架
3. 记录完整轨迹

---

## 五、推荐 Schema 对比

### 当前实现的最小 Schema

```json
{
  // ✅ 已有核心字段
  "instance_id": "django__django-11099",
  "model_name_or_path": "qwen-turbo",
  "full_output": "...",
  "model_patch": "...",
  "latency_ms": 7039,
  "cost": 0.000728,

  // ❌ 推荐但缺失的字段
  "dataset": "SWE-bench_Lite_oracle",      // 缺失
  "split": "test",                         // 缺失
  "prompt": "...",                         // 缺失（节省空间）
  "model_args": {...},                     // 缺失
  "passed": true,                          // 缺失（需评估）
  "test_result": {...},                    // 缺失（需评估）
  "timestamp": "2025-09-29T...",          // 部分有（Qwen/DeepSeek）
  "run_id": "run-20250929-001",           // 缺失

  // ✅ 扩展元数据
  "qwen_meta": {
    "usage": {...},
    "provider": "Qwen (DashScope)",
    ...
  }
}
```

---

## 六、字段缺失原因分析

### 🎯 有意缺失（设计选择）

| 字段 | 原因 | 影响 |
|------|------|------|
| **prompt** | 节省存储空间（prompt 很长）| ⚠️ 无法重现/调试 |
| **system_message** | 固定内容，无需重复存储 | ✅ 可接受 |
| **model_args** | 在命令行参数中，不在输出 | ⚠️ 可追溯性差 |
| **dataset/split** | 文件名包含此信息 | ⚠️ 需解析文件名 |

### 🔴 API 限制

| 字段 | 原因 |
|------|------|
| **confidence/score** | API 不返回 |
| **http_status** | 被 OpenAI SDK 抽象掉 |
| **choices** | 只请求 1 个回复 |

### 🟡 评估分离

| 字段 | 原因 |
|------|------|
| **passed** | 需要运行测试后才知道 |
| **test_result** | 在 evaluation.json 中 |
| **gold/reference** | 在原始数据集中 |

### 🟢 可补充字段

| 字段 | 优先级 | 实现难度 |
|------|--------|----------|
| **dataset** | 高 | 简单 |
| **split** | 高 | 简单 |
| **timestamp** | 高 | 简单（部分已有）|
| **model_args** | 中 | 简单 |
| **run_id** | 中 | 简单 |
| **prompt** | 中 | 简单（但占空间）|
| **error** | 高 | 中等 |
| **retries** | 低 | 中等 |

---

## 七、元数据完整度评分

### 评分标准（基于你的清单）

| 类别 | 总字段数 | Claude Code | Qwen | DeepSeek |
|------|----------|-------------|------|----------|
| **核心字段** | 10 | 8/10 (80%) | 9/10 (90%) | 9/10 (90%) |
| **性能字段** | 5 | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| **Token 字段** | 5 | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) |
| **元信息字段** | 8 | 3/8 (38%) | 3/8 (38%) | 3/8 (38%) |
| **Agent 字段** | 7 | 2/7 (29%) | 0/7 (0%) | 1/7 (14%) |
| **总体覆盖** | 35 | 23/35 (66%) | 22/35 (63%) | 23/35 (66%) |

### 详细评分

#### Claude Code: 66% (23/35) ⭐⭐⭐⭐

**优势**：
- ✅ 最完整的缓存信息
- ✅ 工具使用追踪
- ✅ 会话 ID

**劣势**：
- ❌ 缺少 timestamp
- ❌ 缺少 finish_reason
- ❌ 缺少 response_id

#### Qwen: 63% (22/35) ⭐⭐⭐⭐

**优势**：
- ✅ 完整的 OpenAI 标准字段
- ✅ response_id, finish_reason
- ✅ timestamp (created)

**劣势**：
- ❌ 无缓存信息
- ❌ 无工具使用信息
- ❌ 无 Agent 支持

#### DeepSeek: 66% (23/35) ⭐⭐⭐⭐

**优势**：
- ✅ Prompt 缓存统计
- ✅ 推理模型支持（reasoning_content）
- ✅ 完整的 OpenAI 标准字段

**劣势**：
- ❌ 无详细工具使用信息
- ❌ 缓存信息较 Claude 简单
- ❌ Agent 支持有限

---

## 八、改进建议

### 🔥 高优先级补充（建议立即实现）

1. **添加 dataset 和 split 字段**
   ```python
   output_dict["dataset"] = dataset_name_or_path
   output_dict["split"] = split
   ```

2. **添加 timestamp 字段**（Claude Code 缺少）
   ```python
   from datetime import datetime
   output_dict["timestamp"] = datetime.now().isoformat()
   ```

3. **添加 model_args 字段**
   ```python
   output_dict["model_args"] = {
       "temperature": temperature,
       "max_tokens": max_tokens,
       "timeout": timeout
   }
   ```

4. **添加 error 字段**（失败时）
   ```python
   if response_data is None:
       output_dict["error"] = "API call failed"
       output_dict["exception"] = str(error)
   ```

5. **统一 finish_reason**（Claude Code 缺少）
   ```python
   # Claude Code 应从 response 中提取
   output_dict["finish_reason"] = response.stop_reason
   ```

### 🟡 中优先级补充

6. **添加 run_id**
   ```python
   run_id = os.environ.get("RUN_ID", f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
   output_dict["run_id"] = run_id
   ```

7. **添加 prompt 字段**（可选，占空间）
   ```python
   if save_prompts:  # 配置项
       output_dict["prompt"] = prompt
   ```

8. **添加 http_status**（捕获异常时）
   ```python
   try:
       response = client.call(...)
   except APIError as e:
       output_dict["http_status"] = e.status_code
   ```

### 🟢 低优先级扩展

9. **Agent 支持**（如果需要多步推理）
   - trajectory 数组
   - tools_used 实际调用
   - sandbox_stdout/stderr

10. **重试机制**
    ```python
    output_dict["retries"] = retry_count
    ```

---

## 九、快速抽取命令（基于当前实现）

### 基本统计

```bash
# 总数
jq -s 'length' predictions.jsonl

# 平均延迟
jq -s '[.[].latency_ms] | add/length' predictions.jsonl

# 总成本
jq -s '[.[].cost] | add' predictions.jsonl

# Token 使用（Qwen/DeepSeek）
jq -s '[.[].qwen_meta.usage.total_tokens] | add' qwen_predictions.jsonl
jq -s '[.[].deepseek_meta.usage.total_tokens] | add' deepseek_predictions.jsonl

# Token 使用（Claude Code - 含缓存）
jq -s '[.[].claude_code_meta.usage | .input_tokens + .cache_read_input_tokens + .output_tokens] | add' claude_predictions.jsonl
```

### 高级查询

```bash
# 列出所有 instance_id
jq -r '.instance_id' predictions.jsonl

# 查找高延迟实例（>30s）
jq 'select(.latency_ms > 30000) | {id: .instance_id, latency: .latency_ms}' predictions.jsonl

# 查找昂贵实例
jq 'select(.cost > 0.1) | {id: .instance_id, cost}' predictions.jsonl

# 按提供商分组统计
jq -s 'group_by(.qwen_meta.provider // .deepseek_meta.provider // "Claude") | map({provider: .[0].qwen_meta.provider // .[0].deepseek_meta.provider // "Claude", count: length})' predictions.jsonl

# 缓存效率（Claude Code）
jq '.claude_code_meta.usage | {cache_read: .cache_read_input_tokens, cache_create: .cache_creation_input_tokens, direct_input: .input_tokens, efficiency: (.cache_read_input_tokens / (.input_tokens + .cache_read_input_tokens + .cache_creation_input_tokens))}' claude_predictions.jsonl
```

---

## 十、总结与建议

### ✅ 当前优势

1. **核心字段完整**：instance_id, model, output, patch, latency, cost 都有
2. **Token 追踪完善**：三个模型都提供详细的 token 使用信息
3. **成本计算准确**：都有精确的成本估算
4. **提供商特色**：
   - Claude Code: 最佳缓存追踪
   - Qwen: OpenAI 标准兼容
   - DeepSeek: 推理模型支持

### ⚠️ 主要不足

1. **缺少上下文信息**：dataset, split, model_args 未存储
2. **缺少时间追踪**：Claude Code 缺 timestamp
3. **缺少错误追踪**：失败时无详细 error 字段
4. **Agent 支持弱**：无轨迹、工具调用详情
5. **可追溯性差**：无 run_id, 无 prompt 保存

### 🎯 推荐改进路径

#### 第一阶段：补充基础字段（1小时工作量）
- ✅ 添加 dataset, split, timestamp
- ✅ 添加 model_args
- ✅ 统一 finish_reason

#### 第二阶段：增强错误处理（2小时工作量）
- ✅ 添加 error, exception 字段
- ✅ 添加 http_status
- ✅ 添加重试计数

#### 第三阶段：Agent 支持（1周工作量）
- 🔄 实现多轮对话
- 🔄 添加工具调用框架
- 🔄 记录完整轨迹

### 📊 最终建议

**当前实现已经足够好**（60-70%覆盖），对于 SWE-bench 评测已经满足需求：
- ✅ 所有核心评测字段都有
- ✅ 可以进行成本、性能分析
- ✅ 可以追踪 token 使用

**如果要达到 90%+ 覆盖**，建议按第一、第二阶段补充字段。

**Agent 支持**可以作为未来扩展，但不是当前 SWE-bench 单步推理场景的必需功能。

---

**文档版本**: 1.0
**最后更新**: 2025-09-29
**对比模型**: Claude Code (v2.0.0), Qwen (DashScope), DeepSeek (DashScope)