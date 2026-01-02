#!/usr/bin/env bash
#
# Machine profile management for dotfiles
# Different configurations for laptop, desktop, server, and VM
#

# Machine profiles directory
MACHINE_PROFILES_DIR="${STATE_DIR}/machines"

# ============================================================================
# MACHINE PROFILE DEFINITIONS
# ============================================================================

# Default configurations for each machine type
declare -A MACHINE_PROFILE_LAPTOP=(
    [type]="laptop"
    [preferred_wm]="hyprland"
    [power_management]="enabled"
    [battery_widget]="enabled"
    [bluetooth]="enabled"
    [wifi_tools]="enabled"
    [touchpad]="enabled"
    [multimonitor]="auto"
    [description]="Laptop configuration with power management and battery support"
)

declare -A MACHINE_PROFILE_DESKTOP=(
    [type]="desktop"
    [preferred_wm]="i3"
    [power_management]="disabled"
    [battery_widget]="disabled"
    [bluetooth]="optional"
    [wifi_tools]="optional"
    [touchpad]="disabled"
    [multimonitor]="enabled"
    [gaming_perf]="optional"
    [storage_large]="enabled"
    [description]="Desktop configuration with multi-monitor support"
)

declare -A MACHINE_PROFILE_SERVER=(
    [type]="server"
    [preferred_wm]="none"
    [power_management]="disabled"
    [battery_widget]="disabled"
    [bluetooth]="disabled"
    [wifi_tools]="optional"
    [touchpad]="disabled"
    [multimonitor]="disabled"
    [headless]="true"
    [minimal]="true"
    [sshd]="enabled"
    [description]="Minimal server configuration without WM"
)

declare -A MACHINE_PROFILE_VM=(
    [type]="vm"
    [preferred_wm]="i3"
    [power_management]="disabled"
    [battery_widget]="disabled"
    [bluetooth]="disabled"
    [wifi_tools]="disabled"
    [touchpad]="disabled"
    [multimonitor]="auto"
    [guest_tools]="enabled"
    [description]="Virtual machine configuration with guest tools"
)

# ============================================================================
# MACHINE PROFILE SAVE/LOAD
# ============================================================================

# Save current machine profile
save_machine_profile() {
    local profile_name="$1"

    if [[ -z "$profile_name" ]]; then
        # Auto-detect and use machine type as profile name
        profile_name=$(detect_machine_type)
    fi

    init_state
    mkdir -p "$MACHINE_PROFILES_DIR"

    local profile_file="${MACHINE_PROFILES_DIR}/${profile_name}.conf"

    log "Saving machine profile: $profile_name"

    cat > "$profile_file" << EOF
# Machine Profile: $profile_name
# Generated: $(date -Iseconds)

MACHINE_TYPE="$profile_name"
MACHINE_PROFILE_NAME="$profile_name"
EOF

    # Add machine-specific settings
    case "$profile_name" in
        laptop)
            cat >> "$profile_file" << 'EOF'
PREFERRED_WM="hyprland"
POWER_MANAGEMENT="enabled"
BATTERY_WIDGET="enabled"
BLUETOOTH="enabled"
WIFI_TOOLS="enabled"
EOF
            ;;
        desktop)
            cat >> "$profile_file" << 'EOF'
PREFERRED_WM="i3"
POWER_MANAGEMENT="disabled"
BATTERY_WIDGET="disabled"
MULTIMONITOR="enabled"
STORAGE_LARGE="enabled"
EOF
            ;;
        server)
            cat >> "$profile_file" << 'EOF'
PREFERRED_WM="none"
HEADLESS="true"
MINIMAL="true"
SSHD="enabled"
EOF
            ;;
        vm)
            cat >> "$profile_file" << 'EOF'
PREFERRED_WM="i3"
GUEST_TOOLS="enabled"
EOF
            ;;
    esac

    success "Machine profile saved: $profile_name"
    log "Profile file: $profile_file"
}

# Load a machine profile
load_machine_profile() {
    local profile_name="$1"

    if [[ -z "$profile_name" ]]; then
        error "Profile name is required"
        return 1
    fi

    local profile_file="${MACHINE_PROFILES_DIR}/${profile_name}.conf"

    if [[ ! -f "$profile_file" ]]; then
        error "Machine profile not found: $profile_name"
        return 1
    fi

    log "Loading machine profile: $profile_name"

    # Source the profile file
    source "$profile_file"

    success "Machine profile loaded: $profile_name"

    # Show profile details
    if [[ -n "$MACHINE_TYPE" ]]; then
        log "Machine Type: $MACHINE_TYPE"
    fi
    if [[ -n "$PREFERRED_WM" ]]; then
        log "Preferred WM: $PREFERRED_WM"
    fi
}

# Get recommended WM for machine type
get_recommended_wm() {
    local machine_type="$1"

    case "$machine_type" in
        laptop)
            echo "hyprland"
            ;;
        desktop)
            echo "i3"
            ;;
        server)
            echo "none"
            ;;
        vm)
            echo "i3"
            ;;
        *)
            echo "auto"
            ;;
    esac
}

# Show machine profile details
show_machine_profile() {
    local profile_name="$1"

    if [[ -z "$profile_name" ]]; then
        # Show detected machine type
        local detected
        detected=$(detect_machine_type)
        echo "Detected Machine Type: $detected"
        echo ""
        echo "Recommended WM: $(get_recommended_wm "$detected")"
        return 0
    fi

    local profile_file="${MACHINE_PROFILES_DIR}/${profile_name}.conf"

    if [[ ! -f "$profile_file" ]]; then
        error "Machine profile not found: $profile_name"
        return 1
    fi

    echo ""
    echo "Machine Profile: $profile_name"
    echo "================================"

    # Source and display profile
    source "$profile_file"

    if [[ -n "$MACHINE_TYPE" ]]; then
        echo "Type: $MACHINE_TYPE"
    fi
    if [[ -n "$PREFERRED_WM" ]]; then
        echo "Preferred WM: $PREFERRED_WM"
    fi
    if [[ -n "$POWER_MANAGEMENT" ]]; then
        echo "Power Management: $POWER_MANAGEMENT"
    fi
    if [[ -n "$BATTERY_WIDGET" ]]; then
        echo "Battery Widget: $BATTERY_WIDGET"
    fi
    if [[ -n "$MULTIMONITOR" ]]; then
        echo "Multi-Monitor: $MULTIMONITOR"
    fi
    if [[ -n "$HEADLESS" ]]; then
        echo "Headless Mode: $HEADLESS"
    fi

    echo ""
}

# List available machine profiles
list_machine_profiles() {
    echo ""
    echo "Available Machine Profiles:"
    echo ""

    init_state

    if [[ ! -d "$MACHINE_PROFILES_DIR" ]]; then
        echo "  No machine profiles found."
        echo ""
        echo "Create one with: ./install.sh --machine-profile-save <name>"
        return 0
    fi

    local profiles=()
    while IFS= read -r -d '' profile; do
        profiles+=("$(basename "$profile" .conf)")
    done < <(find "$MACHINE_PROFILES_DIR" -maxdepth 1 -name "*.conf" -print0 2>/dev/null | sort -z)

    if [[ ${#profiles[@]} -eq 0 ]]; then
        echo "  No machine profiles found."
        return 0
    fi

    # Show detected type
    local detected
    detected=$(detect_machine_type)
    echo "  Currently Detected: $detected"
    echo ""

    for profile in "${profiles[@]}"; do
        local profile_file="${MACHINE_PROFILES_DIR}/${profile}.conf"
        echo "  • $profile"

        # Show preferred WM from profile
        local wm
        wm=$(grep "^PREFERRED_WM=" "$profile_file" 2>/dev/null | cut -d'"' -f2)
        if [[ -n "$wm" ]]; then
            echo "    Preferred WM: $wm"
        fi
    done

    echo ""
}

# ============================================================================
# WM CONFLICT RESOLUTION
# ============================================================================

# Check for WM conflicts in selected items
check_wm_conflicts() {
    local selected_items=("$@")

    local has_i3=false
    local has_hyprland=false

    for item in "${selected_items[@]}"; do
        case "$item" in
            I3)
                has_i3=true
                ;;
            HYPRLAND)
                has_hyprland=true
                ;;
        esac
    done

    if [[ "$has_i3" == "true" && "$has_hyprland" == "true" ]]; then
        return 1  # Conflict detected
    fi

    return 0  # No conflict
}

# Resolve WM conflict interactively
resolve_wm_conflict() {
    local selected_items=("$@")

    warn "Window Manager Conflict Detected!"
    warn "You have selected both i3-gaps and Hyprland."
    warn "These cannot be installed simultaneously."
    echo ""

    local machine_type
    machine_type=$(detect_machine_type)

    local recommended_wm
    recommended_wm=$(get_recommended_wm "$machine_type")

    log "Recommended WM for $machine_type: $recommended_wm"
    echo ""

    # Show FZF menu for resolution
    local choice
    choice=$(printf "Use i3-gaps (X11)\nUse Hyprland (Wayland)\nUse Recommended: $recommended_wm\nCancel Installation" | \
        fzf \
            --height 30% \
            --prompt="Resolve conflict > " \
            --header "Select which Window Manager to install" \
            --border || echo "Cancel")

    case "$choice" in
        "Use i3-gaps (X11)"|"i3-gaps"|"i3")
            # Remove HYPRLAND from selection
            local new_items=()
            for item in "${selected_items[@]}"; do
                if [[ "$item" != "HYPRLAND" ]]; then
                    new_items+=("$item")
                fi
            done
            selected_items=("${new_items[@]}")
            log "Selected: i3-gaps"
            ;;
        "Use Hyprand (Wayland)"|"Hyprland"|"hyprland")
            # Remove I3 from selection
            local new_items=()
            for item in "${selected_items[@]}"; do
                if [[ "$item" != "I3" ]]; then
                    new_items+=("$item")
                fi
            done
            selected_items=("${new_items[@]}")
            log "Selected: Hyprland"
            ;;
        "Use Recommended: $recommended_wm"*)
            case "$recommended_wm" in
                i3)
                    local new_items=()
                    for item in "${selected_items[@]}"; do
                        if [[ "$item" != "HYPRLAND" ]]; then
                            new_items+=("$item")
                        fi
                    done
                    selected_items=("${new_items[@]}")
                    ;;
                hyprland)
                    local new_items=()
                    for item in "${selected_items[@]}"; do
                        if [[ "$item" != "I3" ]]; then
                            new_items+=("$item")
                        fi
                    done
                    selected_items=("${new_items[@]}")
                    ;;
            esac
            log "Selected: $recommended_wm (recommended for $machine_type)"
            ;;
        "Cancel Installation"|"Cancel"|"")
            return 1
            ;;
    esac

    # Output updated items list
    printf '%s\n' "${selected_items[@]}"
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

export -f save_machine_profile load_machine_profile
export -f get_recommended_wm show_machine_profile list_machine_profiles
export -f check_wm_conflicts resolve_wm_conflict
