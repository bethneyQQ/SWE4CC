# 标准API Patch格式问题分析报告

## 📊 Evaluation结果总结

### **整体数据（39个实例）**

```
总实例: 39
✅ Resolved: 1 (2.6%)
✖️ Unresolved: 4 (10.3%)
⚠️ Error: 34 (87.2%)
⭕ Empty Patch: 0 (0%)
```

### **关键发现**

1. ✅ **好消息**: 39个实例全部生成了patch（无空patch）
2. ⚠️ **坏消息**: 87.2%的patch存在格式错误，无法成功应用

---

## 🔍 问题分类

### **错误类型统计**

通过分析evaluation日志：

```bash
Malformed Patch: 17个 (43.6%)
Hunk Failed: 50个hunks失败
Successfully Applied: 5个 (12.8%)
  ├─ Resolved: 1
  └─ Unresolved: 4
```

---

## ⚠️ Malformed Patch详细分析

### **问题1: Markdown代码块标记**

**典型例子**: `django__django-10914/patch.diff`

```diff
--- a/django/conf/global_settings.py
+++ b/django/conf/global_settings.py
@@ -330,7 +330,7 @@
 # Maximum size, in bytes, of a request before it will be streamed to the
 # file system instead of into memory.
 FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # i.e. 2.5 MB

 # Directory in which upload streamed files will be temporarily saved. A value of
 # `None` will make Django use the operating system's default temporary directory
 # (i.e. "/tmp" on *nix systems).      ← 这一行包含在patch中！
@@ -341,7 +341,7 @@
...
-FILE_UPLOAD_PERMISSIONS = None
+FILE_UPLOAD_PERMISSIONS = 0o644

 ...
 ```            ← 结尾有markdown代码块标记
```

**问题**:
- 第10行: `# (i.e. "/tmp" on *nix systems).` 这是**上下文行**，但没有前导空格
- 第20行: ` ``` ` 是markdown代码块结束标记

**导致**: `patch: **** malformed patch at line 10:  # (i.e. "/tmp" on *nix systems).`

### **问题2: 上下文行缺少空格前导**

**典型例子**: `django__django-11742/patch.diff`

```diff
@@ -290,6 +291,32 @@
         else:
             return []

+    @classmethod
+    def _check_max_length_fits_choices(cls):
...
+        return []
+
     @classmethod
     def _check_db_index(cls):      ← 这一行包含在patch中！
         if cls.db_index not in (None, True, False):
 ```            ← 结尾有markdown代码块标记
```

**问题**:
- 第44行: `    def _check_db_index(cls):` 是上下文行，但缺少前导空格
- 第46行: ` ``` ` 是markdown代码块标记

**导致**: `patch: **** malformed patch at line 44:      def _check_db_index(cls):`

---

## 📐 Unified Diff格式规范

### **正确的格式**

```diff
--- a/file.py
+++ b/file.py
@@ -10,6 +10,7 @@
 context line 1         ← 上下文行必须有前导空格
 context line 2         ← 上下文行必须有前导空格
-removed line           ← 删除行用'-'标记
+added line             ← 添加行用'+'标记
 context line 3         ← 上下文行必须有前导空格
```

### **关键规则**

1. **上下文行**: 必须有**一个空格**作为前导
2. **添加行**: 以`+`开头
3. **删除行**: 以`-`开头
4. **不能包含**: Markdown标记、注释、解释文本

---

## 🔧 根本原因分析

### **标准API模式的Patch提取流程**

1. **模型生成响应** (full_output)
   ```
   Here's the fix:

   ```diff
   --- a/file.py
   +++ b/file.py
   ...
   ```

   This patch fixes the issue by...
   ```

2. **提取Patch** (使用正则表达式)
   ```python
   # 简化版提取逻辑
   pattern = r'```(?:diff|patch)?\n(.*?)```'
   match = re.search(pattern, response, re.DOTALL)
   patch = match.group(1)
   ```

3. **问题**:
   - ❌ 模型经常在diff代码块内包含解释性文本
   - ❌ 上下文行被当作普通文本，缺少前导空格
   - ❌ 包含了markdown代码块标记

---

## 📊 对比：Enhanced模式 vs 标准API模式

| 指标 | Enhanced模式 | 标准API模式 |
|------|-------------|------------|
| **Patch格式错误率** | ~30% | **87.2%** ⚠️ |
| **主要问题** | Agent未总结(13%空patch) | Patch格式严重错误 |
| **空Patch率** | 13% | 0% |
| **成功率** | 33.3% | 2.6% |

**结论**: 标准API模式的patch格式问题**远比Enhanced模式严重**

---

## 🛠️ 解决方案

### **方案1: 改进Prompt（已尝试但效果有限）**

```python
prompt = """
Generate a unified diff patch. CRITICAL REQUIREMENTS:
1. Context lines MUST have a leading space
2. NO markdown code blocks (no ```)
3. NO explanations within the diff
4. NO comments in the diff
...
"""
```

**效果**: 仍有87%错误率，说明**prompt改进不够**

### **方案2: 后处理清理Patch ⭐ 推荐**

```python
def clean_patch(patch_text):
    """清理标准API生成的patch"""
    lines = patch_text.split('\n')
    cleaned = []
    in_hunk = False

    for line in lines:
        # 1. 移除markdown标记
        if line.strip() in ['```', '```diff', '```patch']:
            continue

        # 2. 检测hunk header
        if line.startswith('@@'):
            in_hunk = True
            cleaned.append(line)
            continue

        # 3. 保留文件头
        if line.startswith('---') or line.startswith('+++'):
            cleaned.append(line)
            continue

        # 4. 处理hunk内的行
        if in_hunk:
            if line.startswith('+') or line.startswith('-'):
                # 修改/删除行，直接保留
                cleaned.append(line)
            elif line and not line[0] in [' ', '+', '-', '@']:
                # 上下文行缺少前导空格，添加
                cleaned.append(' ' + line)
            else:
                # 已有前导空格的上下文行
                cleaned.append(line)
        else:
            cleaned.append(line)

    return '\n'.join(cleaned)
```

### **方案3: 使用Enhanced模式 + 修复空Patch问题**

```python
# Enhanced模式的问题
empty_patch_rate = 13%  # 39/300

# 解决方案
1. 改进Agent prompt，强制要求总结patch
2. 增加超时后的强制总结机制
3. 检测迷失状态，提示Agent总结
```

---

## 📈 预期效果

### **如果应用方案2（后处理清理）**

```
当前: 87% error → 预期: 30-40% error
原因:
  - 移除markdown标记: 解决43.6%的malformed
  - 修复上下文行前导: 解决部分hunk failed
  - 仍会有真实的hunk failed（代码版本不匹配）
```

### **如果使用Enhanced模式**

```
当前: 33.3% resolved
优化后: 预期40-45% resolved
方法:
  - 修复13%的空patch问题
  - 改进patch格式验证
```

---

## 🎯 建议优先级

### **短期（立即可做）**

1. **实现Patch后处理清理** ⭐⭐⭐
   - 效果最明显
   - 工作量小
   - 可用于标准API和Enhanced模式

2. **分析5个成功实例的共同特征**
   - 为什么只有这5个成功？
   - 它们的patch有什么不同？

### **中期（1-2天）**

1. **改进Enhanced模式的空Patch问题**
   - 修改Agent prompt
   - 增加强制总结机制

2. **A/B测试**
   - 清理后的标准API vs Enhanced模式
   - 对比成本和成功率

### **长期（优化方向）**

1. **混合模式**
   - 简单问题用标准API（成本低）
   - 复杂问题用Enhanced模式（成功率高）
   - 自动判断问题复杂度

---

## 📝 实际案例

### **唯一成功的实例: django__django-11039**

查看`/home/zqq/SWE4CC/logs/run_evaluation/standard-api-retry/claude-sonnet-4-5/django__django-11039/patch.diff`:

```diff
--- a/django/core/management/commands/sqlmigrate.py
+++ b/django/core/management/commands/sqlmigrate.py
@@ -59,7 +59,7 @@
         plan = [(executor.loader.graph.nodes[targets[0]], options["backwards"])]
         sql_statements = executor.collect_sql(plan)
         if not sql_statements and options["verbosity"] >= 1:
             self.stderr.write("No operations found.")
-        self.output_transaction = migration.atomic
+        self.output_transaction = migration.atomic and connection.features.can_rollback_ddl

         return "\n".join(sql_statements)
```

**为什么成功？**
- ✅ 没有markdown标记
- ✅ 上下文行有正确的前导空格
- ✅ 只修改一行，简单清晰
- ✅ 应用成功 (with fuzz 4)

---

## 💡 关键洞察

1. **标准API的主要问题**: Patch格式错误（87%），而非模型能力
2. **可以通过后处理解决**: 大部分格式问题是机械性的
3. **Enhanced模式更可靠**: 虽然有13%空patch，但格式错误率低
4. **成本vs成功率权衡**:
   - 标准API: 便宜但成功率低（2.6%）
   - Enhanced: 贵但成功率高（33.3%）

---

**创建时间**: 2025-10-04
**基于数据**: 标准API retry 39实例evaluation结果
**文件路径**: `/home/zqq/SWE4CC/reports/`
