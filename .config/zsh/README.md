# Zsh Configuration with Znap Plugin Manager

This directory contains liang's Z-Shell configuration using Znap as the primary plugin manager.

## 🚀 Migration Complete (2026-01-01)

Successfully migrated from dual plugin managers (Znap + Zinit) to Znap-only for better performance and maintainability.

## 📁 Configuration Structure

```
~/.config/zsh/
├── .zshrc              # Main configuration file
├── env.zsh             # Environment variables
├── keys.zsh            # Key bindings
├── fzf.zsh             # FZF configuration
├── theme.zsh           # Theme and appearance
├── aliases.zsh         # Command aliases
├── functions.zsh       # Custom functions
├── utility.zsh         # Utility functions
├── options.zsh         # Shell options
├── keybinds.zsh        # Key bindings
├── prompt.zsh          # Prompt configuration
├── sunnyvale.zsh       # Location-specific settings
└── plugins/            # Znap-managed plugins
    └── [various repos]
```

## 🔌 Plugin Manager: Znap

**Why Znap?**
- ✅ Fast-as-hell startup times
- ✅ Simple syntax (`znap source <repo>`)
- ✅ Automatic caching and compilation
- ✅ Smart dependency management
- ✅ No complex ice commands needed

### Active Plugins

```bash
# Core functionality
znap source ohmyzsh/ohmyzsh plugins/git/git.plugin.zsh
znap source zsh-users/zsh-completions
znap source zsh-users/zsh-autosuggestions
znap source zsh-users/zsh-syntax-highlighting
znap source zsh-users/zsh-history-substring-search

# Enhanced features
znap source zdharma-continuum/history-search-multi-word
znap source Aloxaf/fzf-tab
znap source hlissner/zsh-autopair
znap source MichaelAquilina/zsh-you-should-use

# Utilities
znap source thewtex/tmux-mem-cpu-load
znap source chrissicool/zsh-256color

# Oh-My-Zsh snippets
znap source ohmyzsh/ohmyzsh plugins/colored-man-pages/colored-man-pages.plugin.zsh
znap source ohmyzsh/ohmyzsh plugins/command-not-found/command-not-found.plugin.zsh
```

## 🛠️ External Tools

- **Starship**: Custom prompt configuration
- **Zoxide**: Smart directory navigation
- **Direnv**: Environment management per directory
- **Atuin**: Enhanced shell history
- **Exa/Bat**: Modern ls and cat alternatives (system-managed)

## 📊 Performance

- **Startup time**: ~0.14 seconds
- **Memory usage**: Optimized with lazy loading
- **Plugin loading**: Parallel execution where possible

## 🔧 Maintenance

### Adding New Plugins
```bash
# Add to ~/.config/zsh/.zshrc
znap source username/repo-name
```

### Updating Plugins
```bash
# Znap automatically handles updates
# Manual update if needed:
znap pull
```

### Removing Plugins
1. Remove `znap source` line from `.zshrc`
2. Restart shell
3. Znap will handle cleanup

## 🗂️ Backup Information

Original Zinit configuration backed up to:
- `~/.config/zsh.backup.<timestamp>`
- `~/.config/zsh/plugins.zsh.backup`

## 📋 Migration Benefits

1. **Simplified configuration** - single plugin manager
2. **Faster startup** - no competing managers
3. **Cleaner code** - reduced complexity
4. **Better maintainability** - unified approach
5. **Reduced errors** - no conflicts between managers

---

**Configuration maintained by**: liang
**GitHub**: https://github.com/ll931217
**Last updated**: 2026-01-01
