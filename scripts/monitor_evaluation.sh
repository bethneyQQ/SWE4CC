#!/bin/bash
# Monitor evaluation progress

LOG_FILE="/home/zqq/SWE4CC/logs/evaluation_restart_20251004_175650.log"
PID=318212

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║         SWE-bench Evaluation Progress Monitor                      ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if process is running
if ps -p $PID > /dev/null 2>&1; then
    echo "✅ Process Status: Running (PID: $PID)"
else
    echo "❌ Process Status: Not running"
    echo ""
    echo "Evaluation may have completed or crashed."
    echo "Check the log file and report directory for results."
    exit 1
fi

echo ""
echo "📊 Current Progress:"
echo "───────────────────────────────────────────────────────────────────"

# Get the last progress line from log
LAST_LINE=$(tail -1 "$LOG_FILE")
echo "  $LAST_LINE"

# Extract statistics if available
if [[ $LAST_LINE =~ ([0-9]+)/([0-9]+).*✓=([0-9]+).*✖=([0-9]+).*error=([0-9]+) ]]; then
    CURRENT="${BASH_REMATCH[1]}"
    TOTAL="${BASH_REMATCH[2]}"
    PASSED="${BASH_REMATCH[3]}"
    FAILED="${BASH_REMATCH[4]}"
    ERRORS="${BASH_REMATCH[5]}"

    PERCENTAGE=$((CURRENT * 100 / TOTAL))
    REMAINING=$((TOTAL - CURRENT))

    echo ""
    echo "  Progress: $CURRENT/$TOTAL ($PERCENTAGE%)"
    echo "  Passed: $PASSED"
    echo "  Failed: $FAILED"
    echo "  Errors: $ERRORS"
    echo "  Remaining: $REMAINING"
fi

echo ""
echo "📁 Files:"
echo "───────────────────────────────────────────────────────────────────"
echo "  Log: $LOG_FILE"
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(ls -lh "$LOG_FILE" | awk '{print $5}')
    echo "       Size: $LOG_SIZE"
fi

echo ""
echo "  Report dir: /home/zqq/SWE4CC/reports/claude-4.5-sonnet-evaluation/"
if [ -d "/home/zqq/SWE4CC/reports/claude-4.5-sonnet-evaluation" ]; then
    echo "       Status: Directory exists"
    FILE_COUNT=$(find /home/zqq/SWE4CC/reports/claude-4.5-sonnet-evaluation -type f 2>/dev/null | wc -l)
    echo "       Files: $FILE_COUNT"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "Commands:"
echo "  Watch progress: watch -n 10 './scripts/monitor_evaluation.sh'"
echo "  View full log: tail -f $LOG_FILE"
echo "  Stop process: kill $PID"
echo "═══════════════════════════════════════════════════════════════════"
