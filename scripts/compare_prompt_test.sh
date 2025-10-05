#!/bin/bash
# 对比新旧Prompt在3个格式错误实例上的效果
#
# 测试实例:
# 1. astropy__astropy-14995 - 格式错误
# 2. django__django-11001 - 格式错误
# 3. django__django-11019 - 格式错误

set -e  # 遇到错误立即退出

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Prompt对比测试 - 3个格式错误实例${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 测试实例ID
TEST_INSTANCES="astropy__astropy-14995,django__django-11001,django__django-11019"

echo -e "${YELLOW}测试实例:${NC}"
echo "  1. astropy__astropy-14995"
echo "  2. django__django-11001"
echo "  3. django__django-11019"
echo ""

# 创建测试目录
TEST_DIR="test_prompt_comparison"
mkdir -p "$TEST_DIR"

echo -e "${BLUE}步骤 1: 准备旧Prompt的结果${NC}"
echo "从现有predictions中提取这3个实例的结果..."

python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path

# 读取原始predictions
with open('results/claude-3.5-sonnet__SWE-bench_Lite_oracle__test.jsonl') as f:
    all_preds = [json.loads(line) for line in f]

# 提取测试实例
test_ids = ['astropy__astropy-14995', 'django__django-11001', 'django__django-11019']
old_preds = [p for p in all_preds if p['instance_id'] in test_ids]

# 保存
output_dir = Path('test_prompt_comparison')
output_dir.mkdir(exist_ok=True)

with open(output_dir / 'old_prompt_predictions.jsonl', 'w') as f:
    for pred in old_preds:
        f.write(json.dumps(pred) + '\n')

print(f"✅ 已保存 {len(old_preds)} 个旧Prompt的predictions")

# 创建对比报告的表头
with open(output_dir / 'comparison_summary.md', 'w') as f:
    f.write("# Prompt对比测试结果\n\n")
    f.write("## 测试实例\n\n")
    for i, inst_id in enumerate(test_ids, 1):
        f.write(f"{i}. `{inst_id}`\n")
    f.write("\n---\n\n")
PYTHON_SCRIPT

echo -e "${GREEN}✓ 旧Prompt结果已提取${NC}\n"

echo -e "${BLUE}步骤 2: 用新Prompt生成predictions${NC}"
echo "调用Claude Code为3个实例生成patches (使用新Prompt)..."
echo ""

# 使用专门的脚本，只处理这3个实例
python3 scripts/run_single_instances.py \
  --instance_ids "$TEST_INSTANCES" \
  --model claude-3.5-sonnet \
  --output_dir "$TEST_DIR/new_prompt_results"

echo -e "${GREEN}✓ 新Prompt predictions已生成${NC}\n"

echo -e "${BLUE}步骤 3: 评估新Prompt的结果${NC}"

python3 swebench/harness/run_evaluation.py \
  --predictions_path "$TEST_DIR/new_prompt_results"/*.jsonl \
  --run_id new_prompt_test \
  --max_workers 4

echo -e "${GREEN}✓ 新Prompt评估完成${NC}\n"

echo -e "${BLUE}步骤 4: 生成对比分析${NC}"

python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path
from datetime import datetime

test_dir = Path('test_prompt_comparison')

# 加载旧结果
with open('reports/claude-3.5-sonnet.full_eval.json') as f:
    old_eval = json.load(f)

# 加载新结果
new_eval_path = Path('reports/new_prompt_test.json')
if new_eval_path.exists():
    with open(new_eval_path) as f:
        new_eval = json.load(f)
else:
    print("警告: 新评估结果未找到")
    new_eval = {}

test_ids = ['astropy__astropy-14995', 'django__django-11001', 'django__django-11019']

# 生成详细对比报告
report = f"""# Prompt对比测试结果

**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试概况

- **测试实例数**: 3
- **实例类型**: 格式错误 (malformed patch)
- **对比维度**: 旧Prompt vs 新Prompt

---

## 测试实例详情

"""

# 对每个实例进行对比
for idx, inst_id in enumerate(test_ids, 1):
    report += f"### {idx}. {inst_id}\n\n"

    # 旧结果状态
    old_status = "❌ ERROR"
    if inst_id in old_eval.get('resolved_ids', []):
        old_status = "✅ RESOLVED"
    elif inst_id in old_eval.get('unresolved_ids', []):
        old_status = "⚠️ UNRESOLVED"

    # 新结果状态
    new_status = "🔄 TESTING"
    if new_eval:
        if inst_id in new_eval.get('resolved_ids', []):
            new_status = "✅ RESOLVED"
        elif inst_id in new_eval.get('unresolved_ids', []):
            new_status = "⚠️ UNRESOLVED"
        elif inst_id in new_eval.get('error_ids', []):
            new_status = "❌ ERROR"

    report += f"| Prompt版本 | 状态 |\n"
    report += f"|-----------|------|\n"
    report += f"| 旧Prompt | {old_status} |\n"
    report += f"| 新Prompt | {new_status} |\n\n"

    # 检查旧的错误日志
    old_log = Path(f'logs/run_evaluation/full_eval/claude-3.5-sonnet/{inst_id}/run_instance.log')
    if old_log.exists():
        log_content = old_log.read_text(errors='ignore')
        if 'malformed patch' in log_content:
            import re
            match = re.search(r'malformed patch at line (\d+): (.+)', log_content)
            if match:
                report += f"**旧Prompt错误**: Line {match.group(1)}: `{match.group(2)[:60]}`\n\n"

    # 检查新的错误日志
    new_log = Path(f'logs/run_evaluation/new_prompt_test/{inst_id}/run_instance.log')
    if new_log.exists():
        log_content = new_log.read_text(errors='ignore')
        if 'malformed patch' in log_content:
            import re
            match = re.search(r'malformed patch at line (\d+): (.+)', log_content)
            if match:
                report += f"**新Prompt错误**: Line {match.group(1)}: `{match.group(2)[:60]}`\n\n"
        elif 'resolved: True' in log_content:
            report += f"**新Prompt**: ✅ Patch格式正确，成功解决问题！\n\n"
        elif 'resolved: False' in log_content:
            report += f"**新Prompt**: ⚠️ Patch格式正确但测试未通过\n\n"

    report += "---\n\n"

# 汇总统计
report += """## 汇总对比

| 指标 | 旧Prompt | 新Prompt | 变化 |
|------|---------|----------|------|
"""

old_errors = sum(1 for id in test_ids if id in old_eval.get('error_ids', []))
old_resolved = sum(1 for id in test_ids if id in old_eval.get('resolved_ids', []))
old_unresolved = sum(1 for id in test_ids if id in old_eval.get('unresolved_ids', []))

new_errors = 0
new_resolved = 0
new_unresolved = 0

if new_eval:
    new_errors = sum(1 for id in test_ids if id in new_eval.get('error_ids', []))
    new_resolved = sum(1 for id in test_ids if id in new_eval.get('resolved_ids', []))
    new_unresolved = sum(1 for id in test_ids if id in new_eval.get('unresolved_ids', []))

report += f"| 格式错误 | {old_errors}/3 | {new_errors}/3 | {'-' + str(old_errors - new_errors) if old_errors > new_errors else '+' + str(new_errors - old_errors)} |\n"
report += f"| 成功解决 | {old_resolved}/3 | {new_resolved}/3 | {'+' + str(new_resolved - old_resolved) if new_resolved > old_resolved else str(new_resolved - old_resolved)} |\n"
report += f"| 测试失败 | {old_unresolved}/3 | {new_unresolved}/3 | {'+' + str(new_unresolved - old_unresolved) if new_unresolved > old_unresolved else str(new_unresolved - old_unresolved)} |\n"

report += "\n---\n\n"

# 结论
if new_eval:
    improvement = (new_resolved - old_resolved) + ((old_errors - new_errors) * 0.5)
    if improvement > 0:
        report += f"## ✅ 结论\n\n新Prompt表现**更好**，改善了 {improvement:.1f} 个实例\n\n"
    elif improvement < 0:
        report += f"## ⚠️ 结论\n\n新Prompt表现**更差**，退化了 {-improvement:.1f} 个实例\n\n"
    else:
        report += f"## 📊 结论\n\n新旧Prompt表现**相当**\n\n"

    if new_errors < old_errors:
        report += f"格式错误显著减少: {old_errors} → {new_errors}\n\n"

report += """## 下一步建议

"""

if new_eval and new_errors < old_errors:
    report += "- ✅ 新Prompt在格式正确性上有改善，建议扩大测试范围\n"
    report += "- 建议测试更多实例 (20-50个) 来确认效果\n"
else:
    report += "- 需要进一步分析新Prompt为何没有改善格式问题\n"
    report += "- 检查patch提取逻辑是否正确\n"

# 保存报告
with open(test_dir / 'comparison_report.md', 'w') as f:
    f.write(report)

print("✅ 对比报告已生成")
print("")
print("=" * 50)
print(report)
print("=" * 50)

PYTHON_SCRIPT

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   测试完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📊 查看详细报告:"
echo "   cat test_prompt_comparison/comparison_report.md"
echo ""
echo "📁 相关文件:"
echo "   - 旧Prompt结果: test_prompt_comparison/old_prompt_predictions.jsonl"
echo "   - 新Prompt结果: test_prompt_comparison/new_prompt_results/*.jsonl"
echo "   - 评估日志: logs/run_evaluation/new_prompt_test/"
echo ""
