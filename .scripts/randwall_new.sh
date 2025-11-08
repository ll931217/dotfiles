#!/bin/bash

# Configuration
WALLPAPER_CACHE_DIR="$HOME/.wallpapers_cache/" # Directory to cache downloaded wallpapers
TRANSITION="wipe"                              # Transition effect (simple, random, left, right, top, bottom, wipe, wave, grow)
TRANSITION_DURATION=3                          # Transition duration in seconds
TRANSITION_FPS=60                              # Transition FPS
TRANSITION_STEP=255                            # Color step for transitions
API_KEY=""                                     # Optional: Your Wallhaven API key (leave empty for public access)
SORTING="toplist"                              # Basically What kind of content should we get
AI_ART_FILTER="1"                              # 0=AI art, 1=No AI art
MIN_RESOLUTION="1920x1080"                     # Minimum resolution filter
RATIO="16x9"                                   # Screen Ratios
PURITY="100"                                   # Purity filter: 100=SFW, 010=Sketchy, 001=NSFW, 111=All
CATEGORIES="110"                               # Categories: 1xx=General, x1x=Anime, xx1=People, 111=All
MAX_PAGES=5                                    # Maximum pages to search through for variety

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
    sleep 2 # Give daemon time to start
  fi
}

# Function to create cache directory
create_cache_dir() {
  if [ ! -d "$WALLPAPER_CACHE_DIR" ]; then
    echo "Creating wallpaper cache directory: $WALLPAPER_CACHE_DIR"
    mkdir -p "$WALLPAPER_CACHE_DIR"
  fi
}

# Function to get random wallpaper from Wallhaven toplist
get_wallhaven_toplist_wallpaper() {
  local page_num=$((RANDOM % MAX_PAGES + 1))
  local api_url="https://wallhaven.cc/api/v1/search"
  local params="?topRange=1M&sorting=${SORTING}&order=desc&page=${page_num}&ratios=${RATIO}&atleast=${MIN_RESOLUTION}&purity=${PURITY}&categories=${CATEGORIES}&ai_art_filter=${AI_ART_FILTER}"

  # Add API key if provided
  if [ -n "$API_KEY" ]; then
    params="${params}&apikey=${API_KEY}"
  fi

  local full_url="${api_url}${params}"

  echo "Fetching wallpapers from Wallhaven toplist (page $page_num)..." >&2
  echo "API URL: $full_url" >&2

  # Fetch JSON response
  local json_response
  json_response=$(curl -s -H "User-Agent: Wallpaper-Script/1.0" "$full_url")

  if [ $? -ne 0 ] || [ -z "$json_response" ]; then
    echo "Error: Failed to fetch data from Wallhaven API"
    return 1
  fi

  # Check if we got valid JSON with data
  if ! echo "$json_response" | jq -e '.data' >/dev/null 2>&1; then
    echo "Error: Invalid response from Wallhaven API"
    echo "Response (first 500 chars): ${json_response:0:500}"
    return 1
  fi

  # Extract all wallpaper URLs using jq
  local wallpaper_urls
  wallpaper_urls=$(echo "$json_response" | jq -r '.data[].path')

  if [ -z "$wallpaper_urls" ]; then
    echo "Error: No wallpapers found in API response"
    return 1
  fi

  # Convert to array and pick random wallpaper
  local wallpaper_array=()
  while IFS= read -r url; do
    wallpaper_array+=("$url")
  done <<<"$wallpaper_urls"

  local array_size=${#wallpaper_array[@]}

  if [ $array_size -eq 0 ]; then
    echo "Error: No valid wallpaper URLs found"
    return 1
  fi

  echo "Found $array_size wallpapers, selecting random one..." >&2

  local random_index=$((RANDOM % array_size))
  local selected_wallpaper="${wallpaper_array[$random_index]}"

  echo "Selected wallpaper: $selected_wallpaper" >&2
  # Return only the URL, nothing else
  echo "$selected_wallpaper"
}

# Function to download wallpaper
download_wallpaper() {
  local wallpaper_url=$1
  local filename=$(basename "$wallpaper_url")
  local local_path="${WALLPAPER_CACHE_DIR}${filename}"

  # Check if wallpaper already exists in cache
  if [ -f "$local_path" ]; then
    echo "Wallpaper already cached: $local_path" >&2
    echo "$local_path"
    return 0
  fi

  echo "Downloading wallpaper: $wallpaper_url" >&2

  # Direct URL download since we now get proper URLs from jq
  echo "Downloading from: $wallpaper_url" >&2
  echo "Saving to: $local_path" >&2

  # Use verbose curl to see what's happening
  if curl -f -L --max-time 30 --progress-bar -H "User-Agent: Wallpaper-Script/1.0" -o "$local_path" "$wallpaper_url"; then
    # Verify the downloaded file is actually an image
    if file "$local_path" | grep -q -E "(JPEG|PNG|GIF|WebP)"; then
      echo "Downloaded successfully: $local_path" >&2
      echo "$local_path"
      return 0
    else
      echo "Downloaded file is not a valid image, removing..." >&2
      rm -f "$local_path"
      return 1
    fi
  else
    echo "Error: Failed to download wallpaper from $wallpaper_url" >&2
    return 1
  fi
}

# Function to clean old cached wallpapers (keep only 20 most recent)
cleanup_cache() {
  local cache_limit=20
  local file_count=$(find "$WALLPAPER_CACHE_DIR" -type f | wc -l)

  if [ "$file_count" -gt "$cache_limit" ]; then
    echo "Cleaning up old cached wallpapers..." >&2
    find "$WALLPAPER_CACHE_DIR" -type f -printf '%T@ %p\n' | sort -n | head -n -"$cache_limit" | cut -d' ' -f2- | xargs rm -f
  fi
}

# Function to set wallpaper with specified parameters
set_wallpaper() {
  local wallpaper=$1
  local session_type=$(get_session_type)

  case "$session_type" in
  "wayland")
    echo "Setting wallpaper with swww..."
    check_swww_daemon
    if swww img "$wallpaper" \
      --resize crop \
      --transition-type "$TRANSITION" \
      --transition-fps "$TRANSITION_FPS" \
      --transition-duration "$TRANSITION_DURATION" \
      --transition-step "$TRANSITION_STEP"; then
      echo "Wallpaper set successfully!"
    else
      echo "Error: Failed to set wallpaper with swww"
      return 1
    fi
    ;;
  "x11")
    echo "Setting wallpaper with feh..."
    if feh --bg-fill "$wallpaper"; then
      echo "Wallpaper set successfully!"
    else
      echo "Error: Failed to set wallpaper with feh"
      return 1
    fi
    ;;
  *)
    echo "Error: Unknown session type. Cannot set wallpaper."
    return 1
    ;;
  esac
}

# Function to check dependencies
check_dependencies() {
  local missing_deps=()

  # Check for curl
  if ! command -v curl >/dev/null 2>&1; then
    missing_deps+=("curl")
  fi

  # Check for jq
  if ! command -v jq >/dev/null 2>&1; then
    missing_deps+=("jq")
  fi

  # Check for session-specific dependencies
  local session_type=$(get_session_type)
  case "$session_type" in
  "wayland")
    if ! command -v swww >/dev/null 2>&1; then
      missing_deps+=("swww")
    fi
    ;;
  "x11")
    if ! command -v feh >/dev/null 2>&1; then
      missing_deps+=("feh")
    fi
    ;;
  esac

  if [ ${#missing_deps[@]} -gt 0 ]; then
    echo "Error: Missing dependencies: ${missing_deps[*]}"
    echo "Please install the missing packages and try again."
    exit 1
  fi
}

# Main execution
main() {
  echo "=== Wallhaven Random Wallpaper Setter ==="

  # Check dependencies
  check_dependencies

  # Create cache directory
  create_cache_dir

  # Clean up old cached files
  cleanup_cache

  # Get random wallpaper URL from Wallhaven toplist
  local wallpaper_url
  if ! wallpaper_url=$(get_wallhaven_toplist_wallpaper); then
    echo "Error: Failed to get wallpaper from Wallhaven"
    exit 1
  fi

  if [ -z "$wallpaper_url" ]; then
    echo "Error: No wallpaper URL returned"
    exit 1
  fi

  # Download wallpaper
  local local_wallpaper
  if ! local_wallpaper=$(download_wallpaper "$wallpaper_url"); then
    echo "Error: Failed to download wallpaper"
    exit 1
  fi

  if [ -z "$local_wallpaper" ]; then
    echo "Error: No local wallpaper path returned"
    exit 1
  fi

  # Set wallpaper
  set_wallpaper "$local_wallpaper"

  if [ $? -eq 0 ]; then
    echo "=== Wallpaper update completed successfully! ==="
  else
    echo "=== Wallpaper update failed! ==="
    exit 1
  fi
}

# Show help
show_help() {
  cat <<EOF
Usage: $0 [OPTIONS]

A script to set random wallpapers from Wallhaven.cc toplist

Options:
  -h, --help    Show this help message
  -k, --key     Set Wallhaven API key (optional, for authenticated requests)

Configuration:
  Edit the script to modify:
  - MIN_RESOLUTION: Minimum wallpaper resolution (default: 1920x1080)
  - PURITY: Content filter (100=SFW, 010=Sketchy, 001=NSFW, 111=All)
  - CATEGORIES: Categories (1xx=General, x1x=Anime, xx1=People, 111=All)
  - TRANSITION: Wallpaper transition effect
  - WALLPAPER_CACHE_DIR: Directory for cached wallpapers

Examples:
  $0                    # Set random wallpaper from toplist
  $0 -k YOUR_API_KEY    # Use API key for authenticated requests

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
  -h | --help)
    show_help
    exit 0
    ;;
  -k | --key)
    API_KEY="$2"
    shift 2
    ;;
  *)
    echo "Unknown option: $1"
    show_help
    exit 1
    ;;
  esac
done

# Run the script
main
