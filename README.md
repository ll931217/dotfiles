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

### Chezmoi Source State

The repository is migrating to chezmoi for home-directory configuration
management. The source root is `home/`, selected by `.chezmoiroot`.

Portable content is rendered into the home directory:

```text
home/dot_zshrc       -> ~/.zshrc
home/dot_tmux.conf   -> ~/.tmux.conf
home/dot_config/     -> ~/.config/
home/dot_scripts/    -> ~/.scripts/
```

`migration/source-manifest.yaml` records the intended source-to-target mapping
and identifies private, generated, platform-specific, and review-required
content.

### Installation

Use the repository entrypoint:

```bash
./install.sh
```

The entrypoint delegates to `bootstrap/install.sh`, which:

1. Installs chezmoi into a user-local location when necessary.
2. Initializes chezmoi against this repository.
3. Shows `chezmoi diff`.
4. Applies changes only after confirmation.

Useful modes:

```bash
./install.sh --dry-run
./install.sh --no-apply
./install.sh --force
```

Package installation is disabled by default. Configure
`home/.chezmoidata.toml` with `machine.install_packages = true` before
enabling the package hook. Optional AUR/Homebrew packages require
`machine.install_optional = true`.

### Provisioning Hooks

Chezmoi manages content; lifecycle hooks handle narrowly scoped side effects:

- `run_onchange_before_10-install-packages.sh.tmpl` installs declared packages.
- `run_after_20-refresh-font-cache.sh.tmpl` refreshes Linux font caches.
- `run_onchange_after_30-install-tmux-plugins.sh.tmpl` optionally updates TPM.

The older registry/state installer remains under `scripts/` during migration,
but it is no longer the default entrypoint. It should not be used alongside
chezmoi for the same targets.

### Platform and Private Configuration

Machine policy lives in chezmoi data rather than the legacy
`~/.config/dotfiles` state directory. OS and window-manager-specific content
is controlled with templates and `.chezmoiignore.tmpl`.

Plaintext credentials are excluded from source state. The existing
`.config/zsh/keys.zsh` values were imported into the local gopass store under
`dotfiles-secrets/`; the private chezmoi template reads them with `gopass`.
The old local file remains until gopass decryption is confirmed.

### Existing Configuration Patterns

**Theme consistency:** Catppuccin and Tokyo Night variants are shared across
terminal, editor, and utility configurations.

**Zsh modularity:** `~/.zshrc` delegates to `~/.config/zsh/.zshrc`, which loads
the modular `options.zsh`, `aliases.zsh`, `functions.zsh`, `keybinds.zsh`,
`theme.zsh`, `fzf.zsh`, `env.zsh`, and `utility.zsh` files.
