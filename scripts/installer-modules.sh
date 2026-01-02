#!/usr/bin/env bash
#
# Installation modules for dotfiles installation system
# Provides installation functions for each component type
#

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# GENERIC INSTALLER
# ============================================================================

# Generic installer for config-based items (symlinks)
install_config_item() {
    local item_name="$1"
    local item_var="ITEM_${item_name}"

    local config_path
    local target_path
    local packages

    config_path=$(get_item_value "$item_var" "config_path")
    target_path=$(get_item_value "$item_var" "target_path")
    packages=$(get_item_value "$item_var" "packages")

    # Expand variables (handle $REPO_ROOT, $HOME, etc.)
    local expanded_config
    local expanded_target
    expanded_config="$(eval echo "$config_path")"
    expanded_target="$(eval echo "$target_path")"

    # Check if already installed
    if get_item_status "$item_name"; then
        log "Already installed: $item_name (skipping)"
        return 0
    fi

    # Install packages if specified
    if [[ -n "$packages" ]]; then
        log "Installing packages for $item_name..."
        install_packages "$packages"
    fi

    # Create symlink if config path is set
    if [[ -n "$expanded_config" ]]; then
        create_symlink "$expanded_config" "$expanded_target"
    fi

    success "Installed: $item_name"
}

# ============================================================================
# SPECIALIZED INSTALLERS
# ============================================================================

# Install NeoVim (delegates to 06-neovim.sh)
install_neovim() {
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would install NeoVim with LazyVim config"
        return 0
    fi

    log "Installing NeoVim with LazyVim configuration..."
    bash "$SCRIPT_DIR/06-neovim.sh"
}

# Install fonts (delegates to 02-fonts.sh)
install_fonts() {
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would install system fonts"
        return 0
    fi

    log "Installing system fonts..."
    bash "$SCRIPT_DIR/02-fonts.sh"
}

# Install base dependencies (delegates to 01-dependencies.sh)
install_base_dependencies() {
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would install base dependencies"
        return 0
    fi

    log "Installing base dependencies..."
    bash "$SCRIPT_DIR/01-dependencies.sh"
}

# Install Window Manager (delegates to 04-install-wm.sh)
install_wm() {
    local wm="$1"  # I3 or HYPRLAND

    if [[ -z "$wm" ]]; then
        error "No WM specified"
        return 1
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would install window manager: $wm"
        return 0
    fi

    # Export WM for the script
    export WM="${wm,,}"

    log "Installing window manager: $wm..."
    bash "$SCRIPT_DIR/04-install-wm.sh"
}

# Configure Window Manager (delegates to 05-configure-wm.sh)
configure_wm() {
    local wm="$1"  # i3 or hyprland

    if [[ -z "$wm" ]]; then
        error "No WM specified"
        return 1
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would configure window manager: $wm"
        return 0
    fi

    # Export WM for the script
    export WM="${wm,,}"

    log "Configuring window manager: $wm..."
    bash "$SCRIPT_DIR/05-configure-wm.sh"
}

# ============================================================================
# ITEM ROUTER
# ============================================================================

# Route item to appropriate installer
install_item() {
    local item_name="$1"

    log "Processing: $item_name"

    # Check dependencies first
    if ! check_dependencies "$item_name"; then
        warn "Skipping $item_name due to missing dependencies"
        return 1
    fi

    # Check for module delegation
    local module="${ITEM_${item_name}[module]}"
    module="${!module}"

    if [[ -n "$module" ]]; then
        # Delegate to module script
        case "$item_name" in
            NEONVIM)
                install_neovim
                ;;
            FONTS)
                install_fonts
                ;;
            BASE_DEPS)
                install_base_dependencies
                ;;
            *)
                install_config_item "$item_name"
                ;;
        esac
    else
        # Special handling for window managers
        case "$item_name" in
            I3)
                install_wm "i3"
                configure_wm "i3"
                ;;
            HYPRLAND)
                install_wm "hyprland"
                configure_wm "hyprland"
                ;;
            *)
                install_config_item "$item_name"
                ;;
        esac
    fi
}

# ============================================================================
# BATCH OPERATIONS
# ============================================================================

# Install multiple items
install_items() {
    local items=("$@")
    local failed=()
    local succeeded=()

    # Initialize state and create snapshot before changes
    init_state

    # Create snapshot if not in dry-run mode
    if [[ $DRY_RUN == false ]]; then
        local snapshot_id
        snapshot_id=$(create_snapshot "pre-install" "${items[@]}")
        log "Created snapshot: $snapshot_id"
    fi

    for item in "${items[@]}"; do
        if install_item "$item"; then
            succeeded+=("$item")
            # Mark as installed in state
            if [[ $DRY_RUN == false ]]; then
                mark_item_installed "$item"
            fi
        else
            failed+=("$item")
        fi
    done

    # Update repository hash after installation
    if [[ $DRY_RUN == false ]]; then
        update_repo_hash
    fi

    # Summary
    echo ""
    echo "Installation Summary:"
    echo "  Succeeded: ${#succeeded[@]}"
    echo "  Failed: ${#failed[@]}"

    if [[ ${#succeeded[@]} -gt 0 ]]; then
        echo -e "${GREEN}✓${NC} ${succeeded[*]}"
    fi

    if [[ ${#failed[@]} -gt 0 ]]; then
        echo -e "${RED}✗${NC} ${failed[*]}"
    fi

    # Show snapshot info for rollback
    if [[ $DRY_RUN == false && ${#succeeded[@]} -gt 0 ]]; then
        echo ""
        log "To rollback, use: ./install.sh --rollback <snapshot-id>"
        log "Use --list-snapshots to see all snapshots"
    fi
}

# Update existing items (skip already installed)
update_items() {
    local items=("$@")

    # Initialize state
    init_state

    local snapshot_id
    snapshot_id=$(create_snapshot "pre-update" "${items[@]}")
    log "Created snapshot: $snapshot_id"

    for item in "${items[@]}"; do
        if get_item_status "$item"; then
            log "Updating: $item"
            # For now, just re-run install (idempotent for symlinks)
            install_item "$item"
        else
            log "Not installed, skipping: $item"
        fi
    done

    update_repo_hash

    log "To rollback, use: ./install.sh --rollback <snapshot-id>"
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

export -f install_config_item install_neovim install_fonts install_base_dependencies
export -f install_wm configure_wm install_item install_items update_items
