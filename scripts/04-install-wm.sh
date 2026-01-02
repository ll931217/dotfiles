#!/usr/bin/env bash
#
# Script 04: Install Window Manager and Display Manager
#

set -e

# Load DRY_RUN flag if set by parent
[[ -n "$DRY_RUN" ]] || DRY_RUN=false

# Source logging functions
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

log "=== Installing Window Manager and Display Manager ==="

# Install display manager if needed
if [[ "$INSTALL_DM" == true ]]; then
    log "Installing display manager: $DM"
    
    if [[ "$DM" == "sddm" ]]; then
        dry_run_cmd "sudo pacman -S --noconfirm sddm sddm-kcm"
        dry_run_cmd "sudo systemctl enable sddm.service"
        
        # Install sddm theme (optional)
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would install SDDM theme: sddm-sugar-candy-git"
            log "[DRY RUN] (would fall back to default if installation fails)"
        else
            yay -S --needed --noconfirm sddm-sugar-candy-git 2>/dev/null || {
                warn "Failed to install SDDM theme, using default"
            }
        fi
        
        success "SDDM installation completed"
        
    elif [[ "$DM" == "lightdm" ]]; then
        dry_run_cmd "sudo pacman -S --noconfirm lightdm lightdm-gtk-greeter"
        dry_run_cmd "sudo systemctl enable lightdm.service"
        success "LightDM installation completed"
        
    elif [[ "$DM" == "gdm" ]]; then
        dry_run_cmd "sudo pacman -S --noconfirm gdm"
        dry_run_cmd "sudo systemctl enable gdm.service"
        success "GDM installation completed"
    fi
else
    log "Skipping display manager installation (using existing: $DM)"
fi

# Install and configure window manager
if [[ "$WM" == "i3" ]]; then
    log "Installing i3-gaps and related packages..."
    
    I3_PACKAGES=(
        "i3-wm"
        "i3status"
        "i3lock"
        "i3blocks"
        "rofi"
        "picom"
        "feh"
        "xorg-server"
        "xorg-xinit"
        "xorg-xrandr"
        "xorg-xset"
        "xorg-xsetroot"
        "xorg-xprop"
        "xterm"
    )
    
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would install ${#I3_PACKAGES[@]} i3 packages:"
        for pkg in "${I3_PACKAGES[@]}"; do
            log "  - $pkg"
        done
        log "[DRY RUN] Would install AUR package: i3-scrot"
    else
        sudo pacman -S --noconfirm "${I3_PACKAGES[@]}"
        
        # Install AUR packages for i3
        yay -S --needed --noconfirm i3-scrot
    fi
    
    # Configure display manager for i3
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would configure display manager for i3"
        log "[DRY RUN]   Session file: /usr/share/xsessions/i3.desktop"
    else
        configure_dm_for_i3
    fi
    
    success "i3-gaps installation completed"
    
elif [[ "$WM" == "hyprland" ]]; then
    log "Installing Hyprland and related packages..."
    
    HYPRLAND_PACKAGES=(
        "hyprland"
        "waybar"
        "waybar-hyprland"
        "wlogout"
        "wlsunset"
        "kanshi"
        "swaybg"
        "rofi-wayland"
        "fuzzel"
    )
    
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would install ${#HYPRLAND_PACKAGES[@]} Hyprland packages:"
        for pkg in "${HYPRLAND_PACKAGES[@]}"; do
            log "  - $pkg"
        done
        log "[DRY RUN] Would install AUR packages: hyprlock, hypridle, hyprpaper"
    else
        sudo pacman -S --noconfirm "${HYPRLAND_PACKAGES[@]}"
        
        # Install AUR packages for Hyprland
        yay -S --needed --noconfirm hyprlock hypridle hyprpaper
    fi
    
    # Configure display manager for Hyprland
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would configure display manager for Hyprland"
        log "[DRY RUN]   Session file: /usr/share/wayland-sessions/hyprland.desktop"
    else
        configure_dm_for_hyprland
    fi
    
    success "Hyprland installation completed"
fi

# Configure input methods (Japanese/Chinese support if needed)
if [[ $DRY_RUN == true ]]; then
    log "[DRY RUN] Would install fcitx5 for input method support:"
    log "[DRY RUN]   - fcitx5-im"
    log "[DRY RUN]   - fcitx5-mozc"
    log "[DRY RUN]   - fcitx5-chinese-addons"
else
    log "Installing fcitx5 for input method support..."
    sudo pacman -S --noconfirm fcitx5-im fcitx5-mozc fcitx5-chinese-addons
fi

success "Window Manager and Display Manager installation script completed"

configure_dm_for_i3() {
    local dm_conf=""
    local session_file="/usr/share/xsessions/i3.desktop"
    
    if [[ -f "$session_file" ]]; then
        log "i3 session file found"
    else
        warn "i3 session file not found, may need manual configuration"
    fi
    
    # For sddm, ensure i3 is available as an option
    if systemctl is-enabled sddm.service &>/dev/null; then
        log "SDDM will offer i3 as a session option"
    fi
}

configure_dm_for_hyprland() {
    local dm_conf=""
    local session_file="/usr/share/wayland-sessions/hyprland.desktop"
    
    if [[ -f "$session_file" ]]; then
        log "Hyprland session file found"
    else
        warn "Hyprland session file not found, may need manual configuration"
    fi
    
    # For sddm, ensure hyprland is available as an option
    if systemctl is-enabled sddm.service &>/dev/null; then
        log "SDDM will offer Hyprland as a session option"
    fi
}
