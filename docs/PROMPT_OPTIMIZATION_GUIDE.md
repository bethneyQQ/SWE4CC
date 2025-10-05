# SWE-bench Prompt优化指南

## 概述

本文档总结了基于业界最佳实践优化Claude Code prompt的方法，以提高SWE-bench评估的一次成功率。

---

## 优化依据

### 1. SWE-bench官方最佳实践 (2024)

来源: OpenAI GPT-4.1 Prompting Guide, SWE-bench Technical Reports

**关键发现**:
- ✅ **明确的步骤规划** → 提升4%通过率
- ✅ **清晰的工具描述** → 提升2%通过率
- ✅ **3个简单指令** → 提升近20%通过率
- ✅ **完整代码块而非最小改动** → 减少"懒惰"代码

**顶级模型表现** (SWE-bench Verified):
```
Claude 4.5 Sonnet:  76.8%
ACoder:             76.4%
TRAE:               75.2%
GPT-4.1 Agent:      55.0%
```

### 2. Unified Diff格式最佳实践

来源: aider.chat研究, GNU diffutils文档

**关键要求**:
```diff
--- a/file.py          # 文件头必须精确
+++ b/file.py
@@ -10,8 +10,9 @@      # Hunk头格式
 context line           # 上下文行以空格开头 (CRITICAL!)
-deleted line           # 删除行以 - 开头
+added line             # 添加行以 + 开头
 more context           # 再次强调：上下文行需要前导空格！
```

**常见错误**:
❌ 忘记上下文行的前导空格 → malformed patch
❌ 使用行号而非hunk头 → 无法应用
❌ 最小化改动导致上下文不足 → 匹配失败
❌ 代码块不完整 → 逻辑错误

### 3. LLM Patch生成研究

来源: Cognition AI, Medium articles on SWE-bench

**有效策略**:
1. **显式结构化输出** - 要求特定的响应格式
2. **示例驱动** - 提供正确格式的示例
3. **多步骤推理** - 分析 → 设计 → 实现
4. **格式验证提醒** - 强调patch会被自动测试

---

## 新Prompt设计

### 核心改进

| 方面 | 旧Prompt | 新Prompt | 预期提升 |
|------|---------|----------|---------|
| 结构 | 简单说明 | 3步骤框架 | +4% |
| 格式说明 | 1行泛泛描述 | 详细6点要求+示例 | +15-20% |
| 上下文要求 | 未提及 | 明确要求3+行 | +5-10% |
| 输出结构 | 无要求 | 3部分结构化 | +3-5% |
| 错误预防 | 无 | 关键点大写强调 | +5% |

### 新Prompt特性

```python
# 位置: swebench/inference/run_claude_code.py:prepare_claude_code_prompt()

1. 三步骤框架 (基于OpenAI研究)
   - Step 1: Analysis
   - Step 2: Solution Design
   - Step 3: Generate Patch

2. 详细格式要求 (基于aider.chat)
   - 6个关键规则
   - 正确格式示例
   - 关键点大写强调 (THIS IS CRITICAL)

3. 结构化输出
   - ## Problem Analysis
   - ## Solution Approach
   - ## Patch

4. 心理提示
   - "patch will be automatically applied and tested"
   - "Format errors will cause immediate failure"
```

---

## 预期效果分析

### 当前问题分布 (300个实例)

```
✅ 已解决:           68  (22.7%)
❌ 测试失败:         74  (24.7%)  ← Prompt可改善
❌ Patch格式错误:    98  (32.7%)  ← Prompt可改善
❌ Patch应用失败:    23  (7.7%)   ← Prompt可改善
❌ Docker限流:       37  (12.3%)  ← 已解决(认证)
```

### 改进预测

#### 保守估计 (+20-30%)

```
格式错误: 98个 → 20-30个  (减少70%)
  - 明确的空格要求
  - 完整上下文要求
  - 示例驱动学习

应用失败: 23个 → 10-15个  (减少40%)
  - 完整代码块要求
  - 更好的上下文匹配

测试失败: 74个 → 55-60个  (减少20%)
  - 多步骤推理
  - 边界情况考虑
  - 兼容性检查

总通过率: 22.7% → 45-55%
```

#### 乐观估计 (+30-40%)

基于Claude 4.5 Sonnet在SWE-bench Verified达到76.8%的表现：

```
格式错误: 98个 → 10-15个  (减少85%)
应用失败: 23个 → 5-8个    (减少70%)
测试失败: 74个 → 45-50个  (减少35%)

总通过率: 22.7% → 55-65%
```

---

## 验证方法

### 小规模测试

建议先在10-20个失败实例上测试：

```bash
# 1. 选择各类错误的代表性实例
python3 -c "
import json
eval_data = json.load(open('reports/claude-3.5-sonnet.full_eval.json'))
error_ids = eval_data['error_ids'][:10]  # 前10个错误实例
print(' '.join(error_ids))
" > test_instances.txt

# 2. 用新prompt重新生成
python3 swebench/inference/run_claude_code.py \
  --instances_path test_instances.txt \
  --model_name claude-3.5-sonnet \
  --output_dir results/test_new_prompt

# 3. 评估新结果
python3 swebench/harness/run_evaluation.py \
  --predictions_path results/test_new_prompt/*.jsonl \
  --run_id test_new_prompt

# 4. 对比结果
python3 scripts/generate_comprehensive_report.py \
  --predictions results/test_new_prompt/*.jsonl \
  --eval-report reports/test_new_prompt.json \
  --log-dir logs/run_evaluation/test_new_prompt
```

### 关键指标

对比新旧prompt在相同实例上的表现：

| 指标 | 目标 |
|------|------|
| 格式错误率 | < 10% (当前32.7%) |
| 应用失败率 | < 5% (当前7.7%) |
| 测试通过率 | > 50% (当前22.7%) |
| 平均成本 | ≤ $0.15/instance (当前$0.11) |

---

## A/B测试建议

### 方案1: 分层采样

```python
# 从每类错误中采样
format_errors_sample = 10个
application_errors_sample = 5个
test_failures_sample = 10个

总测试样本 = 25个
预计成本 = 25 * $0.15 = $3.75
预计时间 = 25 * 30秒 = 12.5分钟
```

### 方案2: 对照实验

```
控制组: 保持原prompt，重新运行50个失败实例
实验组: 使用新prompt，运行相同50个实例

对比指标:
- 格式正确率
- Patch应用成功率
- 测试通过率
- 成本/延迟变化
```

---

## 持续优化

### 迭代改进流程

```
1. 收集失败案例
   ↓
2. 分析失败模式
   ↓
3. 调整prompt针对性规则
   ↓
4. 小规模验证 (10-20个)
   ↓
5. 全量部署或继续迭代
```

### 监控指标

创建监控脚本跟踪：
- 各类错误的比例变化
- 新出现的错误模式
- 成本效益比
- 平均解决时间

---

## 参考文献

1. **OpenAI GPT-4.1 Prompting Guide** (2024)
   - https://cookbook.openai.com/examples/gpt4-1_prompting_guide

2. **Aider: Unified Diffs Make GPT-4 Turbo 3X Less Lazy**
   - https://aider.chat/docs/unified-diffs.html

3. **SWE-bench Leaderboard** (2024)
   - https://www.swebench.com/

4. **Cognition AI: SWE-bench Technical Report**
   - https://cognition.ai/blog/swe-bench-technical-report

5. **SWE-bench Paper** (ICLR 2024)
   - Jimenez et al., "SWE-bench: Can Language Models Resolve Real-world Github Issues?"

6. **GNU Diffutils: Unified Format**
   - http://www.gnu.org/software/diffutils/manual/html_node/Unified-Format.html

---

## 附录: Prompt版本历史

### v1.0 (原始版本)
- 简单的3行说明
- 无具体格式要求
- 通过率: 22.7%

### v2.0 (当前优化版本)
- 三步骤框架
- 详细格式规范
- 示例和警告
- 预期通过率: 45-65%

### 未来改进方向
- [ ] Few-shot示例 (从成功案例中提取)
- [ ] 项目特定的风格指南
- [ ] 动态上下文调整
- [ ] 自我验证步骤
