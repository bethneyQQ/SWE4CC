#!/bin/bash
# 运行smoke test (后台)

cd /home/zqq/SWE4CC

LOG_FILE="logs/retry_smoke_test_$(date +%Y%m%d_%H%M%S).log"

echo "启动Smoke Test..."
echo "日志文件: $LOG_FILE"

nohup python3 scripts/retry_failed_instances.py --smoke-test > "$LOG_FILE" 2>&1 &
PID=$!

echo "进程ID: $PID"
echo ""
echo "监控命令:"
echo "  tail -f $LOG_FILE"
echo "  ps aux | grep $PID"
echo ""
echo "等待5秒后显示初始输出..."
sleep 5
tail -20 "$LOG_FILE"
