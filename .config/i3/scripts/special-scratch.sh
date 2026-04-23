#!/usr/bin/env bash

WIN_W=1600
WIN_H=800
POLYBAR_H=40

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

px=$((ox + (ow - WIN_W - 220) / 2))
py=$((oy + (oh - POLYBAR_H - WIN_H - 100) / 2))

if ! xdotool search --classname "special-scratchpad" >/dev/null 2>&1; then
  alacritty --class "special-scratchpad,special-scratchpad" &
  sleep 0.5
fi

i3-msg '[instance="special-scratchpad"] scratchpad show'
sleep 0.05
i3-msg "[instance=\"special-scratchpad\"] move position $px $py"
