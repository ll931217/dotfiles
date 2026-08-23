#!/usr/bin/env bash

icon="$HOME/Pictures/icon.png"
tmpbg='/tmp/screen.png'

(($#)) && { icon=$1; }

scrot "$tmpbg"
magick "$tmpbg" -scale 10% -scale 1000% "$tmpbg"
magick "$tmpbg" "$icon" -gravity center -composite -matte "$tmpbg"
i3lock -u -i "$tmpbg"
