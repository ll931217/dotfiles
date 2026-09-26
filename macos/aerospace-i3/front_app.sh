#!/bin/bash
set -euo pipefail
app=${INFO:-}
if [ "${SENDER:-}" != front_app_switched ] || [ -z "$app" ]; then
  app=$(aerospace list-windows --focused --format '%{app-name}') || exit 0
fi
[ -n "$app" ] || exit 0
sketchybar --set "${NAME:-front_app}" "label=$app" background.drawing=on icon.color=0xff0f0f0f label.color=0xff0f0f0f \
  "icon=$("$CONFIG_DIR/plugins/icons.sh" "$app")"
