#!/usr/bin/env bash

# Hook for PostToolUse - Track command execution and send notifications for long-running tasks

# Read hook input from stdin
INPUT=$(cat)

# Extract tool information
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')

# Get tool response
TOOL_RESPONSE=$(echo "$INPUT" | jq -r '.tool_response // {}')

# Only track specific tools (Bash, Write, Edit are most common)
if [[ ! "$TOOL_NAME" =~ ^(Bash|Write|Edit|Read)$ ]]; then
    exit 0
fi

# Get context
CURRENT_TIME=$(date '+%H:%M:%S')
DIR_NAME=$(basename "$CWD" 2>/dev/null || echo "unknown")

# Get tmux session
TMUX_SESSION=""
if [ -n "$TMUX" ]; then
    TMUX_SESSION=$(tmux display-message -p '#S' 2>/dev/null)
fi

# Get git branch
GIT_BRANCH=""
if [ -d "$CWD/.git" ] 2>/dev/null; then
    GIT_BRANCH=$(git -C "$CWD" branch --show-current 2>/dev/null || echo "")
fi

# Check if command failed
SUCCESS=$(echo "$TOOL_RESPONSE" | jq -r '.success // true')

if [ "$SUCCESS" = "false" ]; then
    # Command failed - send notification
    TITLE="❌ Claude Code - Tool Failed"

    # Get error details
    if [ "$TOOL_NAME" = "Bash" ]; then
        ERROR=$(echo "$TOOL_RESPONSE" | jq -r '.stderr // .error // "Unknown error"')
        BODY="${ERROR:0:150}"
    elif [ "$TOOL_NAME" = "Write" ]; then
        BODY="Failed to write file"
    elif [ "$TOOL_NAME" = "Edit" ]; then
        BODY="Failed to edit file"
    elif [ "$TOOL_NAME" = "Read" ]; then
        BODY="Failed to read file"
    else
        BODY="$TOOL_NAME failed"
    fi

    # Add context
    CONTEXT=""
    if [ -n "$TMUX_SESSION" ]; then
        CONTEXT="📺 $TMUX_SESSION"
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

    if [ -n "$CONTEXT" ]; then
        BODY="$BODY
$CONTEXT"
    fi

    notify-send -u critical "$TITLE" "$BODY"

    # Log failure
    LOG_DIR="$HOME/.claude/hooks-logs"
    mkdir -p "$LOG_DIR"
    echo "[$CURRENT_TIME] FAILURE | Tool: $TOOL_NAME | Dir: $DIR_NAME | Tmux: ${TMUX_SESSION:-N/A}" >> "$LOG_DIR/tool-failures.log"
fi

exit 0
