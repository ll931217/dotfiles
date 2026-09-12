#!/bin/bash
sketchybar --add item wm_mode left \
  --set wm_mode drawing=off background.drawing=on background.color=0xffe7894c label.color=0xff0f0f0f \
  --add event aerospace_workspace_change \
  --add item aerospace_anchor left \
  --set aerospace_anchor drawing=off \
  --add item aerospace_dummy left \
  --set aerospace_dummy drawing=off updates=on update_freq=30 \
    script="/bin/bash \"$CONFIG_DIR/plugins/spaces.sh\"" \
  --subscribe aerospace_dummy aerospace_workspace_change front_app_switched space_windows_change system_woke display_change
/bin/bash "$CONFIG_DIR/plugins/spaces.sh"
