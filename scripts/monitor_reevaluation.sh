#!/bin/bash
# 监控重新评估进度

LOG_FILE="logs/reevaluation_malformed.log"
OUTPUT_DIR="logs/run_evaluation/reevaluation/claude-3.5-sonnet"
REPORT_FILE="reports/claude-3.5-sonnet.reevaluation_malformed.json"

echo "=========================================="
echo "重新评估进度监控"
echo "=========================================="
echo ""

# 检查进程是否在运行
PID=$(pgrep -f "reevaluate_failed_instances")
if [ -n "$PID" ]; then
    echo "✅ 评估进程正在运行 (PID: $PID)"
    ps -p $PID -o pid,stat,%cpu,%mem,etime,cmd --no-headers
else
    echo "⚠️  评估进程未运行"
fi
echo ""

# 显示最新日志
echo "📋 最新日志 (最后10行):"
echo "----------------------------------------"
tail -10 "$LOG_FILE" 2>/dev/null || echo "日志文件不存在"
echo ""

# 统计进度
if [ -d "$OUTPUT_DIR" ]; then
    echo "📊 评估进度统计:"
    echo "----------------------------------------"

    # 统计已完成的实例
    COMPLETED=$(find "$OUTPUT_DIR" -name "report.json" 2>/dev/null | wc -l)
    echo "已完成实例: $COMPLETED / 98"

    # 统计已解决的实例
    RESOLVED=0
    for report in "$OUTPUT_DIR"/*/report.json; do
        if [ -f "$report" ] && grep -q '"resolved": true' "$report" 2>/dev/null; then
            RESOLVED=$((RESOLVED + 1))
        fi
    done
    echo "已解决实例: $RESOLVED / $COMPLETED"

    # 统计仍然失败的
    FAILED=$(grep -l "malformed patch\|Patch Apply Failed" "$OUTPUT_DIR"/*/run_instance.log 2>/dev/null | wc -l)
    echo "仍然失败: $FAILED"

    # 计算百分比
    if [ $COMPLETED -gt 0 ]; then
        PROGRESS=$((COMPLETED * 100 / 98))
        RESOLVE_RATE=$((RESOLVED * 100 / COMPLETED))
        echo ""
        echo "完成进度: ${PROGRESS}%"
        echo "解决率: ${RESOLVE_RATE}%"
    fi
else
    echo "⚠️  输出目录不存在，评估尚未开始或刚启动"
fi

echo ""
echo "=========================================="
echo "监控命令:"
echo "----------------------------------------"
echo "实时日志:  tail -f $LOG_FILE"
echo "进度统计:  watch -n 10 $0"
echo "查看报告:  cat $REPORT_FILE | jq '.'"
echo ""
echo "最近完成的实例:"
ls -lt "$OUTPUT_DIR"/*/report.json 2>/dev/null | head -5 | awk '{print $9}' | xargs -I {} dirname {} | xargs basename 2>/dev/null
echo "=========================================="
