#!/bin/bash

# Configuration
WALLPAPER_DIR="$HOME/.wallpapers/" # Change this to your wallpapers directory
TRANSITION="wipe"                  # Transition effect (simple, random, left, right, top, bottom, wipe, wave, grow)
TRANSITION_DURATION=3              # Transition duration in seconds
TRANSITION_FPS=60                  # Transition FPS
TRANSITION_STEP=255                # Color step for transitions

if [[ $# -eq 1 ]]; then
  WALLPAPER_DIR="$1"
fi

if [[ -n "$WALLPAPER_DIR" ]]; then
  if [ ! -d "$WALLPAPER_DIR" ]; then
    echo "Error: '$WALLPAPER_DIR' is not an existing directory"
  fi
fi

# Function to detect session type
get_session_type() {
  if [ -n "$WAYLAND_DISPLAY" ]; then
    echo "wayland"
  elif [ -n "$DISPLAY" ]; then
    echo "x11"
  else
    echo "unknown"
  fi
}

# Function to check if swww is running
check_swww_daemon() {
  if ! pgrep -x "swww-daemon" >/dev/null; then
    echo "Starting swww daemon..."
    swww-daemon
  fi
}

# Function to get a random wallpaper
get_random_wallpaper() {
  find "$WALLPAPER_DIR" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) | shuf -n 1
}

# Function to set wallpaper with specified parameters
set_wallpaper() {
  local wallpaper=$1
  local session_type=$(get_session_type)

  case "$session_type" in
  "wayland")
    echo "Setting wallpaper with swww..."
    # Check if swww daemon is running (only for Wayland)
    if [ "$(get_session_type)" = "wayland" ]; then
      check_swww_daemon
    fi
    swww img "$wallpaper" \
      --resize crop \
      --transition-type "$TRANSITION" \
      --transition-fps "$TRANSITION_FPS" \
      --transition-duration "$TRANSITION_DURATION" \
      --transition-step "$TRANSITION_STEP"
    ;;
  "x11")
    echo "Setting wallpaper with feh..."
    feh --bg-fill "$wallpaper"
    ;;
  *)
    echo "Unknown session type. Cannot set wallpaper."
    exit 1
    ;;
  esac
}

# Main execution
main() {
  # Ensure the wallpaper directory exists
  if [ ! -d "$WALLPAPER_DIR" ]; then
    echo "Error: Wallpaper directory does not exist: $WALLPAPER_DIR"
    exit 1
  fi

  # Get and set random wallpaper
  wallpaper=$(get_random_wallpaper)

  if [ -f "$wallpaper" ]; then
    echo "Setting wallpaper: $wallpaper"
    set_wallpaper "$wallpaper"
  else
    echo "Error: No valid wallpapers found in $WALLPAPER_DIR"
    exit 1
  fi
}

# Run the script
main
