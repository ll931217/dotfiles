#!/bin/bash
# Warm, high-contrast palette from the i3 configuration.
export ITEM_COLOR=0xff0f0f0f
export ACCENT_COLOR=0xffe7894c
sketchybar --bar height=30 color=0xff0f0f0f blur_radius=0 padding_left=8 padding_right=8 \
  --default icon.color=0xfff2ecdd label.color=0xfff2ecdd \
    background.color="$ACCENT_COLOR" background.corner_radius=4 background.drawing=off
