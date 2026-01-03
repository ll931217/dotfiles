#!/usr/bin/env bash

# Hook for PreToolUse - Warn about dangerous commands before execution
# Currently monitors Bash tool for potentially dangerous operations

# Read hook input from stdin
INPUT=$(cat)

# Extract tool information
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input // {}')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')

# Only check Bash commands
if [ "$TOOL_NAME" != "Bash" ]; then
    exit 0
fi

# Get the command
COMMAND=$(echo "$TOOL_INPUT" | jq -r '.command // empty')

if [ -z "$COMMAND" ]; then
    exit 0
fi

# Define dangerous patterns
DANGEROUS_PATTERNS=(
    "rm -rf /"
    "rm -rf \./"
    "dd if="
    ":(){ :|:& };:"
    "> /dev/sd"
    "mkfs."
    "chmod 777 /"
    "chown -R"
    ":wq"
    "!!"
)

# Define warning patterns (not dangerous but worth noting)
WARNING_PATTERNS=(
    "git push --force"
    "git reset --hard"
    "git branch -D"
    "docker rm -f"
    "kubectl delete"
    "DROP TABLE"
    "DELETE FROM"
)

# Check for dangerous patterns
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qE "$pattern"; then
        # Get context
        DIR_NAME=$(basename "$(pwd)" 2>/dev/null || echo "unknown")
        TMUX_SESSION=""
        if [ -n "$TMUX" ]; then
            TMUX_SESSION=$(tmux display-message -p '#S' 2>/dev/null)
        fi

        # Send critical notification
        notify-send -u critical -t 10000 \
            "⚠️ Claude Code - DANGEROUS COMMAND" \
            "Attempting: ${COMMAND:0:80}
📺 ${TMUX_SESSION:-no tmux} | 📁 $DIR_NAME"

        # Log it
        LOG_DIR="$HOME/.claude/hooks-logs"
        mkdir -p "$LOG_DIR"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] DANGEROUS COMMAND | Session: $SESSION_ID | Dir: $DIR_NAME | Command: $COMMAND" >> "$LOG_DIR/danger.log"

        # Don't block, just warn
        exit 0
    fi
done

# Check for warning patterns
for pattern in "${WARNING_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qE "$pattern"; then
        # Get context
        DIR_NAME=$(basename "$(pwd)" 2>/dev/null || echo "unknown")
        TMUX_SESSION=""
        if [ -n "$TMUX" ]; then
            TMUX_SESSION=$(tmux display-message -p '#S' 2>/dev/null)
        fi

        # Send normal notification
        notify-send -u normal \
            "⚡ Claude Code - Warning" \
            "Executing: ${COMMAND:0:80}
📺 ${TMUX_SESSION:-no tmux} | 📁 $DIR_NAME"

        # Log it
        LOG_DIR="$HOME/.claude/hooks-logs"
        mkdir -p "$LOG_DIR"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING | Session: $SESSION_ID | Dir: $DIR_NAME | Command: $COMMAND" >> "$LOG_DIR/danger.log"

        exit 0
    fi
done

exit 0
