# Znap Plugin Manager - Quick Maintenance Guide

## 🚀 Daily Operations

### Add a New Plugin
```bash
# Edit ~/.config/zsh/.zshrc
znap source username/repo-name

# Or add to appropriate category section
```

### Update All Plugins
```bash
# Automatic (recommended)
# Znap handles updates in background

# Manual update if needed
znap pull
```

### Check Plugin Status
```bash
# See installed plugins
ls ~/.config/zsh/plugins/

# Check Znap status
znap status 2>/dev/null || echo "Znap is working"
```

## 🔧 Troubleshooting

### Slow Startup
```bash
# Time your shell startup
time zsh -i -c "exit"

# If > 0.5s, check:
# 1. Internet connectivity (first-time plugin loads)
# 2. Plugin count - remove unused ones
# 3. Heavy external tool initializations
```

### Plugin Not Working
```bash
# Reload configuration
source ~/.config/zsh/.zshrc

# Check plugin exists
znap source username/repo-name --test 2>/dev/null

# Remove and reinstall
# 1. Remove line from .zshrc
# 2. Restart shell
# 3. Add line back
```

### Completions Missing
```bash
# Rebuild completions
rm -f ~/.zcompdump*
autoload -Uz compinit && compinit -C

# Restart shell
```

## 📊 Performance Tips

1. **Keep plugin count minimal** - only what you actually use
2. **Use lazy loading** for heavy tools when possible
3. **Regular cleanup** - remove unused plugins
4. **Monitor startup time** weekly

## 🗑️ Cleanup Commands

### Remove Unused Plugins
```bash
# Remove plugin references from .zshrc
# Restart shell - Znap handles cleanup
```

### Clear Znap Cache (if issues)
```bash
# WARNING: This will re-download all plugins
rm -rf ~/.config/zsh/plugins/
# Restart shell to rebuild
```

## 📝 Common Plugin Patterns

### Oh-My-Zsh Plugins
```bash
znap source ohmyzsh/ohmyzsh plugins/plugin-name/plugin-name.plugin.zsh
```

### Standalone Plugins
```bash
znap source username/plugin-name
```

### GitHub Sources
```bash
znap source https://github.com/username/plugin-name
```

---

**Remember**: Znap is designed to be "fire and forget". Most operations are automatic!
