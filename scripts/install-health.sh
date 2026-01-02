#!/usr/bin/env bash
#
# Health check system for dotfiles installation
# Comprehensive verification of installations, configs, and dependencies
#

# ============================================================================
# SYMLINK VERIFICATION
# ============================================================================

# Check if a symlink is valid (points to existing file in repo)
check_symlink_valid() {
    local target="$1"

    if [[ ! -L "$target" ]]; then
        return 1
    fi

    local link_target
    link_target=$(readlink "$target")

    # Check if link target exists
    [[ -e "$link_target" ]]
}

# Verify all symlinks for installed items
check_all_symlinks() {
    log "Checking symlink integrity..."

    local errors=0
    local warnings=0

    for item in $(get_all_items); do
        local item_var="ITEM_${item}"
        local detection
        detection=$(get_item_value "$item_var" "detection")

        if [[ "$detection" != "symlink" ]]; then
            continue
        fi

        local config_path
        local target_path
        config_path=$(get_item_value "$item_var" "config_path")
        target_path=$(get_item_value "$item_var" "target_path")

        # Expand variables
        config_path="$(eval echo "$config_path")"
        target_path="$(eval echo "$target_path")"

        if [[ -L "$target_path" ]]; then
            if ! check_symlink_valid "$target_path"; then
                error "Broken symlink: $target_path"
                ((errors++))
            fi
        fi
    done

    if [[ $errors -eq 0 ]]; then
        success "All symlinks are valid"
    else
        error "Found $errors broken symlink(s)"
    fi

    return $errors
}

# ============================================================================
# PACKAGE VERIFICATION
# ============================================================================

# Check if required packages are installed
check_packages() {
    log "Checking package installation..."

    local errors=0
    local missing_packages=()

    for item in $(get_all_items); do
        # Only check installed items
        if ! get_item_status "$item"; then
            continue
        fi

        local item_var="ITEM_${item}"
        local packages
        packages=$(get_item_value "$item_var" "packages")

        if [[ -z "$packages" ]]; then
            continue
        fi

        for pkg in $packages; do
            if ! is_package_installed "$pkg"; then
                missing_packages+=("$pkg (for $item)")
                ((errors++))
            fi
        done
    done

    if [[ $errors -eq 0 ]]; then
        success "All required packages are installed"
    else
        warn "Missing packages:"
        for pkg in "${missing_packages[@]}"; do
            echo "  - $pkg"
        done
    fi

    return $errors
}

# ============================================================================
# CONFIG VALIDATION
# ============================================================================

# Check if config files are valid (parseable)
check_configs() {
    log "Checking config file validity..."

    local errors=0
    local warnings=0

    # Check shell configs
    if [[ -f "$HOME/.zshrc" ]]; then
        if zsh -n "$HOME/.zshrc" 2>/dev/null; then
            log "✓ .zshrc syntax OK"
        else
            warn "⚠ .zshrc has syntax errors"
            ((warnings++))
        fi
    fi

    # Check tmux config
    if command -v tmux &>/dev/null && [[ -f "$HOME/.tmux.conf" ]]; then
        if tmux -f "$HOME/.tmux.conf" start-server 2>/dev/null; then
            log "✓ .tmux.conf OK"
        else
            warn "⚠ .tmux.conf has errors"
            ((warnings++))
        fi
    fi

    # Check starship config
    if command -v starship &>/dev/null && [[ -f "$HOME/.config/starship.toml" ]]; then
        if starship print-config 2>/dev/null | grep -q "starship"; then
            log "✓ starship.toml OK"
        else
            warn "⚠ starship.toml may have issues"
            ((warnings++))
        fi
    fi

    # Check terminal emulator configs
    for term in alacritty kitty wezterm; do
        local config_dir="$HOME/.config/$term"
        if [[ -d "$config_dir" ]]; then
            log "✓ $term config exists"
        fi
    done

    # Check window manager configs
    if [[ -d "$HOME/.config/i3" ]]; then
        if i3 -C -c "$HOME/.config/i3/config" >/dev/null 2>&1; then
            log "✓ i3 config OK"
        else
            warn "⚠ i3 config has errors"
            ((warnings++))
        fi
    fi

    if [[ -f "$HOME/.config/hypr/hyprland.conf" ]]; then
        if hyprctl config reload 2>/dev/null || [[ $? -eq 1 ]]; then
            log "✓ Hyprland config exists"
        fi
    fi

    # Check editor configs
    if [[ -f "$HOME/.vimrc" ]]; then
        log "✓ .vimrc exists"
    fi

    if [[ -d "$HOME/.config/nvim" ]]; then
        if command -v nvim &>/dev/null; then
            log "✓ NeoVim config exists"
        fi
    fi

    if [[ $errors -eq 0 && $warnings -eq 0 ]]; then
        success "All configs are valid"
    elif [[ $errors -eq 0 ]]; then
        warn "Found $warnings warning(s)"
    else
        error "Found $errors error(s) and $warnings warning(s)"
    fi

    return $errors
}

# ============================================================================
# DEPENDENCY VERIFICATION
# ============================================================================

# Check if all dependencies are satisfied
check_dependencies_all() {
    log "Checking item dependencies..."

    local errors=0

    for item in $(get_all_items); do
        # Only check installed items
        if ! get_item_status "$item"; then
            continue
        fi

        if ! check_dependencies "$item"; then
            ((errors++))
        fi
    done

    if [[ $errors -eq 0 ]]; then
        success "All dependencies satisfied"
    else
        error "Found $errors missing dependencies"
    fi

    return $errors
}

# ============================================================================
# SYSTEM INTEGRATION CHECKS
# ============================================================================

# Check shell integration
check_shell_integration() {
    log "Checking shell integration..."

    local errors=0

    # Check if ZSH is using the dotfiles config
    if [[ -L "$HOME/.zshrc" ]]; then
        local zshrc_target
        zshrc_target=$(readlink "$HOME/.zshrc")

        if [[ "$zshrc_target" == *"dotfiles"* ]]; then
            log "✓ ZSH using dotfiles config"
        else
            warn "⚠ ZSH config is not from dotfiles"
            ((errors++))
        fi
    fi

    # Check if starship is being used
    if command -v starship &>/dev/null; then
        if grep -q "starship" "$HOME/.zshrc" 2>/dev/null; then
            log "✓ Starship prompt integrated"
        else
            warn "⚠ Starship installed but not in .zshrc"
        fi
    fi

    return $errors
}

# Check WM/DM integration
check_wm_integration() {
    log "Checking window manager integration..."

    local running_wm
    running_wm=$(detect_running_wm)

    if [[ "$running_wm" != "none" && "$running_wm" != "unknown" ]]; then
        log "✓ Running WM: $running_wm"

        # Check if WM config is from dotfiles
        case "$running_wm" in
            i3|i3-gaps)
                if [[ -L "$HOME/.config/i3/config" ]]; then
                    log "✓ i3 config from dotfiles"
                else
                    warn "⚠ i3 config not from dotfiles"
                fi
                ;;
            hyprland)
                if [[ -L "$HOME/.config/hypr/hyprland.conf" ]] || [[ -L "$HOME/.config/hypr" ]]; then
                    log "✓ Hyprland config from dotfiles"
                else
                    warn "⚠ Hyprland config not from dotfiles"
                fi
                ;;
        esac
    else
        log "No WM running or running in headless mode"
    fi

    return 0
}

# Check editor integration
check_editor_integration() {
    log "Checking editor integration..."

    if [[ -L "$HOME/.vimrc" ]]; then
        local vimrc_target
        vimrc_target=$(readlink "$HOME/.vimrc")

        if [[ "$vimrc_target" == *"dotfiles"* ]]; then
            log "✓ Vim/NeoVim config from dotfiles"
        fi
    fi

    # Check for NeoVim-specific config
    if [[ -L "$HOME/.config/nvim" ]]; then
        log "✓ NeoVim config from dotfiles"
    fi

    return 0
}

# ============================================================================
# COMPREHENSIVE HEALTH CHECK
# ============================================================================

# Run all health checks and generate report
run_health_check() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           Dotfiles Health Check                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    local total_errors=0
    local total_warnings=0
    local check_results=()

    # Run individual checks
    echo "Running health checks..."
    echo ""

    # Symlink check
    if check_all_symlinks; then
        check_results+=("✓ Symlinks: PASS")
    else
        check_results+=("✗ Symlinks: FAIL")
        ((total_errors++))
    fi
    echo ""

    # Package check
    if check_packages; then
        check_results+=("✓ Packages: PASS")
    else
        check_results+=("⚠ Packages: WARNINGS")
        ((total_warnings++))
    fi
    echo ""

    # Config validation
    if check_configs; then
        check_results+=("✓ Configs: PASS")
    else
        check_results+=("⚠ Configs: WARNINGS")
        ((total_warnings++))
    fi
    echo ""

    # Dependencies check
    if check_dependencies_all; then
        check_results+=("✓ Dependencies: PASS")
    else
        check_results+=("✗ Dependencies: FAIL")
        ((total_errors++))
    fi
    echo ""

    # Integration checks
    if check_shell_integration; then
        check_results+=("✓ Shell Integration: PASS")
    else
        check_results+=("⚠ Shell Integration: WARNINGS")
        ((total_warnings++))
    fi
    echo ""

    check_wm_integration
    check_results+=("• WM Integration: CHECKED")
    echo ""

    check_editor_integration
    check_results+=("• Editor Integration: CHECKED")
    echo ""

    # Summary
    echo "════════════════════════════════════════════════════════════"
    echo "Health Check Summary:"
    echo ""

    for result in "${check_results[@]}"; do
        echo "  $result"
    done

    echo ""
    if [[ $total_errors -eq 0 && $total_warnings -eq 0 ]]; then
        success "All health checks passed!"
        return 0
    elif [[ $total_errors -eq 0 ]]; then
        warn "Health check completed with $total_warnings warning(s)"
        return 0
    else
        error "Health check failed: $total_errors error(s), $total_warnings warning(s)"
        return 1
    fi
}

# Quick health check (only critical items)
run_quick_health_check() {
    local errors=0

    for item in $(get_all_items); do
        if get_item_status "$item"; then
            # Item claims to be installed, verify it
            local item_var="ITEM_${item}"
            local detection
            local target_path

            detection=$(get_item_value "$item_var" "detection")
            target_path=$(get_item_value "$item_var" "target_path")
            target_path="$(eval echo "$target_path")"

            case "$detection" in
                symlink)
                    if [[ ! -L "$target_path" ]]; then
                        error "Broken installation: $item (symlink missing)"
                        ((errors++))
                    fi
                    ;;
                file)
                    if [[ ! -f "$target_path" ]]; then
                        error "Broken installation: $item (file missing)"
                        ((errors++))
                    fi
                    ;;
                dir)
                    if [[ ! -d "$target_path" ]]; then
                        error "Broken installation: $item (directory missing)"
                        ((errors++))
                    fi
                    ;;
                command)
                    if ! is_command_installed "$item"; then
                        error "Broken installation: $item (command not found)"
                        ((errors++))
                    fi
                    ;;
            esac
        fi
    done

    return $errors
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

export -f check_symlink_valid check_all_symlinks
export -f check_packages check_configs check_dependencies_all
export -f check_shell_integration check_wm_integration check_editor_integration
export -f run_health_check run_quick_health_check
