# Dotfiles Installation Scripts

This directory contains automated installation scripts for setting up a complete development environment on Arch Linux with your dotfiles.

## Overview

The installation is modular and interactive, allowing you to customize your setup. The scripts will:
- Prompt you to choose between i3-gaps (X11) or Hyprland (Wayland)
- Detect and configure your display manager (SDDM by default)
- Automatically detect and configure multi-monitor setups
- Install all necessary dependencies
- Configure fonts, shell, and applications
- Work in both bare metal and VM environments

## Prerequisites

Before running the installation, ensure you have:
- A fresh Arch Linux installation (or Arch-based distro)
- Internet connection
- User account with sudo privileges
- Approximately 2-3 GB of free disk space

## Quick Start

```bash
cd ~/GitHub/dotfiles/scripts
./install.sh
```

### Dry Run Mode

Test the installation without making any changes to your system:

```bash
cd ~/GitHub/dotfiles/scripts
./install.sh --dry-run
```

See [DRY_RUN_GUIDE.md](DRY_RUN_GUIDE.md) for detailed information about dry-run mode.

The installation will guide you through interactive prompts.

## Installation Flow

The main `install.sh` script orchestrates the following steps:

### 1. **Main Installer** (`install.sh`)
- Validates environment (not root, detects VM)
- Installs yay (AUR helper) if needed
- Prompts for window manager selection
- Detects and configures display manager
- Detects connected monitors
- Runs all sub-scripts in sequence

### 2. **Dependencies** (`01-dependencies.sh`)
- Updates system packages
- Installs core utilities (git, curl, wget, etc.)
- Installs development tools (bat, eza, ripgrep, fd, fzf)
- Installs shell tools (zoxide, atuin, direnv, starship)
- Installs desktop applications (ranger, feh, rofi, picom, etc.)
- Installs AUR helper (yay)
- Installs AUR packages

### 3. **Fonts** (`02-fonts.sh`)
- Copies fonts from repository
- Downloads JetBrains Mono Nerd Font
- Downloads Hack Nerd Font
- Refreshes font cache

### 4. **Symlinks** (`03-create-symlinks.sh`)
- Creates symlinks for shell configurations (.zshrc, .tmux.conf, .vimrc)
- Links scripts directory
- Links wallpapers directory
- Links all .config entries (skipping gnome-terminal)
- Handles existing files by creating backups

### 5. **Window Manager** (`04-install-wm.sh`)
- Installs display manager (SDDM, LightDM, or GDM)
- Enables display manager service
- Installs i3-gaps OR Hyprland based on selection
- Installs WM-specific dependencies
- Configures display manager for chosen WM

### 6. **WM Configuration** (`05-configure-wm.sh`)
- **For i3-gaps**:
  - Configures multi-monitor or single-monitor setup
  - Adjusts workspace assignments
  - Configures i3status bar
  - Applies VM-specific optimizations (if in VM)
  - Creates i3status config
- **For Hyprland**:
  - Configures monitor layout
  - Creates/modifies Hyprland config
  - Configures Waybar
  - Applies VM-specific optimizations (if in VM)
  - Creates Waybar config and style

### 7. **NeoVim** (`06-neovim.sh`)
- Installs NeoVim
- Installs Node.js and Python packages for NeoVim
- Installs pnpm
- Backs up existing NeoVim config
- Clones LazyVim configuration
- Installs NeoVim plugins

## Features

### Window Manager Selection
Choose between:
- **i3-gaps**: Traditional X11 tiling window manager
- **Hyprland**: Modern Wayland tiling window manager with animations

### Display Manager Detection
The script:
- Detects existing display managers (SDDM, LightDM, GDM)
- Prompts to use existing or install SDDM
- Configures chosen display manager for your WM

### Multi-Monitor Support
Automatically detects and configures:
- Single monitor setups
- Dual monitor configurations
- Primary and secondary monitor assignment
- Workspace distribution across monitors

### VM Compatibility
When running in a VM, the script:
- Disables or reduces visual effects (blur, animations)
- Reduces gaps and borders
- Optimizes performance
- Maintains full functionality

## What Gets Installed

### Core Utilities
- Development tools: git, base-devel, jq
- Modern replacements: bat (cat), eza (ls), ripgrep (grep), fd (find)
- Shell enhancements: zoxide, atuin, direnv, starship
- System tools: htop, btop, neofetch, fastfetch, tree

### Desktop Environment
- **i3-gaps**: i3-wm, i3status, i3lock, rofi, picom, feh
- **Hyprland**: hyprland, hyprlock, hypridle, waybar, fuzzel
- **Both**: rofi, dunst, flameshot, playerctl, pavucontrol

### Fonts
- JetBrains Mono Nerd Font (primary terminal font)
- Hack Nerd Font (alternative)
- Noto Fonts (CJK support)
- Source Han Sans (Chinese/Japanese)
- Custom fonts from repository (SF Pro, Liga SF Mono)

### Applications
- File manager: ranger
- Terminal emulators: configured for alacritty, kitty, wezterm, ghostty
- Media: mpv, playerctl
- Screenshots: flameshot
- Input method: fcitx5 with Mozc and Chinese addons

### Editor
- NeoVim with LazyVim configuration
- Node.js, Python, and pnpm integration
- LSP support and code completion

## Configuration Files

After installation, your dotfiles will be symlinked to:
```
~/.zshrc                    → dotfiles/.zshrc
~/.tmux.conf                → dotfiles/.tmux.conf
~/.vimrc                    → dotfiles/.vimrc
~/.scripts                  → dotfiles/.scripts
~/.wallpapers               → dotfiles/.wallpapers
~/.config/                  → dotfiles/.config/*
```

## Monitor Detection

The script uses `xrandr` to detect connected monitors. The configuration automatically adapts:
- **Dual monitors**: Workspaces 1-9 on primary, 10 on secondary
- **Single monitor**: All workspaces on the single display
- **VM**: Single monitor configuration (even if multiple detected)

## Troubleshooting

### Installation Fails
Check the log file:
```bash
cat /tmp/dotfiles-install.log
```

### Fonts Not Showing
Refresh font cache manually:
```bash
fc-cache -f -v
```

### Display Manager Not Starting
Enable the service:
```bash
sudo systemctl enable sddm  # or lightdm/gdm
sudo systemctl start sddm
```

### NeoVim Plugins Not Installing
Open NeoVim and run:
```vim
:Lazy sync
```

### Monitor Configuration Incorrect
Edit the WM config manually:
- i3: `~/.config/i3/config`
- Hyprland: `~/.config/hypr/hyprland.conf`

## Customization

### Modify Packages
Edit `01-dependencies.sh` to add/remove packages.

### Change Fonts
Edit `02-fonts.sh` to download different fonts.

### Adjust WM Configuration
Edit the base configs in `dotfiles/.config/i3/` or `dotfiles/.config/hypr/` before running the installer.

### Skip Steps
Comment out unwanted scripts in `install.sh`:
```bash
# bash "$SCRIPT_DIR/06-neovim.sh"  # Skip NeoVim installation
```

## Uninstallation

To remove dotfiles and restore backups:
```bash
./uninstall.sh
```

This will:
- Remove all symlinks
- Restore backups if they exist
- Uninstall packages (optional)

## Post-Installation

After rebooting, you can:

1. **Set your shell to zsh** (if not already):
   ```bash
   chsh -s /bin/zsh
   ```

2. **Install any additional terminal emulators**:
   ```bash
   # For example
   sudo pacman -S alacritty kitty wezterm
   yay -S ghostty
   ```

3. **Customize your wallpaper**:
   ```bash
   # Use one of the included wallpapers
   feh --bg-scale ~/.wallpapers/your-image.jpg
   
   # Or use the random wallpaper script
   ~/.scripts/randwall.sh
   ```

4. **Configure browser**:
   - Install userChrome.css for Firefox customization
   - Copy `chrome/` directory to Firefox profile

5. **Start your workflow**:
   - Open terminal with `Mod + Enter` (i3) or `Super + Enter` (Hyprland)
   - Launch applications with `Mod + d` (i3) or `Super + E` (Hyprland)
   - Use workspaces `Mod/ + 1-0` for different tasks

## VM-Specific Notes

When testing in a VM:
- The script automatically detects VM environment
- Disables compositing effects for better performance
- Reduces visual animations
- Works with VirtualBox, VMware, QEMU/KVM

## Contributing

If you make improvements to these scripts:
1. Test on both bare metal and VM
2. Test with both i3-gaps and Hyprland
3. Test with single and multi-monitor setups
4. Update this README

## License

MIT License - See main repository for details.
