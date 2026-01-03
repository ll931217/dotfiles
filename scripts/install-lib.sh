#!/usr/bin/env bash
#
# Core library functions for dotfiles installation system
# Provides logging, detection, symlink operations, and system detection
#

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Internal logging helper
_log_to_file() {
    local input="$1"
    if [[ -n "$LOG_FILE" ]]; then
        echo -e "$input" | tee -a "$LOG_FILE" >&2
    else
        echo -e "$input" >&2
    fi
}

# Logging functions
log() {
    _log_to_file "${BLUE}[INFO]${NC} $*"
}

success() {
    _log_to_file "${GREEN}[SUCCESS]${NC} $*"
}

warn() {
    _log_to_file "${YELLOW}[WARNING]${NC} $*"
}

error() {
    _log_to_file "${RED}[ERROR]${NC} $*"
}

info() {
    _log_to_file "${CYAN}[INFO]${NC} $*"
}

# ============================================================================
# DETECTION FUNCTIONS
# ============================================================================

# Check if a symlink is installed and points to the repo
is_symlink_installed() {
    local source="$1"
    local target="$2"

    [[ -L "$target" ]] && [[ "$(readlink -f "$target")" == "$(readlink -f "$source")" ]]
}

# Check if a file exists
is_file_installed() {
    local target="$1"
    [[ -f "$target" ]]
}

# Check if a directory exists
is_dir_installed() {
    local target="$1"
    [[ -d "$target" ]]
}

# Check if a command is available
is_command_installed() {
    command -v "$1" &>/dev/null
}

# Check if a package is installed (pacman or yay)
is_package_installed() {
    local pkg="$1"
    pacman -Qi "$pkg" &>/dev/null || yay -Qi "$pkg" &>/dev/null
}

# Get status for any item based on hybrid detection (command-first, then file/symlink fallback)
get_item_status() {
    local item_name="$1"
    local item_var="ITEM_${item_name}"

    # Get binary name from [binary] field, fallback to lowercase item name
    local binary
    binary=$(get_item_value "$item_var" "binary")
    if [[ -z "$binary" ]]; then
        binary="${item_name,,}"  # Convert item name to lowercase for command
    fi

    # Try command detection first (primary method)
    if is_command_installed "$binary"; then
        return 0
    fi

    # Fallback to detection method (file/symlink/dir)
    local detection_method
    detection_method=$(get_item_value "$item_var" "detection")

    local config_path
    local target_path
    config_path=$(get_item_value "$item_var" "config_path")
    target_path=$(get_item_value "$item_var" "target_path")

    # Expand variables in paths (handle $REPO_ROOT, $HOME, etc.)
    if [[ -n "$config_path" ]]; then
        config_path="$(eval echo "$config_path")"
    fi
    if [[ -n "$target_path" ]]; then
        target_path="$(eval echo "$target_path")"
    fi

    case "$detection_method" in
        symlink)
            is_symlink_installed "$config_path" "$target_path"
            ;;
        file)
            is_file_installed "$target_path"
            ;;
        dir)
            is_dir_installed "$target_path"
            ;;
        package)
            is_package_installed "$item_name"
            ;;
        *)
            return 1
            ;;
    esac
}

# ============================================================================
# SYMLINK OPERATIONS
# ============================================================================

# Create a symlink with backup support
create_symlink() {
    local source="$1"
    local target="$2"

    # Create parent directory if it doesn't exist
    local target_dir
    target_dir=$(dirname "$target")

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

# Remove a symlink and restore from backup if available
remove_symlink() {
    local target="$1"

    if [[ ! -L "$target" ]]; then
        warn "Not a symlink: $target"
        return 1
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would remove symlink: $target"
        # Check for backup
        local backup
        backup=$(find "$(dirname "$target")" -name "$(basename "$target").backup.*" 2>/dev/null | sort -r | head -1)
        if [[ -n "$backup" ]]; then
            log "[DRY RUN] Would restore from: $backup"
        fi
        return 0
    fi

    rm "$target"
    log "Removed symlink: $target"

    # Restore from backup if exists
    local backup
    backup=$(find "$(dirname "$target")" -name "$(basename "$target").backup.*" 2>/dev/null | sort -r | head -1)
    if [[ -n "$backup" ]]; then
        mv "$backup" "$target"
        success "Restored from backup: $target"
    fi
}

# Create a timestamped backup of a file
backup_file() {
    local target="$1"

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would backup: $target"
        return 0
    fi

    if [[ -e "$target" ]]; then
        local backup_path="${target}.backup.$(date +%Y%m%d%H%M%S)"
        cp -a "$target" "$backup_path"
        success "Backed up: $target -> $backup_path"
        echo "$backup_path"
    fi
}

# ============================================================================
# SYSTEM DETECTION
# ============================================================================

# Detect machine type: laptop, desktop, server, or vm
detect_machine_type() {
    # Check if running in VM first
    if systemd-detect-virt &>/dev/null; then
        echo "vm"
        return 0
    fi

    # Check for server (no GUI)
    if ! systemctl is-active --quiet display-manager.service 2>/dev/null; then
        if ! [[ -e "/etc/systemd/system/display-manager.service" ]]; then
            echo "server"
            return 0
        fi
    fi

    # Check for laptop (mobile chassis)
    if [[ -d "/sys/class/power_supply" ]]; then
        local battery_count
        battery_count=$(find /sys/class/power_supply -name "BAT*" 2>/dev/null | wc -l)
        if [[ $battery_count -gt 0 ]]; then
            echo "laptop"
            return 0
        fi
    fi

    # Default to desktop
    echo "desktop"
    return 0
}

# Detect current environment: X11 or Wayland
detect_environment() {
    if [[ -n "$WAYLAND_DISPLAY" ]]; then
        echo "wayland"
    elif [[ -n "$DISPLAY" ]]; then
        echo "x11"
    else
        echo "headless"
    fi
}

# Detect running window manager
detect_running_wm() {
    local env
    env=$(detect_environment)

    case "$env" in
        wayland)
            if [[ -n "$HYPRLAND_INSTANCE_SIGNATURE" ]]; then
                echo "hyprland"
            elif pgrep -x "sway" >/dev/null; then
                echo "sway"
            else
                echo "unknown"
            fi
            ;;
        x11)
            if pgrep -x "i3" >/dev/null; then
                echo "i3"
            elif pgrep -x "i3-gaps" >/dev/null; then
                echo "i3-gaps"
            elif pgrep -x "openbox" >/dev/null; then
                echo "openbox"
            else
                echo "unknown"
            fi
            ;;
        *)
            echo "none"
            ;;
    esac
}

# Detect existing display manager
detect_display_manager() {
    if systemctl is-active --quiet display-manager.service 2>/dev/null; then
        local dm
        dm=$(systemctl status display-manager.service 2>/dev/null | grep "Loaded:" | grep -oP '/[\w-]+.service' | head -1 | cut -d'/' -f2 | cut -d'.' -f1 || echo "")
        if [[ -n "$dm" ]]; then
            echo "$dm"
        fi
    fi
}

# ============================================================================
# PACKAGE INSTALLATION
# ============================================================================

# Install packages using pacman or yay
install_packages() {
    local packages="$1"

    if [[ -z "$packages" ]]; then
        return 0
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would install packages: $packages"
        return 0
    fi

    log "Installing packages: $packages"

    # Check if yay is available
    if command -v yay &>/dev/null; then
        yay -S --needed --noconfirm $packages
    else
        sudo pacman -S --needed --noconfirm $packages
    fi
}

# Check if dependencies are satisfied
check_dependencies() {
    local item_name="$1"
    local item_var="ITEM_${item_name}"
    local deps

    deps=$(get_item_value "$item_var" "dependencies")

    if [[ -z "$deps" ]]; then
        return 0
    fi

    for dep in $deps; do
        if ! is_command_installed "$dep" && ! is_package_installed "$dep"; then
            warn "Missing dependency for $item_name: $dep"
            return 1
        fi
    done
    return 0
}

# ============================================================================
# ASSOCIATIVE ARRAY HELPERS
# ============================================================================

# Get value from associative array by indirect reference
# Usage: get_item_value ITEM_ZSH "name" -> returns "ZSH"
get_item_value() {
    local item_var="$1"
    local key="$2"
    local ref="${item_var}[${key}]"
    echo "${!ref}"
}

# ============================================================================
# MISC UTILITIES
# ============================================================================

# Confirm with user
confirm() {
    local prompt="$1"
    local default="${2:-Y}"

    local response
    read -rp "$prompt [$default] " response

    if [[ -z "$response" ]]; then
        response="$default"
    fi

    [[ "$response" =~ ^[Yy]$ ]]
}

# Check if running as root
check_not_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root. Run as regular user."
        exit 1
    fi
}

# Export functions for use in subshells
export -f log success warn error info
export -f is_symlink_installed is_file_installed is_dir_installed
export -f is_command_installed is_package_installed get_item_status
export -f create_symlink remove_symlink backup_file
export -f detect_machine_type detect_environment detect_running_wm detect_display_manager
export -f install_packages check_dependencies confirm check_not_root
