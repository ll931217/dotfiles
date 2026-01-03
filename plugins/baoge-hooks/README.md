# Baoge Hooks Plugin

Comprehensive hook system for Claude Code with notifications, context monitoring, and tool tracking.

## Overview

The Baoge Hooks Plugin provides a suite of Git-style hooks for Claude Code that enhance the development experience with:

- **Rich Notifications**: Get informed about tool usage, failures, and session events
- **Context Monitoring**: Track your token usage and context window capacity
- **Safety Alerts**: Get warned before running dangerous commands
- **Session Tracking**: Monitor your work sessions with start/end notifications
- **Tool Tracking**: Keep track of command executions and failures

## Installation

### Option 1: Via Main install.sh (Recommended)

1. Run the main installer:
   ```bash
   ./install.sh
   ```

2. Select `baoge-hooks` from the menu when prompted

3. The installer will:
   - Create `~/.scripts/opencode/` directory
   - Copy all hook scripts to the directory
   - Set executable permissions
   - Register the plugin in Claude Code settings

### Option 2: Manual Installation

1. Create the scripts directory:
   ```bash
   mkdir -p ~/.scripts/opencode
   ```

2. Copy the plugin scripts:
   ```bash
   cp plugins/baoge-hooks/scripts/*.sh ~/.scripts/opencode/
   chmod +x ~/.scripts/opencode/*.sh
   ```

3. Register the plugin in your Claude Code settings (`~/.claude/settings.json`):
   ```json
   {
     "plugins": [
       {
         "name": "baoge-hooks",
         "path": "/path/to/dotfiles/plugins/baoge-hooks"
       }
     ]
   }
   ```

4. Restart Claude Code to activate the hooks

## Uninstallation

### Via Main install.sh

1. Run the main installer:
   ```bash
   ./install.sh
   ```

2. Select the uninstall option for baoge-hooks

### Manual Uninstallation

1. Remove the plugin from Claude Code settings (`~/.claude/settings.json`):
   - Remove the baoge-hooks entry from the `plugins` array

2. Delete the scripts directory:
   ```bash
   rm -rf ~/.scripts/opencode
   ```

3. Restart Claude Code to deactivate the hooks

## Hooks

The plugin includes the following hooks:

| Hook Type | Script | Description |
|-----------|--------|-------------|
| **Notification** | `enhanced-notify.sh` | Rich notifications with context and formatting |
| **PreToolUse** | `danger-alert.sh` | Warns before running dangerous commands (rm, git push --force, etc.) |
| **PostToolUse** | `tool-tracker.sh` | Tracks tool usage and failures for debugging |
| **PreCompact** | `bd prime` | Optimizes beads database before compaction |
| **SessionStart** | `session-start-notify.sh` | Notifies when a Claude Code session starts |
| **SessionEnd** | `session-end-notify.sh` | Notifies when a Claude Code session ends |
| **Stop** | `stop-notify.sh` | Notifies on task completion |
| **Stop** | `context-monitor.sh` | Monitors token usage and context window capacity |

## Configuration

### Hook Customization

Each hook script can be customized by editing the files in `~/.scripts/opencode/`:

#### Enhanced Notifications (`enhanced-notify.sh`)

Customize notification behavior:
- **Notification style**: Change icons, colors, and formatting
- **Context level**: Adjust how much context is included
- **Sound effects**: Enable/disable audio notifications

```bash
# Edit the notification settings
vim ~/.scripts/opencode/enhanced-notify.sh
```

#### Danger Alerts (`danger-alert.sh`)

Customize which commands trigger warnings:
- **Dangerous commands**: Add/remove commands from the watchlist
- **Warning style**: Change the warning message format
- **Confirmation requirement**: Toggle whether confirmation is needed

```bash
# Edit the danger command list
vim ~/.scripts/opencode/danger-alert.sh
```

#### Context Monitor (`context-monitor.sh`)

Customize context monitoring:
- **Warning threshold**: Set when to warn about token usage (default: 80%)
- **Critical threshold**: Set when to show critical alerts (default: 95%)
- **Statistics**: Toggle detailed statistics display

```bash
# Edit the threshold settings
vim ~/.scripts/opencode/context-monitor.sh
```

### Plugin Settings

Configure plugin behavior in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "baoge-hooks": {
      "enabled": true,
      "notification_style": "rich",
      "danger_confirm": true,
      "context_threshold": 80
    }
  }
}
```

## Troubleshooting

### Hooks Not Running

**Problem**: Hooks are not being executed.

**Solutions**:
1. Check that the plugin is registered in `~/.claude/settings.json`
2. Verify scripts have executable permissions: `ls -la ~/.scripts/opencode/`
3. Check Claude Code logs for errors
4. Restart Claude Code

### Permission Denied Errors

**Problem**: Getting "Permission denied" when hooks run.

**Solutions**:
1. Make scripts executable: `chmod +x ~/.scripts/opencode/*.sh`
2. Check file ownership: `ls -la ~/.scripts/opencode/`
3. Ensure scripts are in the correct location

### Notifications Not Appearing

**Problem**: Not receiving notifications.

**Solutions**:
1. Check your desktop notification settings
2. Verify the notification daemon is running
3. Test notification manually: `bash ~/.scripts/opencode/enhanced-notify.sh`

### Context Monitor Warnings

**Problem**: Frequent warnings about context window.

**Solutions**:
1. Adjust the threshold in `context-monitor.sh`
2. Clear old context: Restart Claude Code
3. Run `bd prime` to optimize beads database

## File Structure

```
plugins/baoge-hooks/
├── plugin.json          # Plugin configuration
├── README.md            # This file
├── install.sh           # Installation script
├── uninstall.sh         # Uninstallation script
└── scripts/
    ├── enhanced-notify.sh
    ├── danger-alert.sh
    ├── context-monitor.sh
    ├── tool-tracker.sh
    ├── session-start-notify.sh
    ├── session-end-notify.sh
    └── stop-notify.sh
```

## Requirements

- **Operating System**: Linux (tested on Arch Linux)
- **Shell**: bash (required for hook scripts)
- **Claude Code**: Latest version with plugin support
- **Dependencies**:
  - `notify-send` (libnotify) - for desktop notifications
  - `bd` (beads) - for issue tracking integration

## Testing

After installation, test the hooks:

1. **Test Notifications**:
   ```bash
   bash ~/.scripts/opencode/enhanced-notify.sh
   ```

2. **Test Danger Alert**:
   - Run a dangerous command in Claude Code: `rm -rf /tmp/test`
   - You should see a warning before execution

3. **Test Context Monitor**:
   ```bash
   bash ~/.scripts/opencode/context-monitor.sh
   ```

4. **Test Session Hooks**:
   - Restart Claude Code
   - Check for session start notification
   - Close Claude Code
   - Check for session end notification

## Tips

- **Reduce Notification Noise**: Disable individual hooks in `plugin.json` if you don't need them
- **Customize Warnings**: Add your own dangerous commands to `danger-alert.sh`
- **Track Token Usage**: Use context-monitor.sh to understand your token consumption patterns
- **Integration with Beads**: The PreCompact hook automatically runs `bd prime` to keep your issue tracker optimized

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues, questions, or suggestions:

- Open an issue in the dotfiles repository
- Check the main `.claude/HOOKS_SETUP.md` for detailed hook documentation
- Review `.claude/scripts/README.md` for script-specific documentation

## License

This plugin is part of the dotfiles repository and follows the same license.

## Changelog

### Version 1.0.0 (2026-01-03)
- Initial release
- 8 hooks implemented
- Full notification system
- Context monitoring
- Danger alerts
- Session tracking

## Acknowledgments

Created by **baoge** as part of a comprehensive dotfiles setup for Claude Code.

Inspired by the need for better visibility into Claude Code operations and token usage.
