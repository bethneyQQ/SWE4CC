#!/bin/bash
# 重新评估失败的实例
# 使用方法: ./scripts/reevaluate_errors.sh

set -e

echo "========================================="
echo "重新评估 Claude-3.5-Sonnet 错误实例"
echo "========================================="

# 配置
MODEL_NAME="claude-3.5-sonnet"
PREDICTIONS_FILE="predictions/${MODEL_NAME}.full_eval.jsonl"
EVAL_OUTPUT_DIR="logs/run_evaluation/reevaluation_fixed/${MODEL_NAME}"
REPORT_FILE="reports/${MODEL_NAME}.reevaluation.json"

# 检查predictions文件是否存在
if [ ! -f "$PREDICTIONS_FILE" ]; then
    echo "错误: 预测文件不存在: $PREDICTIONS_FILE"
    exit 1
fi

# 读取错误实例ID
echo "正在从评估结果中提取错误实例ID..."
python3 << 'EOF'
import json

# 从evaluation report读取错误实例
with open('reports/claude-3.5-sonnet.full_eval.json', 'r') as f:
    eval_data = json.load(f)

error_ids = eval_data['error_ids']
print(f"找到 {len(error_ids)} 个错误实例")

# 按错误类型分组
malformed_ids = []
docker_ids = []
patch_failed_ids = []

import os
log_dir = 'logs/run_evaluation/full_eval/claude-3.5-sonnet'

for error_id in error_ids:
    log_file = os.path.join(log_dir, error_id, 'run_instance.log')
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            content = f.read()
            if 'malformed patch' in content:
                malformed_ids.append(error_id)
            elif 'Too Many Requests' in content or 'toomanyrequests' in content:
                docker_ids.append(error_id)
            else:
                patch_failed_ids.append(error_id)

# 保存到文件以便shell脚本使用
with open('.error_instances.json', 'w') as f:
    json.dump({
        'all': error_ids,
        'malformed_patch': malformed_ids,
        'docker_rate_limit': docker_ids,
        'patch_apply_failed': patch_failed_ids
    }, f, indent=2)

print(f"- Malformed patch: {len(malformed_ids)}")
print(f"- Docker rate limit: {len(docker_ids)}")
print(f"- Patch apply failed: {len(patch_failed_ids)}")
print("\n错误实例ID已保存到 .error_instances.json")
EOF

# 询问用户要重新评估哪些实例
echo ""
echo "请选择要重新评估的实例类型:"
echo "1) 仅 Malformed Patch 错误 (98个, 已修复)"
echo "2) 仅 Docker Rate Limit 错误 (37个, 需要Docker认证)"
echo "3) 所有错误实例 (158个)"
echo "4) 自定义实例列表"
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo "重新评估 Malformed Patch 错误实例..."
        INSTANCE_TYPE="malformed_patch"
        ;;
    2)
        echo "重新评估 Docker Rate Limit 错误实例..."
        INSTANCE_TYPE="docker_rate_limit"
        echo "警告: 请确保已配置 Docker Hub 认证!"
        read -p "是否继续? (y/n): " confirm
        if [ "$confirm" != "y" ]; then
            echo "取消操作"
            exit 0
        fi
        ;;
    3)
        echo "重新评估所有错误实例..."
        INSTANCE_TYPE="all"
        ;;
    4)
        echo "请输入实例ID列表文件路径:"
        read -p "文件路径: " custom_file
        if [ ! -f "$custom_file" ]; then
            echo "错误: 文件不存在"
            exit 1
        fi
        INSTANCE_TYPE="custom"
        CUSTOM_FILE="$custom_file"
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac

# 创建临时实例列表文件
if [ "$INSTANCE_TYPE" = "custom" ]; then
    cp "$CUSTOM_FILE" .reevaluation_instances.txt
else
    python3 << EOF
import json
with open('.error_instances.json', 'r') as f:
    error_data = json.load(f)

instance_ids = error_data['$INSTANCE_TYPE']
with open('.reevaluation_instances.txt', 'w') as f:
    for instance_id in instance_ids:
        f.write(instance_id + '\n')

print(f"将重新评估 {len(instance_ids)} 个实例")
EOF
fi

# 运行评估
echo ""
echo "开始重新评估..."
echo "输出目录: $EVAL_OUTPUT_DIR"
echo ""

python3 -m swebench.harness.run_evaluation \
    --predictions_path "$PREDICTIONS_FILE" \
    --swe_bench_tasks "princeton-nlp/SWE-bench_Lite" \
    --log_dir "$EVAL_OUTPUT_DIR" \
    --testbed "/tmp/testbed" \
    --skip_existing \
    --timeout 900 \
    --verbose \
    --instance_ids $(cat .reevaluation_instances.txt | tr '\n' ' ')

# 生成重新评估报告
echo ""
echo "生成重新评估报告..."
python3 << 'EOF'
import json
import os
from pathlib import Path

eval_dir = Path('logs/run_evaluation/reevaluation_fixed/claude-3.5-sonnet')
if not eval_dir.exists():
    print("错误: 评估目录不存在")
    exit(1)

# 统计结果
results = {
    'total_reevaluated': 0,
    'completed': 0,
    'resolved': 0,
    'still_failed': 0,
    'error_types': {}
}

# 读取每个实例的结果
for instance_dir in eval_dir.iterdir():
    if not instance_dir.is_dir():
        continue

    instance_id = instance_dir.name
    results['total_reevaluated'] += 1

    # 检查report.json
    report_file = instance_dir / 'report.json'
    if report_file.exists():
        with open(report_file) as f:
            report = json.load(f)
            if instance_id in report:
                instance_report = report[instance_id]
                if instance_report.get('resolved', False):
                    results['resolved'] += 1
                results['completed'] += 1
    else:
        # 检查日志文件看是否还有错误
        log_file = instance_dir / 'run_instance.log'
        if log_file.exists():
            with open(log_file) as f:
                content = f.read()
                if 'malformed patch' in content:
                    results['still_failed'] += 1
                    results['error_types']['malformed_patch'] = \
                        results['error_types'].get('malformed_patch', 0) + 1
                elif 'Patch Apply Failed' in content:
                    results['still_failed'] += 1
                    results['error_types']['patch_apply_failed'] = \
                        results['error_types'].get('patch_apply_failed', 0) + 1

# 保存报告
with open('reports/claude-3.5-sonnet.reevaluation.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n重新评估完成!")
print(f"总计重新评估: {results['total_reevaluated']} 个实例")
print(f"成功完成: {results['completed']} 个")
print(f"已解决: {results['resolved']} 个")
print(f"仍然失败: {results['still_failed']} 个")
if results['error_types']:
    print("\n仍然失败的错误类型:")
    for error_type, count in results['error_types'].items():
        print(f"  - {error_type}: {count}")

print(f"\n详细报告已保存到: reports/claude-3.5-sonnet.reevaluation.json")
EOF

# 清理临时文件
rm -f .error_instances.json .reevaluation_instances.txt

echo ""
echo "重新评估完成!"
