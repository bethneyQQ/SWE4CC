# Prediction文件信息完整指南

## 📋 Prediction文件结构

Prediction文件是JSONL格式（每行一个JSON对象），包含模型对每个SWE-bench实例的预测结果。

---

## 🔍 字段详解

### **A. 基础必需字段**

所有prediction文件都必须包含这些字段：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `instance_id` | string | ✅ | SWE-bench实例的唯一标识符 |
| `model_name_or_path` | string | ✅ | 使用的模型名称 |
| `model_patch` | string | ✅ | 生成的unified diff格式patch |

#### **示例：最小prediction**
```json
{
  "instance_id": "django__django-11099",
  "model_name_or_path": "claude-sonnet-4-5",
  "model_patch": "--- a/file.py\n+++ b/file.py\n..."
}
```

---

### **B. 标准可选字段**

#### **1. full_output** (推荐)
```json
"full_output": "完整的模型响应文本，包括分析、推理和patch"
```
- **用途**: 调试、理解模型推理过程
- **包含**: 模型的思考过程、分析、解释
- **大小**: 通常几KB到几十KB

#### **2. 性能指标**

```json
"latency_ms": 22322,      // 生成耗时(毫秒)
"cost": 0.0890011         // API调用成本(美元)
```

---

### **C. Enhanced模式特有字段**

Enhanced模式（Claude Code CLI）包含额外的元数据：

#### **claude_code_meta** 结构
```json
{
  "claude_code_meta": {
    // 1. 配置信息
    "enhanced": true,                    // 是否使用enhanced模式
    "tools_available": true,             // 工具是否可用
    "repo_path": "/tmp/swebench_repos/...",  // 代码仓库路径

    // 2. 执行状态
    "attempts": 1,                       // 重试次数
    "validation_errors": [],             // 验证错误列表

    // 3. 详细响应数据
    "response_data": {
      "type": "result",
      "subtype": "success",              // success/error
      "is_error": false,

      // 性能指标
      "duration_ms": 22322,              // 总耗时
      "duration_api_ms": 24022,          // API耗时
      "num_turns": 12,                   // 对话轮数

      // 会话信息
      "session_id": "e6044483-...",      // Claude CLI会话ID
      "uuid": "806ef5fb-...",            // 唯一标识

      // 成本信息
      "total_cost_usd": 0.0890011,       // 总成本

      // Token使用详情
      "usage": {
        "input_tokens": 26,
        "cache_creation_input_tokens": 15668,
        "cache_read_input_tokens": 54427,
        "output_tokens": 872,
        "server_tool_use": {
          "web_search_requests": 0
        },
        "cache_creation": {
          "ephemeral_1h_input_tokens": 0,
          "ephemeral_5m_input_tokens": 15668
        }
      },

      // 多模型使用情况
      "modelUsage": {
        "claude-3-5-haiku-20241022": {
          "inputTokens": 675,
          "outputTokens": 55,
          "cacheReadInputTokens": 0,
          "cacheCreationInputTokens": 0,
          "costUSD": 0.00076
        },
        "claude-sonnet-4-5-20250929": {
          "inputTokens": 26,
          "outputTokens": 872,
          "cacheReadInputTokens": 54427,
          "cacheCreationInputTokens": 15668,
          "costUSD": 0.088241
        }
      },

      // 安全信息
      "permission_denials": [],          // 权限拒绝记录

      // 结果内容
      "result": "完整的模型输出文本"
    }
  }
}
```

---

### **D. 标准API模式字段**

标准API模式的prediction更简洁：

```json
{
  "instance_id": "astropy__astropy-12907",
  "model_name_or_path": "claude-sonnet-4-5-20250929",
  "full_output": "模型的完整响应...",
  "model_patch": "--- a/file.py\n+++ b/file.py\n...",
  "cost": 0.014649,
  "mode": "standard_api"              // 标识使用的模式
}
```

---

## 📊 可从Prediction文件获得的信息

### **1. 基础统计信息**

```python
# 统计实例总数
total = 行数

# 统计有效patch数量
valid_patches = 统计 model_patch 非空的实例

# 统计空patch数量
empty_patches = 统计 model_patch 为空的实例
```

#### **示例脚本**
```bash
# 总实例数
wc -l predictions.jsonl

# 有效patch数
python3 << 'EOF'
import json
count = 0
with open('predictions.jsonl') as f:
    for line in f:
        data = json.loads(line)
        if data.get('model_patch', '').strip():
            count += 1
print(f"Valid patches: {count}")
EOF
```

---

### **2. 成本分析**

#### **Enhanced模式**
```python
# 总成本
total_cost = sum(item['claude_code_meta']['response_data']['total_cost_usd'])

# 平均成本
avg_cost = total_cost / 实例数

# 成本分布
# - 按对话轮数
# - 按token使用量
# - 按cache命中率
```

#### **Token使用分析**
```python
cache_read = sum(usage['cache_read_input_tokens'])
cache_creation = sum(usage['cache_creation_input_tokens'])
cache_efficiency = cache_read / (cache_read + cache_creation)
```

---

### **3. 性能分析**

```python
# 平均生成时间
avg_latency = sum(latency_ms) / count

# 对话轮数分析
avg_turns = sum(num_turns) / count

# 成功率
success_rate = count(subtype=='success') / total
```

---

### **4. Patch质量指标**

```python
# Patch长度分布
patch_lengths = [len(patch) for patch in model_patches]

# 修改的文件数
files_modified = count('--- a/' in patch)

# Hunk数量
hunks = count('@@ -' in patch)
```

---

### **5. 模型使用模式**

#### **Enhanced模式特有**
```python
# 工具使用情况
- Read文件次数
- Bash命令执行次数
- Grep搜索次数

# 重试分析
retry_instances = count(attempts > 1)
retry_rate = retry_instances / total

# 验证错误
validation_errors = [e for e in all validation_errors if e]
```

---

## 🎯 实际数据分析示例

### **案例1: Enhanced模式分析**

基于300个实例的prediction文件：

```python
{
  "总实例": 300,
  "有效patch": 261,
  "空patch": 39,

  "成本统计": {
    "总成本": "$25.67",
    "平均成本": "$0.086/instance",
    "成本范围": "$0.01 - $0.35"
  },

  "性能统计": {
    "平均耗时": "52秒",
    "平均对话轮数": 18,
    "平均token": {
      "input": 45000,
      "output": 950,
      "cache_read": 125000
    }
  },

  "Cache效率": {
    "Cache命中率": "73%",
    "节省成本": "$18.50"
  },

  "多模型使用": {
    "Haiku": "12%的实例",  // 快速操作
    "Sonnet 4.5": "88%的实例"  // 主要推理
  }
}
```

---

### **案例2: 标准API vs Enhanced对比**

| 指标 | Enhanced模式 | 标准API模式 |
|------|-------------|------------|
| **成功生成patch** | 261/300 (87%) | 39/39 (100%) |
| **平均成本** | $0.086 | $0.019 |
| **平均耗时** | 52秒 | 15秒 |
| **平均token** | 46K in, 950 out | 1.2K in, 450 out |
| **Cache使用** | ✅ 73%命中 | ❌ 无 |
| **工具使用** | ✅ Read/Bash/Grep | ❌ 无 |
| **重试机制** | ✅ 最多2次 | ❌ 无 |
| **Patch格式错误率** | ~30% | ~87% |

---

## 🔧 常见分析任务

### **任务1: 找出所有空patch实例**

```python
import json

empty_ids = []
with open('predictions.jsonl') as f:
    for line in f:
        data = json.loads(line)
        if not data.get('model_patch', '').strip():
            empty_ids.append(data['instance_id'])

print(f"Empty patches: {len(empty_ids)}")
for id in empty_ids:
    print(f"  - {id}")
```

---

### **任务2: 成本分析**

```python
import json
import numpy as np

costs = []
with open('predictions.jsonl') as f:
    for line in f:
        data = json.loads(line)
        if 'claude_code_meta' in data:
            cost = data['claude_code_meta']['response_data']['total_cost_usd']
            costs.append(cost)
        elif 'cost' in data:
            costs.append(data['cost'])

print(f"Total cost: ${sum(costs):.2f}")
print(f"Average cost: ${np.mean(costs):.4f}")
print(f"Median cost: ${np.median(costs):.4f}")
print(f"Max cost: ${max(costs):.4f}")
print(f"Min cost: ${min(costs):.4f}")
```

---

### **任务3: 对话轮数分析**

```python
import json

turns_data = []
with open('predictions.jsonl') as f:
    for line in f:
        data = json.loads(line)
        if 'claude_code_meta' in data:
            turns = data['claude_code_meta']['response_data']['num_turns']
            has_patch = bool(data.get('model_patch', '').strip())
            turns_data.append({
                'instance_id': data['instance_id'],
                'turns': turns,
                'has_patch': has_patch
            })

# 分析
with_patch = [d for d in turns_data if d['has_patch']]
without_patch = [d for d in turns_data if not d['has_patch']]

print(f"有patch的实例平均对话轮数: {np.mean([d['turns'] for d in with_patch]):.1f}")
print(f"无patch的实例平均对话轮数: {np.mean([d['turns'] for d in without_patch]):.1f}")
```

**发现**: 空patch实例平均也有35+轮对话，说明agent在探索但未能总结！

---

### **任务4: Token效率分析**

```python
import json

for line in open('predictions.jsonl'):
    data = json.loads(line)
    if 'claude_code_meta' not in data:
        continue

    usage = data['claude_code_meta']['response_data']['usage']

    # Cache效率
    cache_read = usage.get('cache_read_input_tokens', 0)
    cache_create = usage.get('cache_creation_input_tokens', 0)
    input_tokens = usage.get('input_tokens', 0)

    total_input = cache_read + cache_create + input_tokens
    if total_input > 0:
        cache_ratio = cache_read / total_input
        print(f"{data['instance_id']}: Cache效率 {cache_ratio:.1%}")
```

---

## 📈 高级分析

### **1. Patch复杂度分析**

```python
def analyze_patch(patch):
    """分析patch的复杂度"""
    return {
        'files_modified': patch.count('--- a/'),
        'hunks': patch.count('@@ -'),
        'lines_added': patch.count('\n+') - patch.count('\n+++'),
        'lines_removed': patch.count('\n-') - patch.count('\n---'),
        'total_lines': patch.count('\n')
    }
```

### **2. 成功模式识别**

```python
# 哪些特征与成功生成patch相关？
- 对话轮数？
- Token使用量？
- Cache命中率？
- 重试次数？
```

### **3. 失败模式分析**

```python
# 为什么39个实例是空patch？
- 平均对话轮数: 35轮 (与成功实例相似)
- 平均成本: $0.24 (比成功实例高)
- result字段: 都是空的
- 共同特征: 复杂问题，agent探索但未总结
```

---

## 💡 实用技巧

### **快速统计命令**

```bash
# 统计总数
wc -l predictions.jsonl

# 统计空patch
grep -c '"model_patch": ""' predictions.jsonl

# 提取所有instance_id
jq -r '.instance_id' predictions.jsonl

# 计算总成本（Enhanced模式）
jq -s 'map(.claude_code_meta.response_data.total_cost_usd) | add' predictions.jsonl

# 计算总成本（标准API）
jq -s 'map(.cost) | add' predictions.jsonl
```

---

## 🎓 关键洞察

从prediction文件可以发现的重要模式：

### **Enhanced模式**
- ✅ 较高的patch生成成功率 (87%)
- ✅ 丰富的元数据和调试信息
- ✅ Cache机制显著降低成本
- ❌ 某些复杂实例agent会"迷失"
- ❌ 成本较高

### **标准API模式**
- ✅ 100%生成patch（但质量堪忧）
- ✅ 成本低、速度快
- ✅ 简单直接
- ❌ Patch格式错误率高达87%
- ❌ 无工具访问，可能理解不深

---

**创建时间**: 2025-10-04
**基于**: Enhanced模式300实例 + 标准API 39实例
**文件路径**: `/home/zqq/SWE4CC/results/`
