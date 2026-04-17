#!/usr/bin/env bash
# If no window with instance "special" exists, launch it
if ! xdotool search --classname "special-scratchpad" >/dev/null 2>&1; then
  alacritty --class "special-scratchpad,special-scratchpad" &
  sleep 0.5 # wait for window to open before showing scratchpad
fi

i3-msg '[instance="special-scratchpad"] scratchpad show'
