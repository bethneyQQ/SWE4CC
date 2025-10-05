# Evaluation日志信息完整指南

## 📊 Evaluation日志结构

Evaluation日志包含3个层级的信息：

### 1. **主日志文件** (`evaluate_standard_api.log`)
整体进度和汇总信息

### 2. **实例级日志** (`logs/run_evaluation/.../instance_id/run_instance.log`)
每个实例的详细执行过程

### 3. **报告文件** (`reports/.../report.json`)
结构化的evaluation结果

---

## 🔍 详细信息类型

### **A. 整体进度信息**

```
Evaluation: 82%|████████▏ | 32/39 [11:03<01:52, 16.10s/it, ✓=1, ✖=3, error=28]
```

| 字段 | 含义 | 示例值 |
|------|------|--------|
| 82% | 完成百分比 | 已完成32/39 |
| 32/39 | 当前/总数 | 32个已处理 |
| [11:03<01:52] | 已用<预计剩余 | 11分钟已用，1分52秒剩余 |
| 16.10s/it | 平均速度 | 每个实例16秒 |
| ✓=1 | **Resolved** | 测试通过的实例数 |
| ✖=4 | **Unresolved** | 测试失败的实例数 |
| error=34 | **Error** | Patch应用失败等错误 |

---

### **B. Patch应用详情**

#### **成功应用**
```
>>>>> Applied Patch:
patching file django/core/management/commands/sqlmigrate.py
Hunk #1 succeeded at 55 with fuzz 4 (offset -4 lines).
```

#### **失败类型1: Malformed Patch**
```
patch: **** malformed patch at line 10: """Transform an option..."""
```
**问题**: Patch格式不正确
- 上下文行缺少空格前导
- 包含了markdown代码块标记
- 包含了注释或解释文本

#### **失败类型2: Hunk Failed**
```
Hunk #1 FAILED at 1285.
1 out of 1 hunk FAILED -- saving rejects to file *.rej
```
**问题**: 上下文不匹配
- 代码已改变
- 行号偏移过大
- 基于错误的代码版本

#### **失败类型3: File Not Found**
```
can't find file to patch at input line 3
No file to patch. Skipping patch.
```
**问题**: 文件路径错误

#### **失败类型4: Reversed/Duplicate**
```
Reversed (or previously applied) patch detected! Assuming -R.
```
**问题**: Patch方向相反或已应用

#### **成功但有Fuzz**
```
Hunk #1 succeeded at 55 with fuzz 4 (offset -4 lines).
```
**含义**: Patch成功应用，但有些上下文不完全匹配
- `fuzz 4`: 容忍了4行差异
- `offset -4 lines`: 实际位置偏移了-4行

---

### **C. 测试执行结果**

#### **详细的测试报告**
```json
{
  "patch_is_None": false,
  "patch_exists": true,
  "patch_successfully_applied": true,
  "resolved": true,
  "tests_status": {
    "FAIL_TO_PASS": {
      "success": ["test_sqlmigrate_for_non_transactional_databases"],
      "failure": []
    },
    "PASS_TO_PASS": {
      "success": ["test1", "test2", ...],
      "failure": []
    },
    "FAIL_TO_FAIL": {
      "success": [],
      "failure": []
    },
    "PASS_TO_FAIL": {
      "success": [],
      "failure": []
    }
  }
}
```

#### **测试分类详解**

| 类别 | 含义 | 理想结果 |
|------|------|---------|
| **FAIL_TO_PASS** | 修复应该通过的测试 | success非空，failure为空 ✅ |
| **PASS_TO_PASS** | 不应该破坏的测试 | success非空，failure为空 ✅ |
| **FAIL_TO_FAIL** | 仍然失败的测试 | - |
| **PASS_TO_FAIL** | 新引入的失败 | success为空，failure为空 ✅ |

#### **Resolved判定标准**
```python
resolved = (
    patch_successfully_applied == True AND
    FAIL_TO_PASS.success 包含所有目标测试 AND
    PASS_TO_FAIL.failure == []
)
```

---

### **D. 最终汇总信息**

```
Total instances: 39
Instances submitted: 39       # 提交evaluation的实例数
Instances completed: 5        # 完成evaluation的实例数
Instances incomplete: 0       # 未完成的
Instances resolved: 1         # ✅ 通过所有测试
Instances unresolved: 4       # ✖️ 部分/全部测试失败
Instances with empty patches: 0  # 空patch
Instances with errors: 34     # ⚠️ Patch应用失败等
Unstopped containers: 0       # Docker清理状态
Unremoved images: 2           # Docker镜像清理状态
```

---

### **E. 实例级详细日志内容**

每个实例的`run_instance.log`包含：

#### **1. 容器创建**
```
2025-10-04 21:37:57 - INFO - Creating container for django__django-11039...
2025-10-04 21:38:01 - INFO - Container created: 757a6117...
2025-10-04 21:38:01 - INFO - Container started
```

#### **2. Patch应用过程**
```
2025-10-04 21:38:01 - INFO - Intermediate patch written to .../patch.diff
2025-10-04 21:38:02 - INFO - Failed to apply patch: git apply --verbose
2025-10-04 21:38:02 - INFO - Failed to apply patch: git apply --verbose --reject
2025-10-04 21:38:02 - INFO - >>>>> Applied Patch: [详细信息]
```

#### **3. 代码变更对比**
```
2025-10-04 21:38:02 - INFO - Git diff before:
diff --git a/django/core/management/commands/sqlmigrate.py
[完整的diff内容]
```

#### **4. 测试执行**
```
2025-10-04 21:38:11 - INFO - Test output written to .../test_output.txt
```

#### **5. 测试结果**
```
2025-10-04 21:38:11 - INFO - report: {
    'patch_successfully_applied': True,
    'resolved': True,
    'tests_status': {...}
}
Result for django__django-11039: resolved: True
```

#### **6. 清理**
```
2025-10-04 21:38:26 - INFO - Attempting to remove image...
2025-10-04 21:38:26 - INFO - Image removed.
```

---

### **F. 可以查看的相关文件**

对于每个实例，evaluation会生成：

```
logs/run_evaluation/{run_id}/{model}/{instance_id}/
├── run_instance.log         # 主日志文件
├── patch.diff              # 应用的patch
├── test_output.txt         # 测试输出
└── *.rej                   # Patch失败的rejected部分 (如果有)
```

---

## 🎯 常见分析场景

### **场景1: 查看为什么某个instance失败了**
```bash
# 查看该实例的完整日志
cat logs/run_evaluation/{run_id}/{model}/{instance_id}/run_instance.log

# 查看patch内容
cat logs/run_evaluation/{run_id}/{model}/{instance_id}/patch.diff

# 查看测试输出
cat logs/run_evaluation/{run_id}/{model}/{instance_id}/test_output.txt
```

### **场景2: 统计各类错误的数量**
```bash
# 统计malformed patch
grep -r "malformed patch" logs/run_evaluation/{run_id}/ | wc -l

# 统计hunk failed
grep -r "FAILED" logs/run_evaluation/{run_id}/ | wc -l

# 统计file not found
grep -r "can't find file" logs/run_evaluation/{run_id}/ | wc -l
```

### **场景3: 找出所有resolved的实例**
```bash
grep -r "resolved: True" logs/run_evaluation/{run_id}/ | cut -d'/' -f5
```

---

## 📊 实际案例：标准API Retry Evaluation

### **结果分析**
```
总实例: 39
✅ Resolved: 1 (2.6%)
✖️ Unresolved: 4 (10.3%)
⚠️ Error: 34 (87.2%)
```

### **错误分布**
```
Malformed Patch: ~15个 (38%)
  - 缺少空格前导
  - 包含markdown代码块
  - 包含注释文本

Hunk Failed: ~12个 (31%)
  - 上下文不匹配
  - 行号偏移

File Not Found: ~2个 (5%)

Reversed Patch: ~2个 (5%)

Fuzz应用成功: ~3个 (8%)
```

### **成功案例**
- **django__django-11039**: ✅ Resolved
  - Patch成功应用 (with fuzz)
  - FAIL_TO_PASS测试通过
  - 无PASS_TO_FAIL

---

## 🔧 改进建议

基于evaluation日志分析：

### **针对Malformed Patch**
1. 改进prompt，强调不要包含markdown代码块
2. 强调上下文行必须有空格前导
3. 使用后处理脚本清理patch格式

### **针对Hunk Failed**
1. 提供更多上下文行
2. 使用更准确的行号定位
3. 考虑基于语义而非行号的patch

### **针对整体低成功率**
1. 标准API生成的patch格式问题严重 (87%错误率)
2. Enhanced模式虽然也有问题，但格式错误率更低
3. 建议使用Enhanced模式 + patch格式后处理

---

**创建时间**: 2025-10-04
**基于**: Standard API Retry Evaluation (39 instances)
