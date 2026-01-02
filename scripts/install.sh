#!/usr/bin/env bash
#
# Interactive dotfiles installation system
# Main entry point for installing and managing dotfiles configurations
#

set -e

# ============================================================================
# SCRIPT CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="/tmp/dotfiles-install.log"

# Mode flags
MODE="interactive"
DRY_RUN=false
CONFIG_ONLY=false
UPDATE_MODE=false

# Export for sub-scripts
export SCRIPT_DIR REPO_ROOT LOG_FILE DRY_RUN

# ============================================================================
# SOURCE LIBRARY FILES
# ============================================================================

source "$SCRIPT_DIR/install-lib.sh"
source "$SCRIPT_DIR/installer-registry.sh"
source "$SCRIPT_DIR/fzf-helpers.sh"
source "$SCRIPT_DIR/installer-modules.sh"
source "$SCRIPT_DIR/install-state.sh"
source "$SCRIPT_DIR/install-profiles.sh"
source "$SCRIPT_DIR/install-health.sh"
source "$SCRIPT_DIR/install-uninstall.sh"
source "$SCRIPT_DIR/install-secrets.sh"
source "$SCRIPT_DIR/install-machine-profiles.sh"

# ============================================================================
# CLI ARGUMENT PARSING
# ============================================================================

show_help() {
    cat << 'EOF'
Interactive Dotfiles Installation System

USAGE:
    ./install.sh [OPTIONS]

MODES:
    (no args)               Interactive mode (default)
    --full                  Install all components
    --update                Update existing installations
    --config-only           Only symlink configs, skip packages

QUICK COMMANDS:
    --status                Show installation dashboard
    --list                  List all available items
    --check, --health       Run health check

SAFETY MODES:
    --dry-run               Preview without changes
    --uninstall             Remove all installations
    --uninstall-items <...> Uninstall specific items
    --rollback <id>         Rollback to snapshot ID (use --list-snapshots)
    --list-snapshots        List available snapshots for rollback
    --cleanup               Clean up old backups and snapshots
    --state                 Show state summary

PROFILE MANAGEMENT:
    --profile-save <name>   Save current selection as profile
    --profile-load <name>   Load and install a profile
    --profile-list          List saved profiles
    --profile-delete <name> Delete a profile

MACHINE PROFILES:
    --machine-profile <name>    Set machine profile (laptop/desktop/server)
    --machine-profile-save      Save current as machine profile
    --machine-profile-show      Show machine profile details
    --detect-machine            Auto-detect machine type

SECRETS MANAGEMENT:
    --init-secrets             Initialize secrets management (pass + direnv)
    --add-secret <name>        Add a new secret
    --list-secrets             List all stored secrets
    --generate-direnv <dir>    Generate .envrc for directory

OTHER:
    -h, --help              Show this help message

EXAMPLES:
    ./install.sh                         # Interactive installation
    ./install.sh --full                  # Install everything
    ./install.sh --dry-run               # Preview changes
    ./install.sh --status                # Show what's installed
    ./install.sh --profile-load minimal  # Install saved profile
EOF
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --full)
                MODE="full"
                shift
                ;;
            --update)
                MODE="update"
                UPDATE_MODE=true
                shift
                ;;
            --config-only)
                CONFIG_ONLY=true
                shift
                ;;
            --status)
                MODE="status"
                shift
                ;;
            --list)
                MODE="list"
                shift
                ;;
            --check|--health)
                MODE="health"
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                LOG_FILE="/tmp/dotfiles-dryrun.log"
                shift
                ;;
            --uninstall)
                MODE="uninstall-all"
                shift
                ;;
            --uninstall-items)
                MODE="uninstall-items"
                shift
                # Collect remaining args as items to uninstall
                UNINSTALL_ITEMS=("$@")
                break
                ;;
            --cleanup)
                MODE="cleanup"
                shift
                ;;
            --rollback)
                MODE="rollback"
                ROLLBACK_ID="$2"
                shift 2
                ;;
            --list-snapshots)
                MODE="list-snapshots"
                shift
                ;;
            --state)
                MODE="state"
                shift
                ;;
            --profile-save)
                MODE="profile-save"
                PROFILE_NAME="$2"
                shift 2
                ;;
            --profile-load)
                MODE="profile-load"
                PROFILE_NAME="$2"
                shift 2
                ;;
            --profile-list)
                MODE="profile-list"
                shift
                ;;
            --profile-delete)
                MODE="profile-delete"
                PROFILE_NAME="$2"
                shift 2
                ;;
            --machine-profile)
                MODE="machine-profile"
                MACHINE_PROFILE="$2"
                shift 2
                ;;
            --machine-profile-save)
                MODE="machine-profile-save"
                shift
                ;;
            --machine-profile-show)
                MODE="machine-profile-show"
                shift
                ;;
            --detect-machine)
                MODE="detect-machine"
                shift
                ;;
            --init-secrets)
                MODE="init-secrets"
                shift
                ;;
            --add-secret)
                MODE="add-secret"
                SECRET_NAME="$2"
                shift 2
                ;;
            --list-secrets)
                MODE="list-secrets"
                shift
                ;;
            --generate-direnv)
                MODE="generate-direnv"
                DIRENV_DIR="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done
}

# ============================================================================
# MAIN INSTALLATION FLOW
# ============================================================================

# Interactive installation flow
install_interactive() {
    log "Starting interactive installation..."

    check_not_root

    # Detect system
    local machine_type
    machine_type=$(detect_machine_type)
    log "Detected machine type: $machine_type"

    # Select mode (install/update/uninstall/status)
    local selected_mode
    selected_mode=$(show_main_menu)

    case "$selected_mode" in
        "install")
            install_interactive_flow
            ;;
        "update")
            update_interactive_flow
            ;;
        "uninstall")
            warn "Uninstall not yet implemented"
            ;;
        "status")
            show_status_dashboard
            ;;
        "list")
            list_all_items
            ;;
        "health")
            run_health_check
            ;;
        "exit")
            log "Installation cancelled"
            exit 0
            ;;
    esac
}

# Interactive installation flow
install_interactive_flow() {
    # Select categories
    local selected_categories
    selected_categories=$(show_category_menu) || {
        log "No categories selected"
        return 1
    }

    # Select items from categories
    local selected_items
    selected_items=$(show_item_menu $selected_categories) || {
        log "No items selected"
        return 1
    }

    # Convert to array
    local items_array=()
    while IFS= read -r item; do
        [[ -n "$item" ]] && items_array+=("$item")
    done <<< "$selected_items"

    # Check for WM conflicts and resolve if needed
    if ! check_wm_conflicts "${items_array[@]}"; then
        local resolved_items
        resolved_items=$(resolve_wm_conflict "${items_array[@]}") || {
            log "Installation cancelled"
            return 1
        }

        # Rebuild array from resolved items
        items_array=()
        while IFS= read -r item; do
            [[ -n "$item" ]] && items_array+=("$item")
        done <<< "$resolved_items"
    fi

    # Show confirmation
    if ! show_confirmation "${items_array[@]}"; then
        log "Installation cancelled by user"
        return 0
    fi

    # Execute installation
    if [[ $DRY_RUN == true ]]; then
        log "========================================="
        log "DRY RUN MODE - No changes will be made"
        log "========================================="
        log ""
    fi

    log "Starting installation..."

    install_items "${items_array[@]}"

    echo ""
    if [[ $DRY_RUN == true ]]; then
        success "DRY RUN completed!"
        log "Run without --dry-run to perform actual installation"
    else
        success "Installation completed!"
        log "You may need to restart your shell or WM for changes to take effect"
    fi
}

# Interactive update flow
update_interactive_flow() {
    log "Starting interactive update..."

    # Select categories
    local selected_categories
    selected_categories=$(show_category_menu) || {
        log "No categories selected"
        return 1
    }

    # Select items from categories
    local selected_items
    selected_items=$(show_item_menu $selected_categories) || {
        log "No items selected"
        return 1
    }

    # Convert to array
    local items_array=()
    while IFS= read -r item; do
        [[ -n "$item" ]] && items_array+=("$item")
    done <<< "$selected_items"

    # Update items
    update_items "${items_array[@]}"

    success "Update completed!"
}

# Full installation (all items)
install_full() {
    log "Starting full installation..."

    check_not_root

    # Get all items
    local all_items=($(get_all_items))

    log "Installing ${#all_items[@]} items..."

    if ! show_confirmation "${all_items[@]}"; then
        log "Installation cancelled by user"
        return 0
    fi

    # Run original installation scripts for compatibility
    if [[ $DRY_RUN == true ]]; then
        log "========================================="
        log "DRY RUN MODE - No changes will be made"
        log "========================================="
        log ""
    fi

    log "Running full installation scripts..."

    bash "$SCRIPT_DIR/01-dependencies.sh"
    bash "$SCRIPT_DIR/02-fonts.sh"
    bash "$SCRIPT_DIR/03-create-symlinks.sh"
    bash "$SCRIPT_DIR/04-install-wm.sh"
    bash "$SCRIPT_DIR/05-configure-wm.sh"
    bash "$SCRIPT_DIR/06-neovim.sh"

    echo ""
    if [[ $DRY_RUN == true ]]; then
        success "DRY RUN completed!"
    else
        success "Full installation completed!"
        log "Please reboot to start using your new environment"
    fi
}

# ============================================================================
# HEALTH CHECK
# ============================================================================

# Wrapper for health check - dispatches to install-health.sh functions
run_health_check() {
    # Quick check first for fast feedback
    if run_quick_health_check; then
        # If quick check passes, run comprehensive check from install-health.sh
        # Call the comprehensive version
        local error_count=0

        # Run comprehensive checks
        check_all_symlinks || ((error_count++))
        check_packages || true  # Warnings are OK
        check_configs || true  # Warnings are OK
        check_dependencies_all || ((error_count++))
        check_shell_integration || true
        check_wm_integration || true
        check_editor_integration || true

        return $error_count
    else
        # Quick check failed - show errors
        return 1
    fi
}

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

main() {
    # Parse CLI arguments
    parse_arguments "$@"

    # Initialize log file
    echo "Dotfiles installation started: $(date)" > "$LOG_FILE"

    # Execute based on mode
    case "$MODE" in
        interactive)
            install_interactive
            ;;
        full)
            install_full
            ;;
        update)
            # For update mode, check if items were specified or use interactive
            if [[ ${#SELECTED_ITEMS[@]} -eq 0 ]]; then
                install_interactive
            else
                update_items "${SELECTED_ITEMS[@]}"
            fi
            ;;
        status)
            show_status_dashboard
            ;;
        list)
            list_all_items
            ;;
        health)
            run_health_check
            ;;
        uninstall-all)
            init_state
            uninstall_all
            ;;
        uninstall-items)
            if [[ ${#UNINSTALL_ITEMS[@]} -eq 0 ]]; then
                error "No items specified for uninstall"
                exit 1
            fi
            init_state
            uninstall_items "${UNINSTALL_ITEMS[@]}"
            ;;
        cleanup)
            init_state
            full_cleanup
            ;;
        rollback)
            if [[ -z "$ROLLBACK_ID" ]]; then
                error "Please specify a snapshot ID. Use --list-snapshots to see available snapshots."
                exit 1
            fi
            rollback_to_snapshot "$ROLLBACK_ID"
            ;;
        list-snapshots)
            list_snapshots
            ;;
        state)
            show_state_summary
            ;;
        profile-save)
            if [[ -z "$PROFILE_NAME" ]]; then
                error "Profile name is required"
                exit 1
            fi
            # Get items from state or prompt user
            error "Profile save requires interactive mode. Use --help for more info."
            exit 1
            ;;
        profile-load)
            if [[ -z "$PROFILE_NAME" ]]; then
                error "Profile name is required"
                exit 1
            fi
            init_state
            local profile_items
            profile_items=$(load_profile "$PROFILE_NAME")
            if [[ -z "$profile_items" ]]; then
                exit 1
            fi
            log "Loading profile: $PROFILE_NAME"
            show_profile_details "$PROFILE_NAME"
            if confirm "Install items from this profile?"; then
                local items_array=()
                while IFS= read -r item; do
                    [[ -n "$item" ]] && items_array+=("$item")
                done <<< "$profile_items"
                install_items "${items_array[@]}"
            fi
            ;;
        profile-list)
            list_profiles
            ;;
        profile-delete)
            if [[ -z "$PROFILE_NAME" ]]; then
                error "Profile name is required"
                exit 1
            fi
            delete_profile "$PROFILE_NAME"
            ;;
        machine-profile)
            if [[ -z "$MACHINE_PROFILE" ]]; then
                error "Profile name is required"
                exit 1
            fi
            init_state
            load_machine_profile "$MACHINE_PROFILE"
            ;;
        machine-profile-save)
            init_state
            save_machine_profile "$MACHINE_PROFILE"
            ;;
        machine-profile-show)
            if [[ -n "$MACHINE_PROFILE" ]]; then
                show_machine_profile "$MACHINE_PROFILE"
            else
                show_machine_profile
            fi
            ;;
        detect-machine)
            local machine_type
            machine_type=$(detect_machine_type)
            echo "Detected machine type: $machine_type"
            ;;
        init-secrets)
            init_secrets
            ;;
        add-secret)
            if [[ -z "$SECRET_NAME" ]]; then
                error "Secret name is required"
                exit 1
            fi
            init_secrets
            add_secret "$SECRET_NAME"
            ;;
        list-secrets)
            list_secrets
            ;;
        generate-direnv)
            if [[ -z "$DIRENV_DIR" ]]; then
                error "Directory is required"
                exit 1
            fi
            init_secrets
            generate_direnv "$DIRENV_DIR"
            ;;
        *)
            error "Unknown mode: $MODE"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
