#!/usr/bin/env bash
# Theme Consistency Checker
#
# Uses frontend-developer + frontend-design skill to validate theme consistency
# across all configuration files.
#
# Usage:
#   ./scripts/check-theme-consistency.sh [--theme <name>] [--fix] [--verbose]
#
# Options:
#   --theme <name>   Check specific theme (catppuccin, tokyonight, gruvbox, etc.)
#   --fix           Generate fixes for inconsistencies
#   --verbose       Show detailed analysis
#   --help          Show this help message

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Options
THEME_NAME=""
FIX=false
VERBOSE=false

# Theme color palettes (normalized for comparison)
declare -A THEME_COLORS=(
  # Catppuccin Mocha
  ["catppuccin_mocha_bg"]="#1e1e2e"
  ["catppuccin_mocha_fg"]="#cdd6f4"
  ["catppuccin_mocha_color1"]="#f38ba8"  # red
  ["catppuccin_mocha_color2"]="#a6e3a1"  # green
  ["catppuccin_mocha_color3"]="#f9e2af"  # yellow
  ["catppuccin_mocha_color4"]="#89b4fa"  # blue
  ["catppuccin_mocha_color5"]="#f5c2e7"  # pink
  ["catppuccin_mocha_color6"]="#94e2d5"  # cyan
  ["catppuccin_mocha_color7"]="#bac2de"  # comment

  # Tokyo Night
  ["tokyonight_bg"]="#1a1b26"
  ["tokyonight_fg"]="#c0caf5"
  ["tokyonight_color1"]="#f7768e"  # red
  ["tokyonight_color2"]="#9ece6a"  # green
  ["tokyonight_color3"]="#e0af68"  # yellow
  ["tokyonight_color4"]="#7aa2f7"  # blue
  ["tokyonight_color5"]="#bb9af7"  # purple
  ["tokyonight_color6"]="#7dcfff"  # cyan
  ["tokyonight_color7"]="#565f89"  # comment
)

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --theme)
      THEME_NAME="$2"
      shift 2
      ;;
    --fix)
      FIX=true
      shift
      ;;
    --verbose)
      VERBOSE=true
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
  echo -e "${GREEN}[PASS]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[FAIL]${NC} $1"
}

log_theme() {
  echo -e "${MAGENTA}[THEME]${NC} $1"
}

# Get repository root
get_repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || echo "$HOME/GitHub/dotfiles"
}

# Extract colors from config files
extract_colors_from_config() {
  local config_file="$1"
  local config_type="$2"

  case "$config_type" in
    alacritty|kitty|wezterm)
      # Extract colors from YAML/Lua configs
      grep -i "color" "$config_file" 2>/dev/null | grep -i "#[0-9a-fA-F]\{6\}" | sed 's/.*#\([0-9a-fA-F]\{6\}\).*/#\1/' || true
      ;;
    vim|nvim)
      # Extract colors from Vim/Lua configs
      grep -i "guifg\|guibg" "$config_file" 2>/dev/null | grep -i "#[0-9a-fA-F]\{6\}" | sed 's/.*#\([0-9a-fA-F]\{6\}\).*/#\1/' || true
      ;;
    zsh|starship)
      # Extract colors from shell configs
      grep -i "color" "$config_file" 2>/dev/null | grep -o "#[0-9a-fA-F]\{6\}" || true
      ;;
    *)
      # Generic hex color extraction
      grep -o "#[0-9a-fA-F]\{6\}" "$config_file" 2>/dev/null || true
      ;;
  esac
}

# Normalize color values
normalize_color() {
  local color="$1"
  # Convert to lowercase
  color=$(echo "$color" | tr '[:upper:]' '[:lower:]')
  # Ensure # prefix
  if [[ ! "$color" =~ ^# ]]; then
    color="#$color"
  fi
  echo "$color"
}

# Check if two colors are similar (within tolerance)
colors_match() {
  local color1="$1"
  local color2="$2"
  local tolerance="${3:-0}"

  # Remove # prefix for comparison
  color1="${color1#\#}"
  color2="${color2#\#}"

  # Simple string comparison (can be enhanced with color distance calculation)
  [[ "$color1" == "$color2" ]]
}

# Detect theme from config file
detect_config_theme() {
  local config_file="$1"

  # Check for theme indicators in file path or name
  local filename=$(basename "$config_file" | tr '[:upper:]' '[:lower:]')

  if [[ "$filename" =~ catppuccin ]]; then
    echo "catppuccin"
  elif [[ "$filename" =~ tokyo(night|_night) ]]; then
    echo "tokyonight"
  elif [[ "$filename" =~ gruvbox ]]; then
    echo "gruvbox"
  elif [[ "$filename" =~ dracula ]]; then
    echo "dracula"
  elif [[ "$filename" =~ nord ]]; then
    echo "nord"
  else
    # Try to detect from content
    if grep -qi "catppuccin" "$config_file" 2>/dev/null; then
      echo "catppuccin"
    elif grep -qi "tokyo.*night" "$config_file" 2>/dev/null; then
      echo "tokyonight"
    elif grep -qi "gruvbox" "$config_file" 2>/dev/null; then
      echo "gruvbox"
    else
      echo "unknown"
    fi
  fi
}

# Check individual config for theme consistency
check_config_theme() {
  local config_file="$1"
  local config_type="$2"
  local expected_theme="$3"

  local detected_theme=$(detect_config_theme "$config_file")
  local theme_match="false"
  local inconsistencies=()

  if [[ "$VERBOSE" == "true" ]]; then
    log_info "Checking: $config_file"
    log_info "  Detected: $detected_theme"
    log_info "  Expected: $expected_theme"
  fi

  # Check if theme matches
  if [[ "$detected_theme" == "$expected_theme" ]] || [[ "$expected_theme" == "" ]]; then
    theme_match="true"
  else
    inconsistencies+=("Theme mismatch: detected $detected_theme, expected $expected_theme")
  fi

  # Extract colors and validate
  local colors=$(extract_colors_from_config "$config_file" "$config_type")
  local color_count=$(echo "$colors" | wc -l)

  if [[ "$VERBOSE" == "true" && $color_count -gt 0 ]]; then
    log_info "  Found $color_count unique colors"
  fi

  # Return results
  echo "$config_file|$config_type|$theme_match|${inconsistencies[*]}"
}

# Scan all configs for theme consistency
scan_all_configs() {
  local repo_root=$(get_repo_root)
  local config_base="$repo_root/.config"
  local detected_theme=""

  log_info "Scanning configurations for theme consistency..."
  echo ""

  # First pass: detect the most common theme
  declare -a theme_counts
  local theme_map=""

  # Check common config directories
  local configs_to_check=(
    "alacritty:alacritty"
    "kitty:kitty"
    "nvim:nvim"
    "zsh:.zshrc"
    "starship:starship.toml"
    "bat:bat"
    "fzf:fzf"
  )

  # Detect theme across all configs
  for config_pair in "${configs_to_check[@]}"; do
    local config_name="${config_pair%%:*}"
    local config_file="${config_pair##*:}"
    local full_path="$config_base/$config_file"

    if [[ -f "$full_path" ]]; then
      local theme=$(detect_config_theme "$full_path")
      if [[ "$theme" != "unknown" ]]; then
        theme_map="$theme_map$theme|"
      fi
    fi
  done

  # Find most common theme
  if [[ -n "$theme_map" ]]; then
    # Convert to array and find most frequent
    IFS='|' read -ra themes <<< "$theme_map"
    local max_count=0
    local common_theme=""

    for theme in "${themes[@]}"; do
      if [[ -n "$theme" ]]; then
        local count=$(echo "$theme_map" | grep -o "$theme" | wc -l)
        if [[ $count -gt $max_count ]]; then
          max_count=$count
          common_theme="$theme"
        fi
      fi
    done

    detected_theme="$common_theme"
  fi

  # Use provided theme if specified
  if [[ -n "$THEME_NAME" ]]; then
    detected_theme="$THEME_NAME"
  fi

  if [[ -z "$detected_theme" ]]; then
    log_warning "Could not detect a theme. Use --theme <name> to specify."
    return 1
  fi

  log_theme "Detected theme: ${detected_theme^}"
  echo ""

  # Second pass: check each config for consistency
  declare -a results=()
  local total_configs=0
  local consistent_configs=0
  local inconsistent_configs=0

  for config_pair in "${configs_to_check[@]}"; do
    local config_name="${config_pair%%:*}"
    local config_type="${config_pair##*:}"
    local full_path="$config_base/$config_type"

    if [[ -f "$full_path" ]]; then
      ((total_configs++))
      local result=$(check_config_theme "$full_path" "$config_type" "$detected_theme")

      local file="${result%%|*}"
      local rest="${result#*|}"
      local type="${rest%%|*}"
      local rest="${rest#*|}"
      local match="${rest%%|*}"
      local issues="${rest#*|}"

      results+=("$result")

      if [[ "$match" == "true" ]]; then
        ((consistent_configs++))
        log_success "$config_name ($config_type)"
      else
        ((inconsistent_configs++))
        log_error "$config_name ($config_type)"
        if [[ -n "$issues" ]]; then
          echo "  └─ $issues"
        fi
      fi
    fi
  done

  # Summary
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Theme Consistency Summary"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Theme: ${detected_theme^}"
  echo "Total configs checked: $total_configs"
  echo "Consistent: $consistent_configs"
  echo "Inconsistent: $inconsistent_configs"
  echo ""

  # Overall result
  if [[ $inconsistent_configs -eq 0 ]]; then
    log_success "All configs are consistent with $detected_theme theme!"
    return 0
  else
    log_warning "Some configs are inconsistent with $detected_theme theme"
    echo ""
    echo "Recommendations:"
    echo "  1. Review theme application in inconsistent configs"
    echo "  2. Consider using theme-specific config files"
    echo "  3. Run with --fix to generate suggested fixes"
    return 1
  fi
}

# Generate fix suggestions
generate_fixes() {
  local repo_root=$(get_repo_root)
  local config_base="$repo_root/.config"

  log_info "Generating fix suggestions..."

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Theme Fix Suggestions"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  # Suggest using frontend-design skill for proper theme application
  echo "For optimal theme consistency, use the frontend-design skill:"
  echo ""
  echo "  Skill(skill='frontend-design', args='Apply consistent ${THEME_NAME:-catppuccin} theme across all configs')"
  echo ""
  echo "This will:"
  echo "  - Analyze current theme application"
  echo "  - Generate consistent color schemes"
  echo "  - Provide specific config updates"
  echo ""

  # List config-specific suggestions
  echo "Config-specific updates:"
  echo ""

  local configs=(
    "alacritty:Update colors section in alacritty.yml"
    "kitty:Update color_scheme in kitty.conf"
    "nvim:Update colorscheme in init.lua"
    "zsh:Update LS_COLORS and prompt colors"
    "starship:Update palette in starship.toml"
    "bat:Update theme in config"
    "fzf:Update colors in fzf.zsh"
  )

  for suggestion in "${configs[@]}"; do
    local config="${suggestion%%:*}"
    local action="${suggestion##*:}"
    echo "  • $config: $action"
  done

  echo ""
}

# Main function
main() {
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Theme Consistency Checker"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  if [[ "$FIX" == "true" ]]; then
    generate_fixes
    exit 0
  fi

  # Scan all configs
  scan_all_configs
  local exit_code=$?

  # Offer fixes if inconsistencies found
  if [[ $exit_code -ne 0 ]]; then
    echo ""
    echo "Run with --fix to see suggested fixes."
  fi

  exit $exit_code
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
