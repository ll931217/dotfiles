#!/usr/bin/env bash
#
# Script 05: Configure Window Manager based on system setup
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load DRY_RUN flag if set by parent
[[ -n "$DRY_RUN" ]] || DRY_RUN=false

# Source logging functions
LOG_FILE="/tmp/dotfiles-install.log"

log() {
    echo -e "\033[0;34m[INFO]\033[0m $*" | tee -a "$LOG_FILE"
}

success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $*" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "\033[1;33m[WARNING]\033[0m $*" | tee -a "$LOG_FILE"
}

# Helper function for dry-run execution
dry_run_cmd() {
    if [[ $DRY_RUN == true ]]; then
        log "[DRY RUN] Would execute: $*"
        return 0
    else
        eval "$@"
    fi
}

log "=== Configuring Window Manager ==="

# Get monitor information
detect_monitors_config() {
    if command -v xrandr &>/dev/null && xrandr &>/dev/null; then
        CONNECTED_MONITORS=$(xrandr --query 2>/dev/null | grep " connected" | awk '{print $1}')
        MONITOR_COUNT=$(echo "$CONNECTED_MONITORS" | wc -l)
        
        # Get monitor list as array
        mapfile -t MONITOR_ARRAY <<< "$CONNECTED_MONITORS"
    else
        # Default for Wayland or when X is not running
        CONNECTED_MONITORS="eDP-1"
        MONITOR_COUNT=1
        MONITOR_ARRAY=("eDP-1")
    fi
}

configure_i3() {
    log "Configuring i3-gaps for $MONITOR_COUNT monitor(s)"
    
    detect_monitors_config
    
    local i3_config="$HOME/.config/i3/config"
    local i3_config_dir=$(dirname "$i3_config")
    
    # Create i3 config directory
    mkdir -p "$i3_config_dir"
    
    # Copy base i3 config from repo
    if [[ -f "$REPO_ROOT/.config/i3/config" ]]; then
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would copy i3 config from repo to $i3_config"
        else
            cp "$REPO_ROOT/.config/i3/config" "$i3_config"
        fi
    else
        warn "Base i3 config not found in repository"
        return
    fi
    
    # Configure monitors in i3 config
    if [[ $MONITOR_COUNT -gt 1 ]]; then
        log "Configuring multi-monitor setup"
        
        # Get first two monitors
        local primary="${MONITOR_ARRAY[0]}"
        local secondary="${MONITOR_ARRAY[1]}"
        
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would configure multi-monitor in i3 config:"
            log "[DRY RUN]   Primary monitor: $primary"
            log "[DRY RUN]   Secondary monitor: $secondary"
            log "[DRY RUN]   Workspaces 1-9 → $primary"
            log "[DRY RUN]   Workspace 10 → $secondary"
            log "[DRY RUN]   Would update xrandr command and bar configuration"
        else
            # Update i3 config with monitor setup
            sed -i "s/workspace 1 output DP-0/workspace 1 output $primary/g" "$i3_config"
            sed -i "s/workspace 2 output DP-0/workspace 2 output $primary/g" "$i3_config"
            sed -i "s/workspace 3 output DP-0/workspace 3 output $primary/g" "$i3_config"
            sed -i "s/workspace 4 output DP-0/workspace 4 output $primary/g" "$i3_config"
            sed -i "s/workspace 5 output DP-0/workspace 5 output $primary/g" "$i3_config"
            sed -i "s/workspace 6 output DP-0/workspace 6 output $primary/g" "$i3_config"
            sed -i "s/workspace 7 output DP-0/workspace 7 output $primary/g" "$i3_config"
            sed -i "s/workspace 8 output DP-0/workspace 8 output $primary/g" "$i3_config"
            sed -i "s/workspace 9 output DP-0/workspace 9 output $primary/g" "$i3_config"
            sed -i "s/workspace 10 output HDMI-0/workspace 10 output $secondary/g"
            
            # Update autostart xrandr command
            sed -i "s|exec --no-startup-id xrandr --output DP-0 --primary --output HDMI-0 --auto --rotate left --left-of DP-0|exec --no-startup-id xrandr --output $primary --primary --output $secondary --auto --right-of $primary|g" "$i3_config"
            
            # Update i3status bar
            sed -i "s/output HDMI-0/output $secondary/g" "$i3_config"
            
            success "Multi-monitor i3 configuration: Primary=$primary, Secondary=$secondary"
        fi
    else
        log "Configuring single-monitor setup"
        
        local monitor="${MONITOR_ARRAY[0]}"
        
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would configure single-monitor in i3 config:"
            log "[DRY RUN]   Monitor: $monitor"
            log "[DRY RUN]   Would comment out multi-monitor workspace assignments"
            log "[DRY RUN]   Would comment out xrandr command"
            log "[DRY RUN]   Would set bar to display on all outputs"
        else
            # Update i3 config for single monitor
            sed -i "s/workspace 1 output DP-0/# workspace 1 output $monitor/g" "$i3_config"
            sed -i "s/workspace 2 output DP-0/# workspace 2 output $monitor/g" "$i3_config"
            sed -i "s/workspace 3 output DP-0/# workspace 3 output $monitor/g" "$i3_config"
            sed -i "s/workspace 4 output DP-0/# workspace 4 output $monitor/g" "$i3_config"
            sed -i "s/workspace 5 output DP-0/# workspace 5 output $monitor/g" "$i3_config"
            sed -i "s/workspace 6 output DP-0/# workspace 6 output $monitor/g" "$i3_config"
            sed -i "s/workspace 7 output DP-0/# workspace 7 output $monitor/g" "$i3_config"
            sed -i "s/workspace 8 output DP-0/# workspace 8 output $monitor/g" "$i3_config"
            sed -i "s/workspace 9 output DP-0/# workspace 9 output $monitor/g" "$i3_config"
            sed -i "s/workspace 10 output HDMI-0/# workspace 10 output $monitor/g"
            
            # Comment out multi-monitor xrandr command
            sed -i "s|^exec --no-startup-id xrandr|# exec --no-startup-id xrandr|g" "$i3_config"
            
            # Update i3status bar for single monitor
            sed -i "s/output HDMI-0/output all/g" "$i3_config"
            
            success "Single-monitor i3 configuration: $monitor"
        fi
    fi
    
    # VM-specific adjustments
    if [[ "$VM_TYPE" != "none" ]]; then
        log "Applying VM-specific i3 adjustments"
        
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would apply VM optimizations to i3 config:"
            log "[DRY RUN]   - Disable picom compositing"
            log "[DRY RUN]   - Reduce gaps from 5 to 2"
        else
            # Disable some effects that don't work well in VMs
            sed -i "s|^exec_always --no-startup-id picom|# exec_always --no-startup-id picom (disabled in VM)|g" "$i3_config"
            
            # Reduce gaps for VMs
            sed -i "s/^gaps inner 5/gaps inner 2/g" "$i3_config"
            
            success "VM adjustments applied"
        fi
    fi
    
    # Create i3status config
    local i3status_config="$HOME/.config/i3/i3status.conf"
    mkdir -p "$(dirname "$i3status_config")"
    
    if [[ -f "$REPO_ROOT/.config/i3/i3status.conf" ]]; then
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would copy i3status config from repo"
        else
            cp "$REPO_ROOT/.config/i3/i3status.conf" "$i3status_config"
        fi
    else
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would create basic i3status config"
        else
            # Create basic i3status config
            cat > "$i3status_config" << 'EOF'
general {
    colors = true
    interval = 5
}

order += "disk /"
order += "battery all"
order += "wireless _first_"
order += "ethernet _first_"
order += "load"
order += "tztime local"

wireless _first_ {
    format_up = "W: (%quality at %essid) %ip"
    format_down = "W: down"
}

ethernet _first_ {
    format_up = "E: %ip (%speed)"
    format_down = "E: down"
}

battery all {
    format = "%status %percentage %remaining"
}

tztime local {
    format = "%Y-%m-%d %H:%M:%S"
}

load {
    format = "%1min"
}

disk "/" {
    format = "%free"
}
EOF
        fi
    fi
}

configure_hyprland() {
    log "Configuring Hyprland for $MONITOR_COUNT monitor(s)"
    
    detect_monitors_config
    
    local hyprland_config="$HOME/.config/hypr/hyprland.conf"
    local hyprland_config_dir=$(dirname "$hyprland_config")
    
    # Create Hyprland config directory
    mkdir -p "$hyprland_config_dir"
    
    # Copy base Hyprland config from repo
    if [[ -f "$REPO_ROOT/.config/hypr/hyprland.conf" ]]; then
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would copy Hyprland config from repo to $hyprland_config"
        else
            cp "$REPO_ROOT/.config/hypr/hyprland.conf" "$hyprland_config"
        fi
    else
        warn "Base Hyprland config not found in repository, creating basic config"
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would create basic Hyprland config"
        else
            create_basic_hyprland_config "$hyprland_config"
        fi
    fi
    
    # Configure monitors
    if [[ $MONITOR_COUNT -gt 1 ]]; then
        log "Configuring multi-monitor setup for Hyprland"
        
        local primary="${MONITOR_ARRAY[0]}"
        local secondary="${MONITOR_ARRAY[1]}"
        
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would configure multi-monitor in Hyprland config:"
            log "[DRY RUN]   Primary: $primary (highres, auto, 1x scale)"
            log "[DRY RUN]   Secondary: $secondary (highres, auto, 1x scale)"
        else
            # Add monitor configuration to Hyprland config
            cat >> "$hyprland_config" << EOF

# Auto-configured monitors
monitor=$primary,highres,auto,1
monitor=$secondary,highres,auto,1,mirror
EOF
            
            success "Multi-monitor Hyprland configuration: Primary=$primary, Secondary=$secondary"
        fi
    else
        log "Configuring single-monitor setup for Hyprland"
        
        local monitor="${MONITOR_ARRAY[0]}"
        
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would configure single-monitor in Hyprland config:"
            log "[DRY RUN]   Monitor: $monitor (preferred, auto, 1x scale)"
        else
            # Add single monitor configuration
            cat >> "$hyprland_config" << EOF

# Auto-configured monitor
monitor=$monitor,preferred,auto,1
EOF
            
            success "Single-monitor Hyprand configuration: $monitor"
        fi
    fi
    
    # VM-specific adjustments
    if [[ "$VM_TYPE" != "none" ]]; then
        log "Applying VM-specific Hyprland adjustments"
        
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would apply VM optimizations to Hyprland config:"
            log "[DRY RUN]   - Disable blur"
            log "[DRY RUN]   - Disable animations"
        else
            # Disable blur and effects for VMs
            sed -i "s/^decoration:blur:enabled = true/decoration:blur:enabled = false/g" "$hyprland_config"
            
            # Reduce animations
            sed -i "s/^animations:enabled = true/animations:enabled = false/g" "$hyprland_config"
            
            success "VM adjustments applied"
        fi
    fi
    
    # Configure Waybar for Hyprland
    configure_waybar
}

configure_waybar() {
    log "Configuring Waybar for Hyprland"
    
    local waybar_config="$HOME/.config/waybar/config"
    local waybar_style="$HOME/.config/waybar/style.css"
    
    mkdir -p "$(dirname "$waybar_config")"
    
    # Copy waybar configs from repo if available
    if [[ -f "$REPO_ROOT/.config/waybar/config" ]]; then
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would copy Waybar config from repo"
        else
            cp "$REPO_ROOT/.config/waybar/config" "$waybar_config"
        fi
    else
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would create basic Waybar config"
        else
            create_basic_waybar_config "$waybar_config"
        fi
    fi
    
    if [[ -f "$REPO_ROOT/.config/waybar/style.css" ]]; then
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would copy Waybar style from repo"
        else
            cp "$REPO_ROOT/.config/waybar/style.css" "$waybar_style"
        fi
    else
        if [[ $DRY_RUN == true ]]; then
            log "[DRY RUN] Would create basic Waybar style"
        else
            create_basic_waybar_style "$waybar_style"
        fi
    fi
    
    success "Waybar configured"
}

create_basic_hyprland_config() {
    local config="$1"
    cat > "$config" << 'EOF'
# Autogenerated Hyprland config

# Input
input {
    kb_layout = us
    follow_mouse = 1
    sensitivity = 0
}

# General
general {
    gaps_in = 5
    gaps_out = 20
    border_size = 2
    col.active_border = rgba(33ccffee)
    col.inactive_border = rgba(595959aa)
    layout = dwindle
}

# Decoration
decoration {
    rounding = 10
    blur {
        enabled = true
        size = 3
        passes = 2
    }
    drop_shadow = yes
    shadow_range = 4
    shadow_render_power = 3
}

# Animations
animations {
    enabled = true
    bezier = myBezier, 0.05, 0.9, 0.1, 1.05
    animation = windows, 1, 7, myBezier
    animation = windowsOut, 1, 7, default, popin 80%
    animation = border, 1, 10, default
    animation = borderangle, 1, 8, default
    animation = fade, 1, 7, default
    animation = workspaces, 1, 6, default
}

# Keybindings
$mod = SUPER

bind = $mod, Return, exec, kitty
bind = $mod, Q, killactive,
bind = $mod, M, exit,
bind = $mod, E, exec, rofi -show drun
bind = $mod, Space, togglefloating,
bind = $mod, F, fullscreen
bind = $mod, 1, workspace, 1
bind = $mod, 2, workspace, 2
bind = $mod, 3, workspace, 3
bind = $mod, 4, workspace, 4
bind = $mod, 5, workspace, 5
bind = $mod SHIFT, 1, movetoworkspace, 1
bind = $mod SHIFT, 2, movetoworkspace, 2
bind = $mod SHIFT, 3, movetoworkspace, 3
bind = $mod SHIFT, 4, movetoworkspace, 4
bind = $mod SHIFT, 5, movetoworkspace, 5

# Media keys
bind = ,XF86AudioPlay, exec, playerctl play-pause
bind = ,XF86AudioNext, exec, playerctl next
bind = ,XF86AudioPrev, exec, playerctl previous
bind = ,XF86AudioMute, exec, wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
bind = ,XF86MonBrightnessUp, exec, brightnessctl set +5%
bind = ,XF86MonBrightnessDown, exec, brightnessctl set 5%-

# Startup
exec-once = waybar
exec-once = dunst
exec-once = fcitx5 -d
EOF
}

create_basic_waybar_config() {
    local config="$1"
    cat > "$config" << 'EOF'
{
    "layer": "top",
    "position": "top",
    "height": 30,
    "spacing": 0,
    "modules-left": ["hyprland/workspaces", "hyprland/mode", "hyprland/window"],
    "modules-center": ["clock"],
    "modules-right": ["pulseaudio", "network", "cpu", "memory", "battery", "tray"],
    
    "hyprland/workspaces": {
        "disable-scroll": true,
        "all-outputs": true,
        "format": "{name}"
    },
    
    "clock": {
        "format": "{:%Y-%m-%d %H:%M:%S}",
        "tooltip-format": "<tt>{calendar}</tt>"
    },
    
    "pulseaudio": {
        "scroll-step": 5,
        "format": "{icon} {volume}%",
        "format-muted": "Muted",
        "format-icons": {
            "default": ["", "", ""]
        },
        "on-click": "pavucontrol"
    },
    
    "network": {
        "format-wifi": " {signalStrength}%",
        "format-ethernet": " {ipaddr}",
        "format-disconnected": " Disconnected",
        "tooltip-format": "{ifname}: {ipaddr}"
    },
    
    "cpu": {
        "format": " {usage}%",
        "tooltip": true
    },
    
    "memory": {
        "format": " {}%"
    },
    
    "battery": {
        "states": {
            "warning": 30,
            "critical": 15
        },
        "format": "{icon} {capacity}%",
        "format-charging": " {capacity}%",
        "format-plugged": " {capacity}%",
        "format-icons": ["", "", "", "", ""]
    },
    
    "tray": {
        "icon-size": 21,
        "spacing": 10
    }
}
EOF
}

create_basic_waybar_style() {
    local style="$1"
    cat > "$style" << 'EOF'
* {
    font-family: "JetBrains Mono Nerd Font", "Font Awesome 6 Free", monospace;
    font-size: 14px;
    min-height: 0;
    margin: 0;
    padding: 0;
}

window#waybar {
    background: #1e1e2e;
    color: #cdd6f4;
}

tooltip {
    background: #1e1e2e;
    border: 1px solid #313244;
}

tooltip label {
    color: #cdd6f4;
}

#workspaces {
    margin: 0 8px;
}

#workspaces button {
    padding: 0 10px;
    color: #45475a;
    background: #1e1e2e;
}

#workspaces button.active {
    color: #cdd6f4;
    background: #313244;
}

#clock {
    padding: 0 10px;
}

#pulseaudio, #network, #cpu, #memory, #battery {
    padding: 0 10px;
}

#tray {
    padding: 0 10px;
}
EOF
}

# Main configuration logic
if [[ "$WM" == "i3" ]]; then
    configure_i3
elif [[ "$WM" == "hyprland" ]]; then
    configure_hyprland
else
    warn "Unknown window manager: $WM"
fi

success "Window Manager configuration script completed"
