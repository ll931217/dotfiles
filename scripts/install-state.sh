#!/usr/bin/env bash
#
# State management for dotfiles installation system
# Tracks installations, versions, backups, and snapshots for rollback capability
#

# Get script directory and state paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE_DIR="${HOME}/.config/dotfiles"
STATE_FILE="${STATE_DIR}/state.json"
BACKUP_DIR="${STATE_DIR}/backups"

# Export for subshells
export STATE_DIR STATE_FILE BACKUP_DIR

# ============================================================================
# STATE INITIALIZATION
# ============================================================================

# Initialize state directory and file
init_state() {
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would initialize state directory: $STATE_DIR"
        return 0
    fi

    # Create state directory if it doesn't exist
    if [[ ! -d "$STATE_DIR" ]]; then
        mkdir -p "$STATE_DIR"
        log "Created state directory: $STATE_DIR"
    fi

    # Create backup directory
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        log "Created backup directory: $BACKUP_DIR"
    fi

    # Initialize state file if it doesn't exist
    if [[ ! -f "$STATE_FILE" ]]; then
        cat > "$STATE_FILE" << EOF
{
  "version": "1.0.0",
  "created_at": "$(date -Iseconds)",
  "last_updated": "$(date -Iseconds)",
  "repo_hash": "",
  "machine_profile": "auto",
  "installed_items": {},
  "snapshots": []
}
EOF
        log "Initialized state file: $STATE_FILE"
    fi
}

# Load state from JSON file
load_state() {
    if [[ ! -f "$STATE_FILE" ]]; then
        init_state
    fi

    # Use jq to parse JSON safely
    if command -v jq &>/dev/null; then
        cat "$STATE_FILE"
    else
        warn "jq not installed, state functions limited"
        cat "$STATE_FILE"
    fi
}

# Save state to JSON file
save_state() {
    local state_json="$1"

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would save state to: $STATE_FILE"
        return 0
    fi

    # Ensure state directory exists
    init_state >/dev/null 2>&1

    # Update last_updated timestamp
    if command -v jq &>/dev/null; then
        echo "$state_json" | jq --arg last_updated "$(date -Iseconds)" '.last_updated = $last_updated' > "$STATE_FILE"
    else
        # Fallback without jq
        echo "$state_json" > "$STATE_FILE"
    fi

    log "State saved to: $STATE_FILE"
}

# Get a specific value from state
get_state_value() {
    local key="$1"

    if [[ ! -f "$STATE_FILE" ]]; then
        return 1
    fi

    if command -v jq &>/dev/null; then
        jq -r ".$key // empty" "$STATE_FILE" 2>/dev/null
    else
        # Fallback: grep for simple keys
        grep -oP "\"$key\":\s*\"[^\"]*\"" "$STATE_FILE" | cut -d'"' -f4
    fi
}

# ============================================================================
# ITEM INSTALLATION TRACKING
# ============================================================================

# Mark an item as installed
mark_item_installed() {
    local item_name="$1"
    local item_var="ITEM_${item_name}"
    local item_name_disp
    item_name_disp=$(get_item_value "$item_var" "name")

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would mark as installed: $item_name"
        return 0
    fi

    init_state

    # Get current git hash for version tracking
    local git_hash
    git_hash=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")

    local timestamp
    timestamp=$(date -Iseconds)

    if command -v jq &>/dev/null; then
        # Update state with jq
        local tmp_file
        tmp_file=$(mktemp)

        jq --arg item "$item_name" \
           --arg name "$item_name_disp" \
           --arg version "$git_hash" \
           --arg installed_at "$timestamp" \
           '.installed_items[$item] = {
               name: $name,
               version: $version,
               installed_at: $installed_at
           }' "$STATE_FILE" > "$tmp_file"

        mv "$tmp_file" "$STATE_FILE"
    else
        warn "jq not installed, cannot update state properly"
    fi

    log "Marked as installed: $item_name (version: $git_hash)"
}

# Remove item from installed state
mark_item_uninstalled() {
    local item_name="$1"

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would mark as uninstalled: $item_name"
        return 0
    fi

    if [[ ! -f "$STATE_FILE" ]]; then
        return 0
    fi

    if command -v jq &>/dev/null; then
        local tmp_file
        tmp_file=$(mktemp)

        jq --arg item "$item_name" 'del(.installed_items[$item])' "$STATE_FILE" > "$tmp_file"

        mv "$tmp_file" "$STATE_FILE"
    fi

    log "Marked as uninstalled: $item_name"
}

# Check if item is in installed state
is_item_marked_installed() {
    local item_name="$1"

    if [[ ! -f "$STATE_FILE" ]]; then
        return 1
    fi

    if command -v jq &>/dev/null; then
        local result
        result=$(jq -r ".installed_items[\"$item_name\"] // empty" "$STATE_FILE" 2>/dev/null)
        [[ -n "$result" ]]
    else
        grep -q "\"$item_name\":" "$STATE_FILE" 2>/dev/null
    fi
}

# Get installed items from state
get_installed_items() {
    if [[ ! -f "$STATE_FILE" ]]; then
        return 0
    fi

    if command -v jq &>/dev/null; then
        jq -r '.installed_items | keys[]' "$STATE_FILE" 2>/dev/null
    else
        grep -oP '"installed_items":\s*\{[^}]+\}' "$STATE_FILE" | grep -oP '"[^"]+":' | tr -d '":'
    fi
}

# Get item installation info
get_item_info() {
    local item_name="$1"
    local field="$2"

    if [[ ! -f "$STATE_FILE" ]]; then
        return 1
    fi

    if command -v jq &>/dev/null; then
        jq -r ".installed_items[\"$item_name\"][\"$field\"] // empty" "$STATE_FILE" 2>/dev/null
    fi
}

# ============================================================================
# VERSION TRACKING
# ============================================================================

# Update repository hash in state
update_repo_hash() {
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would update repository hash"
        return 0
    fi

    if [[ ! -f "$STATE_FILE" ]]; then
        init_state
    fi

    local git_hash
    git_hash=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")

    if command -v jq &>/dev/null; then
        local tmp_file
        tmp_file=$(mktemp)

        jq --arg hash "$git_hash" '.repo_hash = $hash' "$STATE_FILE" > "$tmp_file"
        mv "$tmp_file" "$STATE_FILE"
    fi

    log "Repository hash updated: $git_hash"
}

# Check if repository has updates
check_repo_updates() {
    if [[ ! -f "$STATE_FILE" ]]; then
        return 1
    fi

    local current_hash
    current_hash=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")

    local stored_hash
    stored_hash=$(get_state_value "repo_hash")

    if [[ "$current_hash" != "$stored_hash" && -n "$stored_hash" ]]; then
        warn "Dotfiles repository has been updated"
        log "Stored hash: $stored_hash"
        log "Current hash: $current_hash"
        return 0
    fi

    return 1
}

# ============================================================================
# SNAPSHOT SYSTEM
# ============================================================================

# Create a snapshot before making changes
create_snapshot() {
    local snapshot_name="${1:-auto}"
    local items=("${@:2}")

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would create snapshot: $snapshot_name"
        return 0
    fi

    init_state

    local snapshot_id
    snapshot_id="$(date +%Y%m%d-%H%M%S)-${snapshot_name}"

    local timestamp
    timestamp=$(date -Iseconds)

    # Collect current backups
    local backup_list=()
    for item in "${items[@]}"; do
        local item_var="ITEM_${item}"
        local target_path
        target_path=$(get_item_value "$item_var" "target_path")
        target_path=$(eval echo "$target_path")

        # Check for existing backups
        local target_dir
        target_dir=$(dirname "$target_path")
        local backup
        backup=$(find "$target_dir" -name "$(basename "$target_path").backup.*" 2>/dev/null | sort -r | head -1)

        if [[ -n "$backup" ]]; then
            backup_list+=("$backup")
        fi
    done

    # Add snapshot to state
    if command -v jq &>/dev/null; then
        local tmp_file
        tmp_file=$(mktemp)

        local items_json
        items_json=$(printf '%s\n' "${items[@]}" | jq -R . | jq -s .)

        local backups_json
        backups_json=$(printf '%s\n' "${backup_list[@]}" | jq -R . | jq -s .)

        jq --arg id "$snapshot_id" \
           --arg timestamp "$timestamp" \
           --argjson items "$items_json" \
           --argjson backups "$backups_json" \
           '.snapshots += [{
               id: $id,
               created_at: $timestamp,
               items: $items,
               backups: $backups
           }]' "$STATE_FILE" > "$tmp_file"

        mv "$tmp_file" "$STATE_FILE"
    fi

    success "Snapshot created: $snapshot_id"
    echo "$snapshot_id"
}

# Get list of snapshots
get_snapshots() {
    if [[ ! -f "$STATE_FILE" ]]; then
        return 0
    fi

    if command -v jq &>/dev/null; then
        jq -r '.snapshots[] | "\(.id) \(.created_at)"' "$STATE_FILE" 2>/dev/null
    fi
}

# Get snapshot details
get_snapshot_info() {
    local snapshot_id="$1"

    if [[ ! -f "$STATE_FILE" ]]; then
        return 1
    fi

    if command -v jq &>/dev/null; then
        jq -r ".snapshots[] | select(.id == \"$snapshot_id\")" "$STATE_FILE" 2>/dev/null
    fi
}

# Delete old snapshots (keep only N most recent)
cleanup_old_snapshots() {
    local keep_count="${1:-5}"

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would clean up old snapshots (keeping last $keep_count)"
        return 0
    fi

    if [[ ! -f "$STATE_FILE" ]]; then
        return 0
    fi

    if command -v jq &>/dev/null; then
        local tmp_file
        tmp_file=$(mktemp)

        jq --argjson keep "$keep_count" \
           '.snapshots = (.snapshots | length > $keep | if . then .snapshots[-($keep):] else .snapshots end)' \
           "$STATE_FILE" > "$tmp_file"

        mv "$tmp_file" "$STATE_FILE"
    fi

    log "Cleaned up old snapshots (kept last $keep_count)"
}

# ============================================================================
# ROLLBACK SYSTEM
# ============================================================================

# Rollback to a specific snapshot
rollback_to_snapshot() {
    local snapshot_id="$1"

    if [[ ! -f "$STATE_FILE" ]]; then
        error "No state file found. Cannot rollback."
        return 1
    fi

    log "Rolling back to snapshot: $snapshot_id"

    # Get snapshot info
    local snapshot_info
    snapshot_info=$(get_snapshot_info "$snapshot_id")

    if [[ -z "$snapshot_info" ]]; then
        error "Snapshot not found: $snapshot_id"
        return 1
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would rollback to snapshot: $snapshot_id"
        log "Snapshot info:"
        echo "$snapshot_info"
        return 0
    fi

    # Restore from backups
    if command -v jq &>/dev/null; then
        local backups
        backups=$(echo "$snapshot_info" | jq -r '.backups[]' 2>/dev/null)

        while IFS= read -r backup; do
            if [[ -n "$backup" && -f "$backup" ]]; then
                local target
                target="${backup%.backup.*}"
                target="${backup%%/backup*}"

                # Determine original target path
                local backup_dir
                backup_dir=$(dirname "$backup")
                local backup_name
                backup_name=$(basename "$backup")
                local original_name
                original_name="${backup_name%.backup.*}"

                # Try to find the original location
                if [[ "$backup" =~ ^(.*)\.backup\.[0-9]+$ ]]; then
                    target="${BASH_REMATCH[1]}"
                fi

                if [[ -n "$target" ]]; then
                    log "Restoring: $backup -> $target"
                    cp -a "$backup" "$target"
                    success "Restored: $target"
                fi
            fi
        done <<< "$backups"
    fi

    success "Rollback to snapshot $snapshot_id completed"
    log "You may need to restart your shell or WM for changes to take effect"
}

# List available snapshots for rollback
list_snapshots() {
    echo ""
    echo "Available Snapshots:"
    echo ""

    if [[ ! -f "$STATE_FILE" ]]; then
        warn "No state file found. No snapshots available."
        return 0
    fi

    local count
    count=0

    if command -v jq &>/dev/null; then
        while IFS= read -r line; do
            ((count++))
            local snapshot_id
            local created_at
            snapshot_id=$(echo "$line" | cut -d' ' -f1)
            created_at=$(echo "$line" | cut -d' ' -f2-)

            echo "  [$count] $snapshot_id"
            echo "      Created: $created_at"

            # Show items in snapshot
            local items
            items=$(jq -r ".snapshots[] | select(.id == \"$snapshot_id\") | .items[]" "$STATE_FILE" 2>/dev/null)
            if [[ -n "$items" ]]; then
                echo "      Items: $(echo "$items" | tr '\n' ',' | sed 's/,$//')"
            fi
            echo ""
        done < <(get_snapshots)
    fi

    if [[ $count -eq 0 ]]; then
        echo "  No snapshots found."
    fi
}

# ============================================================================
# STATE UTILITIES
# ============================================================================

# Export all state as JSON for backup/restore
export_state() {
    local output_file="${1:-${STATE_DIR}/state-export-$(date +%Y%m%d-%H%M%S).json}"

    if [[ ! -f "$STATE_FILE" ]]; then
        error "No state file found to export"
        return 1
    fi

    cp "$STATE_FILE" "$output_file"
    success "State exported to: $output_file"
}

# Import state from JSON file
import_state() {
    local input_file="$1"

    if [[ ! -f "$input_file" ]]; then
        error "File not found: $input_file"
        return 1
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would import state from: $input_file"
        return 0
    fi

    # Validate JSON
    if command -v jq &>/dev/null; then
        if ! jq empty "$input_file" 2>/dev/null; then
            error "Invalid JSON file: $input_file"
            return 1
        fi
    fi

    cp "$input_file" "$STATE_FILE"
    success "State imported from: $input_file"
}

# Show state summary
show_state_summary() {
    echo ""
    echo "Dotfiles Installation State:"
    echo ""

    if [[ ! -f "$STATE_FILE" ]]; then
        warn "No state file found. Run installer to initialize."
        return 0
    fi

    if command -v jq &>/dev/null; then
        local version
        local created
        local updated
        local repo_hash
        local machine_profile

        version=$(jq -r '.version // "unknown"' "$STATE_FILE")
        created=$(jq -r '.created_at // "unknown"' "$STATE_FILE")
        updated=$(jq -r '.last_updated // "unknown"' "$STATE_FILE")
        repo_hash=$(jq -r '.repo_hash // "unknown"' "$STATE_FILE")
        machine_profile=$(jq -r '.machine_profile // "auto"' "$STATE_FILE")

        echo "Version: $version"
        echo "Created: $created"
        echo "Updated: $updated"
        echo "Repository: $repo_hash"
        echo "Profile: $machine_profile"
        echo ""

        local installed_count
        installed_count=$(jq -r '.installed_items | length' "$STATE_FILE")

        echo "Installed Items: $installed_count"

        if [[ $installed_count -gt 0 ]]; then
            jq -r '.installed_items | to_entries[] | "  \(.key): \(.value.name) (v\(.value.version))"' "$STATE_FILE"
        fi
        echo ""

        local snapshot_count
        snapshot_count=$(jq -r '.snapshots | length' "$STATE_FILE")
        echo "Snapshots: $snapshot_count"
    fi
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

export -f init_state load_state save_state get_state_value
export -f mark_item_installed mark_item_uninstalled is_item_marked_installed
export -f get_installed_items get_item_info
export -f update_repo_hash check_repo_updates
export -f create_snapshot get_snapshots get_snapshot_info cleanup_old_snapshots
export -f rollback_to_snapshot list_snapshots
export -f export_state import_state show_state_summary
