#!/usr/bin/env bash
# Context window monitoring hook - notifies when context reaches 80%

# Threshold percentage (can be adjusted)
THRESHOLD_PERCENTAGE=80
NOTIFICATION_STATE_FILE="$HOME/.claude/context-alert-state"
ALERT_COOLDOWN_MINUTES=5

# Read hook input
INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')

# Exit if no transcript path
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

# Calculate context usage from transcript
# This is a simplified approach - counting lines in the JSONL file
# Each line represents a turn in the conversation
TRANSCRIPT_LINES=$(wc -l < "$TRANSCRIPT_PATH" 2>/dev/null || echo "0")

# Estimate tokens (rough approximation: ~4 characters per token average)
# This is not exact but gives a reasonable estimate for notification purposes
FILE_SIZE=$(wc -c < "$TRANSCRIPT_PATH" 2>/dev/null || echo "0")
ESTIMATED_TOKENS=$((FILE_SIZE / 4))

# Assume 200k context window for Claude Code (adjust if using enterprise)
MAX_CONTEXT=200000

# Calculate percentage
PERCENTAGE=$((ESTIMATED_TOKENS * 100 / MAX_CONTEXT))

# Check cooldown to avoid spamming notifications
LAST_ALERT_TIME=0
if [ -f "$NOTIFICATION_STATE_FILE" ]; then
    LAST_ALERT_TIME=$(cat "$NOTIFICATION_STATE_FILE" 2>/dev/null || echo "0")
fi

CURRENT_TIME=$(date +%s)
COOLDOWN_SECONDS=$((ALERT_COOLDOWN_MINUTES * 60))

# Only notify if threshold reached and cooldown has passed
if [ $PERCENTAGE -ge $THRESHOLD_PERCENTAGE ]; then
    if [ $((CURRENT_TIME - LAST_ALERT_TIME)) -ge $COOLDOWN_SECONDS ]; then
        # Update last alert time
        echo "$CURRENT_TIME" > "$NOTIFICATION_STATE_FILE"
        
        # Send notification
        CURRENT_DIR=$(echo "$INPUT" | jq -r '.cwd // empty' | xargs basename 2>/dev/null || echo "unknown")
        URGENCY="normal"
        ICON="dialog-warning"
        
        # Increase urgency for very high context usage
        if [ $PERCENTAGE -ge 90 ]; then
            URGENCY="critical"
            ICON="dialog-error"
        elif [ $PERCENTAGE -ge 85 ]; then
            URGENCY="high"
            ICON="dialog-warning"
        fi
        
        notify-send -u "$URGENCY" -i "$ICON" \
            "📊 Context Window at ${PERCENTAGE}%" \
            "Estimated ${ESTIMATED_TOKENS}/${MAX_CONTEXT} tokens used in: ${CURRENT_DIR}"
        
        # Log to alert
        LOG_DIR="$HOME/.claude/hooks-logs"
        mkdir -p "$LOG_DIR"
        SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
        LOG_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        LOG_MESSAGE="[${LOG_TIMESTAMP}] Context at ${PERCENTAGE}% (${ESTIMATED_TOKENS} tokens) - Session: ${SESSION_ID}"
        echo "$LOG_MESSAGE" >> "$LOG_DIR/context-monitor.log"
    fi
fi

exit 0
