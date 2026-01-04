#!/bin/bash
# Simple script to toggle Alacritty border based on focus
# This runs in the background and monitors i3 focus events

LOG_FILE="$HOME/.scripts/alacritty_border.log"
FOCUSED_BORDER=3
UNFOCUSED_BORDER=0

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Kill any existing instances (but not this one)
OTHER_INSTANCES=$(pgrep -f "alacritty_border_simple.sh" | grep -v "^$$")
if [ -n "$OTHER_INSTANCES" ]; then
    echo "$OTHER_INSTANCES" | xargs kill 2>/dev/null
    log "Killed existing instances"
fi

log "Starting Alacritty border monitor (PID: $$)..."

# Monitor i3 events
i3-msg -t subscribe '["window"]' -- | while read -r line; do
    # Check if this is a focus event
    if echo "$line" | grep -q '"change":"focus"'; then
        # Get the focused window's class
        FOCUSED_WINDOW=$(i3-msg -t get_tree | jq -r '.. | select(.focused? == true) | .window_class // empty')
        
        if [ "$FOCUSED_WINDOW" = "Alacritty" ]; then
            log "Alacritty focused - setting border to $FOCUSED_BORDER"
            i3-msg "[class=\"Alacritty\"] border pixel $FOCUSED_BORDER"
        else
            log "Alacritty unfocused - setting border to $UNFOCUSED_BORDER"
            i3-msg "[class=\"Alacritty\"] border pixel $UNFOCUSED_BORDER"
        fi
    fi
done
