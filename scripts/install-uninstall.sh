#!/usr/bin/env bash
#
# Uninstall system for dotfiles
# Remove installations and restore from backups
#

# ============================================================================
# ITEM UNINSTALL
# ============================================================================

# Uninstall a single item
uninstall_item() {
    local item_name="$1"

    log "Uninstalling: $item_name"

    local item_var="ITEM_${item}"
    local config_path
    local target_path
    local packages

    config_path=$(get_item_value "$item_var" "config_path")
    target_path=$(get_item_value "$item_var" "target_path")
    packages=$(get_item_value "$item_var" "packages")

    # Expand variables
    local expanded_target
    expanded_target="$(eval echo "$target_path")"

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would uninstall: $item_name"
        log "[DRY RUN] Would remove: $expanded_target"

        if [[ -n "$packages" ]]; then
            log "[DRY RUN] Would optionally remove packages: $packages"
        fi

        return 0
    fi

    # Check if item is installed
    if ! get_item_status "$item_name"; then
        warn "Item not installed: $item_name"
        return 0
    fi

    # Remove symlink or file
    if [[ -L "$expanded_target" ]]; then
        remove_symlink "$expanded_target"
    elif [[ -e "$expanded_target" ]]; then
        # Backup before removing if not a symlink
        backup_file "$expanded_target"
        rm -rf "$expanded_target"
        log "Removed: $expanded_target"
    fi

    # Mark as uninstalled in state
    mark_item_uninstalled "$item_name"

    success "Uninstalled: $item_name"
}

# Uninstall multiple items
uninstall_items() {
    local items=("$@")

    if [[ ${#items[@]} -eq 0 ]]; then
        error "No items specified for uninstall"
        return 1
    fi

    log "Uninstalling ${#items[@]} item(s)..."

    # Create snapshot before uninstall
    local snapshot_id
    snapshot_id=$(create_snapshot "pre-uninstall" "${items[@]}")
    log "Created snapshot: $snapshot_id"

    local failed=()
    local succeeded=()

    for item in "${items[@]}"; do
        if uninstall_item "$item"; then
            succeeded+=("$item")
        else
            failed+=("$item")
        fi
    done

    # Summary
    echo ""
    echo "Uninstall Summary:"
    echo "  Succeeded: ${#succeeded[@]}"
    echo "  Failed: ${#failed[@]}"

    if [[ ${#succeeded[@]} -gt 0 ]]; then
        echo -e "${GREEN}✓${NC} ${succeeded[*]}"
    fi

    if [[ ${#failed[@]} -gt 0 ]]; then
        echo -e "${RED}✗${NC} ${failed[*]}"
    fi

    echo ""
    log "To rollback, use: ./install.sh --rollback $snapshot_id"
}

# ============================================================================
# FULL UNINSTALL
# ============================================================================

# Uninstall all dotfiles (complete cleanup)
uninstall_all() {
    warn "This will remove ALL dotfiles installations!"
    warn "This action cannot be undone."

    if ! confirm "Are you sure you want to uninstall everything?"; then
        log "Uninstall cancelled"
        return 0
    fi

    echo ""
    log "Starting full uninstall..."

    # Create final snapshot
    local all_items
    mapfile -t all_items < <(get_all_items)

    local snapshot_id
    snapshot_id=$(create_snapshot "pre-uninstall-all" "${all_items[@]}")
    log "Created snapshot: $snapshot_id"

    # Uninstall all items
    local count=0
    for item in "${all_items[@]}"; do
        if get_item_status "$item"; then
            uninstall_item "$item"
            ((count++))
        fi
    done

    echo ""
    success "Uninstalled $count item(s)"
    log "Snapshot ID: $snapshot_id"
    log "To restore, use: ./install.sh --rollback $snapshot_id"

    # Optionally remove state file
    if confirm "Remove state file as well?"; then
        rm -f "${STATE_DIR}/state.json"
        log "State file removed"
    fi
}

# ============================================================================
# BACKUP RESTORATION
# ============================================================================

# Restore a single file from backup
restore_from_backup() {
    local target_path="$1"

    if [[ ! -e "$target_path" && ! -L "$target_path" ]]; then
        warn "Target does not exist: $target_path"
        return 1
    fi

    local target_dir
    target_dir=$(dirname "$target_path")
    local target_name
    target_name=$(basename "$target_path")

    # Find the most recent backup
    local backup
    backup=$(find "$target_dir" -name "${target_name}.backup.*" 2>/dev/null | sort -r | head -1)

    if [[ -z "$backup" ]]; then
        warn "No backup found for: $target_path"
        return 1
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would restore from backup: $backup"
        log "[DRY RUN] Would restore to: $target_path"
        return 0
    fi

    # Remove current file/symlink
    rm -rf "$target_path"

    # Restore from backup
    cp -a "$backup" "$target_path"

    success "Restored: $target_path"
    log "From backup: $backup"
}

# Restore all files from backups
restore_all_backups() {
    log "Restoring all files from backups..."

    local restored=0

    # Find all backups in home directory
    while IFS= read -r backup; do
        local target
        target="${backup%.backup.*}"

        if restore_from_backup "$target"; then
            ((restored++))
        fi
    done < <(find "$HOME" -maxdepth 3 -name ".*.backup.*" 2>/dev/null)

    success "Restored $restored file(s) from backups"
}

# ============================================================================
# CLEANUP FUNCTIONS
# ============================================================================

# Clean up old backups (keep only N most recent)
cleanup_old_backups() {
    local keep_count="${1:-5}"

    log "Cleaning up old backups (keeping last $keep_count)..."

    local cleaned=0

    # Find all backup files
    while IFS= read -r backup_file; do
        local target_name
        target_name=$(basename "$backup_file" | sed 's/\.backup\.[0-9]*$//')

        # Find all backups for this target
        local target_dir
        target_dir=$(dirname "$backup_file")

        local all_backups
        mapfile -t all_backups < <(find "$target_dir" -name "${target_name}.backup.*" 2>/dev/null | sort -r)

        # Remove excess backups
        if [[ ${#all_backups[@]} -gt $keep_count ]]; then
            for ((i=$keep_count; i<${#all_backups[@]}; i++)); do
                if [[ $DRY_RUN == true ]]; then
                    log "[DRY RUN] Would remove old backup: ${all_backups[$i]}"
                else
                    rm "${all_backups[$i]}"
                    ((cleaned++))
                fi
            done
        fi
    done < <(find "$HOME" -maxdepth 3 -name "*.backup.*" 2>/dev/null)

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would clean up $cleaned old backup(s)"
    elif [[ $cleaned -gt 0 ]]; then
        success "Cleaned up $cleaned old backup(s)"
    else
        log "No old backups to clean"
    fi
}

# Clean up orphaned backups (backups without current installation)
cleanup_orphaned_backups() {
    log "Cleaning up orphaned backups..."

    local cleaned=0

    # Find all backup files
    while IFS= read -r backup; do
        local target
        target="${backup%.backup.*}"

        # Check if target exists
        if [[ ! -e "$target" && ! -L "$target" ]]; then
            if [[ $DRY_RUN == true ]]; then
                log "[DRY RUN] Would remove orphaned backup: $backup"
            else
                rm "$backup"
                ((cleaned++))
            fi
        fi
    done < <(find "$HOME" -maxdepth 3 -name ".*.backup.*" 2>/dev/null)

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would clean up $cleaned orphaned backup(s)"
    elif [[ $cleaned -gt 0 ]]; then
        success "Cleaned up $cleaned orphaned backup(s)"
    else
        log "No orphaned backups found"
    fi
}

# Clean up old state snapshots
cleanup_old_snapshots() {
    local keep_count="${1:-10}"

    log "Cleaning up old snapshots (keeping last $keep_count)..."

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would clean up old snapshots"
        return 0
    fi

    cleanup_old_snapshots "$keep_count"
}

# Full cleanup (backups, snapshots, state)
full_cleanup() {
    warn "This will clean up old backups and snapshots."
    warn "This operation cannot be undone."

    if ! confirm "Continue with cleanup?"; then
        log "Cleanup cancelled"
        return 0
    fi

    echo ""

    # Clean old backups
    cleanup_old_backups 5
    echo ""

    # Clean orphaned backups
    cleanup_orphaned_backups
    echo ""

    # Clean old snapshots
    cleanup_old_snapshots 10
    echo ""

    success "Cleanup completed"
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

export -f uninstall_item uninstall_items uninstall_all
export -f restore_from_backup restore_all_backups
export -f cleanup_old_backups cleanup_orphaned_backups cleanup_old_snapshots full_cleanup
