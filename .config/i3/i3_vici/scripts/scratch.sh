#!/usr/bin/env bash

# TERMINAL="alacritty"
TERMINAL="st"
# TERMINAL="wezterm"
# TERMINAL="ghostty"
CLASS_PREFIX="default"
EXTRA_ARGS=""
INSTANCE_OVERRIDE=""

usage() {
  echo "Usage: $0 [-t terminal] [-c class_prefix] [-a 'extra args']"
  echo "  -t  Terminal emulator to launch (default: alacritty)"
  echo "  -c  WM_CLASS prefix for the scratchpad window (default: cc)"
  echo "  -a  Extra arguments passed to the terminal"
  exit 1
}

while getopts ":t:c:a:i:h" opt; do
  case $opt in
  t) TERMINAL="$OPTARG" ;;
  c) CLASS_PREFIX="$OPTARG" ;;
  a) EXTRA_ARGS="$OPTARG" ;;
  i) INSTANCE_OVERRIDE="$OPTARG" ;;
  h) usage ;;
  :)
    echo "Option -$OPTARG requires an argument." >&2
    usage
    ;;
  \?)
    echo "Unknown option: -$OPTARG" >&2
    usage
    ;;
  esac
done

# -i lets callers match a window whose WM_CLASS instance they can't control
# (e.g. Chrome PWAs report instance=crx_<appid> and ignore --class when a
# browser process for the profile already exists).
INSTANCE="${INSTANCE_OVERRIDE:-${CLASS_PREFIX}-scratchpad}"

# Serialize concurrent invocations so a double-press can't spawn duplicates.
LOCKFILE="/tmp/scratch-${INSTANCE}.lock"
LOGFILE="/tmp/scratch-${INSTANCE}.log"
exec 9>"$LOCKFILE"
if ! flock -n 9; then
  printf '[%s] pid=%d lock held on %s, bailing\n' \
    "$(date '+%F %T')" "$$" "$LOCKFILE" | tee -a "$LOGFILE" >&2
  exit 0
fi

source "$HOME/.config/i3/scripts/common.sh"

exists() {
  i3-msg -t get_tree |
    jq -e --arg inst "$INSTANCE" \
      'first(.. | objects | select(.window_properties?.instance == $inst)) // empty' \
      >/dev/null
}

if ! exists; then
  # 9>&- closes the lock fd in the forked child so the flock doesn't outlive
  # this script. Otherwise alacritty (and its child claude/jd) inherit fd 9
  # and hold the lock for their entire lifetime, making every later toggle bail.
  case "$TERMINAL" in
  alacritty)
    alacritty --class "$INSTANCE,$INSTANCE" $EXTRA_ARGS 9>&- &
    ;;
  kitty)
    kitty --class "$INSTANCE" $EXTRA_ARGS 9>&- &
    ;;
  foot)
    foot --app-id "$INSTANCE" $EXTRA_ARGS 9>&- &
    ;;
  wezterm)
    wezterm start --class "$INSTANCE" $EXTRA_ARGS 9>&- &
    ;;
  ghostty)
    # ghostty --class needs a dotted GTK app-id; i3 for_window rules match class=.*-scratchpad
    ghostty --class="scratch.$INSTANCE" --x11-instance-name="$INSTANCE" $EXTRA_ARGS 9>&- &
    ;;
  st)
    # st: -c sets WM_CLASS class (i3 rules match class=".*-scratchpad"),
    # -n sets the instance (what exists() greps for). Needs both.
    st -c "$INSTANCE" -n "$INSTANCE" $EXTRA_ARGS 9>&- &
    ;;
  xterm)
    xterm -name "$INSTANCE" $EXTRA_ARGS 9>&- &
    ;;
  *)
    "$TERMINAL" $EXTRA_ARGS 9>&- &
    ;;
  esac
  # Poll for the window to appear instead of a fixed sleep.
  for _ in $(seq 1 100); do
    exists && break
    sleep 0.02
  done
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
