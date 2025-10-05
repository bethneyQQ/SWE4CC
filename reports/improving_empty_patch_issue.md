# 改进Enhanced模式空Patch问题的方案

## ❓ 问题回答

**问：改进Enhanced模式需要修改Claude Code CLI吗？**

**答：不需要！** 所有改进都通过**修改inference脚本中的prompt**来实现。

---

## 📋 当前架构

### **Enhanced模式的工作流程**

```
1. Python脚本 (run_enhanced_claude_code.py)
   ├─ 读取SWE-bench实例数据
   ├─ 准备代码仓库
   └─ 生成prompt (enhanced_prompts.py)
       ↓
2. 调用Claude Code CLI
   ├─ 传入prompt
   ├─ CLI agent自主探索
   └─ 返回结果
       ↓
3. Python脚本提取patch
   └─ 从CLI输出中提取patch
```

### **关键文件**

- `/home/zqq/SWE4CC/swebench/inference/enhanced_prompts.py` - Prompt生成
- `/home/zqq/SWE4CC/swebench/inference/run_claude_code.py` - CLI调用逻辑
- `/home/zqq/SWE4CC/scripts/run_enhanced_claude_code.py` - 主执行脚本

**修改点：只需修改这些Python文件的prompt，无需改动Claude Code CLI**

---

## 🎯 空Patch问题分析

### **当前数据**

```
Enhanced模式300实例:
  - 有效patch: 261 (87%)
  - 空patch: 39 (13%)
```

### **空Patch的原因**

从日志分析发现：

```
空patch实例特征:
  - 平均对话轮数: 35+轮
  - 平均成本: $0.24 (比成功实例高)
  - result字段: 为空
  - 共同模式: Agent探索了很多，但最后没有总结patch
```

**根本原因：Agent "迷失" - 探索了代码但忘记了最终任务**

---

## 🛠️ 改进方案（无需修改CLI）

### **方案1: 改进Prompt结构 ⭐⭐⭐**

**修改文件**: `/home/zqq/SWE4CC/swebench/inference/enhanced_prompts.py`

#### **当前Prompt的问题**

```python
# 当前 (第86行之前)
prompt = """...
Remember: You have tools! Use Read to see the actual code before generating the patch."""
```

- ❌ 结尾太弱，容易被Agent忽略
- ❌ 没有强调"必须输出patch"
- ❌ 探索和输出阶段不够清晰

#### **改进版Prompt**

```python
def prepare_enhanced_claude_code_prompt(datum: Dict, repo_path: str) -> str:
    instance_id = datum.get("instance_id", "unknown")
    problem = datum.get("problem_statement", "")
    hints = datum.get("hints_text", "")
    base_commit = datum.get("base_commit", "")

    prompt = f"""You are debugging issue {instance_id} in a git repository.

**REPOSITORY INFO:**
- Path: {repo_path}
- Commit: {base_commit}
- You have full access to read files using the Read tool
- You can search code using Grep tool
- You can run commands using Bash tool

**PROBLEM DESCRIPTION:**
{problem}

**HINTS (files that may be relevant):**
{hints if hints else "No specific hints provided - you'll need to explore the codebase"}

**YOUR TASK (CRITICAL - DO NOT SKIP THE FINAL STEP):**

**PHASE 1: EXPLORATION (Use Tools)**
1. Use Bash to navigate to {repo_path}
2. Use Grep/Bash to locate relevant files
3. Use Read to examine the actual code at this commit
4. Analyze the issue and identify what needs to change

**PHASE 2: SOLUTION (MANDATORY OUTPUT)**
5. Generate a unified diff patch
6. Output the patch in a ```diff``` code block

⚠️ **CRITICAL**: You MUST end with a patch in ```diff``` format. Do not stop after exploration!

**PATCH REQUIREMENTS:**
- Use EXACT line numbers from the files you read
- Context lines MUST start with a space character ` `
- Include 3+ lines of context before and after changes
- Must end with a newline

**OUTPUT FORMAT (MANDATORY):**
```diff
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -10,6 +10,7 @@
 def function():
     existing_line = True
-    old_code()
+    new_code()
 return result
```

**🚨 REMINDER**: Your final message MUST contain a ```diff``` code block with the patch!"""

    return prompt
```

**关键改进点**：
1. ✅ 分为两个阶段：EXPLORATION和SOLUTION
2. ✅ 多次强调"MUST end with a patch"
3. ✅ 使用视觉标记（⚠️、🚨）增强注意
4. ✅ 明确要求"final message MUST contain patch"

---

### **方案2: 添加强制总结机制 ⭐⭐**

**修改文件**: `/home/zqq/SWE4CC/swebench/inference/run_claude_code.py`

#### **实现逻辑**

```python
def run_claude_code_with_summary_enforcement(prompt, repo_path, max_turns=50):
    """
    调用Claude Code CLI并在必要时强制要求总结
    """
    # 1. 调用CLI
    result = run_claude_code_cli(prompt, repo_path)

    # 2. 检查是否有patch
    patch = extract_patch_from_output(result['output'])

    # 3. 如果没有patch且对话轮数较多，发送总结请求
    if not patch and result.get('num_turns', 0) > 30:
        summary_prompt = """
You've explored the codebase extensively. Now PLEASE PROVIDE YOUR FINAL PATCH.

Based on your analysis, generate the unified diff patch to fix this issue.

Format:
```diff
--- a/file.py
+++ b/file.py
...
```

DO NOT explore further. Just output the patch based on what you've already learned."""

        # 继续对话，要求总结
        result = continue_claude_code_session(summary_prompt)
        patch = extract_patch_from_output(result['output'])

    return result, patch
```

**实现方式**：
- 在Python脚本中检测"对话轮数多但无patch"的情况
- 自动追加一个"请总结patch"的消息
- 利用Claude Code CLI的session功能继续对话

---

### **方案3: 添加中途检查点 ⭐**

**修改文件**: `/home/zqq/SWE4CC/swebench/inference/enhanced_prompts.py`

#### **改进Prompt添加检查点**

```python
prompt = f"""...

**WORKFLOW WITH CHECKPOINTS:**

**CHECKPOINT 1: After exploring (~ 10-20 tool uses)**
Stop and ask yourself: "Have I understood the issue and located the relevant code?"
If YES → Proceed to CHECKPOINT 2
If NO → Continue exploring

**CHECKPOINT 2: Before generating patch**
You should now have:
  - ✅ Located the file(s) to modify
  - ✅ Read the actual file content
  - ✅ Identified the exact lines to change

Now generate the patch.

**CHECKPOINT 3: FINAL OUTPUT (MANDATORY)**
Your response MUST contain:
```diff
--- a/file.py
+++ b/file.py
...
```

If you don't have enough information, generate your BEST ATTEMPT patch rather than no patch."""
```

---

### **方案4: 使用两阶段Prompt ⭐⭐**

**概念**: 分两次调用Claude Code CLI

```python
# 第一阶段: 探索
exploration_prompt = """Explore the codebase to understand this issue.
Output: Summary of what you found and what needs to change."""

exploration_result = run_claude_code(exploration_prompt)

# 第二阶段: 生成patch（基于探索结果）
patch_prompt = f"""Based on your previous exploration:
{exploration_result['output']}

Now generate the unified diff patch.
Your ENTIRE response should be:
```diff
...
```
"""

patch_result = run_claude_code(patch_prompt)
```

**优点**：
- ✅ 清晰分离探索和生成
- ✅ 第二阶段只有一个任务：生成patch
- ✅ 不容易"忘记"最终目标

**缺点**：
- ❌ 需要两次CLI调用（成本增加）
- ❌ 无法利用第一阶段的工具使用context

---

## 📊 方案对比

| 方案 | 工作量 | 成本影响 | 预期效果 | 推荐度 |
|------|--------|---------|---------|--------|
| **方案1: 改进Prompt** | 低 | 无 | +5-8% | ⭐⭐⭐ |
| **方案2: 强制总结** | 中 | +小量 | +8-10% | ⭐⭐⭐ |
| **方案3: 检查点** | 低 | 无 | +3-5% | ⭐⭐ |
| **方案4: 两阶段** | 高 | +50% | +10-12% | ⭐ |

---

## 🎯 推荐实施方案

### **阶段1: 立即实施（今天）**

**方案1 + 方案3组合**
- 改进`enhanced_prompts.py`中的prompt结构
- 添加视觉提示和明确的阶段划分
- 添加检查点提醒

**预期效果**：
- 空patch率从13%降至5-8%
- 成本无增加
- 工作量：30分钟

### **阶段2: 短期优化（明天）**

**实施方案2**
- 在`run_claude_code.py`中添加检测逻辑
- 当对话轮数>30且无patch时，自动追加总结请求
- 需要研究Claude Code CLI的session API

**预期效果**：
- 空patch率从5-8%降至2-3%
- 成本增加<5%（仅对部分实例追加请求）
- 工作量：2-3小时

### **阶段3: 长期实验（可选）**

**小规模测试方案4**
- 对10个复杂实例测试两阶段方法
- 对比成本和成功率
- 决定是否全面采用

---

## 💻 代码示例：方案1实现

**修改文件**: `/home/zqq/SWE4CC/swebench/inference/enhanced_prompts.py`

**第8行开始替换为**：

```python
def prepare_enhanced_claude_code_prompt(datum: Dict, repo_path: str) -> str:
    """
    Create an enhanced prompt with clear phases and mandatory patch output.

    改进点:
    1. 明确分为EXPLORATION和SOLUTION两个阶段
    2. 多次强调必须输出patch
    3. 使用视觉标记增强注意
    """
    instance_id = datum.get("instance_id", "unknown")
    problem = datum.get("problem_statement", "")
    hints = datum.get("hints_text", "")
    base_commit = datum.get("base_commit", "")

    prompt = f"""You are fixing issue {instance_id} in a git repository.

**REPOSITORY:**
- Path: {repo_path}
- Commit: {base_commit}
- Tools: Read, Grep, Bash

**PROBLEM:**
{problem}

**RELEVANT FILES:**
{hints if hints else "Search for relevant files using Grep/Bash"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**YOUR WORKFLOW (2 PHASES - BOTH MANDATORY):**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📍 PHASE 1: EXPLORATION (Use your tools)**
1. Navigate to {repo_path}
2. Find relevant files (use Grep/Bash)
3. Read the actual code (use Read tool)
4. Identify what needs to change

**📍 PHASE 2: SOLUTION (MANDATORY - DO NOT SKIP)**
5. Generate unified diff patch
6. Output in ```diff``` code block

⚠️ **CRITICAL**: After exploration, you MUST generate the patch!
🚨 **REMINDER**: Do not end your response without a ```diff``` block!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**PATCH FORMAT (MANDATORY OUTPUT):**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```diff
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -10,6 +10,7 @@
 def function():
     existing = True
-    old_line()
+    new_line()
+    added_line()
 return result
```

**PATCH REQUIREMENTS:**
✓ Context lines start with space ` `
✓ Use exact line numbers from Read output
✓ Include 3+ context lines before/after
✓ End with newline

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 **YOUR GOAL**: Explore the code, then generate the patch. Both steps are REQUIRED!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    return prompt
```

---

## ✅ 总结

**回答你的问题**：
- ❌ **不需要修改Claude Code CLI**
- ✅ **只需修改Python inference脚本中的prompt**
- ✅ **所有改进都在用户代码层面**

**最简单有效的方案**：
1. 修改`enhanced_prompts.py`的prompt（30分钟）
2. 添加视觉提示和明确的阶段划分
3. 多次强调"MUST output patch"

**预期效果**：
- 空patch率：13% → 5-8%（立即）→ 2-3%（方案2后）
- 成本：无增加（方案1）→ +小量（方案2）
- 整体成功率：33.3% → 38-40%

---

**创建时间**: 2025-10-04
**文件路径**: `/home/zqq/SWE4CC/reports/`
