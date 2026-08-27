#!/usr/bin/env bash

# Ensure we're in a valid working directory
cd "$HOME" || exit 1

# Kill existing polybar instances
killall -q polybar

# Wait until all polybar processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

# Launch polybar on all connected monitors
if type "polybar" >/dev/null 2>&1; then
    for m in $(polybar --list-monitors | cut -d":" -f1); do
        MONITOR=$m polybar --reload main &
    done
else
    echo "Polybar not found"
fi

echo "Polybar launched..."
