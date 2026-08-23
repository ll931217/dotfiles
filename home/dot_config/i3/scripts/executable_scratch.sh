#!/usr/bin/env bash

TERMINAL="alacritty"
CLASS_PREFIX="default"
EXTRA_ARGS=""

usage() {
  echo "Usage: $0 [-t terminal] [-c class_prefix] [-a 'extra args']"
  echo "  -t  Terminal emulator to launch (default: alacritty)"
  echo "  -c  WM_CLASS prefix for the scratchpad window (default: cc)"
  echo "  -a  Extra arguments passed to the terminal"
  exit 1
}

while getopts ":t:c:a:h" opt; do
  case $opt in
    t) TERMINAL="$OPTARG" ;;
    c) CLASS_PREFIX="$OPTARG" ;;
    a) EXTRA_ARGS="$OPTARG" ;;
    h) usage ;;
    :) echo "Option -$OPTARG requires an argument." >&2; usage ;;
    \?) echo "Unknown option: -$OPTARG" >&2; usage ;;
  esac
done

INSTANCE="${CLASS_PREFIX}-scratchpad"

source "$HOME/.config/i3/scripts/common.sh"

if ! xdotool search --classname "$INSTANCE" >/dev/null 2>&1; then
  case "$TERMINAL" in
    alacritty)
      alacritty --class "$INSTANCE,$INSTANCE" $EXTRA_ARGS &
      ;;
    kitty)
      kitty --class "$INSTANCE" $EXTRA_ARGS &
      ;;
    foot)
      foot --app-id "$INSTANCE" $EXTRA_ARGS &
      ;;
    wezterm)
      wezterm start --class "$INSTANCE" $EXTRA_ARGS &
      ;;
    xterm)
      xterm -name "$INSTANCE" $EXTRA_ARGS &
      ;;
    *)
      "$TERMINAL" $EXTRA_ARGS &
      ;;
  esac
  sleep 0.5
fi

i3-msg -t get_tree | INSTANCE="$INSTANCE" python3 -c "
import json, os, sys, subprocess
current = os.environ['INSTANCE']
def walk(n, ws, out):
    if n.get('type') == 'workspace':
        ws = n.get('name')
    wp = n.get('window_properties') or {}
    inst = wp.get('instance', '')
    if (inst.endswith('-scratchpad')
        and inst != current
        and ws is not None
        and ws != '__i3_scratch'):
        out.append(inst)
    for c in n.get('nodes', []) + n.get('floating_nodes', []):
        walk(c, ws, out)
out = []
walk(json.load(sys.stdin), None, out)
for i in out:
    subprocess.run(['i3-msg', f'[instance=\"{i}\"] move scratchpad'])
"

i3-msg "[instance=\"$INSTANCE\"] scratchpad show"
sleep 0.05
i3-msg "[instance=\"$INSTANCE\"] move position $px $py"
