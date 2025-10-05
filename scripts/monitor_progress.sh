#!/bin/bash
# Monitor SWE-bench Lite full run progress

LOG_FILE="logs/swebench_lite_full_run.log"
RESULT_FILE="results/claude-sonnet-4-5__SWE-bench_Lite_oracle__test.jsonl"

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║         SWE-bench Lite Full Run Progress Monitor                  ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if process is running
if pgrep -f "run_api.py.*claude-sonnet-4-5" > /dev/null; then
    PID=$(pgrep -f "run_api.py.*claude-sonnet-4-5")
    echo "✅ Process Status: Running (PID: $PID)"
else
    echo "❌ Process Status: Not running"
    exit 1
fi

echo ""
echo "📊 Progress Statistics:"
echo "───────────────────────────────────────────────────────────────────"

# Count completed instances
if [ -f "$RESULT_FILE" ]; then
    COMPLETED=$(wc -l < "$RESULT_FILE")
    echo "  Completed: $COMPLETED / 300 instances"
    PERCENTAGE=$((COMPLETED * 100 / 300))
    echo "  Progress: $PERCENTAGE%"

    # Calculate estimated time
    if [ $COMPLETED -gt 0 ]; then
        # Get start time from log
        START_TIME=$(head -1 "$LOG_FILE" | cut -d',' -f1)
        CURRENT_TIME=$(date +"%Y-%m-%d %H:%M:%S")

        # Calculate average time per instance
        ELAPSED_SECONDS=$(( $(date -d "$CURRENT_TIME" +%s) - $(date -d "$START_TIME" +%s) ))
        AVG_TIME=$((ELAPSED_SECONDS / COMPLETED))

        REMAINING=$((300 - COMPLETED))
        ETA_SECONDS=$((AVG_TIME * REMAINING))
        ETA_HOURS=$((ETA_SECONDS / 3600))
        ETA_MINUTES=$(( (ETA_SECONDS % 3600) / 60))

        echo "  Average: ${AVG_TIME}s per instance"
        echo "  Elapsed: $((ELAPSED_SECONDS / 60)) minutes"
        echo "  ETA: ${ETA_HOURS}h ${ETA_MINUTES}m remaining"
    fi
else
    echo "  Completed: 0 / 300 instances"
    echo "  Progress: 0%"
fi

echo ""
echo "📁 Files:"
echo "───────────────────────────────────────────────────────────────────"
echo "  Log: $LOG_FILE"
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(ls -lh "$LOG_FILE" | awk '{print $5}')
    echo "       Size: $LOG_SIZE"
fi

echo "  Results: $RESULT_FILE"
if [ -f "$RESULT_FILE" ]; then
    RESULT_SIZE=$(ls -lh "$RESULT_FILE" | awk '{print $5}')
    echo "       Size: $RESULT_SIZE"
fi

echo ""
echo "🔍 Recent Activity (last 10 lines):"
echo "───────────────────────────────────────────────────────────────────"
tail -10 "$LOG_FILE" | sed 's/^/  /'

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "Commands:"
echo "  Watch progress: watch -n 10 './scripts/monitor_progress.sh'"
echo "  View full log: tail -f $LOG_FILE"
echo "  Stop process: kill $PID"
echo "═══════════════════════════════════════════════════════════════════"
