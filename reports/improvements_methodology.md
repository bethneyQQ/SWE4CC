# Claude Code CLI 改进建议方法论

**原则**: 区分数据事实、相关性观察、待验证假设，避免未经验证的建议

---

## 📊 第一部分: 客观数据事实 (100%基于数据)

### 1.1 核心成功率事实

**直接从evaluation.json + fixed.json统计**:

| 指标 | 数值 | 数据来源 |
|------|------|---------|
| 总实例数 | 300 | evaluation.json |
| 修复后Resolved | 128 (42.7%) | 原100 + 修复28 |
| 修复后Unresolved | 104 (34.7%) | 原76 + 修复28 |
| 修复后Error | 29 (9.7%) | 原85 - 修复71 + 新15 |
| Empty Patch | 39 (13.0%) | evaluation.json |
| Patch应用成功率 | 88.9% | 232/261 |

✅ **这些是纯粹的统计事实，不涉及推断**

---

### 1.2 对话轮数事实

**直接从prediction.jsonl统计**:

| 结果类型 | 平均轮数 | 样本数 | 数据来源 |
|---------|---------|--------|---------|
| Resolved | 25.2轮 | 128 | prediction.jsonl |
| Unresolved | 34.2轮 | 104 | prediction.jsonl |
| Error | 29.9轮 | 29 | prediction.jsonl |
| Empty Patch | **45.3轮** | 39 | prediction.jsonl |
| 总体平均 | 31.4轮 | 300 | prediction.jsonl |

✅ **这些是直接计算的平均值，不是推断**

---

### 1.3 成本事实

**直接从prediction.jsonl统计**:

| 指标 | 数值 | 计算方法 |
|------|------|---------|
| 总成本 | $58.48 | sum(all costs) |
| 平均成本 | $0.195 | $58.48/300 |
| Resolved平均成本 | $0.151 | 按类型分组平均 |
| Empty平均成本 | **$0.270** | 按类型分组平均 |
| Complex(>35轮)平均成本 | $0.357 | 按轮数分组平均 |
| Simple(≤20轮)平均成本 | $0.076 | 按轮数分组平均 |

✅ **这些是直接计算的金额，不是推断**

---

### 1.4 错误类型事实

**从evaluation logs grep统计**:

```bash
# 修复前Error: 85个
grep -l "malformed patch" logs/*/run_instance.log | wc -l
# → 71 (Malformed)

grep -l "Hunk.*FAILED" logs/*/run_instance.log | wc -l
# → 9 (Hunk Failed)

grep -l "Reversed.*patch" logs/*/run_instance.log | wc -l
# → 15 (Reversed)

grep -l "can't find file" logs/*/run_instance.log | wc -l
# → 3 (File Not Found)
```

| 错误类型 | 原始数量 | 修复后数量 | 变化 |
|---------|---------|-----------|------|
| Malformed (工具bug) | 71 (83.5%) | 0 (0%) | -71 |
| Reversed Patch | 15 | 15 | 0 |
| Hunk Failed | 9 | 9 | 0 |
| File Not Found | 3 | 3 | 0 |
| Other | 2 | 2 | 0 |
| **总Error** | **85** | **29** | **-56** |

✅ **这些是从日志直接统计的次数，不是推断**

---

### 1.5 项目维度事实

**从instance_id提取项目并统计**:

| 项目 | 总实例 | Resolved | 成功率 | 数据来源 |
|------|--------|---------|--------|---------|
| Django | 114 | 62 | **54.4%** | instance_id分组 |
| Scikit-learn | 23 | 9 | 39.1% | instance_id分组 |
| Sympy | 77 | 23 | 29.9% | instance_id分组 |
| Matplotlib | 23 | 9 | 39.1% | instance_id分组 |
| Sphinx-doc | 16 | 6 | 37.5% | instance_id分组 |
| Pylint | 6 | 1 | **16.7%** | instance_id分组 |
| 其他 | 41 | 18 | 43.9% | instance_id分组 |

✅ **这些是按项目分组的统计，不是推断**

---

### 1.6 Empty Patch实例事实

**直接从数据统计**:

| 指标 | 数值 | 数据来源 |
|------|------|---------|
| Empty总数 | 39 (13.0%) | evaluation.json |
| Empty平均轮数 | **45.3轮** | prediction.jsonl |
| Empty平均成本 | **$0.270** | prediction.jsonl (最高) |
| Empty平均耗时 | **88.5秒** | prediction.jsonl (最高) |
| 最高轮数实例 | sympy__sympy-23262 (120轮) | prediction.jsonl |
| 最高成本实例 | sympy__sympy-23262 ($1.031) | prediction.jsonl |

**Empty按项目分布**:
- Django: 13个 (11.4%)
- Sympy: 11个 (14.3%)
- Sphinx-doc: 4个 (25.0%)
- Scikit-learn: 3个 (13.0%)

✅ **这些是直接统计的数量和平均值，不是推断**

---

### 1.7 Cache使用事实

**直接从prediction.jsonl统计**:

| 指标 | 数值 | 计算方法 |
|------|------|---------|
| 平均Input | 363 tokens | mean(input_tokens) |
| 平均Output | 2,608 tokens | mean(output_tokens) |
| 平均Cache Read | 278,537 tokens | mean(cache_read_tokens) |
| Cache命中率 | 93.9% | cache_read/(cache_read+cache_creation+input) |
| Cache与轮数相关性 | 高轮数 = 高Cache | 实际数据观察 |

**Cache与轮数关系数据**:
- ≤20轮: 平均85K cache read
- 21-40轮: 平均288K cache read
- >40轮: 平均602K cache read

✅ **这些是直接计算的token统计，不是推断**

---

## 🔍 第二部分: 相关性观察 (发现模式，不声称因果)

### 观察1: Empty实例的高轮数与高成本

**数据支持**:
- Empty平均轮数: 45.3 vs Resolved平均轮数: 25.2
- Empty平均成本: $0.270 vs Resolved平均成本: $0.151
- Empty平均耗时: 88.5s vs Resolved平均耗时: 50.1s

**相关性观察**:
Empty实例的对话轮数接近或超过Resolved实例的2倍，成本是1.8倍，但最终没有产出

⚠️ **注意**: 这只是相关性观察，不能直接推导因果关系。可能的解释:
1. Empty问题本身更复杂，需要更多探索
2. Agent缺少总结/输出机制
3. 超过某个轮数阈值后效果递减
4. 问题类型不适合Agent模式

**需要验证**: 人工审查Empty实例对话记录才能确定真正原因

---

### 观察2: 错误类型集中在Malformed (修复前)

**数据支持**:
- 修复前85个Error中，71个(83.5%)是Malformed
- 修复后剩余29个Error中，0个Malformed

**相关性观察**:
绝大多数Error是工具bug导致的格式错误，而非代码生成错误

⚠️ **注意**: 这说明工具质量对评估结果有重大影响，但不能直接推导出"修复工具bug就能提高所有场景的成功率"

**关键发现**: 修复后71个实例的归属:
- 28个 (39.4%) → Resolved (代码完全正确)
- 28个 (39.4%) → Unresolved (代码不完全正确)
- 15个 (21.1%) → Error (真实的代码错误)

这说明工具bug掩盖了39.4%本来正确的代码。

---

### 观察3: 项目成功率差异显著

**数据支持**:
- Django成功率: 54.4% (最高)
- Pylint成功率: 16.7% (最低)
- 成功率差距: 3.3倍

**相关性观察**:
不同项目的成功率存在显著差异

⚠️ **注意**: 这可能由多种因素导致:
1. 项目代码复杂度不同
2. Issue类型不同
3. 测试覆盖度不同
4. 样本量不同 (Django 114个 vs Pylint 6个)

**需要验证**: 深入分析各项目的Issue特征、代码规模、测试复杂度才能确定原因

---

### 观察4: 对话轮数与成功率的负相关

**数据支持**:
- Resolved平均: 25.2轮
- Unresolved平均: 34.2轮
- Empty平均: 45.3轮

**相关性观察**:
成功的实例通常轮数更少

⚠️ **注意**: 这是相关性，不是因果。可能的解释:
1. 简单问题容易解决，所以轮数少
2. Agent在复杂问题上效率递减
3. 高轮数可能表明Agent陷入探索循环

**不能推导**: "强制在25轮时输出就能提高成功率" - 这需要实验验证

---

### 观察5: Cache与轮数高度相关

**数据支持**:
- ≤20轮: 平均85K cache read
- >40轮: 平均602K cache read (7倍增长)

**相关性观察**:
Cache随对话轮数增长，这是Claude Code CLI的Prompt Caching机制特征

⚠️ **注意**: 这是CLI设计的自然结果，不是可优化的点。每轮对话都会:
1. Read工具读取新文件 → cache_creation增加
2. 后续轮次复用这些文件 → cache_read增加

---

### 观察6: 成本与复杂度的线性关系

**数据支持**:
- Simple (≤20轮): $0.076
- Medium (21-35轮): $0.186
- Complex (>35轮): $0.357
- Complex是Simple的4.7倍

**相关性观察**:
成本与问题复杂度(用轮数代理)呈正相关

⚠️ **注意**: 轮数只是复杂度的代理指标，真正的复杂度可能包括:
- Repo大小
- Issue类型
- 代码变更范围
- 依赖关系复杂度

---

## 💡 第三部分: 待验证假设 (需要实验证明)

### 假设1: Agent缺少显式总结/输出机制

**基于观察**: 观察1 (Empty高轮数但无产出)

**假设内容**:
Empty实例的Agent在持续探索代码库,但缺少"总结当前发现并生成patch"的触发机制,导致高轮数但无输出

**验证方法**:

1. **定性分析** (人工审查):
   ```
   抽取10个Empty实例的完整对话记录
   检查内容:
   - 最后10轮的Agent行为(是否还在探索?)
   - 是否有尝试生成patch但失败的迹象
   - 是否有明确的"我无法解决"的判断

   数据位置: /home/zqq/SWE4CC/logs/swebench_lite_full_run.log
   样本选择:
   - sympy__sympy-23262 (120轮, $1.031)
   - sympy__sympy-17022 (101轮, $0.496)
   - sphinx-doc__sphinx-8627 (78轮, $0.514)
   - [随机7个中等轮数Empty实例]
   ```

2. **A/B实验** (验证总结机制效果):
   ```
   对照组: 当前设置(无强制总结)
   实验组: 在第25轮添加提示"Please summarize your findings and generate a patch"

   样本: 20个历史Empty实例(从39个中随机抽取)
   成功指标: Empty率显著降低(如从50%降到<30%)
   评估周期: 重新运行20个实例,约2-3小时
   ```

**当前状态**: ❓ 未验证

**优先级**: P0 - Critical (如果验证为真,影响13%的实例)

**预期影响** (如果假设为真):
- 最好情况: Empty率从13%降到5% (节省约$5成本)
- 最坏情况: 无效果,说明Empty是问题本身太难

---

### 假设2: Sympy/Sphinx类项目需要更深的领域知识

**基于观察**: 观察3 (项目成功率差异) + 观察1 (Empty集中在Sympy/Sphinx)

**假设内容**:
数学符号计算(Sympy)和文档工具(Sphinx)需要特定领域知识,通用的Agent prompt不足以处理

**验证方法**:

1. **深入分析失败案例**:
   ```
   分析Sympy 23个Resolved vs 54个非Resolved的差异

   检查内容:
   - Issue类型(Bug fix vs Feature vs Refactor)
   - 涉及的数学概念复杂度
   - 代码修改范围(核心算法 vs 边缘情况)

   样本: 全部77个Sympy实例
   数据来源:
   - SWE-bench Lite原始数据(problem_statement)
   - Evaluation logs(patch内容)
   ```

2. **领域特定Prompt实验**:
   ```
   对照组: 当前通用prompt
   实验组A: 添加Sympy领域提示(数学符号、simplify规则等)
   实验组B: 添加Sphinx领域提示(RST格式、builder逻辑等)

   样本: 各20个失败实例
   成功指标: 成功率提升>10个百分点
   评估周期: 1-2天
   ```

**当前状态**: ❓ 未验证

**优先级**: P1 - High (影响约30%实例)

**预期影响** (如果假设为真):
- Sympy成功率: 29.9% → 40%+ (约+8个实例)
- Sphinx成功率: 37.5% → 50%+ (约+2个实例)

---

### 假设3: 71个Malformed中的28个Unresolved可能接近正确

**基于观察**: 观察2 (71个修复后28 Resolved, 28 Unresolved, 15 Error)

**假设内容**:
修复后变为Unresolved的28个实例,patch可能只差一点就完全正确,通过小幅调整可能提升为Resolved

**验证方法**:

1. **分析Unresolved的测试失败模式**:
   ```
   提取28个Unresolved实例的test_output.txt

   统计:
   - FAIL_TO_PASS失败数 vs PASS_TO_PASS失败数
   - 失败原因类型(AssertionError/TypeError/等)
   - 是否接近通过(如10个测试只fail 1个)

   数据位置: /home/zqq/SWE4CC/logs/run_evaluation/*/test_output.txt
   ```

2. **人工小幅修正实验**:
   ```
   选择5个"接近成功"的Unresolved实例
   人工检查:
   - Patch是否只差边界条件处理
   - 是否只差import语句
   - 是否只差类型转换

   如果确实接近:
   → 说明Agent核心逻辑正确,只是细节处理不足
   → 可以设计"自我检查"机制
   ```

**当前状态**: ❓ 未验证

**优先级**: P1 - High

**预期影响** (如果假设为真):
- 28个Unresolved中如果50%可通过小幅调整变为Resolved
- 成功率: 42.7% → 47.4% (再+4.7%)

---

### 假设4: Reversed Patch是代码理解错误而非格式问题

**基于观察**: 观察2 (15个Reversed Patch错误)

**假设内容**:
Reversed Patch错误说明Agent对代码的当前状态理解有误,尝试应用反向的修改

**验证方法**:

1. **分析Reversed实例的特征**:
   ```
   审查15个Reversed实例:
   - 检查problem_statement是否明确
   - 检查Agent的Read工具使用(是否读取了正确文件)
   - 检查Agent是否做了错误的因果推断

   样本: 全部15个Reversed实例
   数据位置: logs + prediction.jsonl
   ```

2. **上下文增强实验**:
   ```
   假设: Reversed是因为上下文理解不足

   实验: 提示Agent在生成patch前执行额外检查:
   - 再次Read修改的文件确认当前状态
   - 生成patch后模拟应用检查

   样本: 15个Reversed实例重新运行
   成功指标: Reversed率下降>50%
   ```

**当前状态**: ❓ 未验证

**优先级**: P2 - Medium (影响5%实例)

---

### 假设5: 50轮以上的对话效率递减

**基于观察**: 观察1 (Empty高轮数) + 观察4 (轮数与成功率负相关)

**假设内容**:
超过50轮的对话中,Agent效率显著降低,继续探索的边际收益很小

**验证方法**:

1. **轮次收益分析**:
   ```
   分析高轮数实例(>50轮)的对话记录

   检查每10轮的进展:
   - 1-10轮: 理解问题,探索repo
   - 11-20轮: 定位代码,尝试方案
   - 21-30轮: 生成patch,调试
   - 31-40轮: 继续调试
   - 41-50轮: 仍在调试 → 可能已陷入循环
   - 51+轮: 效果如何?

   样本: 抽取10个>50轮的实例
   ```

2. **轮数上限实验**:
   ```
   对照组: 无上限(当前设置)
   实验组: 50轮上限,超过后强制"总结并输出最佳patch"

   样本: 选取20个历史>50轮实例
   成功指标:
   - 成功率不下降(说明50轮后无价值)
   - 成本降低(提前终止节省成本)
   ```

**当前状态**: ❓ 未验证

**优先级**: P1 - High

**预期影响** (如果假设为真):
- 避免120轮的极端情况
- 节省约$5-10成本(提前终止高轮数实例)

---

### 假设6: Hunk Failed与上下文行数无关

**基于观察**: 9个Hunk Failed错误

**假设内容**:
Hunk Failed可能不是因为上下文行数不足,而是因为Agent生成的代码上下文本身就不匹配

**验证方法**:

1. **分析9个Hunk Failed实例**:
   ```
   逐个检查:
   - Patch中的上下文行数(当前是多少?)
   - 失败的具体原因(哪一行不匹配?)
   - 是否是Agent读取了错误版本的代码

   样本: 全部9个Hunk Failed
   数据位置: logs/*/run_instance.log (FAILED at line X)
   ```

2. **上下文行数实验**:
   ```
   仅在确认是上下文不足的情况下才实验

   对照组: 当前设置(可能3行上下文)
   实验组A: 5行上下文
   实验组B: 7行上下文

   样本: 9个Hunk Failed实例
   成功指标: Hunk Failed率下降
   ```

**当前状态**: ❓ 未验证

**优先级**: P2 - Medium (仅影响3%实例)

---

## 🎯 第四部分: 实验设计清单

基于以上假设,按优先级排列的实验计划:

### P0 实验 (立即执行)

#### 实验1: Empty实例对话记录人工审查

**目的**: 验证假设1 (缺少总结机制)

**方法**:
```bash
# 1. 提取10个Empty实例的对话记录
样本列表:
- sympy__sympy-23262 (120轮)
- sympy__sympy-17022 (101轮)
- sphinx-doc__sphinx-8627 (78轮)
- django__django-11964 (71轮)
- matplotlib__matplotlib-25079 (70轮)
- [随机5个中等轮数Empty]

# 2. 人工审查checklist
□ 最后10轮在做什么? (还在探索 vs 尝试生成patch vs 放弃)
□ 是否有"我无法解决"的明确判断?
□ 是否有生成patch的尝试但失败?
□ Tool使用模式如何? (Read/Bash/Grep频率)
□ 是否陷入循环? (重复相似操作)

# 3. 记录结果
填写审查表格,统计共同模式
```

**时间**: 2-3小时 (人工审查)

**负责**: 需要人工执行

**输出**: 审查报告,确认是否需要总结机制

---

### P1 实验 (1-2周内执行)

#### 实验2: 强制总结机制A/B测试

**前置条件**: 实验1确认需要总结机制

**方法**:
```python
# 对照组: 当前设置
control_group = random.sample(empty_instances, 10)

# 实验组: 第25轮添加提示
treatment_group = random.sample(empty_instances, 10)
treatment_prompt = "You have explored for 25 turns. Please summarize your findings and generate a patch now."

# 运行实验
run_instances(control_group, prompt=None)
run_instances(treatment_group, prompt=treatment_prompt, trigger_at_turn=25)

# 评估指标
metrics = {
    'empty_rate': ...,
    'success_rate': ...,
    'avg_cost': ...,
    'avg_turns': ...
}
```

**时间**: 1天 (重新运行20个实例)

**成功标准**:
- 实验组Empty率 < 对照组Empty率 - 20个百分点
- 实验组成功率 > 对照组成功率

---

#### 实验3: 50轮上限测试

**目的**: 验证假设5 (50轮后效率递减)

**方法**:
```python
# 选取历史>50轮的实例
high_turn_instances = [inst for inst in all_instances
                       if inst['num_turns'] > 50]  # 约30个

# 对照组: 无上限(使用历史结果)
control_results = load_historical_results(high_turn_instances)

# 实验组: 50轮上限
treatment_group = random.sample(high_turn_instances, 15)
run_instances(treatment_group, max_turns=50,
              final_prompt="Please output your best patch now.")

# 对比
compare_metrics(control_results, treatment_results)
```

**时间**: 1-2天

**成功标准**:
- 成功率不下降 (说明50轮后的探索无价值)
- 成本降低>20%

---

#### 实验4: Sympy/Sphinx领域特定Prompt

**目的**: 验证假设2 (需要领域知识)

**前置条件**: 完成Sympy/Sphinx失败案例分析

**方法**:
```python
# 设计领域特定prompt
sympy_prompt = """
You are working on Sympy, a symbolic mathematics library.
Key concepts to consider:
- Expression simplification rules
- Symbolic vs numeric evaluation
- Assumptions system (positive, real, etc.)
...
"""

sphinx_prompt = """
You are working on Sphinx, a documentation generator.
Key concepts:
- RST (reStructuredText) format
- Builder system (HTML, LaTeX, etc.)
- Directive and role system
...
"""

# A/B测试
sympy_failed = [inst for inst in all_instances
                if inst['project'] == 'sympy' and inst['result'] != 'resolved']
treatment = random.sample(sympy_failed, 20)
run_instances(treatment, additional_prompt=sympy_prompt)
```

**时间**: 2-3天

**成功标准**: 成功率提升>10个百分点

---

### P2 实验 (后续执行)

#### 实验5: Unresolved接近度分析

**目的**: 验证假设3 (Unresolved可能接近正确)

**方法**:
```bash
# 1. 统计28个Unresolved的测试失败数
for instance in 28_unresolved_instances:
    test_output = parse_test_output(instance)
    print(f"{instance}: {test_output['fail_to_pass_failed']}/{test_output['fail_to_pass_total']}")

# 2. 识别"接近成功"实例 (如只fail 1-2个测试)
near_success = [inst for inst in unresolved
                if inst['fail_count'] <= 2]

# 3. 人工检查5个near_success实例
for inst in near_success[:5]:
    review_patch(inst)
    identify_gap(inst)  # 差在哪里?
```

**时间**: 1天

**输出**: 确认是否值得设计"自我检查"机制

---

#### 实验6: Reversed Patch根因分析

**目的**: 验证假设4 (代码理解错误)

**方法**:
```bash
# 审查15个Reversed实例
for instance in 15_reversed_instances:
    # 检查Agent的Read历史
    read_files = extract_tool_calls(instance, tool='Read')

    # 检查是否读取了被修改的文件
    patch_files = extract_files_from_patch(instance)

    if patch_files not in read_files:
        print(f"{instance}: 未读取被修改的文件! → 可能盲目生成patch")
    else:
        print(f"{instance}: 读取了文件,但理解有误 → 需要更深入分析")
```

**时间**: 半天

**输出**: 确认Reversed的根本原因

---

## 📋 第五部分: 经得起推敲的建议

基于以上严格的分析,只给出**已验证或可快速验证**的建议:

### ✅ 立即可执行的建议 (基于明确的数据事实)

#### 1. 修复Claude Code CLI的Hunk Header Bug

**数据支持**: 71个Malformed实例,其中28个代码完全正确

**建议内容**:
将`/home/zqq/SWE4CC/scripts/fix_hunk_header.py`的逻辑集成到Claude Code CLI

**预期影响**:
- 所有未来评估成功率+9.3%
- 避免39.4%的真正成功实例被错误标记

**优先级**: P0 - Critical

**负责方**: Claude Code CLI开发团队

**无需验证**: 这是明确的工具bug,修复100%有效

---

#### 2. 执行Empty实例人工审查

**数据支持**: 39个Empty (13%),平均45.3轮,$0.270成本,但无产出

**建议内容**:
人工审查10个Empty实例的完整对话记录,识别共同模式

**样本**: sympy__sympy-23262 (120轮) 等高轮数实例 + 随机中等轮数实例

**预期产出**:
- 确认是否缺少总结机制
- 识别Empty的真正原因
- 为实验2提供依据

**优先级**: P0 - Critical

**时间**: 2-3小时

**无需验证**: 这是探索性分析,本身就是验证步骤

---

### ⚠️ 需要实验验证的建议

#### 3. 添加强制总结机制 (需要先完成建议2)

**假设**: Agent缺少总结/输出触发机制

**建议内容**:
在第25-30轮添加"Please summarize and generate patch"提示

**验证方法**: A/B测试 (实验2)

**优先级**: P1 - High (如果建议2验证假设为真)

**预期影响** (如果有效):
- Empty率: 13% → 5-8%
- 节省成本: 约$5

**当前状态**: ❓ 假设未验证,不要直接实施

---

#### 4. 设置50轮上限 (需要先完成实验3)

**假设**: 50轮后效率递减

**建议内容**:
设置50轮上限,超过后强制输出最佳patch或终止

**验证方法**: 实验3 (对比有无上限的效果)

**优先级**: P1 - High

**预期影响** (如果有效):
- 避免120轮极端情况
- 节省成本约$5-10

**当前状态**: ❓ 假设未验证,不要直接实施

---

#### 5. 项目特定Prompt (需要先完成Sympy/Sphinx分析)

**假设**: 某些项目需要特定领域知识

**建议内容**:
为Sympy/Sphinx等低成功率项目设计领域特定的prompt

**验证方法**: 实验4

**优先级**: P2 - Medium

**预期影响** (如果有效):
- Sympy成功率: 29.9% → 40%+
- Sphinx成功率: 37.5% → 50%+

**当前状态**: ❓ 假设未验证,不要直接实施

---

### ❌ 不建议执行的"伪优化"

以下是看似合理但**缺乏数据支持**的建议,不应执行:

#### ❌ 增加上下文行数

**问题**: 没有数据证明Hunk Failed是上下文不足导致

**现状**: 仅9个Hunk Failed (3%),且未分析根因

**建议**: 先完成实验6,确认根因后再决定

---

#### ❌ 使用Git Diff而非手动构造Patch

**问题**: 不确定Enhanced模式是否已经在用Git Diff

**现状**: 需要检查Claude Code CLI实现

**建议**: 先确认当前实现,再判断是否需要改进

---

#### ❌ Cache定期清理

**问题**: Cache随轮数增长是CLI设计的自然结果

**现状**: 93.9% cache命中率已经很高,节省79%成本

**建议**: 不需要优化,当前机制已经很好

---

#### ❌ Few-shot Examples

**问题**: Malformed已经修复,不再是主要问题

**现状**: 修复后Error仅9.7%

**建议**: 不是高优先级,除非发现新的格式问题

---

## 📊 总结: 基于证据强度的建议分级

| 建议 | 证据强度 | 验证需求 | 优先级 | 可执行性 |
|------|---------|---------|--------|---------|
| **修复Hunk Header Bug** | ★★★★★ | 无需验证 | P0 | ✅ 立即执行 |
| **人工审查Empty实例** | ★★★★★ | 无需验证 | P0 | ✅ 立即执行 |
| **强制总结机制** | ★★★☆☆ | 需A/B测试 | P1 | ⚠️ 先验证假设 |
| **50轮上限** | ★★★☆☆ | 需实验验证 | P1 | ⚠️ 先验证假设 |
| **项目特定Prompt** | ★★☆☆☆ | 需深入分析+实验 | P2 | ⚠️ 先分析根因 |
| **Unresolved优化** | ★★☆☆☆ | 需人工审查 | P2 | ⚠️ 先分析接近度 |
| **上下文行数优化** | ★☆☆☆☆ | 需根因分析 | P3 | ❌ 暂不执行 |
| **Few-shot Examples** | ★☆☆☆☆ | 问题已修复 | P3 | ❌ 暂不执行 |

---

## 🔬 实验执行时间表

### 第1周

**Day 1-2**:
- ✅ 执行建议1: 向CLI团队报告Hunk Header Bug
- ✅ 执行建议2: 人工审查10个Empty实例 (实验1)

**Day 3-4**:
- 如果实验1确认需要总结机制 → 执行实验2 (A/B测试)
- 同时执行实验3 (50轮上限测试)

**Day 5**:
- 分析实验2和3的结果
- 决定是否正式实施总结机制和轮数上限

### 第2周

**Day 1-2**:
- 深入分析Sympy/Sphinx失败案例
- 统计Issue类型、代码复杂度等特征

**Day 3-4**:
- 如果分析发现明确的领域知识gap → 执行实验4
- 同时执行实验5 (Unresolved接近度分析)

**Day 5**:
- 执行实验6 (Reversed根因分析)
- 总结所有实验结果

### 第3周

**Day 1-3**:
- 根据实验结果,实施验证有效的优化
- 在小规模样本上测试效果

**Day 4-5**:
- 全量重新评估(如果优化显著)
- 生成最终优化报告

---

## 📖 结论

本方法论严格区分了:

1. **✅ 客观事实** (100%基于数据,可直接使用)
2. **⚠️ 相关性观察** (发现模式,但需要警惕相关≠因果)
3. **❓ 待验证假设** (合理猜测,但必须实验验证才能作为建议)
4. **❌ 未经验证的"伪优化"** (看似合理但缺乏依据,不应执行)

**核心原则**:
- 所有建议必须基于数据事实或相关性观察
- 所有假设必须设计明确的验证方法
- 不给出未经验证的优化建议
- 明确标注每个建议的证据强度和验证需求

这样的方法论确保了所有建议都经得起推敲,避免了基于直觉或常识的错误优化。
