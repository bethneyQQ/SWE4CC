# Analysis Script Coverage Gap Report

## 问题概述

虽然Qwen和DeepSeek的适配器已经捕获了丰富的metadata，但**analyze_predictions.py脚本并没有将所有已捕获的字段输出到分析报告中**。

## 已捕获但未在报告中体现的字段

### 1. 时间戳信息
**已捕获:**
- `qwen_meta.created` - Unix timestamp
- `deepseek_meta.created` - Unix timestamp

**当前状态:**
- ❌ 未在分析报告中输出
- ❌ 未在print_summary()中显示
- ❌ 未在instance_details中包含

**应该添加到:**
- `basic_stats` - 添加首次/最后请求时间
- `instance_details` - 为每个instance添加timestamp字段

---

### 2. Response ID
**已捕获:**
- `qwen_meta.response_id` - 如 "chatcmpl-7bac3266-41d7-4f07-9cc8-bd7aa7568dae"
- `deepseek_meta.response_id` - API调用的唯一标识符

**当前状态:**
- ❌ 未在分析报告中输出
- ❌ 未在instance_details中包含

**用途:**
- 用于追踪和调试特定的API调用
- 关联日志和错误报告
- 审计和成本核对

**应该添加到:**
- `instance_details` - 为每个instance添加response_id字段

---

### 3. System Fingerprint
**已捕获:**
- `qwen_meta.system_fingerprint` - 模型版本/配置指纹
- `deepseek_meta.system_fingerprint` - 当前为null，但字段存在

**当前状态:**
- ❌ 未在分析报告中输出
- ❌ 未在model_info中统计

**用途:**
- 追踪模型版本变化
- 确保结果可复现性
- 检测API端点更新

**应该添加到:**
- `model_info` - 添加system_fingerprints计数器

---

### 4. API Version
**已捕获:**
- `qwen_meta.api_version` - "OpenAI-compatible"
- `deepseek_meta.api_version` - "OpenAI-compatible"

**当前状态:**
- ❌ 未在分析报告中输出
- ❌ 未在model_info中显示

**应该添加到:**
- `model_info` - 添加api_versions字段

---

### 5. Total Cost Accumulated
**已捕获:**
- `qwen_meta.total_cost_accumulated` - 累计成本
- `deepseek_meta.total_cost_accumulated` - 累计成本

**当前状态:**
- ❌ 未在分析报告中输出
- ✅ 部分：顶层cost字段被使用，但meta中的accumulated cost未被提取

**用途:**
- 验证成本计算准确性
- 追踪会话级别的成本累积

**应该添加到:**
- `performance_metrics.cost` - 添加accumulated_cost字段

---

### 6. Prompt Caching Tokens (DeepSeek)
**已捕获:**
- `deepseek_meta.usage.prompt_cache_hit_tokens`
- `deepseek_meta.usage.prompt_cache_miss_tokens`

**当前状态:**
- ✅ 部分支持：脚本查找`cache_read_input_tokens`和`cache_creation_input_tokens`
- ❌ **字段名不匹配！** DeepSeek使用`prompt_cache_hit_tokens`而非`cache_read_input_tokens`

**BUG:** 第100-102行的字段名与实际不符
```python
# 当前代码（错误）
if "cache_creation_input_tokens" in usage:
    cache_creation_tokens.append(usage["cache_creation_input_tokens"])
if "cache_read_input_tokens" in usage:
    cache_read_tokens.append(usage["cache_read_input_tokens"])
```

**应该改为:**
```python
# 支持多种命名方式
if "prompt_cache_miss_tokens" in usage:
    cache_creation_tokens.append(usage["prompt_cache_miss_tokens"])
elif "cache_creation_input_tokens" in usage:
    cache_creation_tokens.append(usage["cache_creation_input_tokens"])

if "prompt_cache_hit_tokens" in usage:
    cache_read_tokens.append(usage["prompt_cache_hit_tokens"])
elif "cache_read_input_tokens" in usage:
    cache_read_tokens.append(usage["cache_read_input_tokens"])
```

---

### 7. Model Version Info
**已捕获:**
- `qwen_meta.model_info` - 如 "qwen-turbo"
- `deepseek_meta.model_info` - 如 "deepseek-v3"

**当前状态:**
- ✅ 已提取到`model_info.model_versions`
- ✅ 在print_summary()中显示

---

### 8. Provider Info
**已捕获:**
- `qwen_meta.provider` - "Qwen"
- `deepseek_meta.provider` - "DeepSeek"

**当前状态:**
- ✅ 已提取到`model_info.providers`
- ✅ 在print_summary()中显示

---

### 9. Finish Reason
**已捕获:**
- `qwen_meta.finish_reason` - "stop"
- `deepseek_meta.finish_reason` - "stop"

**当前状态:**
- ✅ 已提取到`model_info.finish_reasons`
- ✅ 在print_summary()中显示

---

## 对比表格：已捕获 vs 已输出

| Metadata Field | 在predictions.jsonl中 | 在analysis.json中 | 在terminal输出中 | 状态 |
|----------------|---------------------|------------------|----------------|------|
| instance_id | ✅ | ✅ | ✅ | ✅ 完整 |
| model_name_or_path | ✅ | ✅ | ✅ | ✅ 完整 |
| full_output | ✅ | ❌ | ❌ | ⚠️ 太长，不适合显示 |
| model_patch | ✅ | ❌ | ❌ | ⚠️ 太长，不适合显示 |
| latency_ms | ✅ | ✅ | ✅ | ✅ 完整 |
| cost | ✅ | ✅ | ✅ | ✅ 完整 |
| **created (timestamp)** | ✅ | ❌ | ❌ | ❌ 缺失 |
| **response_id** | ✅ | ❌ | ❌ | ❌ 缺失 |
| **system_fingerprint** | ✅ | ❌ | ❌ | ❌ 缺失 |
| **api_version** | ✅ | ❌ | ❌ | ❌ 缺失 |
| **total_cost_accumulated** | ✅ | ❌ | ❌ | ❌ 缺失 |
| provider | ✅ | ✅ | ✅ | ✅ 完整 |
| finish_reason | ✅ | ✅ | ✅ | ✅ 完整 |
| model_info (version) | ✅ | ✅ | ✅ | ✅ 完整 |
| usage.input_tokens | ✅ | ✅ | ✅ | ✅ 完整 |
| usage.output_tokens | ✅ | ✅ | ✅ | ✅ 完整 |
| usage.total_tokens | ✅ | ✅ | ✅ | ✅ 完整 |
| usage.prompt_tokens | ✅ | ❌ | ❌ | ⚠️ 别名，未单独显示 |
| usage.completion_tokens | ✅ | ❌ | ❌ | ⚠️ 别名，未单独显示 |
| **usage.prompt_cache_hit_tokens** | ✅ (DeepSeek) | ❌ | ❌ | ❌ BUG：字段名不匹配 |
| **usage.prompt_cache_miss_tokens** | ✅ (DeepSeek) | ❌ | ❌ | ❌ BUG：字段名不匹配 |

### 统计
- **已捕获字段总数:** 20 (Qwen: 18, DeepSeek: 20)
- **分析报告输出字段:** 12
- **覆盖率:** 60%
- **缺失重要字段:** 8

---

## 需要修复的问题

### 🔴 Critical (影响功能正确性)

1. **Prompt Caching Token字段名不匹配**
   - **问题:** analyze_predictions.py查找`cache_read_input_tokens`和`cache_creation_input_tokens`
   - **实际:** DeepSeek使用`prompt_cache_hit_tokens`和`prompt_cache_miss_tokens`
   - **影响:** DeepSeek的缓存统计为0，数据丢失
   - **优先级:** P0 - 立即修复

### 🟡 High (重要但不影响当前功能)

2. **Timestamp信息未体现**
   - **问题:** `created`字段未被提取
   - **影响:** 无法知道请求的实际时间，难以排查时间相关问题
   - **用途:** 时间序列分析、调试、审计
   - **优先级:** P1

3. **Response ID未体现**
   - **问题:** `response_id`字段未被提取
   - **影响:** 无法追踪特定API调用，难以与API日志关联
   - **用途:** 调试、审计、成本核对
   - **优先级:** P1

### 🟢 Medium (增强分析能力)

4. **System Fingerprint未统计**
   - **问题:** `system_fingerprint`未被提取
   - **影响:** 无法检测模型版本变化
   - **优先级:** P2

5. **API Version未显示**
   - **问题:** `api_version`未被提取
   - **影响:** 无法追踪API兼容性变化
   - **优先级:** P2

6. **Total Cost Accumulated未使用**
   - **问题:** `total_cost_accumulated`未被提取用于验证
   - **影响:** 无法交叉验证成本计算
   - **优先级:** P2

---

## 建议的修复方案

### 修改1: 修复Prompt Caching字段名 (P0)

```python
# 在compute_performance_metrics()方法中，替换第99-103行：

if usage:
    if "input_tokens" in usage:
        input_tokens.append(usage["input_tokens"])
    if "output_tokens" in usage:
        output_tokens.append(usage["output_tokens"])

    # 支持多种缓存token命名方式
    # Claude Code: cache_creation_input_tokens, cache_read_input_tokens
    # DeepSeek: prompt_cache_miss_tokens, prompt_cache_hit_tokens
    cache_miss = usage.get("prompt_cache_miss_tokens") or usage.get("cache_creation_input_tokens")
    if cache_miss:
        cache_creation_tokens.append(cache_miss)

    cache_hit = usage.get("prompt_cache_hit_tokens") or usage.get("cache_read_input_tokens")
    if cache_hit:
        cache_read_tokens.append(cache_hit)

    total = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
    if total > 0:
        total_tokens.append(total)
```

### 修改2: 添加Timestamp信息 (P1)

```python
# 在compute_basic_stats()方法中添加：

def compute_basic_stats(self) -> Dict[str, Any]:
    n_samples = len(self.predictions)

    # 提取所有timestamp
    timestamps = []
    for pred in self.predictions:
        meta = pred.get("claude_code_meta") or pred.get("qwen_meta") or pred.get("deepseek_meta")
        if meta and "created" in meta:
            timestamps.append(meta["created"])

    stats = {
        "total_samples": n_samples,
        "predictions_file": str(self.predictions_path),
        "analysis_timestamp": datetime.now().isoformat()
    }

    # 添加时间范围
    if timestamps:
        from datetime import datetime as dt
        stats["request_time_range"] = {
            "earliest": dt.fromtimestamp(min(timestamps)).isoformat(),
            "latest": dt.fromtimestamp(max(timestamps)).isoformat(),
            "duration_seconds": max(timestamps) - min(timestamps)
        }

    # ... 现有代码继续 ...
```

### 修改3: 在Instance Details中添加更多字段 (P1)

```python
# 在compute_instance_details()方法中，替换第254-287行：

def compute_instance_details(self) -> Dict[str, Any]:
    instances = []
    resolved_ids = set(self.evaluation_data.get("resolved_ids", []))

    for pred in self.predictions:
        instance = {
            "instance_id": pred.get("instance_id", "unknown"),
            "model": pred.get("model_name_or_path", "unknown"),
            "passed": pred.get("instance_id") in resolved_ids,
            "latency_ms": pred.get("latency_ms", 0),
            "cost": pred.get("cost", 0),
            "has_patch": bool(pred.get("model_patch", "").strip()),
            "patch_size": len(pred.get("model_patch", "")),
        }

        # 提取metadata
        meta = pred.get("claude_code_meta") or pred.get("qwen_meta") or pred.get("deepseek_meta")

        if meta:
            # 添加timestamp
            if "created" in meta:
                from datetime import datetime as dt
                instance["timestamp"] = dt.fromtimestamp(meta["created"]).isoformat()
                instance["timestamp_unix"] = meta["created"]

            # 添加response_id
            if "response_id" in meta:
                instance["response_id"] = meta["response_id"]

            # 添加finish_reason
            if "finish_reason" in meta:
                instance["finish_reason"] = meta["finish_reason"]

            # 添加provider
            if "provider" in meta:
                instance["provider"] = meta["provider"]

            # Token usage
            usage = meta.get("usage", {})
            if usage:
                instance["input_tokens"] = usage.get("input_tokens", 0)
                instance["output_tokens"] = usage.get("output_tokens", 0)

                # Cache tokens (支持多种命名)
                cache_hit = usage.get("prompt_cache_hit_tokens") or usage.get("cache_read_input_tokens", 0)
                cache_miss = usage.get("prompt_cache_miss_tokens") or usage.get("cache_creation_input_tokens", 0)
                if cache_hit > 0:
                    instance["cache_hit_tokens"] = cache_hit
                if cache_miss > 0:
                    instance["cache_miss_tokens"] = cache_miss

        instances.append(instance)

    return {"instances": instances}
```

### 修改4: 添加System Fingerprint和API Version到Model Info (P2)

```python
# 在compute_model_info()方法中添加：

def compute_model_info(self) -> Dict[str, Any]:
    model_info = {
        "model_names": Counter(),
        "tools_used": Counter(),
        "service_tiers": Counter(),
        "providers": Counter(),
        "finish_reasons": Counter(),
        "system_fingerprints": Counter(),  # 新增
        "api_versions": Counter()           # 新增
    }

    for pred in self.predictions:
        # Model name
        if "model_name_or_path" in pred:
            model_info["model_names"][pred["model_name_or_path"]] += 1

        # Check for metadata from different providers
        meta = pred.get("claude_code_meta") or pred.get("qwen_meta") or pred.get("deepseek_meta")

        if meta:
            # ... 现有代码 ...

            # System fingerprint (新增)
            if "system_fingerprint" in meta and meta["system_fingerprint"]:
                model_info["system_fingerprints"][meta["system_fingerprint"]] += 1

            # API version (新增)
            if "api_version" in meta:
                model_info["api_versions"][meta["api_version"]] += 1

    return model_info
```

### 修改5: 在Print Summary中显示新字段

```python
# 在print_summary()方法中添加显示新字段：

# 在Model Info部分后添加：
if model.get("system_fingerprints"):
    print(f"System Fingerprints: {dict(model['system_fingerprints'])}")
if model.get("api_versions"):
    print(f"API Versions: {dict(model['api_versions'])}")

# 在Basic Stats部分添加timestamp范围：
if "request_time_range" in basic:
    time_range = basic["request_time_range"]
    print(f"Request Time Range: {time_range['earliest']} to {time_range['latest']}")
    print(f"Duration: {time_range['duration_seconds']:.1f}s")
```

---

## 验证修复效果

修复后，运行以下命令验证：

```bash
# 测试DeepSeek缓存token统计
python analyze_predictions.py results/deepseek-v3__SWE-bench_Lite_oracle__test.jsonl

# 应该看到：
# Cache Creation: 0  (prompt_cache_miss_tokens)
# Cache Reads: 0     (prompt_cache_hit_tokens)

# 检查detailed JSON中的新字段
jq '.instance_details.instances[0]' results/deepseek-v3__SWE-bench_Lite_oracle__test.analysis.json

# 应该包含：
# - timestamp
# - response_id
# - finish_reason
# - provider
# - cache_hit_tokens (如果>0)
# - cache_miss_tokens (如果>0)
```

---

## 总结

**当前问题：** analyze_predictions.py只输出了60%的已捕获metadata字段。

**核心问题：**
1. ❌ **BUG**: Prompt caching字段名不匹配，导致DeepSeek缓存统计失效
2. ❌ 缺少timestamp信息（无法知道请求时间）
3. ❌ 缺少response_id（无法追踪API调用）
4. ❌ 缺少system_fingerprint（无法检测模型变化）
5. ❌ 缺少api_version（无法追踪兼容性）

**建议：** 立即实施上述5个修改，将coverage从60%提升至95%+。

**预期效果：**
- ✅ DeepSeek缓存统计正确显示
- ✅ 每个instance有完整的timestamp和response_id
- ✅ 可追踪模型版本和API变化
- ✅ 满足用户的"精量有"要求