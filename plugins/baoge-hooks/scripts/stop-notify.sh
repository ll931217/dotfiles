#!/usr/bin/env bash

# Hook for Stop - notify when Claude Code finishes a task

# Read hook input from stdin
INPUT=$(cat)

# Extract information
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
PERMISSION_MODE=$(echo "$INPUT" | jq -r '.permission_mode // empty')

# Get context
CURRENT_TIME=$(date '+%H:%M:%S')
CURRENT_DIR=$(pwd 2>/dev/null)
DIR_NAME=$(basename "$CURRENT_DIR" 2>/dev/null || echo "unknown")

# Get tmux session
TMUX_SESSION=""
if [ -n "$TMUX" ]; then
    TMUX_SESSION=$(tmux display-message -p '#S' 2>/dev/null)
fi

# Get git branch if available
GIT_BRANCH=""
if [ -d "$CURRENT_DIR/.git" ] 2>/dev/null; then
    GIT_BRANCH=$(git -C "$CURRENT_DIR" branch --show-current 2>/dev/null || echo "")
fi

# Extract last assistant message from transcript if available
LAST_MESSAGE=""
if [ -f "$TRANSCRIPT_PATH" ] && [ -n "$TRANSCRIPT_PATH" ]; then
    # Try to extract the last assistant message (limit to 100 chars)
    LAST_MESSAGE=$(tail -20 "$TRANSCRIPT_PATH" 2>/dev/null | \
        jq -r 'select(.message.role == "assistant") | .message.content[0].text' 2>/dev/null | \
        tail -1 | \
        tr '\n' ' ' | \
        cut -c1-100)
fi

# Build message
TITLE="✅ Claude Code - Task Complete"
BODY="Task completed"

# Add last message if available
if [ -n "$LAST_MESSAGE" ]; then
    BODY="$LAST_MESSAGE"
fi

# Add context
CONTEXT=""

if [ -n "$TMUX_SESSION" ]; then
    CONTEXT="📺 tmux: $TMUX_SESSION"
fi

if [ -n "$GIT_BRANCH" ]; then
    if [ -n "$CONTEXT" ]; then
        CONTEXT="$CONTEXT | 🌿 $GIT_BRANCH"
    else
        CONTEXT="🌿 $GIT_BRANCH"
    fi
fi

if [ -n "$DIR_NAME" ] && [ "$DIR_NAME" != "unknown" ]; then
    if [ -n "$CONTEXT" ]; then
        CONTEXT="$CONTEXT | 📁 $DIR_NAME"
    else
        CONTEXT="📁 $DIR_NAME"
    fi
fi

if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
    if [ -n "$CONTEXT" ]; then
        CONTEXT="$CONTEXT | ♻️ Continuing"
    else
        CONTEXT="♻️ Continuing"
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

notify-send -u normal "$TITLE" "$BODY"

# Log
LOG_DIR="$HOME/.claude/hooks-logs"
mkdir -p "$LOG_DIR"
echo "[$CURRENT_TIME] Stop | Dir: $DIR_NAME | Tmux: ${TMUX_SESSION:-N/A} | Branch: ${GIT_BRANCH:-N/A} | Continue: $STOP_HOOK_ACTIVE" >> "$LOG_DIR/stop.log"

exit 0
