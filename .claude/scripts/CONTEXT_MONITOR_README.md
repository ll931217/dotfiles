# Context Monitor Hook

## Description
Monitors Claude Code context window usage and sends notifications when it reaches 80% (or custom threshold).

## Features
- Configurable threshold percentage (default: 80%)
- Cooldown period to prevent notification spam (default: 5 minutes)
- Dynamic urgency based on context level:
  - 80-84%: Normal urgency
  - 85-89%: High urgency with warning icon
  - 90%+: Critical urgency with error icon
- Logs all alerts to `~/.claude/hooks-logs/context-monitor.log`
- Works with any session

## How It Works
The hook:
1. Reads the transcript file from the session
2. Estimates token usage from file size
3. Calculates percentage of context window (assumes 200k tokens)
4. Sends notification if threshold is reached and cooldown has passed

## Configuration
Edit these variables in the script:
- `THRESHOLD_PERCENTAGE`: Change notification threshold (default: 80)
- `ALERT_COOLDOWN_MINUTES`: Set cooldown between notifications (default: 5)
- `MAX_CONTEXT`: Adjust if using Enterprise 500k context window

## Hook Events
The hook is attached to:
- **PreToolUse**: Runs before each tool is used (frequent checks)
- **Stop**: Runs when Claude finishes responding

## Notifications
Example notifications:
```
📊 Context Window at 82%
Estimated 164000/200000 tokens used in: my-project
```

## Logs
View alert history:
```bash
cat ~/.claude/hooks-logs/context-monitor.log
```

## Limitations
- Token estimation is approximate (based on file size)
- Assumes 200k context window (adjust if using Enterprise)
- Requires JSON-formatted hook input
