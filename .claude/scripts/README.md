# Claude Code Enhanced Hooks - Complete Setup

A comprehensive notification and tracking system for Claude Code with rich context including tmux sessions, git branches, and more.

## Overview

This setup provides 6 different hooks that send desktop notifications at key points in your Claude Code workflow, with contextual information to help you stay informed even when working across multiple sessions.

## Installed Hooks

### 1. **Notification Hook** - All Claude Code notifications
**Script**: `enhanced-notify.sh`
**Trigger**: All notification events
**Events**: `idle_prompt`, `permission_prompt`, `auth_success`, `elicitation_dialog`

**Features**:
- Different urgency levels based on notification type
- Critical urgency for permission prompts and configuration dialogs
- Normal urgency for idle/waiting prompts
- Low urgency for authentication success
- Displays:
  - 📺 tmux session and window name
  - 🌿 git branch (if in git repo)
  - 📁 project directory name
  - 💻 hostname (for remote sessions)
  - 🕐 current timestamp

**Example Notifications**:
```
🤖 Claude Code - Waiting
Awaiting your input
📺 tmux: work:editor | 🌿 feature-branch | 📁 my-project | 🕐 11:37:30

🔐 Claude Code - Permission Needed
Claude needs your permission to use Bash
📺 tmux: work:editor | 📁 my-project | 🕐 11:37:30
```

**Log**: `~/.claude/hooks-logs/notification.log`

---

### 2. **SessionStart Hook** - Session lifecycle
**Script**: `session-start-notify.sh`
**Trigger**: When a Claude Code session starts or resumes
**Events**: `startup`, `resume`, `clear`, `compact`

**Features**:
- Low urgency notifications (won't interrupt)
- Shows session type (new, resumed, cleared, post-compact)
- Displays tmux session and directory context

**Example**:
```
🚀 Claude Code Started
Session started
📺 tmux: work | 📁 my-project | 🕐 11:37:30
```

**Log**: `~/.claude/hooks-logs/session.log`

---

### 3. **SessionEnd Hook** - Session lifecycle
**Script**: `session-end-notify.sh`
**Trigger**: When a Claude Code session ends
**Events**: `clear`, `logout`, `prompt_input_exit`, `other`

**Features**:
- Low urgency notifications
- Shows exit reason
- Displays session context

**Example**:
```
🛑 Claude Code Ended
Logged out
📺 tmux: work | 📁 my-project | 🕐 11:37:30
```

**Log**: `~/.claude/hooks-logs/session.log`

---

### 4. **Stop Hook** - Task completion
**Script**: `stop-notify.sh`
**Trigger**: When Claude Code finishes a task/response
**Events**: Task completion

**Features**:
- Normal urgency notifications
- Extracts and displays the last assistant message (up to 100 chars)
- Shows tmux session, git branch, and directory
- Indicates if Claude is auto-continuing via stop hooks
- Perfect for knowing when long-running tasks complete

**Example**:
```
✅ Claude Code - Task Complete
Successfully built the project
📺 tmux: work | 🌿 main | 📁 my-project | ♻️ Continuing | 🕐 11:37:30
```

**Log**: `~/.claude/hooks-logs/stop.log`

---

### 5. **PreToolUse Hook** - Safety alerts
**Script**: `danger-alert.sh`
**Trigger**: Before Bash commands execute
**Matcher**: `Bash`

**Features**:
- Monitors for potentially dangerous command patterns
- Sends critical warnings before dangerous commands:
  - `rm -rf /` and similar destructive operations
  - `dd` commands (disk operations)
  - Fork bombs
  - Dangerous permission changes
- Sends normal warnings for operations requiring care:
  - `git push --force`
  - `git reset --hard`
  - `kubectl delete`
  - Database `DROP` and `DELETE` operations
- Doesn't block execution, just warns you

**Example**:
```
⚠️ Claude Code - DANGEROUS COMMAND
Attempting: rm -rf ./node_modules
📺 tmux: work | 📁 my-project
```

**Log**: `~/.claude/hooks-logs/danger.log`

---

### 6. **PostToolUse Hook** - Failure tracking
**Script**: `tool-tracker.sh`
**Trigger**: After Bash, Write, Edit, or Read tools complete
**Matcher**: `Bash|Write|Edit|Read`

**Features**:
- Monitors tool execution results
- Sends critical notifications when tools fail
- Provides error details:
  - For Bash: stderr output
  - For Write/Edit/Read: specific failure type
- Displays context to help debug
- Only notifies on failures (success is silent to reduce noise)

**Example**:
```
❌ Claude Code - Tool Failed
No such file or directory
📺 tmux: work | 📁 my-project | 🕐 11:37:30
```

**Log**: `~/.claude/hooks-logs/tool-failures.log`

---

## Log Files

All hooks log to `~/.claude/hooks-logs/`:

| Log File | Purpose |
|----------|---------|
| `notification.log` | All notification events with full context |
| `session.log` | Session start/end events |
| `stop.log` | Task completion events |
| `danger.log` | Dangerous/warning commands |
| `tool-failures.log` | Tool execution failures |

**View logs in real-time**:
```bash
tail -f ~/.claude/hooks-logs/notification.log
tail -f ~/.claude/hooks-logs/session.log
```

---

## Context Information

Each notification includes relevant context icons:

| Icon | Meaning |
|------|---------|
| 📺 | tmux session and window name |
| 🌿 | Current git branch |
| 📁 | Project directory name |
| 💻 | Hostname (for remote sessions) |
| 🕐 | Current timestamp |
| ♻️ | Auto-continuing (stop hook active) |

---

## Quick Start

The hooks are already configured in `~/.claude/settings.json`. Just start a new Claude Code session:

```bash
claude
```

You'll receive notifications for:
- Session start/end
- When Claude needs your input (after 60+ seconds idle)
- Task completions
- Dangerous commands
- Tool failures

---

## Testing

Test your hooks:

```bash
# Test notification hook
echo '{"session_id":"test","cwd":"/home/test","message":"Test","notification_type":"idle_prompt"}' | \
  bash ~/.claude/scripts/enhanced-notify.sh

# Test session start hook
echo '{"session_id":"test","cwd":"/home/test","source":"startup","permission_mode":"default"}' | \
  bash ~/.claude/scripts/session-start-notify.sh

# Test session end hook
echo '{"session_id":"test","cwd":"/home/test","reason":"logout","permission_mode":"default"}' | \
  bash ~/.claude/scripts/session-end-notify.sh

# Test stop hook
echo '{"session_id":"test","transcript_path":"/dev/null","stop_hook_active":"false","permission_mode":"default"}' | \
  bash ~/.claude/scripts/stop-notify.sh

# Test danger alert hook
echo '{"session_id":"test","tool_name":"Bash","tool_input":{"command":"rm -rf /tmp"}}' | \
  bash ~/.claude/scripts/danger-alert.sh

# Test tool tracker hook (failure case)
echo '{"session_id":"test","tool_name":"Bash","tool_response":{"success":false,"stderr":"Error: command failed"},"cwd":"/home/test"}' | \
  bash ~/.claude/scripts/tool-tracker.sh
```

---

## Customization

### Change Notification Icons

Edit each script to change emoji:

| Icon | Current Use | Alternative |
|------|-------------|-------------|
| 🤖 | Robot (waiting) | 🤔, 💭, 🚦 |
| 🔐 | Permissions | 🔒, ⚙️ |
| ✅ | Success/complete | ✓, 🎉, 🎊 |
| 🚀 | Session start | ▶️, 🌟, 📍 |
| 🛑 | Session end | ⏹️, 🔚, 🏁 |
| ⚠️ | Warning | ⚡, 🔥, 🚨 |
| ❌ | Failure | ✗, 🚫, ❗ |

### Adjust Urgency Levels

Change the `-u` flag in `notify-send` commands:

```bash
notify-send -u low        # Quiet, may not appear
notify-send -u normal    # Default visibility
notify-send -u critical  # High priority, stays longer
```

### Add More Dangerous Patterns

Edit `~/.claude/scripts/danger-alert.sh` and add to `DANGEROUS_PATTERNS`:

```bash
DANGEROUS_PATTERNS=(
    "rm -rf /"
    "dd if="
    # Add your patterns:
    "your-dangerous-pattern"
)
```

### Modify Notification Duration

Add `-t` flag (timeout in milliseconds):

```bash
# Show for 5 seconds
notify-send -t 5000 "Title" "Message"

# Show for 10 seconds (danger alerts use this)
notify-send -u critical -t 10000 "Title" "Message"
```

### Disable Specific Hooks

To disable a hook, comment it out in `~/.claude/settings.json`:

```json
"PreToolUse": [
  {
    "matcher": "Bash",
    "hooks": [
      // Comment this out to disable danger alerts
      // {
      //   "type": "command",
      //   "command": "bash ~/.claude/scripts/danger-alert.sh"
      // }
    ]
  }
]
```

---

## Configuration File Location

All hooks are configured in: `~/.claude/settings.json`

**Current configuration**:
- ✅ Notification hook (all notifications)
- ✅ PreToolUse hook (Bash danger alerts)
- ✅ PostToolUse hook (failure tracking for Bash/Write/Edit/Read)
- ✅ PreCompact hook (runs `bd prime`)
- ✅ SessionStart hook (session started notification)
- ✅ SessionEnd hook (session ended notification)
- ✅ Stop hook (task completion notification)

---

## Requirements

The scripts require these utilities:

- **notify-send** - Desktop notifications (libnotify)
- **jq** - JSON processing
- **git** - Git branch information (optional)
- **tmux** - tmux session info (optional)

All are already installed on your system.

---

## Troubleshooting

### Notifications not appearing

1. Test `notify-send` directly:
   ```bash
   notify-send "Test" "This is a test notification"
   ```

2. Check hook logs for errors:
   ```bash
   tail -20 ~/.claude/hooks-logs/*.log
   ```

3. Ensure scripts are executable:
   ```bash
   ls -l ~/.claude/scripts/
   chmod +x ~/.claude/scripts/*.sh
   ```

4. Verify hooks are registered in Claude Code:
   - Start a `claude` session
   - Run `/hooks` to see active hooks

### Tmux information not showing

- Check if you're in a tmux session:
  ```bash
  echo $TMUX
  ```

- Test tmux command:
  ```bash
  tmux display-message -p '#S'
  ```

### Git branch not showing

- Verify you're in a git repository:
  ```bash
  git status
  ```

- Check git is installed:
  ```bash
  which git
  ```

### Too many notifications

Disable specific hooks by editing `~/.claude/settings.json`.

Common adjustments:
- Remove `PostToolUse` hook to stop failure notifications
- Change `danger-alert.sh` to remove warning patterns (keep only dangerous)
- Change `enhanced-notify.sh` to use matcher instead of catching all notifications

Example for idle prompts only:
```json
"Notification": [
  {
    "matcher": "idle_prompt",
    "hooks": [
      {
        "type": "command",
        "command": "bash ~/.claude/scripts/enhanced-notify.sh"
      }
    ]
  }
]
```

### Hooks not executing

1. Check configuration syntax:
   ```bash
   cat ~/.claude/settings.json | jq .
   ```

2. Test a hook manually:
   ```bash
   echo '{"test":"data"}' | bash ~/.claude/scripts/enhanced-notify.sh
   ```

3. Check for errors in Claude Code debug mode:
   ```bash
   claude --debug
   ```

---

## Advanced Usage

### Add Custom Fields to Context

Each script extracts JSON fields from hook input. Available fields vary by event:

```bash
# Common fields
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
PERMISSION_MODE=$(echo "$INPUT" | jq -r '.permission_mode // empty')

# Event-specific fields
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')        # PreToolUse/PostToolUse
NOTIFICATION_TYPE=$(echo "$INPUT" | jq -r '.notification_type // empty')  # Notification
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')    # Stop/SessionStart/SessionEnd
```

### Create Project-Specific Hooks

Add hooks to `.claude/settings.json` in your project directory:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash $CLAUDE_PROJECT_DIR/.claude/project-start.sh"
          }
        ]
      }
    ]
  }
}
```

### Integrate with External Tools

Send alerts to Slack, Discord, etc. by modifying scripts:

```bash
# In a notification script
# Send to Slack
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d "{\"text\":\"Claude Code: $MESSAGE\"}"

# Or use existing Slack CLI
slack send "Claude Code: $MESSAGE"
```

---

## Tips

1. **Watch logs in real-time**: Use `tail -f` to monitor hook activity
2. **Adjust urgency**: Change critical/normal/low to match your preferences
3. **Filter notifications**: Use your notification manager to filter by urgency
4. **Custom patterns**: Add project-specific dangerous patterns to `danger-alert.sh`
5. **Session management**: SessionStart/SessionEnd notifications help track active sessions across tmux windows

---

## Files Summary

| File | Purpose | Hook Event |
|------|---------|------------|
| `enhanced-notify.sh` | Rich notifications | Notification |
| `session-start-notify.sh` | Session start events | SessionStart |
| `session-end-notify.sh` | Session end events | SessionEnd |
| `stop-notify.sh` | Task completion | Stop |
| `danger-alert.sh` | Dangerous command warnings | PreToolUse (Bash) |
| `tool-tracker.sh` | Failure notifications | PostToolUse |

**Location**: `~/.claude/scripts/`

**Configuration**: `~/.claude/settings.json`

**Logs**: `~/.claude/hooks-logs/`

---

## Support

For issues:
1. Check logs: `~/.claude/hooks-logs/`
2. Test hooks manually (see Testing section)
3. Verify configuration: `jq . ~/.claude/settings.json`
4. Run with debug: `claude --debug`

---

Enjoy staying informed about your Claude Code sessions! 🎉
