#!/usr/bin/env bash

# Hook for SessionStart - notify when Claude Code session begins

# Read hook input from stdin
INPUT=$(cat)

# Extract information
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
SOURCE=$(echo "$INPUT" | jq -r '.source // empty')
PERMISSION_MODE=$(echo "$INPUT" | jq -r '.permission_mode // empty')

# Get context
CURRENT_TIME=$(date '+%H:%M:%S')
DIR_NAME=$(basename "$CWD" 2>/dev/null || echo "unknown")

# Get tmux session
TMUX_SESSION=""
if [ -n "$TMUX" ]; then
    TMUX_SESSION=$(tmux display-message -p '#S' 2>/dev/null)
fi

# Build message
TITLE="🚀 Claude Code Started"
BODY="New session started"
CONTEXT=""

# Add source info
case "$SOURCE" in
    startup)
        BODY="Session started"
        ;;
    resume)
        BODY="Session resumed"
        ;;
    clear)
        BODY="Session cleared"
        ;;
    compact)
        BODY="Post-compact session"
        ;;
    *)
        BODY="Session: $SOURCE"
        ;;
esac

# Add context
if [ -n "$TMUX_SESSION" ]; then
    CONTEXT="📺 tmux: $TMUX_SESSION"
fi

if [ -n "$DIR_NAME" ] && [ "$DIR_NAME" != "unknown" ]; then
    if [ -n "$CONTEXT" ]; then
        CONTEXT="$CONTEXT | 📁 $DIR_NAME"
    else
        CONTEXT="📁 $DIR_NAME"
    fi
fi

if [ -n "$CONTEXT" ]; then
    CONTEXT="$CONTEXT | 🕐 $CURRENT_TIME"
else
    CONTEXT="🕐 $CURRENT_TIME"
fi

# Combine
if [ -n "$CONTEXT" ]; then
    BODY="$BODY
$CONTEXT"
fi

notify-send -u low "$TITLE" "$BODY"

# Log
LOG_DIR="$HOME/.claude/hooks-logs"
mkdir -p "$LOG_DIR"
echo "[$CURRENT_TIME] SessionStart | Source: $SOURCE | Mode: $PERMISSION_MODE | Dir: $DIR_NAME | Tmux: ${TMUX_SESSION:-N/A}" >> "$LOG_DIR/session.log"

exit 0
