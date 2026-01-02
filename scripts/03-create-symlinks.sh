#!/usr/bin/env bash
#
# Script 03: Create symlinks for dotfiles
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

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

create_symlink() {
    local source="$1"
    local target="$2"
    
    # Create parent directory if it doesn't exist
    local target_dir=$(dirname "$target")
    
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would create parent directory: $target_dir"
        log "[DRY RUN] Would create symlink: $target -> $source"
        
        if [[ -L "$target" ]]; then
            log "[DRY RUN]   (would remove existing symlink)"
        elif [[ -e "$target" ]]; then
            log "[DRY RUN]   (would backup existing file to ${target}.backup.$(date +%Y%m%d%H%M%S))"
        fi
        return 0
    fi
    
    mkdir -p "$target_dir"
    
    # Remove existing symlink or backup file
    if [[ -L "$target" ]]; then
        rm "$target"
        log "Removed existing symlink: $target"
    elif [[ -e "$target" ]]; then
        warn "Backing up existing file: $target"
        mv "$target" "${target}.backup.$(date +%Y%m%d%H%M%S)"
    fi
    
    # Create symlink
    ln -s "$source" "$target"
    success "Created symlink: $target -> $source"
}

log "=== Creating symlinks ==="

# Shell configuration
create_symlink "$REPO_ROOT/.zshrc" "$HOME/.zshrc"

# Tmux configuration
create_symlink "$REPO_ROOT/.tmux.conf" "$HOME/.tmux.conf"

# Vim configuration
create_symlink "$REPO_ROOT/.vimrc" "$HOME/.vimrc"
create_symlink "$REPO_ROOT/.vimrc.bundles" "$HOME/.vimrc.bundles"

# Scripts
create_symlink "$REPO_ROOT/.scripts" "$HOME/.scripts"

# Fonts directory (if not already copied)
if [[ ! -d "$HOME/.local/share/fonts" ]]; then
    create_symlink "$REPO_ROOT/.local/share/fonts" "$HOME/.local/share/fonts"
else
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Fonts directory exists, would skip symlink creation"
    fi
fi

# Wallpapers
create_symlink "$REPO_ROOT/.wallpapers" "$HOME/.wallpapers"

# Config directory
SOURCE_DIR="$REPO_ROOT/.config"
TARGET_DIR="${XDG_CONFIG_HOME:-$HOME/.config}"

# Get all entries in source config directory
mapfile -t entries < <(find "$SOURCE_DIR" -maxdepth 1 -mindepth 1 2>/dev/null)

if [[ $DRY_RUN == true ]]; then
    log "[DRY RUN] Would process ${#entries[@]} config entries"
fi

for item in "${entries[@]}"; do
    base=$(basename "$item")
    target="$TARGET_DIR/$base"
    
    # Skip certain configs that might be platform-specific
    if [[ "$base" == "gnome-terminal" ]]; then
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Skipping: $base (platform-specific)"
        fi
        continue
    fi
    
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would create symlink for config: $base"
    fi
    
    create_symlink "$item" "$target"
done

# Platform-specific configs
if [[ "$WM" == "hyprland" ]]; then
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Hyprland detected, would configure Wayland-specific configs"
    else
        log "Hyprland detected, configuring Wayland-specific configs..."
    fi
    # Hyprland configs will be handled in configure-wm.sh
else
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] i3 detected, would configure X11-specific configs"
    else
        log "i3 detected, configuring X11-specific configs..."
    fi
    # i3 configs will be handled in configure-wm.sh
fi

success "Symlinks creation script completed"
