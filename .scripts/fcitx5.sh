#!/bin/bash

# Detect current window manager from process list
if pgrep -x "Hyprland" >/dev/null; then
  export QT_IM_MODULE="wayland;fcitx"
  export XMODIFIERS=@im=fcitx
  echo "Detected Hyprland. Environment variables set."
elif pgrep -x "i3" >/dev/null; then
  export GTK_IM_MODULE=fcitx
  export QT_IM_MODULE=fcitx
  export XMODIFIERS=@im=fcitx
  echo "Detected i3wm. Environment variables set."
else
  echo "Could not detect Hyprland or i3wm."
fi
