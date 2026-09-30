[![MIT Licence](https://badges.frapsoft.com/os/mit/mit.svg?v=103)](https://opensource.org/licenses/mit-license.php)
[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badge/)

![LeetArch](https://i.imgur.com/z1yUurS.png)

# Setup

## Requirements

- i3, Eww, Rofi, and Dunst for the Linux desktop
- Python 3, libnotify, playerctl, and an existing PipeWire/PulseAudio session
- JetBrainsMono Nerd Font and Breeze icons
- Picom and feh for the personal desktop; no compositor for work/VDI

See [the desktop setup](#i3-desktop-and-workvdi-setup) for package and profile instructions.

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
home/dot_zshenv          -> ~/.zshenv
home/dot_tmux.conf       -> ~/.tmux.conf
home/dot_config/zsh/     -> ~/.config/zsh/
home/dot_config/         -> ~/.config/
home/dot_scripts/        -> ~/.scripts/
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

On first initialization, choose the machine profile independently of the
operating system:

- `work` renders the Antigen-based Zsh configuration.
- `personal` (the default) renders the Znap-based Zsh configuration.

The choice is stored only on that machine in
`~/.config/chezmoi/chezmoi.toml` as `data.machine.profile`. To change an
existing machine, run `chezmoi init` and select the other profile, or update
that value directly, then review `chezmoi diff` before applying.

Package installation is disabled by default. Configure
`data.machine.install_packages = true` in
`~/.config/chezmoi/chezmoi.toml` to enable the package hook. Package lists
live in `home/.chezmoidata.toml`. Optional AUR/Homebrew packages require
`data.machine.install_optional = true`. Eww is a required AUR package for
Arch i3 desktops and installs through `yay` even when optional packages
are disabled, provided package installation is enabled.

On Termux, run `bash install.sh`. Bootstrap installs chezmoi with `pkg`
when it is missing. Chezmoi identifies Termux as `android`; new setups
default to window manager `none`, and the package hook uses
`packages.android.termux` with `pkg install` (no sudo). Existing machine
choices are preserved when running `chezmoi init` again.

### i3 desktop and work/VDI setup

Both i3 profiles use an Eww bar and control panel, opaque Amp colors,
JetBrainsMono Nerd Font, Breeze icons, and matching Rofi/Dunst styling.
The bar replaces i3bar/i3status, Polybar, and i3blocks. Eww discovers active
outputs and reconciles bars after display disconnects/reconnects; the tray
appears on the primary output with vertically centered icons.
Personal keeps Picom animations. Work starts no compositor, uses no
GPU-specific settings or fixed output names, and is intended for X11 VDI
sessions. Remote-session behavior still needs verification on the target VDI.

| Shortcut | Action |
| --- | --- |
| Super+B | Toggle the control panel (music, volume, calendar, notifications) |
| Super+Tab | Search open windows with Rofi |
| Super+N | Recall the last notification |
| Super+Ctrl+N | Pause/resume notifications |
| Volume keys | Adjust audio with a progress notification |
| Super+Shift+X (work) | Lock with i3lock |

For an existing chezmoi checkout on an Arch work machine, install the desktop
dependencies first. Keep the existing audio server; the controls use `wpctl`
when available and fall back to `pactl`.

```bash
sudo pacman -S --needed i3-wm dunst rofi python libnotify playerctl libpulse \
  breeze-icons ttf-jetbrains-mono-nerd xterm i3lock
yay -S --needed eww
chezmoi edit-config
```

Set these keys in the existing `[data.machine]` table, preserving its other keys:

```toml
[data.machine]
profile = "work"
wm = "i3"
type = "desktop"
```

Apply only the desktop files; this skips provisioning scripts and unrelated
shell/private configuration. Run the following in Bash or Zsh:

```bash
mkdir -p ~/.config/{i3,eww,rofi,dunst}
chezmoi diff --include=files --exclude=scripts ~/.config/i3/config \
  ~/.config/eww ~/.config/rofi/config.rasi ~/.config/rofi/amp.rasi ~/.config/dunst/dunstrc
chezmoi apply --include=files --exclude=scripts ~/.config/i3/config \
  ~/.config/eww ~/.config/rofi/config.rasi ~/.config/rofi/amp.rasi ~/.config/dunst/dunstrc
i3 -C -c ~/.config/i3/config
```

After validation succeeds, activate inside the work i3 session:

```bash
pkill -x picom || true
i3-msg reload
python3 ~/.config/eww/bar.py start
dunstctl reload || (dunst -config ~/.config/dunst/dunstrc >/dev/null 2>&1 &)
```

Verify the panel, audio, tray alignment, and display reconnects before removing
old bar packages. On Arch, run `pacman -Q polybar i3status i3blocks`, then
`sudo pacman -Rns` with only the installed, replaced package names; review the
removal list. Keep `i3-wm`: it also supplies i3bar, which is simply unused.
On other distributions, install native equivalents and an X11-capable Eww
build manually; the repository package hook currently supports Arch Linux only.

### Yazi browser file picker (personal i3 desktops)

On Arch Linux, initialize with `profile = "personal"`, `wm = "i3"`,
`install_packages = true`, and `install_optional = true`. The package hook
installs Yazi, the GTK portal, xterm, Zenity, and the AUR package
`xdg-desktop-portal-termfilechooser-boydaihungst-git` (requires `yay`).
Keep these values under `[data.machine]` in `~/.config/chezmoi/chezmoi.toml`.
For an existing checkout, review `chezmoi diff`, then run `chezmoi apply`.
Package installation remains opt-in; without the optional backend, file
selection falls back to GTK when `xdg-desktop-portal-gtk` is installed.
If you disable package installation, install the listed dependencies yourself.

Browser upload/open dialogs use Yazi in a floating `st` window, or xterm
when st is unavailable. Press Enter to accept a file; use Space to select
several files, then Enter. Press `q` to cancel a file request. For folder
requests, enter the folder and press `q` to accept it; `Shift+Q` cancels.
Save As dialogs use Zenity with overwrite confirmation. This does not
change the default application for opening folders.

Routing lives in `~/.config/xdg-desktop-portal/i3-portals.conf`; other
portal interfaces continue to use GTK. The picker configuration and wrapper
are excluded from work, non-i3, and non-Linux profiles. Other Linux
distributions need equivalent packages installed manually.

The refresh hook reloads the portals and i3 during an active i3 session.
For headless provisioning, log into i3 afterward. Restart the browser if it
cached the old picker. Firefox/Zen additionally need
`widget.use-xdg-desktop-portal.file-picker = 1` in `about:config`.

Lutris launches from the application menu with `GTK_USE_PORTAL=1` via a
managed user desktop entry. Fully quit and reopen Lutris for it to take
effect. Direct terminal launches still need `GTK_USE_PORTAL=1 lutris`.

Verify wrapper behavior with `bash scripts/check-yazi-file-picker.sh`.
For a live check, click a browser file input, select a harmless file in
Yazi, and confirm the selected filename appears in the page.

### Provisioning Hooks

Chezmoi manages content; lifecycle hooks handle narrowly scoped side effects:

- `run_onchange_before_10-install-packages.sh.tmpl` installs declared packages.
- `run_after_20-refresh-font-cache.sh.tmpl` refreshes Linux font caches.
- `run_onchange_after_30-install-tmux-plugins.sh.tmpl` optionally updates TPM.
- `run_onchange_after_40-refresh-file-picker.sh.tmpl` refreshes the i3 file picker.

The older registry/state installer remains under `scripts/` during migration,
but it is no longer the default entrypoint. It should not be used alongside
chezmoi for the same targets.

### Platform and Private Configuration

Machine policy lives in chezmoi data rather than the legacy
`~/.config/dotfiles` state directory. OS and window-manager-specific content
is controlled with templates and `.chezmoiignore.tmpl`.

Plaintext credentials are excluded from source state. The former
`.config/zsh/keys.zsh` values were imported into the local gopass store under
`dotfiles-secrets/`; the private chezmoi template reads them with `gopass`.
The former local plaintext file was removed after readback verification.

### Existing Configuration Patterns

**Theme consistency:** Catppuccin and Tokyo Night variants are shared across
terminal, editor, and utility configurations.

**Zsh modularity:** the minimal `~/.zshenv` bootstrap sets `ZDOTDIR`; every
other Zsh startup file lives under `~/.config/zsh/`. Chezmoi renders
`~/.config/zsh/.zshrc` from either the work or personal profile, and both
profiles load their portable modules from that directory. There is no
`~/.zshrc` shim.
