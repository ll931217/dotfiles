#!/usr/bin/env bash
#
# FZF menu helpers for dotfiles installation system
# Provides interactive menus using fzf for category and item selection
#

# ============================================================================
# FZF CONFIGURATION
# ============================================================================

# Load user's fzf config if available
if [[ -f "$HOME/.config/zsh/fzf.zsh" ]]; then
    source "$HOME/.config/zsh/fzf.zsh" 2>/dev/null || true
fi

# Set default fzf options if not already set
: "${FZF_DEFAULT_OPTS:=--height 40% --layout=reverse --border --marker='✔'}"

# Export for subshells
export FZF_DEFAULT_OPTS

# ============================================================================
# MENU FUNCTIONS
# ============================================================================

# Show main mode selection menu
show_main_menu() {
    local mode
    mode=$(printf "Install\nUpdate\nUninstall\nStatus Dashboard\nList All\nHealth Check\nExit" | \
        fzf \
            --height 30% \
            --prompt="Select mode > " \
            --header="Dotfiles Installation System" \
            --border \
            --reverse)

    case "$mode" in
        "Install")     echo "install" ;;
        "Update")      echo "update" ;;
        "Uninstall")   echo "uninstall" ;;
        "Status Dashboard") echo "status" ;;
        "List All")    echo "list" ;;
        "Health Check") echo "health" ;;
        "Exit"|"")     echo "exit" ;;
        *)             echo "install" ;;  # Default
    esac
}

# Show category selection menu (multi-select)
show_category_menu() {
    local selected=()
    local preview_cmd='echo "$1" | cut -d"|" -f3-'

    # Build category list with format: KEY|NAME|DESCRIPTION|ITEM_COUNT
    local categories_list=()
    for cat in "${CATEGORIES[@]}"; do
        local cat_var="CATEGORY_${cat}"
        local cat_name
        local cat_desc
        local cat_icon
        local item_count

        cat_name=$(get_item_value "$cat_var" "name")
        cat_desc=$(get_item_value "$cat_var" "description")
        cat_icon=$(get_item_value "$cat_var" "icon")
        item_count=$(get_category_item_count "${cat,,}")

        categories_list+=("${cat}|${cat_icon} ${cat_name}|${cat_desc}|${item_count}")
    done

    # Sort by name (second field)
    IFS=$'\n' categories_list=($(sort <<<"${categories_list[*]}"))
    unset IFS

    # Show fzf menu with preview
    local selection
    selection=$(printf '%s\n' "${categories_list[@]}" | \
        fzf \
            --multi \
            --prompt="Select categories > " \
            --header "Select categories to configure (TAB to toggle, CTRL-A to toggle all)" \
            --delimiter '|' \
            --with-nth 2 \
            --preview 'echo "{}" | cut -d"|" -f3' \
            --preview-window=right:40%:wrap \
            --bind 'ctrl-a:toggle-all' \
            --bind 'ctrl-r:select-all+deselect-all' \
            --marker='✔' || echo "")

    if [[ -z "$selection" ]]; then
        return 1
    fi

    # Extract category keys from selection
    while IFS= read -r line; do
        [[ -n "$line" ]] && selected+=("$(echo "$line" | cut -d'|' -f1)")
    done <<< "$selection"

    printf '%s\n' "${selected[@]}"
}

# Show item selection menu for selected categories (multi-select)
show_item_menu() {
    local selected_categories=("$@")
    local selected=()
    local items_list=()

    # Build items list for selected categories
    for cat_key in "${selected_categories[@]}"; do
        local cat_lower="${cat_key,,}"

        for item_name in $(get_all_items); do
            local item_var="ITEM_${item_name}"
            local item_cat
            item_cat=$(get_item_value "$item_var" "category")

            if [[ "$item_cat" == "$cat_lower" ]]; then
                local item_name_disp
                local item_desc
                item_name_disp=$(get_item_value "$item_var" "name")
                item_desc=$(get_item_value "$item_var" "description")

                # Determine status
                local status=""
                local status_icon=""
                if get_item_status "$item_name"; then
                    status="[Installed]"
                    status_icon="✓"
                else
                    status="[Not Installed]"
                    status_icon=" "
                fi

                # Format: KEY|NAME|DESCRIPTION|STATUS|STATUS_ICON
                items_list+=("${item_name}|${status_icon} ${item_name_disp}|${item_desc}|${status}")
            fi
        done
    done

    # Sort by name (second field)
    IFS=$'\n' items_list=($(sort <<<"${items_list[*]}"))
    unset IFS

    # Show fzf menu
    local selection
    selection=$(printf '%s\n' "${items_list[@]}" | \
        fzf \
            --multi \
            --prompt="Select items > " \
            --header "Select items to install (TAB to toggle, CTRL-A to toggle all)" \
            --delimiter '|' \
            --with-nth 2,4 \
            --preview 'echo "{}" | cut -d"|" -f3' \
            --preview-window=right:40%:wrap \
            --bind 'ctrl-a:toggle-all' \
            --bind 'ctrl-r:select-all+deselect-all' \
            --marker='✔' || echo "")

    if [[ -z "$selection" ]]; then
        return 1
    fi

    # Extract item keys from selection
    while IFS= read -r line; do
        [[ -n "$line" ]] && selected+=("$(echo "$line" | cut -d'|' -f1)")
    done <<< "$selection"

    printf '%s\n' "${selected[@]}"
}

# Show confirmation summary before installation
show_confirmation() {
    local selected_items=("$@")

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           Installation Summary                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    local to_install=()
    local already_installed=()
    local to_update=()

    for item in "${selected_items[@]}"; do
        local item_var="ITEM_${item}"
        local item_name=$(get_item_value "$item_var" "name")

        if get_item_status "$item"; then
            already_installed+=("$item_name")
        else
            to_install+=("$item_name")
        fi
    done

    # Show items to install
    if [[ ${#to_install[@]} -gt 0 ]]; then
        echo -e "${GREEN}Will Install:${NC}"
        for item in "${to_install[@]}"; do
            echo "  + $item"
        done
        echo ""
    fi

    # Show already installed items
    if [[ ${#already_installed[@]} -gt 0 ]]; then
        echo -e "${YELLOW}Already Installed (will skip):${NC}"
        for item in "${already_installed[@]}"; do
            echo "  - $item"
        done
        echo ""
    fi

    if [[ $DRY_RUN == true ]]; then
        echo -e "${CYAN}[DRY RUN MODE]${NC} No changes will be made."
        echo ""
    fi

    # Ask for confirmation
    local response
    read -rp "Continue with installation? [Y/n] " response

    if [[ "$response" =~ ^[Nn]$ ]]; then
        return 1
    fi

    return 0
}

# Show conflict resolver
show_conflict_resolver() {
    local conflicts=("$@")

    echo ""
    warn "Conflicts detected:"
    echo ""

    for conflict in "${conflicts[@]}"; do
        local item1="${conflict% vs *}"
        local item2="${conflict#* vs }"

        local item_var1="ITEM_${item1}"
        local item_var2="ITEM_${item2}"
        local name1=$(get_item_value "$item_var1" "name")
        local name2=$(get_item_value "$item_var2" "name")

        echo "  ⚠️  $name1 conflicts with $name2"
    done

    echo ""
    echo "Select which to keep:"

    local options=()
    for conflict in "${conflicts[@]}"; do
        local item1="${conflict% vs *}"
        local item2="${conflict#* vs }"
        local item_var1="ITEM_${item1}"
        local item_var2="ITEM_${item2}"
        local name1=$(get_item_value "$item_var1" "name")
        local name2=$(get_item_value "$item_var2" "name")

        options+=("Keep ${name1}")
        options+=("Keep ${name2}")
    done
    options+=("Keep both (unsafe)")
    options+=("Cancel installation")

    local choice
    choice=$(printf '%s\n' "${options[@]}" | \
        fzf \
            --height 30% \
            --prompt="Resolve conflict > " \
            --header "Select resolution" \
            --border || echo "Cancel")

    case "$choice" in
        "Keep both (unsafe)"|"Cancel installation"|"")
            return 1
            ;;
        *)
            # Extract the item name being kept
            local kept_item="${choice#Keep }"
            echo "$kept_item"
            return 0
            ;;
    esac
}

# Show profile selector
show_profile_selector() {
    local profiles_dir="$HOME/.config/dotfiles/profiles"
    local profiles=()

    if [[ -d "$profiles_dir" ]]; then
        while IFS= read -r -d '' profile; do
            profiles+=("$(basename "$profile" .json)")
        done < <(find "$profiles_dir" -maxdepth 1 -name "*.json" -print0 | sort -z)
    fi

    if [[ ${#profiles[@]} -eq 0 ]]; then
        echo ""
        return 1
    fi

    local selection
    selection=$(printf '%s\n' "${profiles[@]}" | \
        fzf \
            --height 30% \
            --prompt="Select profile > " \
            --header "Saved Profiles" \
            --border \
            --preview="cat '$profiles_dir/{}.json' 2>/dev/null | jq -r '.description // \"No description\"' 2>/dev/null" || echo "")

    echo "$selection"
}

# ============================================================================
# STATUS DASHBOARD
# ============================================================================

# Show installation status dashboard
show_status_dashboard() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           Dotfiles Installation Status                     ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # System info
    local machine_type
    local environment
    local running_wm

    machine_type=$(detect_machine_type)
    environment=$(detect_environment)
    running_wm=$(detect_running_wm)

    echo "System: $(detect_os_type)"
    echo "Machine: ${machine_type}"
    echo "Environment: ${environment}"
    echo "Window Manager: ${running_wm}"
    echo "Dotfiles: ${REPO_ROOT}"
    echo ""

    # Count installed vs available
    local installed=()
    local available=()

    for item in $(get_all_items); do
        if get_item_status "$item"; then
            installed+=("$item")
        else
            available+=("$item")
        fi
    done

    # Show installed
    echo -e "${GREEN}Installed (${#installed[@]}):${NC}"
    if [[ ${#installed[@]} -gt 0 ]]; then
        local installed_names=()
        for item in "${installed[@]}"; do
            local item_var="ITEM_${item}"
            local name
            name=$(get_item_value "$item_var" "name")
            installed_names+=("$name")
        done
        printf "  ✓ %s\n" "${installed_names[@]}" | column -x
    fi
    echo ""

    # Show available
    echo -e "${YELLOW}Available (${#available[@]}):${NC}"
    if [[ ${#available[@]} -gt 0 ]]; then
        local available_names=()
        for item in "${available[@]}"; do
            local item_var="ITEM_${item}"
            local name
            name=$(get_item_value "$item_var" "name")
            available_names+=("$name")
        done
        printf "  • %s\n" "${available_names[@]}" | column -x
    fi
    echo ""

    # Actions
    echo "Actions: [i]install [u]update [c]check [q]uit"
}

# Detect OS type
detect_os_type() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        echo "$ID $VERSION_ID"
    else
        echo "Unknown"
    fi
}

# ============================================================================
# LIST ALL ITEMS
# ============================================================================

# List all available items
list_all_items() {
    echo ""
    echo "Available Configuration Items:"
    echo ""

    for cat in "${CATEGORIES[@]}"; do
        local cat_var="CATEGORY_${cat}"
        local cat_name
        local cat_icon
        cat_name=$(get_item_value "$cat_var" "name")
        cat_icon=$(get_item_value "$cat_var" "icon")

        echo "${cat_icon} ${cat_name}"

        for item in $(get_all_items); do
            local item_var="ITEM_${item}"
            local item_cat
            item_cat=$(get_item_value "$item_var" "category")

            if [[ "$item_cat" == "${cat,,}" ]]; then
                local item_name
                local item_desc
                item_name=$(get_item_value "$item_var" "name")
                item_desc=$(get_item_value "$item_var" "description")

                local status=""
                if get_item_status "$item"; then
                    status=" ${GREEN}[Installed]${NC}"
                fi

                # Use echo -e to interpret color escape sequences
                echo -e "  ${item_name}${status}"
                [[ -n "$item_desc" ]] && echo "    ${item_desc}"
            fi
        done
        echo ""
    done
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

export -f show_main_menu show_category_menu show_item_menu
export -f show_confirmation show_conflict_resolver show_profile_selector
export -f show_status_dashboard list_all_items detect_os_type
