# 重新评估指南

本指南介绍如何在修复patch格式问题后重新评估失败的实例。

## 已完成的修复

### 1. Patch格式修复

已在 `swebench/inference/make_datasets/utils.py` 中添加 `fix_patch_context_lines()` 函数，自动修复patch文件中缺失的上下文行前导空格。

**修复内容:**
- 自动检测patch中的上下文行
- 为缺少前导空格的行添加空格
- 保持已正确格式化的patch不变

**测试:**
```bash
python3 test_patch_fix.py
```

### 2. Docker认证配置（可选）

如果要重新评估Docker rate limit错误，需要配置Docker Hub认证：

```bash
docker login
# 输入你的Docker Hub用户名和密码
```

或者设置环境变量：
```bash
export DOCKER_USERNAME="your_username"
export DOCKER_PASSWORD="your_password"
```

---

## 重新评估方法

### 方法1: 使用Python脚本（推荐）

```bash
# 查看错误实例统计（不实际运行）
python3 scripts/reevaluate_failed_instances.py --dry-run

# 仅重新评估 Malformed Patch 错误 (98个实例)
python3 scripts/reevaluate_failed_instances.py --type malformed

# 仅重新评估 Docker Rate Limit 错误 (37个实例，需要Docker认证)
python3 scripts/reevaluate_failed_instances.py --type docker

# 仅重新评估 Patch Apply Failed 错误 (23个实例)
python3 scripts/reevaluate_failed_instances.py --type patch_failed

# 重新评估所有错误实例 (158个)
python3 scripts/reevaluate_failed_instances.py --type all
```

**参数说明:**
- `--model`: 模型名称（默认: claude-3.5-sonnet）
- `--type`: 错误类型（malformed/docker/patch_failed/all）
- `--timeout`: 超时时间秒数（默认: 900）
- `--dry-run`: 仅显示将要评估的实例，不实际运行
- `--eval-report`: 原始评估报告路径（可选）
- `--predictions`: 预测文件路径（可选）
- `--output-dir`: 输出目录（可选）

### 方法2: 使用Bash脚本

```bash
# 运行交互式脚本
./scripts/reevaluate_errors.sh
```

脚本会提示你选择要重新评估的错误类型，并引导你完成整个过程。

### 方法3: 手动运行评估

如果要手动控制评估过程：

```bash
# 1. 准备实例ID列表（以 Malformed Patch 为例）
python3 << 'EOF'
import json
with open('reports/claude-3.5-sonnet.full_eval.json') as f:
    data = json.load(f)
error_ids = data['error_ids']

# 过滤出 malformed patch 错误
import os
malformed_ids = []
log_dir = 'logs/run_evaluation/full_eval/claude-3.5-sonnet'
for error_id in error_ids:
    log_file = os.path.join(log_dir, error_id, 'run_instance.log')
    if os.path.exists(log_file):
        with open(log_file) as lf:
            if 'malformed patch' in lf.read():
                malformed_ids.append(error_id)

with open('malformed_instances.txt', 'w') as f:
    for iid in malformed_ids:
        f.write(iid + '\n')
print(f"找到 {len(malformed_ids)} 个 malformed patch 错误")
EOF

# 2. 运行评估
python3 -m swebench.harness.run_evaluation \
    --predictions_path predictions/claude-3.5-sonnet.full_eval.jsonl \
    --swe_bench_tasks princeton-nlp/SWE-bench_Lite \
    --log_dir logs/run_evaluation/reevaluation/claude-3.5-sonnet \
    --testbed /tmp/testbed \
    --skip_existing \
    --timeout 900 \
    --verbose \
    --instance_ids $(cat malformed_instances.txt | tr '\n' ' ')
```

---

## 预期结果

### Malformed Patch错误 (98个实例)

**修复前:** 所有实例因patch格式错误失败

**修复后预期:**
- ✅ **80-90个实例 (82-92%)** 应该能成功完成评估
- 其中约40-50%可能解决问题
- 部分实例可能因为其他原因（代码逻辑错误等）未解决

### Docker Rate Limit错误 (37个实例)

**配置Docker认证后:**
- ✅ **35-37个实例 (95-100%)** 应该能成功拉取镜像
- 成功率取决于网络和Docker Hub状态

### Patch Apply Failed错误 (23个实例)

这些错误较难修复，因为是patch内容本身的问题：
- 可能需要Claude Code重新生成patch
- 建议先分析具体失败原因再决定如何处理

---

## 查看结果

### 评估日志

```bash
# 查看特定实例的日志
cat logs/run_evaluation/reevaluation/claude-3.5-sonnet/<instance_id>/run_instance.log

# 查看评估报告
cat logs/run_evaluation/reevaluation/claude-3.5-sonnet/<instance_id>/report.json

# 查看测试输出
cat logs/run_evaluation/reevaluation/claude-3.5-sonnet/<instance_id>/test_output.txt
```

### 重新评估报告

Python脚本会自动生成报告：
```bash
cat reports/claude-3.5-sonnet.reevaluation_malformed.json
```

报告包含:
- 重新评估的实例数
- 成功完成的数量
- 解决的实例列表
- 仍然失败的实例和错误类型
- 成功率改进统计

---

## 合并结果

重新评估成功后，你可以合并结果生成完整的评估报告：

```python
import json
from pathlib import Path

# 读取原始评估结果
with open('reports/claude-3.5-sonnet.full_eval.json') as f:
    original = json.load(f)

# 读取重新评估结果
reevaluation_dir = Path('logs/run_evaluation/reevaluation/claude-3.5-sonnet')

# 更新completed_ids, resolved_ids等
# ... (根据需要实现合并逻辑)
```

---

## 故障排查

### 问题1: 仍然出现 Malformed Patch 错误

**原因:** patch格式修复没有生效

**解决:**
1. 确认修改已保存到 `swebench/inference/make_datasets/utils.py`
2. 检查是否使用了正确的predictions文件
3. 运行测试脚本验证: `python3 test_patch_fix.py`

### 问题2: Docker Rate Limit 仍然失败

**原因:** Docker认证未配置或失败

**解决:**
1. 运行 `docker login` 并输入凭据
2. 检查: `docker pull hello-world`
3. 确认 Docker Hub 账户没有超过速率限制

### 问题3: 评估超时

**原因:** 某些实例需要更长时间

**解决:**
增加超时时间:
```bash
python3 scripts/reevaluate_failed_instances.py --type malformed --timeout 1800
```

### 问题4: Out of Memory

**原因:** 并发容器过多

**解决:**
减少并发数或增加系统内存:
```bash
# 设置并发数（如果评估脚本支持）
export SWE_BENCH_MAX_WORKERS=2
```

---

## 最佳实践

1. **分批评估**: 先评估少数实例验证修复有效，再评估全部

   ```bash
   # 先测试5个实例
   python3 -m swebench.harness.run_evaluation \
       --predictions_path predictions/claude-3.5-sonnet.full_eval.jsonl \
       --instance_ids astropy__astropy-14995 django__django-11001 \
       ... (共5个)
   ```

2. **保留原始日志**: 使用不同的输出目录避免覆盖

   ```bash
   --output-dir logs/run_evaluation/reevaluation/claude-3.5-sonnet
   ```

3. **监控进度**: 使用 `--verbose` 标志查看详细输出

4. **检查磁盘空间**: 评估会生成大量日志和临时文件

   ```bash
   df -h /tmp
   ```

---

## 总结

修复patch格式问题后，预期能够将成功率从 **47.3%** 提升至 **75-80%**。

**建议评估顺序:**
1. 先评估 Malformed Patch 错误（98个）
2. 配置Docker认证后评估 Docker Rate Limit 错误（37个）
3. 最后分析 Patch Apply Failed 错误（23个）

**预期最终结果:**
- 总实例数: 300
- 成功完成: ~240 (80%)
- 实际解决: ~90-110 (30-37%)

这将显著改善Claude-3.5-Sonnet在SWE-bench上的表现！
