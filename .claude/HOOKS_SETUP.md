# Claude Code Hooks Setup

This directory contains notification scripts and configuration for Claude Code hooks.

## Directory Structure

```
~/GitHub/dotfiles/.claude/
├── scripts/              # Hook scripts (symlinked from ~/.claude/scripts/)
│   ├── enhanced-notify.sh           # All Claude Code notifications
│   ├── session-start-notify.sh      # Session start events
│   ├── session-end-notify.sh        # Session end events
│   ├── stop-notify.sh              # Task completion events
│   ├── danger-alert.sh             # Dangerous command warnings
│   ├── tool-tracker.sh             # Tool failure tracking
│   ├── notify-with-context.sh       # Legacy script (can be removed)
│   └── README.md                  # Detailed documentation
├── settings.json          # Claude Code configuration (symlinked from ~/.claude/settings.json)
└── .claude-hooks-setup/ # (optional) Log storage if you want logs in dotfiles too
```

## Symlinks

The following files are symlinked from your dotfiles to the actual Claude Code configuration:

```bash
~/.claude/scripts -> ~/GitHub/dotfiles/.claude/scripts
~/.claude/settings.json -> ~/GitHub/dotfiles/.claude/settings.json
```

## How It Works

1. **Edit scripts** in `~/GitHub/dotfiles/.claude/scripts/`
2. **Changes sync** automatically via symlinks to `~/.claude/`
3. **Commit changes** to your dotfiles git repo
4. **Pull updates** on other machines to sync hooks

## Quick Reference

| Hook | Script | Trigger |
|------|--------|---------|
| Notification | `enhanced-notify.sh` | All notifications (idle, permissions, etc.) |
| SessionStart | `session-start-notify.sh` | When Claude Code starts or resumes |
| SessionEnd | `session-end-notify.sh` | When Claude Code ends |
| Stop | `stop-notify.sh` | When Claude finishes a task |
| PreToolUse | `danger-alert.sh` | Before executing Bash commands |
| PostToolUse | `tool-tracker.sh` | After Bash/Write/Edit/Read tools run |

## Context Information

All notifications include:
- 📺 **tmux** session and window name
- 🌿 **git** branch (if in git repo)
- 📁 **directory** name
- 🕐 **timestamp**
- 💻 **hostname** (for remote sessions)

## Logs

Logs are stored in `~/.claude/hooks-logs/`:

```
~/.claude/hooks-logs/
├── notification.log      # All notifications
├── session.log          # Session start/end
├── stop.log             # Task completions
├── danger.log           # Dangerous commands
└── tool-failures.log    # Tool failures
```

**Note**: Logs are NOT in the dotfiles repo (in `.gitignore`).

## Making Changes

### To modify a hook script:

```bash
# Edit the script in your dotfiles
vim ~/GitHub/dotfiles/.claude/scripts/enhanced-notify.sh

# Changes take effect immediately (via symlink)
```

### To add a new hook:

1. Create the script:
   ```bash
   vim ~/GitHub/dotfiles/.claude/scripts/my-new-hook.sh
   chmod +x ~/GitHub/dotfiles/.claude/scripts/my-new-hook.sh
   ```

2. Update settings.json:
   ```bash
   vim ~/GitHub/dotfiles/.claude/settings.json
   ```

3. Add to the hooks section:
   ```json
   "MyHookEvent": [
     {
       "matcher": "",
       "hooks": [
         {
           "type": "command",
           "command": "bash ~/.claude/scripts/my-new-hook.sh"
         }
       ]
     }
   ]
   ```

### To commit changes:

```bash
cd ~/GitHub/dotfiles
git add .claude/
git commit -m "Update Claude Code hooks"
git push
```

### To sync to another machine:

```bash
cd ~/GitHub/dotfiles
git pull

# If symlinks don't exist:
ln -s ~/GitHub/dotfiles/.claude/scripts ~/.claude/scripts
ln -s ~/GitHub/dotfiles/.claude/settings.json ~/.claude/settings.json
```

## Testing Hooks

Test any hook directly:

```bash
echo '{"session_id":"test","cwd":"/home/test","message":"Test","notification_type":"idle_prompt"}' | \
  bash ~/.claude/scripts/enhanced-notify.sh
```

## Troubleshooting

### Symlinks not working

Check if symlinks exist:
```bash
ls -la ~/.claude/ | grep -E "scripts|settings"
```

Should show:
```
lrwxrwxrwx ... scripts -> /home/USER/GitHub/dotfiles/.claude/scripts
lrwxrwxrwx ... settings.json -> /home/USER/GitHub/dotfiles/.claude/settings.json
```

Recreate if missing:
```bash
ln -s ~/GitHub/dotfiles/.claude/scripts ~/.claude/scripts
ln -s ~/GitHub/dotfiles/.claude/settings.json ~/.claude/settings.json
```

### Changes not taking effect

Claude Code captures hooks at startup. Restart Claude Code to see changes.

### Scripts not executable

```bash
chmod +x ~/GitHub/dotfiles/.claude/scripts/*.sh
```

## Environment Variables

All hooks have access to:

- `CLAUDE_PROJECT_DIR` - Project root directory
- `TMUX` - If in tmux session
- `CLAUDE_CODE_REMOTE` - Set to "true" if in remote environment

## Security Notes

⚠️ **Important**: Hooks execute shell commands on your system.

- Review all scripts before adding to dotfiles
- Test in safe environment first
- Be careful with regex patterns in danger-alert.sh
- Consider adding sensitive commands to danger patterns

## Full Documentation

See `scripts/README.md` for complete documentation including:
- Detailed explanation of each hook
- Customization guide
- Advanced usage
- Troubleshooting tips

## Related Files

Other Claude Code configuration in your dotfiles:

- `.claude/agents/` - Custom agents
- `.claude/commands/` - Custom slash commands
- `.claude/CLAUDE.md` - Project context
- `.claude/skills/` - Custom skills

## Backup

The old configuration is backed up at:
```bash
~/.claude/settings.json.backup
```

You can restore it if needed:
```bash
cp ~/.claude/settings.json.backup ~/.claude/settings.json.backup.old
```

## Contributing

When improving hooks:
1. Test thoroughly
2. Update relevant documentation
3. Commit with descriptive message
4. Share with team if using shared dotfiles

---

**Last Updated**: 2026-01-02
