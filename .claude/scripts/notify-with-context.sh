#!/usr/bin/env bash

# Read hook input from stdin
INPUT=$(cat)

# Extract useful information from the hook input
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
MESSAGE=$(echo "$INPUT" | jq -r '.message // empty')
NOTIFICATION_TYPE=$(echo "$INPUT" | jq -r '.notification_type // empty')

# Get additional context
CURRENT_TIME=$(date '+%H:%M:%S')

# Get directory name (shorter than full path)
DIR_NAME=$(basename "$CWD" 2>/dev/null || echo "unknown")

# Get tmux session name if available
TMUX_SESSION=""
if [ -n "$TMUX" ]; then
    TMUX_SESSION=$(tmux display-message -p '#S' 2>/dev/null)
fi

# Build the notification body
BODY="Awaiting your input"

# Add additional context
CONTEXT=""

if [ -n "$TMUX_SESSION" ]; then
    CONTEXT="📺 tmux: $TMUX_SESSION"
fi

if [ -n "$DIR_NAME" ]; then
    if [ -n "$CONTEXT" ]; then
        CONTEXT="$CONTEXT | 📁 $DIR_NAME"
    else
        CONTEXT="📁 $DIR_NAME"
    fi
fi

if [ -n "$CURRENT_TIME" ]; then
    if [ -n "$CONTEXT" ]; then
        CONTEXT="$CONTEXT | 🕐 $CURRENT_TIME"
    else
        CONTEXT="🕐 $CURRENT_TIME"
    fi
fi

# Combine body with context
if [ -n "$CONTEXT" ]; then
    BODY="$BODY
$CONTEXT"
fi

# Send notification
notify-send "Claude Code" "$BODY"

# Optional: Also log to a file for debugging
LOG_DIR="$HOME/.claude/hooks-logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/notification.log"
echo "[$CURRENT_TIME] Session: $SESSION_ID | Type: $NOTIFICATION_TYPE | Dir: $DIR_NAME | Tmux: ${TMUX_SESSION:-N/A} | Msg: $MESSAGE" >> "$LOG_FILE"

exit 0
