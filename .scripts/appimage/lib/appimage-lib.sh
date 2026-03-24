#!/bin/bash

# AppImage Management Library
# Common functions and utilities for AppImage management scripts

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Special characters
ARROW='➜'
STAR='★'
CHECK='✓'
CROSS='✗'
INFO='ℹ'
ROCKET='🚀'
PACKAGE='📦'
GEAR='⚙'

# Configuration
CONFIG_FILE="$HOME/.scripts/appimage/config.json"
APPS_DIR="$HOME/Applications"
DESKTOP_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons"
LOG_DIR="$HOME/.scripts/appimage/logs"

# Initialize directories
init_directories() {
    mkdir -p "$APPS_DIR"
    mkdir -p "$DESKTOP_DIR"
    mkdir -p "$ICONS_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$(dirname "$CONFIG_FILE")"
}

# Initialize config file if it doesn't exist or is empty
init_config() {
    if [ ! -f "$CONFIG_FILE" ] || [ ! -s "$CONFIG_FILE" ]; then
        echo '{"apps": []}' > "$CONFIG_FILE"
    fi
}

# Print functions
print_info() {
    echo -e "${BLUE}${INFO} $1${NC}"
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}${STAR} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_header() {
    echo -e "${WHITE}${GEAR} $1${NC}"
}

print_section() {
    echo -e "${PURPLE}${ARROW} $1${NC}"
}

print_download() {
    echo -e "${CYAN}${ROCKET} $1${NC}"
}

print_package() {
    echo -e "${GRAY}${PACKAGE} $1${NC}"
}

# Check dependencies
check_dependencies() {
    local missing=()

    if ! command -v jq &>/dev/null; then
        missing+=("jq")
    fi

    if ! command -v curl &>/dev/null; then
        missing+=("curl")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        print_error "Missing required dependencies: ${missing[*]}"
        print_info "Install them with: sudo apt install ${missing[*]}"
        return 1
    fi

    return 0
}

# Version comparison function
version_compare() {
    local version1=$1
    local version2=$2

    # Remove any non-numeric prefix (like 'v') if present
    version1=${version1#v}
    version2=${version2#v}

    # Split version numbers into arrays
    IFS='.' read -ra V1 <<< "$version1"
    IFS='.' read -ra V2 <<< "$version2"

    # Compare each part of the version
    for ((i=0; i<${#V1[@]}; i++)); do
        local num1=${V1[i]}
        local num2=${V2[i]:-0}  # Default to 0 if component doesn't exist

        # Extract numbers from strings (handles "1.2.3a" -> "123")
        num1=$(echo "$num1" | sed 's/[^0-9]//g')
        num2=$(echo "$num2" | sed 's/[^0-9]//g')

        if (( num1 < num2 )); then
            echo "less"
            return
        elif (( num1 > num2 )); then
            echo "greater"
            return
        fi
    done

    # Check if version2 has more components (all zero or not)
    if (( ${#V2[@]} > ${#V1[@]} )); then
        # Check if remaining components are all zeros
        local all_zero=true
        for ((i=${#V1[@]}; i<${#V2[@]}; i++)); do
            local component=${V2[i]}
            component=$(echo "$component" | sed 's/[^0-9]//g')
            if (( component > 0 )); then
                all_zero=false
                break
            fi
        done
        if [ "$all_zero" = "true" ]; then
            echo "equal"
        else
            echo "less"
        fi
    else
        echo "equal"
    fi
}

# Get current version from config
get_app_version() {
    local app_name=$1
    jq -r --arg name "$app_name" '.apps[] | select(.name == $name) | .version // empty' "$CONFIG_FILE" 2>/dev/null
}

# Update app version in config
update_app_version() {
    local app_name=$1
    local new_version=$2

    # Ensure config file exists and is valid
    if [ ! -f "$CONFIG_FILE" ]; then
        init_config
    fi

    # Check if it's valid JSON
    if ! jq empty "$CONFIG_FILE" 2>/dev/null; then
        print_warning "Config file is corrupted, reinitializing..."
        init_config
    fi

    # Check if app exists in config
    local app_exists=$(jq -r --arg name "$app_name" '.apps[] | select(.name == $name) | .name' "$CONFIG_FILE" 2>/dev/null)

    if [ -n "$app_exists" ]; then
        # Update existing entry
        local tmp_file=$(mktemp)
        if jq --arg name "$app_name" --arg version "$new_version" '(.apps[] | select(.name == $name)) |= .version = $version' "$CONFIG_FILE" > "$tmp_file" 2>/dev/null; then
            mv "$tmp_file" "$CONFIG_FILE"
            return 0
        else
            rm -f "$tmp_file"
            print_error "Failed to update version in config"
            return 1
        fi
    else
        # Add new entry to config
        print_warning "App '$app_name' not found in config. Use appimage-manager to add it first."
        return 1
    fi
}

# Add app to config
add_app_to_config() {
    local repo=$1
    local name=$2
    local pattern=$3
    local local_name=$4
    local version=${5:-""}

    # Ensure config file exists and is valid
    if [ ! -f "$CONFIG_FILE" ]; then
        init_config
    fi

    # Check if it's valid JSON
    if ! jq empty "$CONFIG_FILE" 2>/dev/null; then
        print_warning "Config file is corrupted, reinitializing..."
        init_config
    fi

    local tmp_file=$(mktemp)
    if jq --arg repo "$repo" \
      --arg name "$name" \
      --arg pattern "$pattern" \
      --arg local_name "$local_name" \
      --arg version "$version" \
      '.apps += [{
             "repo": $repo,
             "name": $name,
             "pattern": $pattern,
             "local_name": $local_name,
             "version": $version
         }]' "$CONFIG_FILE" > "$tmp_file" 2>/dev/null; then
        mv "$tmp_file" "$CONFIG_FILE"
        return 0
    else
        rm -f "$tmp_file"
        print_error "Failed to add app to config"
        return 1
    fi
}

# Remove app from config
remove_app_from_config() {
    local app_name=$1

    # Ensure config file exists and is valid
    if [ ! -f "$CONFIG_FILE" ]; then
        print_warning "Config file not found"
        return 1
    fi

    # Check if it's valid JSON
    if ! jq empty "$CONFIG_FILE" 2>/dev/null; then
        print_warning "Config file is corrupted, cannot remove app"
        return 1
    fi

    local tmp_file=$(mktemp)
    if jq --arg name "$app_name" 'del(.apps[] | select(.name == $name))' "$CONFIG_FILE" >"$tmp_file" 2>/dev/null; then
        mv "$tmp_file" "$CONFIG_FILE"
        return 0
    else
        rm -f "$tmp_file"
        print_error "Failed to remove app from config"
        return 1
    fi
}

# Get app config
get_app_config() {
    local app_name=$1
    jq -r --arg name "$app_name" '.apps[] | select(.name == $name)' "$CONFIG_FILE" 2>/dev/null
}

# List all apps (returns formatted output)
list_apps() {
    jq -r '.apps[] | "\(.name)|\(.repo)|\(.pattern)|\(.local_name)|\(.version // "")"' "$CONFIG_FILE" 2>/dev/null
}

# List all apps (raw output for piping)
list_apps_raw() {
    jq -r '.apps[] | "\(.name)|\(.repo)|\(.pattern)|\(.local_name)|\(.version // "")"' "$CONFIG_FILE" 2>/dev/null
}

# Validate repo format
validate_repo_format() {
    local repo=$1
    if [[ ! $repo =~ ^[^/]+/[^/]+$ ]]; then
        print_error "Invalid repository format. Use 'owner/repo'"
        return 1
    fi
    return 0
}

# Logging function
log_operation() {
    local operation=$1
    local app_name=$2
    local status=$3
    local message=${4:-""}

    local log_file="$LOG_DIR/operations.log"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] [$operation] [$app_name] [$status] $message" >> "$log_file"
}

# Download with retry
download_with_retry() {
    local url=$1
    local output=$2
    local max_retries=3
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if curl -L -o "$output" "$url"; then
            return 0
        fi

        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $max_retries ]; then
            print_warning "Download failed, retrying ($retry_count/$max_retries)..."
            sleep 2
        fi
    done

    print_error "Failed to download after $max_retries attempts"
    return 1
}

# Check if app is configured
is_app_configured() {
    local app_name=$1
    local app=$(get_app_config "$app_name")
    [ -n "$app" ]
}

# Get app count
get_app_count() {
    jq '.apps | length' "$CONFIG_FILE" 2>/dev/null
}

# Validate config file
validate_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Config file not found: $CONFIG_FILE"
        return 1
    fi

    # Check if it's valid JSON
    if ! jq empty "$CONFIG_FILE" 2>/dev/null; then
        print_error "Config file is not valid JSON"
        return 1
    fi

    # Check if it has apps array
    if ! jq -e '.apps' "$CONFIG_FILE" >/dev/null 2>&1; then
        print_error "Config file is missing apps array"
        return 1
    fi

    return 0
}
