#!/usr/bin/env bash
#
# Component registry for dotfiles installation system
# Defines all categories and installable items using associative arrays
#

# Get repo root and home
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export REPO_ROOT

# ============================================================================
# CATEGORIES
# ============================================================================

declare -A CATEGORY_SHELLS=(
    [name]="Shells"
    [description]="Shell configurations and prompts"
    [icon]="🐚"
)

declare -A CATEGORY_TERMINALS=(
    [name]="Terminal Emulators"
    [description]="Terminal emulator configurations"
    [icon]="🖥️"
)

declare -A CATEGORY_WM=(
    [name]="Window Managers"
    [description]="Window Manager configurations (i3/Hyprland)"
    [icon]="🪟"
    [exclusive]="true"
)

declare -A CATEGORY_EDITOR=(
    [name]="Editor"
    [description]="Editor configurations (NeoVim/Vim)"
    [icon]="📝"
)

declare -A CATEGORY_AI=(
    [name]="AI Tools"
    [description]="AI/LLM agent configurations"
    [icon]="🤖"
)

declare -A CATEGORY_FILE_MANAGERS=(
    [name]="File Managers"
    [description]="File manager configurations"
    [icon]="📁"
)

declare -A CATEGORY_UTILITIES=(
    [name]="Utilities"
    [description]="System utility configurations"
    [icon]="🔧"
)

declare -A CATEGORY_BROWSER=(
    [name]="Browser"
    [description]="Browser configurations"
    [icon]="🌐"
)

declare -A CATEGORY_FONTS=(
    [name]="Fonts"
    [description]="Font installations"
    [icon]="🔤"
)

declare -A CATEGORY_BASE_DEPS=(
    [name]="Base Dependencies"
    [description]="Core system dependencies"
    [icon]="📦"
)

# List of all categories (order for display)
CATEGORIES=(
    "SHELLS"
    "TERMINALS"
    "WM"
    "EDITOR"
    "AI"
    "FILE_MANAGERS"
    "UTILITIES"
    "BROWSER"
    "FONTS"
    "BASE_DEPS"
)

# ============================================================================
# SHELLS
# ============================================================================

declare -A ITEM_ZSH=(
    [name]="ZSH"
    [category]="shells"
    [config_path]="$REPO_ROOT/.zshrc"
    [target_path]="$HOME/.zshrc"
    [detection]="symlink"
    [dependencies]="zsh"
    [packages]="zsh"
    [description]="ZSH shell configuration with starship prompt"
)

declare -A ITEM_STARSHIP=(
    [name]="Starship Prompt"
    [category]="shells"
    [config_path]="$REPO_ROOT/.config/starship.toml"
    [target_path]="$HOME/.config/starship.toml"
    [detection]="symlink"
    [dependencies]="starship"
    [packages]="starship"
    [description]="Cross-shell prompt with rich customization"
)

declare -A ITEM_TMUX=(
    [name]="Tmux"
    [category]="shells"
    [config_path]="$REPO_ROOT/.tmux.conf"
    [target_path]="$HOME/.tmux.conf"
    [detection]="symlink"
    [dependencies]="tmux"
    [packages]="tmux"
    [description]="Terminal multiplexer configuration"
)

# ============================================================================
# TERMINALS
# ============================================================================

declare -A ITEM_ALACRITTY=(
    [name]="Alacritty"
    [category]="terminals"
    [config_path]="$REPO_ROOT/.config/alacritty"
    [target_path]="$HOME/.config/alacritty"
    [detection]="symlink"
    [dependencies]="alacritty"
    [packages]="alacritty"
    [description]="Fast, GPU-accelerated terminal emulator"
)

declare -A ITEM_KITTY=(
    [name]="Kitty"
    [category]="terminals"
    [config_path]="$REPO_ROOT/.config/kitty"
    [target_path]="$HOME/.config/kitty"
    [detection]="symlink"
    [dependencies]="kitty"
    [packages]="kitty"
    [description]="Modern, GPU-accelerated terminal emulator"
)

declare -A ITEM_GHOSTTY=(
    [name]="Ghostty"
    [category]="terminals"
    [config_path]="$REPO_ROOT/.config/ghostty/config"
    [target_path]="$HOME/.config/ghostty/config"
    [detection]="symlink"
    [dependencies]="ghostty"
    [packages]="ghostty"
    [description]="Modern terminal emulator (AUR)"
    [aur]="true"
)

declare -A ITEM_WEZTERM=(
    [name]="WezTerm"
    [category]="terminals"
    [config_path]="$REPO_ROOT/.config/wezterm"
    [target_path]="$HOME/.config/wezterm"
    [detection]="symlink"
    [dependencies]="wezterm"
    [packages]="wezterm"
    [description]="GPU-accelerated terminal emulator and multiplexer"
)

# ============================================================================
# WINDOW MANAGERS
# ============================================================================

declare -A ITEM_I3=(
    [name]="i3-gaps"
    [category]="wm"
    [config_path]="$REPO_ROOT/.config/i3"
    [target_path]="$HOME/.config/i3"
    [detection]="symlink"
    [dependencies]="i3-gaps i3status i3blocks rofi feh polybar"
    [packages]="i3-wm i3status i3blocks rofi feh polybar xorg-server xorg-xinit"
    [conflicts]="HYPRLAND"
    [wm_type]="x11"
    [description]="Tiling window manager for X11 (more gaps, features)"
)

declare -A ITEM_HYPRLAND=(
    [name]="Hyprland"
    [category]="wm"
    [config_path]="$REPO_ROOT/.config/hypr"
    [target_path]="$HOME/.config/hypr"
    [detection]="symlink"
    [dependencies]="hyprland waybar waybar-hyprland wlogout wlsunset"
    [packages]="hyprland waybar waybar-hyprland wlogout wlsunset"
    [conflicts]="I3"
    [wm_type]="wayland"
    [description]="Dynamic tiling Wayland compositor"
)

# ============================================================================
# EDITOR
# ============================================================================

declare -A ITEM_NEONVIM=(
    [name]="NeoVim"
    [category]="editor"
    [config_path]="$REPO_ROOT/.vimrc"
    [target_path]="$HOME/.vimrc"
    [detection]="file"
    [binary]="nvim"
    [dependencies]="neovim"
    [packages]="neovim"
    [description]="NeoVim with LazyVim configuration"
    [module]="06-neovim.sh"
)

declare -A ITEM_VIM=(
    [name]="Vim"
    [category]="editor"
    [config_path]="$REPO_ROOT/.vimrc"
    [target_path]="$HOME/.vimrc"
    [detection]="file"
    [dependencies]="vim"
    [packages]="vim"
    [description]="Vim configuration with plugins"
)

# ============================================================================
# AI TOOLS
# ============================================================================

declare -A ITEM_CLAUDE=(
    [name]="Claude Code"
    [category]="ai"
    [config_path]="$REPO_ROOT/.claude"
    [target_path]="$HOME/.claude"
    [detection]="symlink"
    [dependencies]=""
    [packages]=""
    [description]="Claude Code AI assistant configuration"
)

# Future items can be added here for Continue.dev, Cursor, etc.

# ============================================================================
# FILE MANAGERS
# ============================================================================

declare -A ITEM_RANGER=(
    [name]="Ranger"
    [category]="file_managers"
    [config_path]="$REPO_ROOT/.config/ranger"
    [target_path]="$HOME/.config/ranger"
    [detection]="symlink"
    [dependencies]="ranger"
    [packages]="ranger"
    [description]="TUI file manager with vi key bindings"
)

declare -A ITEM_YAZI=(
    [name]="Yazi"
    [category]="file_managers"
    [config_path]="$REPO_ROOT/.config/yazi"
    [target_path]="$HOME/.config/yazi"
    [detection]="symlink"
    [dependencies]="yazi"
    [packages]="yazi"
    [description]="Blazing fast terminal file manager"
)

# ============================================================================
# UTILITIES
# ============================================================================

declare -A ITEM_BTOP=(
    [name]="Btop"
    [category]="utilities"
    [config_path]="$REPO_ROOT/.config/btop"
    [target_path]="$HOME/.config/btop"
    [detection]="symlink"
    [dependencies]="btop"
    [packages]="btop"
    [description]="Resource monitor with beautiful UI"
)

declare -A ITEM_DUNST=(
    [name]="Dunst"
    [category]="utilities"
    [config_path]="$REPO_ROOT/.config/dunst"
    [target_path]="$HOME/.config/dunst"
    [detection]="symlink"
    [dependencies]="dunst"
    [packages]="dunst"
    [description]="Lightweight notification daemon"
)

declare -A ITEM_ROFI=(
    [name]="Rofi"
    [category]="utilities"
    [config_path]="$REPO_ROOT/.config/rofi"
    [target_path]="$HOME/.config/rofi"
    [detection]="symlink"
    [dependencies]="rofi"
    [packages]="rofi"
    [description]="Window switcher, application launcher and dmenu replacement"
)

declare -A ITEM_CAVA=(
    [name]="Cava"
    [category]="utilities"
    [config_path]="$REPO_ROOT/.config/cava"
    [target_path]="$HOME/.config/cava"
    [detection]="symlink"
    [dependencies]="cava"
    [packages]="cava"
    [description]="Console audio visualizer"
)

declare -A ITEM_FASTFETCH=(
    [name]="Fastfetch"
    [category]="utilities"
    [config_path]="$REPO_ROOT/.config/fastfetch"
    [target_path]="$HOME/.config/fastfetch"
    [detection]="symlink"
    [dependencies]="fastfetch"
    [packages]="fastfetch"
    [description]="Neofetch replacement with more customization"
)

declare -A ITEM_PICOM=(
    [name]="Picom"
    [category]="utilities"
    [config_path]="$REPO_ROOT/.config/picom.conf"
    [target_path]="$HOME/.config/picom.conf"
    [detection]="file"
    [dependencies]="picom"
    [packages]="picom"
    [description]="Lightweight compositor for X11"
)

# ============================================================================
# BROWSER
# ============================================================================

declare -A ITEM_QUTEBROWSER=(
    [name]="Qutebrowser"
    [category]="browser"
    [config_path]="$REPO_ROOT/.config/qutebrowser"
    [target_path]="$HOME/.config/qutebrowser"
    [detection]="symlink"
    [dependencies]="qutebrowser"
    [packages]="qutebrowser"
    [description]="Keyboard-driven browser"
)

# ============================================================================
# FONTS
# ============================================================================

declare -A ITEM_FONTS=(
    [name]="System Fonts"
    [category]="fonts"
    [config_path]="$REPO_ROOT/.local/share/fonts"
    [target_path]="$HOME/.local/share/fonts"
    [detection]="dir"
    [dependencies]=""
    [packages]="jetbrains-mono-font noto-fonts noto-fonts-cjk"
    [description]="Nerd Fonts, JetBrains Mono, Noto CJK"
    [module]="02-fonts.sh"
)

# ============================================================================
# BASE DEPENDENCIES
# ============================================================================

declare -A ITEM_BASE_DEPS=(
    [name]="Core Dependencies"
    [category]="base_deps"
    [config_path]=""
    [target_path]=""
    [detection]="command"
    [dependencies]=""
    [packages]="git curl wget jq base-devel fzf bat eza ripgrep fd zoxide atuin direnv"
    [description]="Core utilities and development tools"
    [module]="01-dependencies.sh"
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Get all items for a category
get_items_for_category() {
    local category="$1"
    local items=()

    for item in $(get_all_items); do
        local item_cat="${ITEM_${item}[category]}"
        item_cat="${!item_cat}"
        if [[ "$item_cat" == "$category" ]]; then
            items+=("$item")
        fi
    done

    printf '%s\n' "${items[@]}"
}

# Get category by name
get_category_by_name() {
    local name="$1"
    for cat in "${CATEGORIES[@]}"; do
        local cat_name="CATEGORY_${cat}[name]"
        cat_name="${!cat_name}"
        if [[ "$cat_name" == "$name" ]]; then
            echo "$cat"
            return 0
        fi
    done
    return 1
}

# Get item count for a category
get_category_item_count() {
    local category="$1"
    local count=0

    for item in $(get_all_items); do
        local item_cat="${ITEM_${item}[category]}"
        item_cat="${!item_cat}"
        if [[ "$item_cat" == "$category" ]]; then
            ((count++))
        fi
    done

    echo "$count"
}

# Get all item names
get_all_items() {
    # List all defined items
    printf '%s\n' \
        ZSH STARSHIP TMUX \
        ALACRITTY KITTY GHOSTTY WEZTERM \
        I3 HYPRLAND \
        NEONVIM VIM \
        CLAUDE \
        RANGER YAZI \
        BTOP DUNST ROFI CAVA FASTFETCH PICOM \
        QUTEBROWSER \
        FONTS \
        BASE_DEPS | sort
}

# Check if item has conflicts
get_item_conflicts() {
    local item="$1"
    local conflicts="${ITEM_${item}[conflicts]}"
    conflicts="${!conflicts}"
    echo "$conflicts"
}

# Check if category is exclusive
is_category_exclusive() {
    local category="$1"
    local exclusive="CATEGORY_${category}[exclusive]"
    exclusive="${!exclusive}"
    [[ "$exclusive" == "true" ]]
}

# Export helper functions
export -f get_items_for_category get_category_by_name get_category_item_count
export -f get_all_items get_item_conflicts is_category_exclusive
