#!/usr/bin/env bash
#
# Script 02: Install fonts
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

# Helper function for dry-run execution
dry_run_cmd() {
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would execute: $*"
        return 0
    else
        eval "$@"
    fi
}

log "=== Installing fonts ==="

# Create font directories
log "Creating font directories..."
dry_run_cmd "mkdir -p '$HOME/.local/share/fonts'"
dry_run_cmd "mkdir -p '$HOME/.local/share/fonts/NFP'"

# Copy fonts from repo
log "Copying fonts from repository..."
if [[ -d "$REPO_ROOT/.local/share/fonts" ]]; then
    FONT_FILES=$(find "$REPO_ROOT/.local/share/fonts" -type f | wc -l)
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would copy $FONT_FILES font files from repository to $HOME/.local/share/fonts"
        log "[DRY RUN] Files include:"
        ls "$REPO_ROOT/.local/share/fonts" 2>/dev/null | head -10 | sed 's/^/[DRY RUN]   /'
        if [[ $(ls "$REPO_ROOT/.local/share/fonts" 2>/dev/null | wc -l) -gt 10 ]]; then
            log "[DRY RUN]   ... and $(( $(ls "$REPO_ROOT/.local/share/fonts" 2>/dev/null | wc -l) - 10 )) more files"
        fi
    else
        cp -r "$REPO_ROOT/.local/share/fonts"/* "$HOME/.local/share/fonts/" 2>/dev/null || true
        success "Copied fonts from repository"
    fi
else
    warn "Fonts directory not found in repository"
fi

# Download JetBrains Mono Nerd Font if not present
JETBRAINS_FONT="$HOME/.local/share/fonts/JetBrainsMonoNerdFont-Regular.ttf"
if [[ ! -f "$JETBRAINS_FONT" ]]; then
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would download JetBrains Mono Nerd Font"
        log "[DRY RUN] Steps:"
        log "[DRY RUN]   1. Clone nerd-fonts repository"
        log "[DRY RUN]   2. Sparse checkout JetBrainsMono"
        log "[DRY RUN]   3. Run install script"
    else
        log "Downloading JetBrains Mono Nerd Font..."
        FONT_DIR="$HOME/.local/share/fonts"
        mkdir -p "$FONT_DIR"
        
        cd /tmp
        rm -rf JetBrainsMono
        git clone --depth 1 --filter=blob:none --sparse https://github.com/ryanoasis/nerd-fonts.git
        cd nerd-fonts
        git sparse-checkout set patched-fonts/JetBrainsMono
        ./install.sh JetBrainsMono
        cd - >/dev/null
        rm -rf nerd-fonts
        
        success "JetBrains Mono Nerd Font installed"
    fi
else
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] JetBrains Mono Nerd Font already present at $JETBRAINS_FONT, would skip"
    else
        success "JetBrains Mono Nerd Font already present"
    fi
fi

# Download Hack Nerd Font if not present
HACK_FONT="$HOME/.local/share/fonts/HackNerdFont-Regular.ttf"
if [[ ! -f "$HACK_FONT" ]]; then
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would download Hack Nerd Font"
        log "[DRY RUN] Steps:"
        log "[DRY RUN]   1. Clone nerd-fonts repository"
        log "[DRY RUN]   2. Sparse checkout Hack"
        log "[DRY RUN]   3. Run install script"
    else
        log "Downloading Hack Nerd Font..."
        cd /tmp
        rm -rf nerd-fonts
        git clone --depth 1 --filter=blob:none --sparse https://github.com/ryanoasis/nerd-fonts.git
        cd nerd-fonts
        git sparse-checkout set patched-fonts/Hack
        ./install.sh Hack
        cd - >/dev/null
        rm -rf nerd-fonts
        
        success "Hack Nerd Font installed"
    fi
else
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Hack Nerd Font already present at $HACK_FONT, would skip"
    else
        success "Hack Nerd Font already present"
    fi
fi

# Install fontconfig for better font rendering
if ! pacman -Qq fontconfig &>/dev/null; then
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would install fontconfig"
    else
        sudo pacman -S --noconfirm fontconfig
    fi
fi

# Refresh font cache
if [[ $DRY_RUN == true ]]; then
    log "[DRY RUN] Would refresh font cache with: fc-cache -f $HOME/.local/share/fonts"
else
    log "Refreshing font cache..."
    fc-cache -f "$HOME/.local/share/fonts"
fi

success "Fonts installation script completed"
