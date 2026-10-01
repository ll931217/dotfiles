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
Menu opens the panel above the clicked bar on that monitor; clicking again
closes it, and clicking the other monitor's Menu moves it there. Super+B uses
the focused monitor. The panel scrolls on small displays; local X11 tests cover
800×600 and 1024×768 without a compositor.
Personal keeps Picom animations. Work starts no compositor, uses no
GPU-specific settings or fixed output names, and is intended for X11 VDI
sessions. Remote-session behavior still needs verification on the target VDI.

| Shortcut | Action |
| --- | --- |
| Super+B | Toggle controls, network selection, AI limits, and calendar |
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

On Ubuntu, build Eww with X11 support and link it into a directory on i3's
`PATH`. i3 does not inherit `~/.cargo/bin` from the login shell, and
`bar.py start` exits silently when `eww` is missing, leaving no bar.

```bash
sudo apt install rustup libgtk-3-dev libdbusmenu-gtk3-dev
rustup default stable   # Eww pins Rust 1.81; apt's cargo package is 1.75
cargo install --locked --git https://github.com/elkowar/eww \
  --no-default-features --features x11 eww
ln -s ~/.cargo/bin/eww ~/.local/bin/eww
python3 ~/.config/eww/bar.py start
eww --config ~/.config/eww active-windows   # expect one bar-<output> per screen
```

#### Network controls

On personal Arch/i3 desktops, the package hook installs `iwgtk` and
`polkit-gnome`. For an existing system using **systemd-networkd + iwd**:

```bash
sudo pacman -S --needed polkit-gnome
yay -S --needed iwgtk
sudo bash scripts/install-eww-network.sh  # Run from this repository's root.
```

Installation does not change connections or routes. The panel offers connected
physical NICs with simple, separate DHCP profiles in `/etc/systemd/network`.
Selecting a preferred NIC requires administrator authentication and persists
route metrics across reboots: 50 for the selected NIC, 600 for alternatives.
Other connections stay available. “Automatic” removes only these managed
overrides and restores the original priorities, including after a NIC is unplugged.
The current-default label refers to IPv4; the saved preference also sets IPv6
router-advertisement metrics. Wi-Fi networks opens iwgtk for scanning and
credential entry; Eww never handles Wi-Fi passwords.

Static routes, policy routing, shared profiles, and unrelated profile overrides
are left to the host administrator. Work/VDI needs no privileged helper or Wi-Fi
package; unsupported hosts display “Network managed by host.” The setup keeps
the existing network stack. Preference transactions, rollback, and cancellation
are tested with fixtures; setup verification does not switch the live route.

#### Claude Code and Codex limits

Codex reads quota metadata through its documented
[`account/rateLimits/read`](https://developers.openai.com/codex/app-server)
method, using the existing CLI login without starting an inference turn.
All returned quota windows retain their provider-reported duration and reset time.
The panel checks every 30 seconds while open; Codex responses are cached for
three minutes. Unavailable data stays unknown, and stale data is labelled.

Claude captures only quota percentages and reset times from its documented
[status-line input](https://code.claude.com/docs/en/statusline). After deploying
Eww, opt in on each machine that uses Claude Code:

```bash
python3 ~/.config/eww/claude_usage.py --install
# To restore the previous status line before removing Eww:
python3 ~/.config/eww/claude_usage.py --uninstall
```

The wrapper preserves the existing status-line renderer and forwards its input
unchanged. Claude limits appear after a subsequent Claude response supplies
quota data; unsupported accounts show an unavailable/waiting state. Private
quota caches live under `~/.cache/eww-usage`; the original renderer is saved under
`~/.local/state/eww-usage` (respecting XDG overrides). No credentials,
conversation text, or quota caches are committed to dotfiles.

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
