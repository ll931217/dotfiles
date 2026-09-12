#!/bin/bash
set -euo pipefail

is_safe_workspace_name() {
  [[ "$1" =~ ^[a-zA-Z0-9_-]+$ ]]
}

# Workspace switching should never rebuild the bar. AeroSpace supplies both
# names, so update only the two affected highlights without querying its tree.
if [ "${SENDER:-}" = "aerospace_workspace_change" ]; then
  focused=${FOCUSED_WORKSPACE:-}
  previous=${PREV_WORKSPACE:-}
  args=()

  if [ "$previous" != "$focused" ] && is_safe_workspace_name "$previous"; then
    args+=(--set "space.$previous" icon.color=0xfff2ecdd background.drawing=off)
  fi
  if is_safe_workspace_name "$focused"; then
    args+=(--set "space.$focused" icon.color=0xff0f0f0f \
      background.color=0xffe7894c background.drawing=on)
  fi

  [ "${#args[@]}" -eq 0 ] || sketchybar "${args[@]}"
  exit 0
fi

# Query actual state: forced updates do not contain workspace event variables.
focused=$(aerospace list-workspaces --focused) || exit 0
[ -n "$focused" ] || exit 0
monitors=$(aerospace list-monitors) || exit 0
args=(--remove '/space\..*/')

while IFS='|' read -r monitor _; do
  monitor=${monitor//[[:space:]]/}
  [ -n "$monitor" ] || continue
  workspaces=$(aerospace list-workspaces --monitor "$monitor") || exit 0
  while IFS= read -r sid; do
    [ -n "$sid" ] || continue
    # Workspace names enter both item names and shell click handlers.
    is_safe_workspace_name "$sid" || continue
    color=0xfff2ecdd
    background=off
    if [ "$sid" = "$focused" ]; then
      color=0xff0f0f0f
      background=on
    fi
    args+=(--add item "space.$sid" left
      --set "space.$sid" "display=$monitor" "icon=$sid" label="" label.drawing=off icon.padding_left=8 icon.padding_right=8
      "icon.color=$color" "label.color=$color"
      background.color=0xffe7894c "background.drawing=$background"
      background.corner_radius=4 "click_script=aerospace workspace $sid"
      --move "space.$sid" before aerospace_anchor)
  done <<< "$workspaces"
done <<< "$monitors"

sketchybar "${args[@]}"
