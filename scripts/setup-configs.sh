#!/usr/bin/env bash
# Multi-Agent Configuration Setup System
#
# This script orchestrates the setup of various configurations using
# specialized agent assignments for different tool categories.
#
# Usage:
#   ./scripts/setup-configs.sh [--config <category>] [--dry-run] [--help]
#
# Options:
#   --config <category>  Setup specific config category (development, terminal, etc.)
#   --dry-run           Show what would be done without making changes
#   --help              Show this help message

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Options
DRY_RUN=false
SPECIFIC_CONFIG=""

# Configuration to specialized agent mappings
# Based on CATEGORIES.yaml structure
declare -A CONFIG_AGENTS=(
  # Development tools
  ["nvim"]="python-pro,javascript-pro"
  ["git"]="deployment-engine"
  ["ranger"]="python-pro"

  # Terminal & Shell
  ["alacritty"]="frontend-developer"
  ["kitty"]="frontend-developer"
  ["ghostty"]="frontend-developer"
  ["wezterm"]="frontend-developer"
  ["zsh"]="python-pro"
  ["starship"]="python-pro"

  # Window managers
  ["i3"]="devops-troubleshooter"
  ["hypr"]="devops-troubleshooter"
  ["awesome"]="devops-troubleshooter"
  ["skhd"]="devops-troubleshooter"
  ["yabai"]="devops-troubleshooter"

  # Applications
  ["qutebrowser"]="frontend-developer"
  ["yazi"]="python-pro"
  ["zathura"]="python-pro"
  ["mpv"]="python-pro"

  # System utilities
  ["tmux"]="python-pro"
  ["fzf"]="python-pro"
  ["bat"]="python-pro"
  ["ripgrep"]="python-pro"
)

# Configuration descriptions
declare -A CONFIG_DESCRIPTIONS=(
  ["nvim"]="Neovim text editor configuration with plugins"
  ["git"]="Git version control configuration"
  ["alacritty"]="Alacritty terminal emulator configuration"
  ["kitty"]="Kitty terminal emulator configuration"
  ["ghostty"]="Ghostty terminal emulator configuration"
  ["wezterm"]="WezTerm terminal emulator configuration"
  ["zsh"]="Zsh shell configuration with plugins"
  ["starship"]="Starship prompt configuration"
  ["i3"]="i3 window manager configuration"
  ["hypr"]="Hyprland window manager configuration"
  ["awesome"]="Awesome WM configuration"
  ["skhd"]="skhd hotkey daemon configuration"
  ["yabai"]="yabai tiling window manager"
  ["qutebrowser"]="qutebrowser browser configuration"
  ["yazi"]="yazi terminal file manager"
  ["zathura"]="zathura PDF viewer"
  ["mpv"]="mpv media player configuration"
  ["tmux"]="tmux terminal multiplexer"
  ["fzf"]="fzf fuzzy finder configuration"
  ["bat"]="bat cat alternative configuration"
  ["ripgrep"]="ripgrep grep alternative"
)

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --config)
      SPECIFIC_CONFIG="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help)
      sed -n '/^# Usage:/,/^$/p' "$0" | sed 's/^# //g' | sed 's/^#//g'
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Logging functions
log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[DONE]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[SKIP]${NC} $1"
}

log_dryrun() {
  echo -e "${CYAN}[DRY]${NC} $1"
}

# Get repository root
get_repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || echo "$HOME/GitHub/dotfiles"
}

# Setup a specific configuration
setup_config() {
  local config_name="$1"
  local config_dir="$2"
  local repo_root="$3"

  # Get assigned agents
  local agents="${CONFIG_AGENTS[$config_name]:-general-purpose}"
  local description="${CONFIG_DESCRIPTIONS[$config_name]:-$config_name configuration}"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Configuration: $config_name"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Description: $description"
  echo "Specialized Agents: $agents"
  echo "Source: $config_dir"
  echo ""

  # Check if config directory exists
  if [[ ! -d "$config_dir" ]]; then
    log_warning "Config directory not found: $config_dir"
    return 1
  fi

  # Dry run mode
  if [[ "$DRY_RUN" == "true" ]]; then
    log_dryrun "Would setup $config_name"
    log_dryrun "  Source: $config_dir"
    log_dryrun "  Agents: $agents"
    return 0
  fi

  # Setup actions based on config type
  case "$config_name" in
    nvim)
      setup_nvim_config "$config_dir" "$agents"
      ;;
    zsh)
      setup_zsh_config "$config_dir" "$agents"
      ;;
    git)
      setup_git_config "$config_dir" "$agents"
      ;;
    *)
      setup_generic_config "$config_name" "$config_dir" "$agents"
      ;;
  esac
}

# Setup Neovim configuration
setup_nvim_config() {
  local config_dir="$1"
  local agents="$2"

  log_info "Setting up Neovim configuration (agents: $agents)..."

  # Create symlinks for nvim config
  local nvim_config="$HOME/.config/nvim"
  local target_dir="$config_dir"

  if [[ -L "$nvim_config" ]]; then
    log_info "Removing existing symlink..."
    rm "$nvim_config"
  elif [[ -d "$nvim_config" && ! -L "$nvim_config" ]]; then
    log_warning "Backing up existing nvim config..."
    mv "$nvim_config" "${nvim_config}.backup.$(date +%s)"
  fi

  log_info "Creating symlink to nvim configuration..."
  ln -s "$target_dir" "$nvim_config"

  # Check if Python and Node.js are available for nvim plugins
  if command -v python3 &>/dev/null; then
    log_info "Python provider available"
  fi

  if command -v node &>/dev/null; then
    log_info "Node.js provider available"
  fi

  log_success "Neovim configuration setup complete"
}

# Setup Zsh configuration
setup_zsh_config() {
  local config_dir="$1"
  local agents="$2"

  log_info "Setting up Zsh configuration (agents: $agents)..."

  # Link zshrc
  local zshrc_source="$config_dir/.zshrc"
  local zshrc_target="$HOME/.zshrc"

  if [[ -f "$zshrc_source" ]]; then
    if [[ -L "$zshrc_target" ]]; then
      rm "$zshrc_target"
    elif [[ -f "$zshrc_target" ]]; then
      mv "$zshrc_target" "${zshrc_target}.backup.$(date +%s)"
    fi

    ln -s "$zshrc_source" "$zshrc_target"
    log_success "Zsh configuration linked"
  fi

  # Setup znap if not present
  local znap_dir="$HOME/.znap"
  if [[ ! -d "$znap_dir" ]]; then
    log_info "Installing znap (zsh plugin manager)..."
    git clone --depth 1 https://github.com/marlonrichert/zsh-snap.git "$znap_dir"
  fi
}

# Setup Git configuration
setup_git_config() {
  local config_dir="$1"
  local agents="$2"

  log_info "Setting up Git configuration (agents: $agents)..."

  # Link git config files
  local git_config_source="$config_dir/.gitconfig"
  local git_config_target="$HOME/.gitconfig"

  if [[ -f "$git_config_source" ]]; then
    if [[ -L "$git_config_target" ]]; then
      rm "$git_config_target"
    elif [[ -f "$git_config_target" ]]; then
      # Merge include file instead of replacing
      if ! grep -q "path = $(basename "$git_config_source")" "$git_config_target" 2>/dev/null; then
        echo "" >> "$git_config_target"
        echo "[include]" >> "$git_config_target"
        echo "  path = ~/.config/git/config" >> "$git_config_target"
      fi
    else
      ln -s "$git_config_source" "$git_config_target"
    fi
    log_success "Git configuration linked"
  fi
}

# Generic configuration setup
setup_generic_config() {
  local config_name="$1"
  local config_dir="$2"
  local agents="$3"

  log_info "Setting up $config_name configuration (agents: $agents)..."

  # Determine target location
  local target_base="$HOME/.config"
  local target_dir="$target_base/$config_name"

  # Create symlink
  if [[ -L "$target_dir" ]]; then
    rm "$target_dir"
  elif [[ -d "$target_dir" && ! -L "$target_dir" ]]; then
    mv "$target_dir" "${target_dir}.backup.$(date +%s)"
  fi

  ln -s "$config_dir" "$target_dir"
  log_success "$config_name configuration linked"
}

# List all available configurations
list_configs() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Available Configurations"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  # Group by category
  echo "📦 Development Tools:"
  for config in nvim git ranger; do
    if [[ -n "${CONFIG_AGENTS[$config]:-}" ]]; then
      local agents="${CONFIG_AGENTS[$config]}"
      local desc="${CONFIG_DESCRIPTIONS[$config]:-}"
      printf "  %-20s %-30s %s\n" "$config" "[$agents]" "$desc"
    fi
  done

  echo ""
  echo "🖥️  Terminal & Shell:"
  for config in alacritty kitty ghostty wezterm zsh starship; do
    if [[ -n "${CONFIG_AGENTS[$config]:-}" ]]; then
      local agents="${CONFIG_AGENTS[$config]}"
      local desc="${CONFIG_DESCRIPTIONS[$config]:-}"
      printf "  %-20s %-30s %s\n" "$config" "[$agents]" "$desc"
    fi
  done

  echo ""
  echo "🪟 Window Managers:"
  for config in i3 hypr awesome skhd yabai; do
    if [[ -n "${CONFIG_AGENTS[$config]:-}" ]]; then
      local agents="${CONFIG_AGENTS[$config]}"
      local desc="${CONFIG_DESCRIPTIONS[$config]:-}"
      printf "  %-20s %-30s %s\n" "$config" "[$agents]" "$desc"
    fi
  done

  echo ""
  echo "📱 Applications:"
  for config in qutebrowser yazi zathura mpv; do
    if [[ -n "${CONFIG_AGENTS[$config]:-}" ]]; then
      local agents="${CONFIG_AGENTS[$config]}"
      local desc="${CONFIG_DESCRIPTIONS[$config]:-}"
      printf "  %-20s %-30s %s\n" "$config" "[$agents]" "$desc"
    fi
  done

  echo ""
  echo "🔧 System Utilities:"
  for config in tmux fzf bat ripgrep; do
    if [[ -n "${CONFIG_AGENTS[$config]:-}" ]]; then
      local agents="${CONFIG_AGENTS[$config]}"
      local desc="${CONFIG_DESCRIPTIONS[$config]:-}"
      printf "  %-20s %-30s %s\n" "$config" "[$agents]" "$desc"
    fi
  done

  echo ""
}

# Main setup function
main() {
  local repo_root=$(get_repo_root)
  local config_base="$repo_root/.config"

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Multi-Agent Configuration Setup"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Repository: $repo_root"
  echo "Config Base: $config_base"
  echo ""

  if [[ "$DRY_RUN" == "true" ]]; then
    log_warning "DRY RUN MODE - No changes will be made"
    echo ""
  fi

  # If specific config requested, setup only that
  if [[ -n "$SPECIFIC_CONFIG" ]]; then
    local config_dir="$config_base/$SPECIFIC_CONFIG"
    setup_config "$SPECIFIC_CONFIG" "$config_dir" "$repo_root"
    exit $?
  fi

  # List available configs
  list_configs

  # Setup all available configs
  echo ""
  log_info "Setting up all available configurations..."

  local setup_count=0
  local skip_count=0

  for config_name in "${!CONFIG_AGENTS[@]}"; do
    local config_dir="$config_base/$config_name"

    if setup_config "$config_name" "$config_dir" "$repo_root"; then
      ((setup_count++))
    else
      ((skip_count++))
    fi
  done

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log_success "Setup complete: $setup_count configured, $skip_count skipped"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
