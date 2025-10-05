# Evaluation JSON报告信息完整指南

## 📊 JSON报告概述

Evaluation JSON报告是SWE-bench评估结果的**结构化汇总**，提供了整体统计信息和所有实例的结果列表，便于快速查询和分析。

### **文件位置**
```
reports/
├── {model_name}.{run_id}-evaluation.json
└── claude-sonnet-4-5.claude-4.5-sonnet-evaluation.json  # 示例
```

---

## 🔍 报告结构详解

### **完整字段列表**

```json
{
  // 1. 整体统计信息
  "total_instances": 300,           // 提交evaluation的总实例数
  "submitted_instances": 300,       // 实际提交的实例数
  "completed_instances": 176,       // 完成evaluation的实例数
  "resolved_instances": 100,        // ✅ 测试通过的实例数
  "unresolved_instances": 76,       // ✖️ 测试失败的实例数
  "empty_patch_instances": 39,      // 空patch的实例数
  "error_instances": 85,            // ⚠️ 错误的实例数（patch应用失败等）

  // 2. 实例ID分类列表
  "completed_ids": [...],           // 所有完成的实例ID列表
  "incomplete_ids": [...],          // 未完成的实例ID列表（通常为空）
  "empty_patch_ids": [...],         // 空patch的实例ID列表
  "submitted_ids": [...],           // 所有提交的实例ID列表
  "resolved_ids": [...],            // ✅ 解决的实例ID列表
  "unresolved_ids": [...],          // ✖️ 未解决的实例ID列表
  "error_ids": [...],               // ⚠️ 错误的实例ID列表

  // 3. 元数据
  "schema_version": 2               // 报告schema版本
}
```

---

## 📐 字段详细说明

### **A. 数值统计字段**

#### **1. total_instances**
- **含义**: 提交到evaluation的总实例数
- **来源**: 输入的prediction文件中的实例数
- **用途**: 计算整体进度和成功率

#### **2. submitted_instances**
- **含义**: 实际提交evaluation的实例数
- **通常情况**: `submitted_instances == total_instances`
- **如果不等**: 说明某些实例被跳过或过滤

#### **3. completed_instances**
- **含义**: 成功完成evaluation流程的实例数
- **包含**: resolved + unresolved（不包括error和empty_patch）
- **计算公式**: `completed = resolved + unresolved`

#### **4. resolved_instances** ✅
- **含义**: 测试完全通过的实例数
- **判定标准**:
  ```python
  resolved = (
      patch_successfully_applied == True AND
      FAIL_TO_PASS.success 包含所有目标测试 AND
      PASS_TO_FAIL.failure == []
  )
  ```
- **这是最重要的成功指标！**

#### **5. unresolved_instances** ✖️
- **含义**: Patch应用成功但测试未全部通过的实例数
- **原因**:
  - FAIL_TO_PASS测试未通过
  - PASS_TO_FAIL有新引入的失败
  - 修复不完全

#### **6. empty_patch_instances**
- **含义**: 模型生成的patch为空的实例数
- **注意**: 这些实例不参与evaluation
- **问题来源**:
  - Enhanced模式: Agent探索但未总结
  - Standard API模式: 模型未生成有效输出

#### **7. error_instances** ⚠️
- **含义**: Evaluation过程中出错的实例数
- **常见原因**:
  - Patch格式错误（malformed patch）
  - Patch应用失败（hunk failed）
  - 文件不存在
  - 容器创建失败

---

### **B. 实例ID列表字段**

每个`*_ids`字段都是一个字符串数组，包含相应类别的所有实例ID。

#### **实例ID列表的关系**

```
总实例数 = submitted_instances
  ├── completed_ids (成功完成evaluation)
  │     ├── resolved_ids (✅ 测试通过)
  │     └── unresolved_ids (✖️ 测试失败)
  ├── empty_patch_ids (空patch，未evaluation)
  ├── error_ids (⚠️ evaluation出错)
  └── incomplete_ids (未完成，通常为空)
```

#### **重要关系**
```python
# 所有实例
submitted_ids = completed_ids + empty_patch_ids + error_ids + incomplete_ids

# 完成的实例
completed_ids = resolved_ids + unresolved_ids

# 验证数量一致性
len(submitted_ids) == total_instances
len(resolved_ids) == resolved_instances
len(unresolved_ids) == unresolved_instances
len(empty_patch_ids) == empty_patch_instances
len(error_ids) == error_instances
```

---

## 📊 从JSON报告可获得的信息

### **1. 整体成功率分析**

```python
import json

with open('evaluation.json') as f:
    report = json.load(f)

total = report['total_instances']
resolved = report['resolved_instances']
unresolved = report['unresolved_instances']
empty = report['empty_patch_instances']
error = report['error_instances']

print(f"总实例: {total}")
print(f"✅ 解决率: {resolved}/{total} ({resolved/total*100:.1f}%)")
print(f"✖️ 未解决: {unresolved}/{total} ({unresolved/total*100:.1f}%)")
print(f"⚠️ 错误率: {error}/{total} ({error/total*100:.1f}%)")
print(f"空Patch: {empty}/{total} ({empty/total*100:.1f}%)")
```

#### **输出示例（Enhanced模式300实例）**
```
总实例: 300
✅ 解决率: 100/300 (33.3%)
✖️ 未解决: 76/300 (25.3%)
⚠️ 错误率: 85/300 (28.3%)
空Patch: 39/300 (13.0%)
```

---

### **2. 按项目分析成功率**

```python
from collections import defaultdict

# 统计每个项目的成功情况
projects = defaultdict(lambda: {'resolved': 0, 'total': 0})

for instance_id in report['submitted_ids']:
    project = instance_id.split('__')[0]
    projects[project]['total'] += 1

for instance_id in report['resolved_ids']:
    project = instance_id.split('__')[0]
    projects[project]['resolved'] += 1

# 计算成功率
for project, stats in sorted(projects.items()):
    rate = stats['resolved'] / stats['total'] * 100
    print(f"{project:30s}: {stats['resolved']:3d}/{stats['total']:3d} ({rate:5.1f}%)")
```

#### **输出示例**
```
astropy                       : 2/6 (33.3%)
django                        : 50/120 (41.7%)
matplotlib                    : 6/25 (24.0%)
scikit-learn                  : 7/26 (26.9%)
sympy                         : 25/90 (27.8%)
...
```

---

### **3. 问题分类分析**

```python
# 分类统计
total = report['total_instances']
resolved = report['resolved_instances']
unresolved = report['unresolved_instances']
empty = report['empty_patch_instances']
error = report['error_instances']

print("问题分类:")
print(f"  1. ✅ 完全解决: {resolved} ({resolved/total*100:.1f}%)")
print(f"  2. ✖️ Patch正确但修复不完全: {unresolved} ({unresolved/total*100:.1f}%)")
print(f"  3. ⚠️ Patch应用失败: {error} ({error/total*100:.1f}%)")
print(f"  4. ⭕ 未生成Patch: {empty} ({empty/total*100:.1f}%)")
```

---

### **4. 快速查询特定实例**

```python
instance_id = "django__django-11039"

if instance_id in report['resolved_ids']:
    print(f"✅ {instance_id}: Resolved")
elif instance_id in report['unresolved_ids']:
    print(f"✖️ {instance_id}: Unresolved")
elif instance_id in report['empty_patch_ids']:
    print(f"⭕ {instance_id}: Empty patch")
elif instance_id in report['error_ids']:
    print(f"⚠️ {instance_id}: Error")
else:
    print(f"❓ {instance_id}: Not found")
```

---

### **5. 导出失败实例列表**

```python
# 导出所有需要重试的实例
failed_ids = (
    report['unresolved_ids'] +
    report['error_ids'] +
    report['empty_patch_ids']
)

print(f"需要重试的实例: {len(failed_ids)}")
with open('failed_instances.txt', 'w') as f:
    for instance_id in failed_ids:
        f.write(f"{instance_id}\n")
```

---

## 🎯 实际案例分析

### **案例1: Enhanced模式 - 300实例评估**

```json
{
  "total_instances": 300,
  "resolved_instances": 100,        // 33.3% 成功
  "unresolved_instances": 76,       // 25.3% 部分成功
  "empty_patch_instances": 39,      // 13.0% 未生成
  "error_instances": 85             // 28.3% 错误
}
```

#### **分析**
- ✅ **成功率33.3%**: 这是实际解决问题的实例比例
- ✖️ **部分成功25.3%**: Patch应用成功但测试未全过
- ⚠️ **错误率28.3%**: 主要是patch格式问题
- ⭕ **空Patch 13.0%**: Agent迷失，未能总结

#### **问题优先级**
1. **最严重**: 28.3%的patch格式错误 → 需要修复patch提取逻辑
2. **次要**: 13%的空patch → 需要改进Agent的总结机制
3. **优化**: 25.3%的测试失败 → 需要提高patch质量

---

### **案例2: 标准API模式 - 39实例评估**

```json
{
  "total_instances": 39,
  "resolved_instances": 1,          // 2.6% 成功
  "unresolved_instances": 4,        // 10.3% 部分成功
  "empty_patch_instances": 0,       // 0% 未生成
  "error_instances": 34             // 87.2% 错误
}
```

#### **分析**
- ⚠️ **错误率87.2%**: 几乎所有patch都有格式问题
- ✅ **成功率2.6%**: 仅1个实例成功
- **优点**: 100%生成了patch（无空patch）
- **缺点**: Patch格式质量极差

---

### **案例3: Enhanced vs Standard API对比**

| 指标 | Enhanced模式 | 标准API模式 | 对比 |
|------|-------------|------------|------|
| **总实例** | 300 | 39 | - |
| **✅ 解决率** | 33.3% | 2.6% | **Enhanced好12.8倍** |
| **✖️ 未解决率** | 25.3% | 10.3% | Enhanced高2.5倍 |
| **⚠️ 错误率** | 28.3% | 87.2% | **Standard高3倍** |
| **⭕ 空Patch率** | 13.0% | 0% | Standard更好 |

**结论**: Enhanced模式虽然有13%的空patch问题，但整体成功率远高于Standard API。

---

## 🔧 JSON报告 vs 其他信息源

### **对比表**

| 信息类型 | JSON报告 | Evaluation日志 | Prediction文件 |
|---------|---------|---------------|---------------|
| **整体统计** | ✅ 快速查看 | ❌ 需解析 | ❌ 需统计 |
| **实例列表** | ✅ 分类清晰 | ❌ 分散 | ❌ 无分类 |
| **详细错误** | ❌ 无 | ✅ 详细信息 | ❌ 无 |
| **Patch内容** | ❌ 无 | ✅ 有 | ✅ 有 |
| **测试结果** | ❌ 无 | ✅ 详细 | ❌ 无 |
| **性能数据** | ❌ 无 | ❌ 无 | ✅ 有 |
| **查询速度** | ✅ 最快 | ❌ 慢 | ✅ 快 |

### **使用建议**

```python
# 1. 快速查看整体情况 → 使用JSON报告
json_report = json.load(open('evaluation.json'))
print(f"成功率: {json_report['resolved_instances']}/{json_report['total_instances']}")

# 2. 查看失败原因 → 查看Evaluation日志
# cat logs/run_evaluation/.../instance_id/run_instance.log

# 3. 分析成本和性能 → 查看Prediction文件
# predictions.jsonl 中的 claude_code_meta
```

---

## 💡 常用查询脚本

### **脚本1: 生成成功率报告**

```python
import json

def analyze_evaluation_report(json_path):
    with open(json_path) as f:
        report = json.load(f)

    total = report['total_instances']

    print("=" * 60)
    print(f"Evaluation报告分析: {json_path}")
    print("=" * 60)

    print(f"\n📊 整体统计:")
    print(f"  总实例数: {total}")
    print(f"  提交数: {report['submitted_instances']}")
    print(f"  完成数: {report['completed_instances']}")

    print(f"\n✅ 成功情况:")
    print(f"  解决实例: {report['resolved_instances']} ({report['resolved_instances']/total*100:.1f}%)")

    print(f"\n❌ 失败情况:")
    print(f"  未解决: {report['unresolved_instances']} ({report['unresolved_instances']/total*100:.1f}%)")
    print(f"  错误: {report['error_instances']} ({report['error_instances']/total*100:.1f}%)")
    print(f"  空Patch: {report['empty_patch_instances']} ({report['empty_patch_instances']/total*100:.1f}%)")

    print(f"\n📝 实例分类:")
    print(f"  Resolved IDs数量: {len(report['resolved_ids'])}")
    print(f"  Unresolved IDs数量: {len(report['unresolved_ids'])}")
    print(f"  Error IDs数量: {len(report['error_ids'])}")
    print(f"  Empty Patch IDs数量: {len(report['empty_patch_ids'])}")

    return report

# 使用
report = analyze_evaluation_report('evaluation.json')
```

---

### **脚本2: 按项目统计**

```python
import json
from collections import defaultdict

def analyze_by_project(json_path):
    with open(json_path) as f:
        report = json.load(f)

    # 统计
    projects = defaultdict(lambda: {
        'total': 0,
        'resolved': 0,
        'unresolved': 0,
        'error': 0,
        'empty': 0
    })

    for instance_id in report['submitted_ids']:
        project = instance_id.split('__')[0]
        projects[project]['total'] += 1

    for instance_id in report['resolved_ids']:
        project = instance_id.split('__')[0]
        projects[project]['resolved'] += 1

    for instance_id in report['unresolved_ids']:
        project = instance_id.split('__')[0]
        projects[project]['unresolved'] += 1

    for instance_id in report['error_ids']:
        project = instance_id.split('__')[0]
        projects[project]['error'] += 1

    for instance_id in report['empty_patch_ids']:
        project = instance_id.split('__')[0]
        projects[project]['empty'] += 1

    # 输出
    print(f"{'Project':<30s} {'Total':>6s} {'✅Resolved':>10s} {'✖️Unresolved':>12s} {'⚠️Error':>8s} {'⭕Empty':>7s} {'Rate':>7s}")
    print("-" * 95)

    for project, stats in sorted(projects.items()):
        rate = stats['resolved'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"{project:<30s} {stats['total']:>6d} {stats['resolved']:>10d} {stats['unresolved']:>12d} {stats['error']:>8d} {stats['empty']:>7d} {rate:>6.1f}%")

    # 总计
    print("-" * 95)
    total = report['total_instances']
    print(f"{'TOTAL':<30s} {total:>6d} {report['resolved_instances']:>10d} {report['unresolved_instances']:>12d} {report['error_instances']:>8d} {report['empty_patch_instances']:>7d} {report['resolved_instances']/total*100:>6.1f}%")

# 使用
analyze_by_project('evaluation.json')
```

---

### **脚本3: 导出失败实例到文件**

```python
import json

def export_failed_instances(json_path, output_path='failed_instances.txt'):
    with open(json_path) as f:
        report = json.load(f)

    failed_ids = (
        report['unresolved_ids'] +
        report['error_ids'] +
        report['empty_patch_ids']
    )

    with open(output_path, 'w') as f:
        for instance_id in sorted(failed_ids):
            f.write(f"{instance_id}\n")

    print(f"导出 {len(failed_ids)} 个失败实例到 {output_path}")
    print(f"  - Unresolved: {len(report['unresolved_ids'])}")
    print(f"  - Error: {len(report['error_ids'])}")
    print(f"  - Empty: {len(report['empty_patch_ids'])}")

    return failed_ids

# 使用
failed = export_failed_instances('evaluation.json')
```

---

## 📈 高级分析

### **1. 时间序列分析**

如果有多次evaluation的JSON报告：

```python
import json
import matplotlib.pyplot as plt

runs = [
    ('run1', 'evaluation_v1.json'),
    ('run2', 'evaluation_v2.json'),
    ('run3', 'evaluation_v3.json'),
]

success_rates = []
for run_name, json_path in runs:
    with open(json_path) as f:
        report = json.load(f)
    rate = report['resolved_instances'] / report['total_instances'] * 100
    success_rates.append(rate)
    print(f"{run_name}: {rate:.1f}%")

# 可视化
plt.plot([r[0] for r in runs], success_rates, marker='o')
plt.xlabel('Run')
plt.ylabel('Success Rate (%)')
plt.title('Success Rate Trend')
plt.show()
```

---

### **2. 交叉分析**

结合JSON报告和Prediction文件：

```python
import json

# 加载JSON报告
with open('evaluation.json') as f:
    eval_report = json.load(f)

# 加载Prediction文件
predictions = {}
with open('predictions.jsonl') as f:
    for line in f:
        pred = json.loads(line)
        predictions[pred['instance_id']] = pred

# 分析: 对话轮数与成功率的关系
resolved_turns = []
unresolved_turns = []

for instance_id in eval_report['resolved_ids']:
    if instance_id in predictions and 'claude_code_meta' in predictions[instance_id]:
        turns = predictions[instance_id]['claude_code_meta']['response_data']['num_turns']
        resolved_turns.append(turns)

for instance_id in eval_report['unresolved_ids']:
    if instance_id in predictions and 'claude_code_meta' in predictions[instance_id]:
        turns = predictions[instance_id]['claude_code_meta']['response_data']['num_turns']
        unresolved_turns.append(turns)

print(f"✅ Resolved平均对话轮数: {sum(resolved_turns)/len(resolved_turns):.1f}")
print(f"✖️ Unresolved平均对话轮数: {sum(unresolved_turns)/len(unresolved_turns):.1f}")
```

---

## 🎓 关键洞察

### **JSON报告的优势**

1. **快速查询**: 整体统计一目了然
2. **结构化**: 易于程序化分析
3. **分类清晰**: 实例按状态分类
4. **轻量级**: 文件小，加载快

### **JSON报告的局限**

1. **无详细信息**: 不包含具体错误信息
2. **无Patch内容**: 需要查看Prediction文件
3. **无测试详情**: 需要查看日志文件

### **最佳实践**

```
1. 快速评估 → 查看JSON报告
   ├─ 成功率多少？
   ├─ 哪些类型的失败最多？
   └─ 哪个项目表现最好/最差？

2. 深入分析 → 结合多个信息源
   ├─ JSON报告: 整体统计
   ├─ Prediction文件: 成本、性能、patch内容
   └─ Evaluation日志: 具体错误原因

3. 问题定位 → 三步走
   ├─ JSON找到失败实例ID
   ├─ 日志文件查看错误详情
   └─ Prediction文件检查生成过程
```

---

## 📌 快速参考

### **常用jq命令**

```bash
# 查看成功率
jq '.resolved_instances, .total_instances' evaluation.json

# 查看所有resolved实例
jq -r '.resolved_ids[]' evaluation.json

# 统计各类别数量
jq '{
  total: .total_instances,
  resolved: .resolved_instances,
  unresolved: .unresolved_instances,
  error: .error_instances,
  empty: .empty_patch_instances
}' evaluation.json

# 导出error实例
jq -r '.error_ids[]' evaluation.json > error_instances.txt
```

---

**创建时间**: 2025-10-04
**基于**: Enhanced模式300实例 + 标准API 39实例
**文件路径**: `/home/zqq/SWE4CC/reports/`
