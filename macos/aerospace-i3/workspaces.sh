#!/bin/bash
set -euo pipefail

# Query actual state: forced updates do not contain workspace event variables.
focused=$(aerospace list-workspaces --focused) || exit 0
[ -n "$focused" ] || exit 0
windows=$(aerospace list-windows --all --format '%{workspace}|%{app-name}') || exit 0
monitors=$(aerospace list-monitors) || exit 0
args=(--remove '/space\..*/')

while IFS='|' read -r monitor _; do
  monitor=${monitor//[[:space:]]/}
  [ -n "$monitor" ] || continue
  workspaces=$(aerospace list-workspaces --monitor "$monitor") || exit 0
  while IFS= read -r sid; do
    [ -n "$sid" ] || continue
    # Workspace names enter both item names and shell click handlers.
    [[ "$sid" =~ ^[a-zA-Z0-9_-]+$ ]] || continue
    count=$(printf '%s\n' "$windows" | awk -F '|' -v sid="$sid" '$1 == sid {n++} END {print n+0}')
    color=0xffb8afa0
    background=off
    if [ "$sid" = "$focused" ]; then
      color=0xff0f0f0f
      background=on
    fi
    label=""
    [ "$count" -eq 0 ] || label="$count"
    args+=(--add item "space.$sid" left
      --set "space.$sid" "display=$monitor" "icon=$sid" "label=$label"
      "icon.color=$color" "label.color=$color"
      "background.drawing=$background" background.color=0xffe7894c
      background.corner_radius=4 "click_script=aerospace workspace $sid"
      --move "space.$sid" before aerospace_anchor)
  done <<< "$workspaces"
done <<< "$monitors"

sketchybar "${args[@]}"
