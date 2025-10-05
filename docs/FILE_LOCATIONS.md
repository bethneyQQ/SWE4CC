# 评估文件位置说明

## 📂 输入文件（已存在）

### 1. 原始评估报告
```bash
reports/claude-3.5-sonnet.full_eval.json
```
包含原始评估的统计信息：completed_ids, error_ids, resolved_ids等

### 2. 预测文件（模型生成的patch）
```bash
results/claude-3.5-sonnet__SWE-bench_Lite_oracle__test.jsonl
```
每行一个JSON，包含：
- `instance_id`: 实例ID
- `model_patch`: 生成的patch
- `full_output`: 完整输出

### 3. 原始评估日志
```bash
logs/run_evaluation/full_eval/claude-3.5-sonnet/
├── astropy__astropy-12907/
│   ├── run_instance.log
│   ├── report.json
│   ├── test_output.txt
│   └── patch.diff
├── django__django-10914/
│   └── ...
└── ...（300个实例目录）
```

## 📁 输出文件（重新评估后生成）

### 1. 重新评估日志（默认位置）
```bash
logs/run_evaluation/reevaluation/claude-3.5-sonnet/
├── <instance_id>/
│   ├── run_instance.log      # 评估运行日志
│   ├── report.json            # 评估结果报告
│   ├── test_output.txt        # 测试输出
│   ├── patch.diff             # 应用的patch
│   └── eval.sh                # 评估脚本
└── ...
```

**每个实例目录包含：**
- **run_instance.log**: 完整的评估日志，包括容器创建、patch应用、测试运行等
- **report.json**: 评估结果，包括resolved状态和测试通过情况
- **test_output.txt**: pytest或其他测试框架的输出
- **patch.diff**: 实际应用到代码的patch文件

### 2. 重新评估汇总报告
```bash
reports/claude-3.5-sonnet.reevaluation_<type>.json
```

**报告类型：**
- `reevaluation_malformed.json` - 仅malformed patch错误的重新评估
- `reevaluation_docker.json` - 仅docker rate limit错误的重新评估
- `reevaluation_patch_failed.json` - 仅patch apply failed错误的重新评估
- `reevaluation_all.json` - 所有错误的重新评估

**报告内容：**
```json
{
  "original_error_count": 98,
  "reevaluated_count": 98,
  "completed": 85,
  "resolved": 42,
  "unresolved": 43,
  "still_failed": 13,
  "success_rate": 86.7,
  "resolve_rate": 49.4,
  "resolved_instances": ["id1", "id2", ...],
  "still_failed_instances": ["id3", "id4", ...],
  "error_types": {
    "malformed_patch": 2,
    "patch_apply_failed": 11
  }
}
```

## 🔧 自定义输出位置

如果要自定义输出位置，使用以下参数：

```bash
python3 scripts/reevaluate_failed_instances.py \
    --type malformed \
    --output-dir /path/to/custom/output \
    --predictions /path/to/predictions.jsonl \
    --eval-report /path/to/eval_report.json
```

## 📊 查看结果的方法

### 1. 查看汇总统计
```bash
cat reports/claude-3.5-sonnet.reevaluation_malformed.json | jq '.'
```

### 2. 查看特定实例的评估日志
```bash
# 查看运行日志
cat logs/run_evaluation/reevaluation/claude-3.5-sonnet/astropy__astropy-14995/run_instance.log

# 查看评估报告
cat logs/run_evaluation/reevaluation/claude-3.5-sonnet/astropy__astropy-14995/report.json | jq '.'

# 查看测试输出
cat logs/run_evaluation/reevaluation/claude-3.5-sonnet/astropy__astropy-14995/test_output.txt
```

### 3. 统计成功率
```bash
# 统计重新评估中成功的实例
ls logs/run_evaluation/reevaluation/claude-3.5-sonnet/*/report.json | wc -l

# 查找已解决的实例
for f in logs/run_evaluation/reevaluation/claude-3.5-sonnet/*/report.json; do
    if grep -q '"resolved": true' "$f"; then
        echo "✓ $(dirname $f | xargs basename)"
    fi
done
```

### 4. 查找仍然失败的实例
```bash
# 查找仍有malformed patch错误的实例
grep -l "malformed patch" logs/run_evaluation/reevaluation/claude-3.5-sonnet/*/run_instance.log

# 查找patch apply失败的实例
grep -l "Patch Apply Failed" logs/run_evaluation/reevaluation/claude-3.5-sonnet/*/run_instance.log
```

## 🎯 典型工作流程

### 步骤1: 运行重新评估
```bash
python3 scripts/reevaluate_failed_instances.py --type malformed
```

### 步骤2: 查看汇总报告
```bash
cat reports/claude-3.5-sonnet.reevaluation_malformed.json | jq '{
    total: .reevaluated_count,
    completed: .completed,
    resolved: .resolved,
    success_rate: .success_rate,
    resolve_rate: .resolve_rate
}'
```

### 步骤3: 检查已解决的实例
```bash
cat reports/claude-3.5-sonnet.reevaluation_malformed.json | jq -r '.resolved_instances[]' | head -10
```

### 步骤4: 分析仍然失败的实例
```bash
# 获取失败实例列表
cat reports/claude-3.5-sonnet.reevaluation_malformed.json | jq -r '.still_failed_instances[]' > failed_instances.txt

# 查看第一个失败实例的详细日志
FIRST_FAILED=$(head -1 failed_instances.txt)
echo "检查实例: $FIRST_FAILED"
cat logs/run_evaluation/reevaluation/claude-3.5-sonnet/$FIRST_FAILED/run_instance.log | tail -50
```

## 📝 文件大小参考

典型的文件大小：
- 评估报告JSON: ~25KB
- 预测文件JSONL: ~2-5MB (300个实例)
- 每个实例日志目录: ~50-200KB
- 重新评估汇总报告: ~5-10KB

## 🔍 快速检查命令

```bash
# 检查所有必需文件
echo "=== 检查输入文件 ==="
ls -lh reports/claude-3.5-sonnet.full_eval.json
ls -lh results/claude-3.5-sonnet__SWE-bench_Lite_oracle__test.jsonl
ls -d logs/run_evaluation/full_eval/claude-3.5-sonnet/ | head -1

echo -e "\n=== 检查输出目录 ==="
ls -d logs/run_evaluation/reevaluation/claude-3.5-sonnet/ 2>/dev/null || echo "尚未创建（首次运行时会自动创建）"

echo -e "\n=== 检查重新评估报告 ==="
ls -lh reports/claude-3.5-sonnet.reevaluation_*.json 2>/dev/null || echo "尚未生成（需要先运行重新评估）"
```

## 💡 提示

1. **磁盘空间**: 重新评估300个实例大约需要 **15-30GB** 磁盘空间（包括Docker容器和日志）

2. **备份**: 建议在重新评估前备份原始评估结果
   ```bash
   tar -czf logs/run_evaluation/full_eval_backup.tar.gz logs/run_evaluation/full_eval/
   ```

3. **清理**: 评估完成后可以清理临时文件
   ```bash
   # 清理Docker容器和镜像（小心使用！）
   docker system prune -a --volumes
   ```

4. **并行评估**: 如果要加速，可以分批评估并合并结果
   ```bash
   # 分成多个batch并行运行
   python3 scripts/reevaluate_failed_instances.py --type malformed --instance-ids id1 id2 id3 &
   python3 scripts/reevaluate_failed_instances.py --type malformed --instance-ids id4 id5 id6 &
   ```
