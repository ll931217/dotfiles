#!/usr/bin/env bash
#
# Script 01: Install core dependencies
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load DRY_RUN flag if set by parent
[[ -n "$DRY_RUN" ]] || DRY_RUN=false

# Source logging functions from main script
LOG_FILE="/tmp/dotfiles-install.log"

log() {
    echo -e "\033[0;34m[INFO]\033[0m $*" | tee -a "$LOG_FILE"
}

success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $*" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "\033[1;33m[WARNING]\033[0m $*" | tee -a "$LOG_FILE"
}

# Helper function for dry-run execution
dry_run_cmd() {
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would execute: $*"
        return 0
    else
        eval "$@"
    fi
}

log "=== Installing core dependencies ==="

# Update system
log "Updating system packages..."
dry_run_cmd "sudo pacman -Syu --noconfirm"

# Core utilities
log "Installing core utilities..."
PACKAGES=(
    "base-devel"
    "git"
    "curl"
    "wget"
    "unzip"
    "xz"
    "zip"
    "p7zip"
    "tree"
    "htop"
    "btop"
    "neofetch"
    "fastfetch"
    "ripgrep"
    "fd"
    "bat"
    "eza"
    "fzf"
    "jq"
    "zoxide"
    "atuin"
    "direnv"
    "ranger"
    "feh"
    "picom"
    "rofi"
    "dunst"
    "flameshot"
    "rofi-rbw"
    "playerctl"
    "brightnessctl"
    "xbacklight"
    "xclip"
    "xsel"
    "pavucontrol"
    "pipewire"
    "pipewire-pulse"
    "pipewire-alsa"
    "wireplumber"
    "networkmanager"
    "bluez"
    "bluez-utils"
    "openssh"
    "tmux"
    "starship"
    "noto-fonts"
    "noto-fonts-cjk"
    "adobe-source-han-sans-cn-fonts"
    "cantarell-fonts"
)

if [[ $DRY_RUN == true ]]; then
    log "[DRY RUN] Would install ${#PACKAGES[@]} core packages"
    for pkg in "${PACKAGES[@]}"; do
        log "  - $pkg"
    done
else
    sudo pacman -S --needed --noconfirm "${PACKAGES[@]}"
fi

# Install yay if not already installed
if ! command -v yay &>/dev/null; then
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would install yay (AUR helper)"
        log "  Steps: pacman -S base-devel git, clone yay AUR, makepkg -si"
    else
        log "Installing yay (AUR helper)..."
        sudo pacman -S --needed --noconfirm base-devel git
        cd /tmp
        rm -rf yay
        git clone https://aur.archlinux.org/yay.git
        cd yay
        makepkg -si --noconfirm
        cd - >/dev/null
        success "yay installed"
    fi
else
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] yay is already installed, would skip"
    else
        success "yay is already installed"
    fi
fi

# Install AUR packages
AUR_PACKAGES=(
    "rofi-rbw"
    "fuzzel"
    "waybar"
)

if [[ $DRY_RUN == true ]]; then
    log "[DRY RUN] Would install ${#AUR_PACKAGES[@]} AUR packages"
    for pkg in "${AUR_PACKAGES[@]}"; do
        log "  - $pkg"
    done
else
    yay -S --needed --noconfirm "${AUR_PACKAGES[@]}"
fi

success "Core dependencies installation script completed"
