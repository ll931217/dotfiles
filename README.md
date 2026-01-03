[![MIT Licence](https://badges.frapsoft.com/os/mit/mit.svg?v=103)](https://opensource.org/licenses/mit-license.php)
[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badge/)

![LeetArch](https://i.imgur.com/z1yUurS.png)

# Setup

## Requirements

- Gnome terminal
- Compton(This is actually optional since I don't use it anymore)
- Rofi
- feh
- Polybar
- i3-gaps
- cava

## Instructions

Run the `install.sh` script to install the configs.

Setting fonts for `gnome-terminal`:

    Nerd fonts, Awesome fonts couldn't list in terminal, so we couldn't select the font we want.

    You can set any font using dconf-editor, under /org/gnome/terminal/legacy/profiles:/:<profile-id>/font.

    e.g. Custom value : Hack Nerd Font Mono Bold 14

    https://askubuntu.com/questions/1046871/nerd-font-not-fond-in-terminal-profile/

Use `feh` to apply the wallpaper.

The 2 files `chrome` folder should be placed in your `Firefox` home directory. To access that, go to `Menu` -> `Help` -> `Troubleshooting Information` -> `Open Directory`.

## AI Coding Agent Integration (Mainly Claude Code)

This dotfiles repository includes a sophisticated [Claude Code](https://claude.ai/code) configuration that transforms it into an AI-assisted development environment. The `.claude/` directory contains:

- **31 specialized agents** for architecture, frontend/backend development, DevOps, security, and more
- **10 custom slash commands** for PRD workflows, git operations, and analysis tools
- **5 specialized skills** for document processing, frontend design, and MCP server creation
- **Advanced hook system** with notifications, session tracking, and tool monitoring
- **Integration with beads** for distributed issue tracking and **worktrunk** for parallel git workflows

### Key Commands

- `/flow:plan` - Create Product Requirements Documents with auto-generated tasks
- `/flow:implement` - Implement approved PRDs with task tracking
- `/tools:parallel-analyze` - Spawn multiple agents for collaborative analysis
- `/tools:debug` - AI-assisted debugging workflows
- `/gh:create-commit` - Standardized git commit creation

For complete documentation on the Claude AI setup, see:

- [`.claude/WORKFLOW.md`](.claude/WORKFLOW.md) - Complete workflow guide
- [`.claude/COMMANDS.md`](.claude/COMMANDS.md) - Custom slash commands reference
- [`.claude/AGENTS.md`](.claude/AGENTS.md) - Available AI agents

---

## Architecture

### Installation System

This dotfiles repository features a **registry-driven modular installation system** that functions as a dependency graph resolver rather than a simple collection of scripts.

#### Registry-Driven Design

The core of the installation system is a central component registry (`.scripts/installer-registry.sh`) that defines all installable components as associative arrays. Each component declares:

- **Dependencies** and **conflicts** for automatic resolution
- **Packages** to install (including AUR support via `yay`)
- **Detection methods** (command availability + file existence checks)
- **Target paths** for symlink creation

This enables the installer to automatically resolve complex dependency relationships and handle mutual exclusivity (e.g., window managers).

#### Hybrid Detection Strategy

Components are detected using a multi-tier fallback system:

1. **Command availability** (primary) - e.g., `command -v nvim`
2. **File/symlink existence** (secondary) - e.g., `~/.config/nvim/init.lua`
3. **Directory existence** (tertiary)

This handles edge cases where packages are installed but not configured, or where configs exist without packages.

#### Installation Library

The `.scripts/` directory contains the core installation library:

```
.scripts/
├── install-lib.sh              # Core utilities (logging, colors, etc.)
├── installer-registry.sh       # Component registry (associative arrays)
├── installer-modules.sh        # Execution engine for components
├── install-state.sh            # State tracking and snapshots
├── install-health.sh           # Health check system
└── fzf-helpers.sh              # Interactive UI helpers
```

#### Adding New Components

To add a new component, edit `installer-registry.sh` and define an associative array:

```bash
declare -A COMPONENT_NAME=(
    [category]="category-name"           # Group for display
    [description]="Human-readable desc"
    [packages]="pkg1 pkg2"               # Pacman packages
    [aur]="aur-pkg1 aur-pkg2"            # AUR packages (optional)
    [symlinks]="src:dest src2:dest2"     # Symlink pairs (optional)
    [conflicts]="OTHER_COMPONENT"        # Mutually exclusive (optional)
    [dependencies]="DEP1 DEP2"           # Required components (optional)
    [detect]="cmd_name"                  # Detection command (optional)
)
```

### State Management

Installation state is tracked in `.install-state.json`:

- Installed versions for each component
- File checksums for change detection
- Backup locations for rollback capability
- Snapshot IDs for point-in-time restoration

The snapshot system creates pre-installation backups, enabling rollback to any previous state via `./install.sh --rollback <id>`.

### Symlink Management

Unlike GNU stow, this system uses custom symlink creation with:

- Timestamped backups before replacing files
- Intelligent handling of existing symlinks
- Dry-run mode for preview
- Conflict resolution

### Health Check System

`./install.sh --health` provides two modes:

- **Quick check**: Validates symlinks exist and commands are available
- **Comprehensive**: Validates configs and tests system integration

### Key Architectural Patterns

**Window Manager Exclusivity**: i3-gaps and Hyprland cannot be installed simultaneously. The registry declares conflicts (`[conflicts]="HYPRLAND"` for i3 items), and the installer enforces mutual exclusion automatically.

**Theme Consistency**: Catppuccin theme used across all terminals (alacritty, kitty, wezterm, ghostty) with multiple flavor variants (mocha, latte, frappe, macchiato).

**Zsh Modularity**:

- `~/.zshrc` redirects to `~/.config/zsh/.zshrc`
- Config split into: `options.zsh`, `aliases.zsh`, `functions.zsh`, `keybinds.zsh`, `theme.zsh`, `fzf.zsh`, `env.zsh`
- Private configs in `~/.config/zsh/private/` (gitignored)
