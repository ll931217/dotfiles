#!/usr/bin/env bash
#
# Script 06: Install and configure NeoVim
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

log "=== Installing and configuring NeoVim ==="

# Install NeoVim
log "Installing NeoVim..."
NEOVIM_PACKAGES=("neovim" "nodejs" "npm" "python" "python-pip")

if [[ $DRY_RUN == true ]]; then
    log "[DRY RUN] Would install NeoVim and dependencies:"
    for pkg in "${NEOVIM_PACKAGES[@]}"; do
        log "  - $pkg"
    done
else
    sudo pacman -S --noconfirm "${NEOVIM_PACKAGES[@]}"
fi

# Install Node.js packages for NeoVim
log "Installing Node.js packages for NeoVim..."
NPM_PACKAGES=("@fsouza/prettierd" "eslint_d")

if [[ $DRY_RUN == true ]]; then
    log "[DRY RUN] Would install Node.js packages:"
    for pkg in "${NPM_PACKAGES[@]}"; do
        log "  - $pkg"
    done
else
    npm install -g "${NPM_PACKAGES[@]}"
fi

# Install Python packages for NeoVim
log "Installing Python packages for NeoVim..."
PYTHON_PACKAGES=("pynvim" "black" "isort" "mypy" "flake8" "pyright")

if [[ $DRY_RUN == true ]]; then
    log "[DRY RUN] Would install Python packages:"
    for pkg in "${PYTHON_PACKAGES[@]}"; do
        log "  - $pkg"
    done
else
    pip install --user "${PYTHON_PACKAGES[@]}"
fi

# Install pnpm if not already installed
if ! command -v pnpm &>/dev/null; then
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would install pnpm"
        log "[DRY RUN] Steps:"
        log "[DRY RUN]   1. Download and run pnpm install script"
        log "[DRY RUN]   2. Set global LTS version"
    else
        log "Installing pnpm..."
        curl -fsSL https://get.pnpm.io/install.sh | sh -
        export PATH="$HOME/.local/share/pnpm:$PATH"
        pnpm env use --global lts
        success "pnpm installed"
    fi
else
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] pnpm already installed, would skip"
    else
        success "pnpm already installed"
    fi
fi

# Backup existing NeoVim config
NEOVIM_BACKUP_DIRS=(
    "$HOME/.config/nvim"
    "$HOME/.local/share/nvim"
    "$HOME/.local/state/nvim"
)

for dir in "${NEOVIM_BACKUP_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would backup existing NeoVim config: $dir"
            log "[DRY RUN]   Would move to ${dir}.backup.$(date +%Y%m%d%H%M%S)"
        else
            log "Backing up existing NeoVim configuration: $dir"
            mv "$dir" "${dir}.backup.$(date +%Y%m%d%H%M%S)"
        fi
    fi
done

# Clone LazyVim configuration
log "Cloning LazyVim configuration..."
NVIM_CONFIG_DIR="$HOME/.config/nvim"

if [[ $DRY_RUN == true ]]; then
    log "[DRY RUN] Would clone LazyVim config to $NVIM_CONFIG_DIR"
    if command -v gh &>/dev/null; then
        log "[DRY RUN]   Using: gh repo clone ll931217/lazyvim_config"
    else
        log "[DRY RUN]   Using: git clone https://github.com/ll931217/lazyvim_config.git"
    fi
else
    if command -v gh &>/dev/null; then
        log "Using GitHub CLI to clone..."
        gh repo clone ll931217/lazyvim_config "$NVIM_CONFIG_DIR" 2>/dev/null || {
            log "GitHub CLI clone failed, falling back to git..."
            git clone https://github.com/ll931217/lazyvim_config.git "$NVIM_CONFIG_DIR"
        }
    else
        log "Using git to clone..."
        git clone https://github.com/ll931217/lazyvim_config.git "$NVIM_CONFIG_DIR"
    fi
fi

# Install LazyVim plugins
log "Installing NeoVim plugins..."
if [[ $DRY_RUN == true ]]; then
    log "[DRY RUN] Would install NeoVim plugins with: nvim --headless '+Lazy! sync' +qa"
    log "[DRY RUN]   This would download and install all plugins"
else
    nvim --headless "+Lazy! sync" +qa 2>/dev/null || {
        warn "Plugin installation encountered issues, but NeoVim should work"
        warn "Run 'nvim' and then ':Lazy sync' to install plugins manually"
    }
fi

success "NeoVim installation script completed"

if [[ $DRY_RUN == false ]]; then
    log "Your NeoVim configuration: ~/.config/nvim"
    log "Run 'nvim' to start using LazyVim"
fi
