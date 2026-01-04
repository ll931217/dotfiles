#!/bin/bash
# Simple script to toggle Alacritty border based on focus
# Uses polling instead of subscribe for better reliability

LOG_FILE="$HOME/.scripts/alacritty_border.log"
FOCUSED_BORDER=3
UNFOCUSED_BORDER=0
POLL_INTERVAL=0.5

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Kill any existing instances
OTHER_INSTANCES=$(pgrep -f "alacritty_border_poll.sh" | grep -v "^$$")
if [ -n "$OTHER_INSTANCES" ]; then
    echo "$OTHER_INSTANCES" | xargs kill 2>/dev/null
    log "Killed existing instances"
fi

log "Starting Alacritty border monitor (PID: $$)..."
log "Polling interval: ${POLL_INTERVAL}s"
log "Focused border: ${FOCUSED_BORDER}px, Unfocused: ${UNFOCUSED_BORDER}px"

LAST_STATE=""

while true; do
    # Get the focused window's class
    FOCUSED_WINDOW=$(i3-msg -t get_tree 2>/dev/null | jq -r '.. | objects | select(.focused? == true) | .window_properties.class // empty' 2>/dev/null)
    
    CURRENT_STATE=""
    if [ "$FOCUSED_WINDOW" = "Alacritty" ]; then
        CURRENT_STATE="focused"
    else
        CURRENT_STATE="unfocused"
    fi
    
    # Only update if state changed
    if [ "$CURRENT_STATE" != "$LAST_STATE" ]; then
        if [ "$CURRENT_STATE" = "focused" ]; then
            log "Alacritty focused - setting border to $FOCUSED_BORDER"
            i3-msg "[class=\"Alacritty\"] border pixel $FOCUSED_BORDER" 2>/dev/null
        else
            log "Alacritty unfocused - setting border to $UNFOCUSED_BORDER"
            i3-msg "[class=\"Alacritty\"] border pixel $UNFOCUSED_BORDER" 2>/dev/null
        fi
        LAST_STATE="$CURRENT_STATE"
    fi
    
    sleep $POLL_INTERVAL
done
