#!/usr/bin/env bash

i3-msg -t get_workspaces | jq -r 'sort_by(.num) | map(.num as $num | .focused as $focused | .name as $name |
  if $focused then
    "%{B#94e2d5}%{F#181825} \($name)%{F-}%{B-}"
  elif $num < (.[].focused | select(. == true) | map(.num) | .[0]) then
    "%{F#bac2de} \($name)%{F-}"
  else
    "%{B#45475a}%{F#bac2de} \($name)%{F-}%{B-}"
  end
) | join("  ")
