#!/usr/bin/env bash
#
# Profile management for dotfiles installation system
# Save, load, list, and manage installation profiles
#

# Profile directory
PROFILES_DIR="${HOME}/.config/dotfiles/profiles"

# Export for subshells
export PROFILES_DIR

# ============================================================================
# PROFILE INITIALIZATION
# ============================================================================

# Initialize profiles directory
init_profiles() {
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would initialize profiles directory: $PROFILES_DIR"
        return 0
    fi

    if [[ ! -d "$PROFILES_DIR" ]]; then
        mkdir -p "$PROFILES_DIR"
        log "Created profiles directory: $PROFILES_DIR"
    fi
}

# ============================================================================
# PROFILE SAVE
# ============================================================================

# Save current item selection as a profile
save_profile() {
    local profile_name="$1"
    shift
    local items=("$@")

    if [[ -z "$profile_name" ]]; then
        error "Profile name is required"
        return 1
    fi

    if [[ ${#items[@]} -eq 0 ]]; then
        error "No items to save in profile"
        return 1
    fi

    init_profiles

    local profile_file="${PROFILES_DIR}/${profile_name}.json"

    if [[ -f "$profile_file" && $DRY_RUN == false ]]; then
        if ! confirm "Profile '$profile_name' already exists. Overwrite?"; then
            log "Profile save cancelled"
            return 0
        fi
    fi

    local timestamp
    timestamp=$(date -Iseconds)

    # Build profile JSON
    local profile_json
    profile_json=$(cat << EOF
{
  "name": "$profile_name",
  "description": "Custom dotfiles profile",
  "created_at": "$timestamp",
  "updated_at": "$timestamp",
  "items": [
EOF
)

    # Add items to JSON
    local first=true
    for item in "${items[@]}"; do
        local item_var="ITEM_${item}"
        local item_name
        local item_category
        local item_description

        item_name=$(get_item_value "$item_var" "name")
        item_category=$(get_item_value "$item_var" "category")
        item_description=$(get_item_value "$item_var" "description")

        if [[ "$first" == "true" ]]; then
            first=false
        else
            profile_json+=","
        fi

        profile_json+=$(cat << EOF
    {
      "key": "$item",
      "name": "$item_name",
      "category": "$item_category",
      "description": "$item_description"
    }
EOF
)
    done

    profile_json+=$(cat << EOF

  ]
}
EOF
)

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would save profile: $profile_file"
        echo "$profile_json" | jq . 2>/dev/null || echo "$profile_json"
        return 0
    fi

    echo "$profile_json" | jq . > "$profile_file"

    success "Profile saved: $profile_name (${#items[@]} items)"
    log "Profile file: $profile_file"
}

# ============================================================================
# PROFILE LOAD
# ============================================================================

# Load a profile and return items
load_profile() {
    local profile_name="$1"

    if [[ -z "$profile_name" ]]; then
        error "Profile name is required"
        return 1
    fi

    local profile_file="${PROFILES_DIR}/${profile_name}.json"

    if [[ ! -f "$profile_file" ]]; then
        error "Profile not found: $profile_name"
        log "Available profiles:"
        list_profiles_names
        return 1
    fi

    # Extract item keys from profile
    if command -v jq &>/dev/null; then
        jq -r '.items[].key' "$profile_file"
    else
        grep -oP '"key":\s*"\K[^"]+' "$profile_file"
    fi
}

# Show profile details
show_profile_details() {
    local profile_name="$1"

    if [[ -z "$profile_name" ]]; then
        error "Profile name is required"
        return 1
    fi

    local profile_file="${PROFILES_DIR}/${profile_name}.json"

    if [[ ! -f "$profile_file" ]]; then
        error "Profile not found: $profile_name"
        return 1
    fi

    echo ""
    echo "Profile: $profile_name"
    echo "================================"

    if command -v jq &>/dev/null; then
        local description
        local created
        local updated
        local items
        local item_count

        description=$(jq -r '.description // "No description"' "$profile_file")
        created=$(jq -r '.created_at // "unknown"' "$profile_file")
        updated=$(jq -r '.updated_at // "unknown"' "$profile_file")
        item_count=$(jq -r '.items | length' "$profile_file")

        echo "Description: $description"
        echo "Created: $created"
        echo "Updated: $updated"
        echo "Items: $item_count"
        echo ""

        # Show items by category
        echo "Items:"
        jq -r '.items[] | "  \(.name) (\(.category))"' "$profile_file"
    else
        cat "$profile_file"
    fi

    echo ""
}

# ============================================================================
# PROFILE LIST
# ============================================================================

# List all available profiles
list_profiles() {
    echo ""
    echo "Available Profiles:"
    echo ""

    init_profiles

    local profiles=()
    if [[ -d "$PROFILES_DIR" ]]; then
        while IFS= read -r -d '' profile; do
            profiles+=("$(basename "$profile" .json)")
        done < <(find "$PROFILES_DIR" -maxdepth 1 -name "*.json" -print0 2>/dev/null | sort -z)
    fi

    if [[ ${#profiles[@]} -eq 0 ]]; then
        echo "  No profiles found."
        echo ""
        echo "Create a profile during installation or use:"
        echo "  ./install.sh --profile-save <name>"
        return 0
    fi

    for profile in "${profiles[@]}"; do
        local profile_file="${PROFILES_DIR}/${profile}.json"

        if [[ -f "$profile_file" ]]; then
            local description
            local item_count
            local updated

            if command -v jq &>/dev/null; then
                description=$(jq -r '.description // "No description"' "$profile_file" 2>/dev/null)
                item_count=$(jq -r '.items | length' "$profile_file" 2>/dev/null)
                updated=$(jq -r '.updated_at // "unknown"' "$profile_file" 2>/dev/null)
            else
                description="N/A"
                item_count="?"
                updated="unknown"
            fi

            echo "  📋 $profile"
            echo "     $description"
            echo "     Items: $item_count | Updated: $updated"
            echo ""
        fi
    done
}

# List only profile names (for error messages)
list_profiles_names() {
    if [[ -d "$PROFILES_DIR" ]]; then
        find "$PROFILES_DIR" -maxdepth 1 -name "*.json" -exec basename {} .json \; 2>/dev/null | sort
    fi
}

# ============================================================================
# PROFILE DELETE
# ============================================================================

# Delete a profile
delete_profile() {
    local profile_name="$1"

    if [[ -z "$profile_name" ]]; then
        error "Profile name is required"
        return 1
    fi

    local profile_file="${PROFILES_DIR}/${profile_name}.json"

    if [[ ! -f "$profile_file" ]]; then
        error "Profile not found: $profile_name"
        log "Available profiles:"
        list_profiles_names
        return 1
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would delete profile: $profile_name"
        return 0
    fi

    if ! confirm "Delete profile '$profile_name'?"; then
        log "Profile deletion cancelled"
        return 0
    fi

    rm "$profile_file"
    success "Profile deleted: $profile_name"
}

# ============================================================================
# PROFILE VALIDATION
# ============================================================================

# Validate a profile (check if all items are still valid)
validate_profile() {
    local profile_name="$1"

    if [[ -z "$profile_name" ]]; then
        error "Profile name is required"
        return 1
    fi

    local profile_file="${PROFILES_DIR}/${profile_name}.json"

    if [[ ! -f "$profile_file" ]]; then
        error "Profile not found: $profile_name"
        return 1
    fi

    echo ""
    log "Validating profile: $profile_name"

    local valid=true
    local invalid_items=()

    if command -v jq &>/dev/null; then
        local items
        items=$(jq -r '.items[].key' "$profile_file" 2>/dev/null)

        while IFS= read -r item; do
            if [[ -z "$item" ]]; then
                continue
            fi

            # Check if item still exists in registry
            local item_var="ITEM_${item}"
            local item_name
            item_name=$(get_item_value "$item_var" "name" 2>/dev/null)

            if [[ -z "$item_name" ]]; then
                invalid_items+=("$item")
                valid=false
            fi
        done <<< "$items"
    fi

    if [[ "$valid" == "true" ]]; then
        success "Profile is valid: $profile_name"
        return 0
    else
        warn "Profile has invalid items:"
        for item in "${invalid_items[@]}"; do
            echo "  - $item (no longer in registry)"
        done
        return 1
    fi
}

# ============================================================================
# PROFILE EXPORT/IMPORT
# ============================================================================

# Export a profile to a file
export_profile() {
    local profile_name="$1"
    local output_file="${2:-${profile_name}-profile.json}"

    local profile_file="${PROFILES_DIR}/${profile_name}.json"

    if [[ ! -f "$profile_file" ]]; then
        error "Profile not found: $profile_name"
        return 1
    fi

    cp "$profile_file" "$output_file"
    success "Profile exported: $output_file"
}

# Import a profile from a file
import_profile() {
    local input_file="$1"
    local profile_name="${2:-$(basename "$input_file" .json)}"

    if [[ ! -f "$input_file" ]]; then
        error "File not found: $input_file"
        return 1
    fi

    # Validate JSON
    if command -v jq &>/dev/null; then
        if ! jq empty "$input_file" 2>/dev/null; then
            error "Invalid JSON file: $input_file"
            return 1
        fi
    fi

    local output_file="${PROFILES_DIR}/${profile_name}.json"

    if [[ -f "$output_file" && $DRY_RUN == false ]]; then
        if ! confirm "Profile '$profile_name' already exists. Overwrite?"; then
            log "Import cancelled"
            return 0
        fi
    fi

    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would import profile: $profile_name"
        return 0
    fi

    # Update timestamp
    if command -v jq &>/dev/null; then
        jq --arg updated "$(date -Iseconds)" '.updated_at = $updated' "$input_file" > "$output_file"
    else
        cp "$input_file" "$output_file"
    fi

    success "Profile imported: $profile_name"
}

# ============================================================================
# FZF PROFILE SELECTOR
# ============================================================================

# Show profile selection menu using fzf
show_profile_selector() {
    init_profiles

    local profiles=()
    if [[ -d "$PROFILES_DIR" ]]; then
        while IFS= read -r -d '' profile; do
            profiles+=("$(basename "$profile" .json)")
        done < <(find "$PROFILES_DIR" -maxdepth 1 -name "*.json" -print0 2>/dev/null | sort -z)
    fi

    if [[ ${#profiles[@]} -eq 0 ]]; then
        return 1
    fi

    # Build list with descriptions
    local profile_list=()
    for profile in "${profiles[@]}"; do
        local profile_file="${PROFILES_DIR}/${profile}.json"
        local description
        local item_count

        if command -v jq &>/dev/null; then
            description=$(jq -r '.description // "No description"' "$profile_file" 2>/dev/null)
            item_count=$(jq -r '.items | length' "$profile_file" 2>/dev/null)
        else
            description="..."
            item_count="?"
        fi

        profile_list+=("${profile}|${description}|${item_count} items")
    done

    # Show fzf menu
    local selection
    selection=$(printf '%s\n' "${profile_list[@]}" | \
        fzf \
            --height 30% \
            --prompt="Select profile > " \
            --header "Saved Profiles (ENTER to view, CTRL-D to delete)" \
            --delimiter '|' \
            --with-nth 1 \
            --preview 'echo "Description: $(echo {} | cut -d"|" -f2)\nItems: $(echo {} | cut -d"|" -f3)"' \
            --preview-window=right:50%:wrap \
            --bind 'ctrl-d:execute(echo {} | cut -d"|" -f1)+abort' || echo "")

    if [[ -z "$selection" ]]; then
        return 1
    fi

    echo "$selection" | cut -d'|' -f1
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

export -f init_profiles
export -f save_profile load_profile show_profile_details
export -f list_profiles list_profiles_names delete_profile
export -f validate_profile export_profile import_profile
export -f show_profile_selector
