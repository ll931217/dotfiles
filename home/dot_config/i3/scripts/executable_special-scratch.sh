#!/usr/bin/env bash
POLYBAR_H=40
WIN_SCALE=0.9 # 80% of screen size

focused_output=$(i3-msg -t get_workspaces | python3 -c "
import json,sys
ws=json.load(sys.stdin)
print(next(w for w in ws if w['focused'])['output'])
")

read -r ow oh ox oy < <(xrandr --query | awk -v out="$focused_output" '
  $1==out && /connected/ {
    match($0, /([0-9]+)x([0-9]+)\+([0-9]+)\+([0-9]+)/, a)
    print a[1], a[2], a[3], a[4]; exit
  }
')

WIN_W=$(echo "$ow $WIN_SCALE" | awk '{printf "%d", $1 * $2}')
WIN_H=$(echo "$oh $WIN_SCALE" | awk '{printf "%d", $1 * $2}')

px=$((ox + (ow - WIN_W) / 2))
py=$((oy + POLYBAR_H + (oh - POLYBAR_H - WIN_H) / 2))

if ! xdotool search --classname "special-scratchpad" >/dev/null 2>&1; then
  alacritty --class "special-scratchpad,special-scratchpad" \
    --override window.dimensions.columns=0 \
    --override window.dimensions.lines=0 &
  sleep 0.5
fi

# Fixes flashing in
i3-msg "[instance=\"special-scratchpad\"] scratchpad show; \
        [instance=\"special-scratchpad\"] resize set $WIN_W $WIN_H; \
        [instance=\"special-scratchpad\"] move position $px $py"
