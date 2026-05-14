#!/usr/bin/env bash

WIN_W=1800
WIN_H=900
POLYBAR_H=0

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

px=$((ox + (ow - WIN_W) / 2))
py=$((oy + (oh - POLYBAR_H - WIN_H) / 2))
