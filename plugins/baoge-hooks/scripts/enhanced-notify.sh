#!/usr/bin/env bash

# Enhanced notification script with rich context for Claude Code hooks

# Read hook input from stdin
INPUT=$(cat)

# Extract useful information from the hook input
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
MESSAGE=$(echo "$INPUT" | jq -r '.message // empty')
NOTIFICATION_TYPE=$(echo "$INPUT" | jq -r '.notification_type // empty')
HOOK_EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // empty')

# Get additional context
CURRENT_TIME=$(date '+%H:%M:%S')
CURRENT_DATE=$(date '+%Y-%m-%d')

# Get directory name (shorter than full path)
DIR_NAME=$(basename "$CWD" 2>/dev/null || echo "unknown")

# Get git branch if available
GIT_BRANCH=""
if [ -d "$CWD/.git" ] 2>/dev/null; then
    GIT_BRANCH=$(git -C "$CWD" branch --show-current 2>/dev/null || echo "")
fi

# Get tmux session name if available
TMUX_SESSION=""
TMUX_WINDOW=""
if [ -n "$TMUX" ]; then
    TMUX_SESSION=$(tmux display-message -p '#S' 2>/dev/null)
    TMUX_WINDOW=$(tmux display-message -p '#W' 2>/dev/null)
fi

# Get hostname
HOSTNAME=$(hostname -s 2>/dev/null || echo "")

# Build notification based on type
TITLE="Claude Code"
BODY=""

case "$NOTIFICATION_TYPE" in
    idle_prompt)
        TITLE="🤖 Claude Code - Waiting"
        BODY="Awaiting your input"
        ;;
    permission_prompt)
        TITLE="🔐 Claude Code - Permission Needed"
        BODY="$MESSAGE"
        ;;
    auth_success)
        TITLE="✅ Claude Code - Auth Success"
        BODY="Authentication successful"
        ;;
    elicitation_dialog)
        TITLE="🔧 Claude Code - Configuration Needed"
        BODY="MCP tool elicitation required"
        ;;
    *)
        TITLE="📢 Claude Code"
        BODY="$MESSAGE"
        ;;
esac

# Add additional context
CONTEXT=""

# Add tmux info
if [ -n "$TMUX_SESSION" ]; then
    if [ -n "$TMUX_WINDOW" ] && [ "$TMUX_WINDOW" != "$TMUX_SESSION" ]; then
        CONTEXT="📺 tmux: $TMUX_SESSION:$TMUX_WINDOW"
    else
        CONTEXT="📺 tmux: $TMUX_SESSION"
    fi
fi

# Add git branch
if [ -n "$GIT_BRANCH" ]; then
    if [ -n "$CONTEXT" ]; then
        CONTEXT="$CONTEXT | 🌿 $GIT_BRANCH"
    else
        CONTEXT="🌿 $GIT_BRANCH"
    fi
fi

# Add directory
if [ -n "$DIR_NAME" ] && [ "$DIR_NAME" != "unknown" ]; then
    if [ -n "$CONTEXT" ]; then
        CONTEXT="$CONTEXT | 📁 $DIR_NAME"
    else
        CONTEXT="📁 $DIR_NAME"
    fi
fi

# Add hostname if not local
if [ -n "$HOSTNAME" ] && [ "$HOSTNAME" != "$(hostname -f 2>/dev/null)" ]; then
    if [ -n "$CONTEXT" ]; then
        CONTEXT="$CONTEXT | 💻 $HOSTNAME"
    else
        CONTEXT="💻 $HOSTNAME"
    fi
fi

# Add time
if [ -n "$CONTEXT" ]; then
    CONTEXT="$CONTEXT | 🕐 $CURRENT_TIME"
else
    CONTEXT="🕐 $CURRENT_TIME"
fi

# Combine body with context
if [ -n "$CONTEXT" ]; then
    BODY="$BODY
$CONTEXT"
fi

# Send notification with urgency based on type
URGENCY="normal"
case "$NOTIFICATION_TYPE" in
    permission_prompt|elicitation_dialog)
        URGENCY="critical"
        ;;
    idle_prompt)
        URGENCY="normal"
        ;;
    auth_success)
        URGENCY="low"
        ;;
esac

notify-send -u "$URGENCY" "$TITLE" "$BODY"

# Log to file for debugging and history
LOG_DIR="$HOME/.claude/hooks-logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/notification.log"
echo "[$CURRENT_DATE $CURRENT_TIME] Event: $NOTIFICATION_TYPE | Session: $SESSION_ID | Dir: $DIR_NAME | Tmux: ${TMUX_SESSION:-N/A}:${TMUX_WINDOW:-N/A} | Branch: ${GIT_BRANCH:-N/A} | Msg: $MESSAGE" >> "$LOG_FILE"

exit 0
