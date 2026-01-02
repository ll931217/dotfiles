#!/usr/bin/env bash
#
# Uninstall script to remove dotfiles and restore backups
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="/tmp/dotfiles-uninstall.log"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
}

# List of symlinks to remove
SYMLINKS=(
    "$HOME/.zshrc"
    "$HOME/.tmux.conf"
    "$HOME/.vimrc"
    "$HOME/.vimrc.bundles"
    "$HOME/.scripts"
    "$HOME/.local/share/fonts"
    "$HOME/.wallpapers"
)

# Remove symlink and restore backup if exists
remove_symlink() {
    local target="$1"
    
    if [[ -L "$target" ]]; then
        log "Removing symlink: $target"
        rm "$target"
        
        # Check for backup
        local backup=$(ls -t "${target}.backup"* 2>/dev/null | head -1)
        if [[ -n "$backup" ]]; then
            log "Restoring backup: $backup"
            mv "$backup" "$target"
            success "Restored: $target"
        fi
    elif [[ -e "$target" ]]; then
        warn "Not a symlink, skipping: $target"
    fi
}

# Remove config directory symlinks
remove_config_symlinks() {
    local target_dir="${XDG_CONFIG_HOME:-$HOME/.config}"
    
    # List of configs to remove (from .config directory)
    local configs=(
        "zsh"
        "alacritty"
        "btop"
        "cava"
        "dunst"
        "fastfetch"
        "ghostty"
        "i3"
        "kitty"
        "picom.conf"
        "qutebrowser"
        "rofi"
        "rofi.conf"
        "starship.toml"
        "wezterm"
        "yazi"
    )
    
    for config in "${configs[@]}"; do
        local target="$target_dir/$config"
        if [[ -L "$target" ]]; then
            log "Removing config symlink: $target"
            rm "$target"
            
            # Check for backup
            local backup=$(ls -t "${target}.backup"* 2>/dev/null | head -1)
            if [[ -n "$backup" ]]; then
                log "Restoring backup: $backup"
                mv "$backup" "$target"
                success "Restored: $target"
            fi
        fi
    done
}

# Remove NeoVim config
remove_neovim() {
    log "Checking NeoVim configuration..."
    
    if [[ -L "$HOME/.config/nvim" ]]; then
        log "Removing NeoVim symlink..."
        rm "$HOME/.config/nvim"
        
        local backup=$(ls -t "$HOME/.config/nvim.backup"* 2>/dev/null | head -1)
        if [[ -n "$backup" ]]; then
            log "Restoring NeoVim backup: $backup"
            mv "$backup" "$HOME/.config/nvim"
            success "Restored NeoVim config"
        fi
    fi
    
    # Check if nvim was installed as a dependency and ask to remove
    if pacman -Qq neovim &>/dev/null; then
        read -p "Remove NeoVim package? [y/N] " remove_nvim
        if [[ $remove_nvim =~ ^[Yy]$ ]]; then
            sudo pacman -Rns --noconfirm neovim
            success "NeoVim package removed"
        fi
    fi
}

# Main uninstallation flow
main() {
    log "Starting dotfiles uninstallation..."
    log "Uninstallation log: $LOG_FILE"
    
    echo ""
    warn "This will remove your dotfiles symlinks and restore backups."
    warn "Your dotfiles repository will NOT be deleted."
    echo ""
    
    read -p "Continue? [y/N] " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log "Uninstallation cancelled"
        exit 0
    fi
    
    echo ""
    log "Removing symlinks..."
    
    for symlink in "${SYMLINKS[@]}"; do
        remove_symlink "$symlink"
    done
    
    echo ""
    log "Removing config symlinks..."
    remove_config_symlinks
    
    echo ""
    remove_neovim
    
    echo ""
    read -p "Remove installed packages? [y/N] " remove_packages
    if [[ $remove_packages =~ ^[Yy]$ ]]; then
        log "Removing installed packages..."
        
        # Remove i3 packages if installed
        if pacman -Qq i3-wm &>/dev/null; then
            log "Removing i3-gaps packages..."
            sudo pacman -Rns --noconfirm i3-wm i3status i3lock i3blocks rofi picom feh xorg-xinit 2>/dev/null || true
        fi
        
        # Remove Hyprland packages if installed
        if pacman -Qq hyprland &>/dev/null; then
            log "Removing Hyprland packages..."
            sudo pacman -Rns --noconfirm hyprland waybar hyprlock hypridle 2>/dev/null || true
        fi
        
        # Remove common packages
        log "Removing common packages..."
        sudo pacman -Rns --noconfirm \
            bat eza ripgrep fd fzf zoxide atuin direnv \
            ranger dunst flameshot playerctl pavucontrol \
            fcitx5-im fcitx5-mozc 2>/dev/null || true
        
        success "Packages removed"
    else
        log "Skipping package removal"
    fi
    
    echo ""
    read -p "Disable display manager? [y/N] " disable_dm
    if [[ $disable_dm =~ ^[Yy]$ ]]; then
        if systemctl is-enabled sddm.service &>/dev/null; then
            log "Disabling SDDM..."
            sudo systemctl disable sddm.service
            success "SDDM disabled"
        fi
        
        if systemctl is-enabled lightdm.service &>/dev/null; then
            log "Disabling LightDM..."
            sudo systemctl disable lightdm.service
            success "LightDM disabled"
        fi
        
        if systemctl is-enabled gdm.service &>/dev/null; then
            log "Disabling GDM..."
            sudo systemctl disable gdm.service
            success "GDM disabled"
        fi
    fi
    
    echo ""
    success "Uninstallation completed!"
    log "Uninstallation log: $LOG_FILE"
    echo ""
    log "Your dotfiles repository is preserved at: $REPO_ROOT"
    log "You can reinstall by running: cd $SCRIPT_DIR && ./install.sh"
    echo ""
}

# Run main function
main "$@"
