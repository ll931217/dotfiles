#!/usr/bin/env zsh

# Configuration
WALLPAPER_CACHE_DIR="$HOME/.wallpapers_cache/" # Directory to cache downloaded wallpapers
TRANSITION="wipe"                              # Transition effect (simple, random, left, right, top, bottom, wipe, wave, grow)
TRANSITION_DURATION=3                          # Transition duration in seconds
TRANSITION_FPS=60                              # Transition FPS
TRANSITION_STEP=255                            # Color step for transitions
API_KEY="$WALLHAVEN_API_KEY"                   # Optional: Your Wallhaven API key (leave empty for public access)
SORTING="favorites"                            # Basically What kind of content should we get: date_added*, relevance, random, views, favorites, toplist
AI_ART_FILTER="0"                              # 0=AI art, 1=No AI art
MIN_RESOLUTION="1920x1080"                     # Minimum resolution filter
RATIO="16x9"                                   # Screen Ratios
PURITY="001"                                   # Purity filter: 100=SFW, 010=Sketchy, 001=NSFW, 111=All
CATEGORIES="111"                               # Categories: 1xx=General, x1x=Anime, xx1=People, 111=All
MAX_PAGES=10                                   # Used to iterate over multiple pages for urls
# Cache configuration
API_CACHE_DIR="/tmp/wallhaven_cache/" # Directory to cache API responses
API_CACHE_FILE="${API_CACHE_DIR}wallpapers_cache.json"
PARAMS_HASH_FILE="${API_CACHE_DIR}params.hash"

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
  if [ ! -d "$API_CACHE_DIR" ]; then
    echo "Creating API cache directory: $API_CACHE_DIR"
    mkdir -p "$API_CACHE_DIR"
  fi
}

# Function to send desktop notification
send_notification() {
  local title="$1"
  local message="$2"
  local urgency="${3:-normal}" # low, normal, critical

  # Check if notify-send is available
  if command -v notify-send >/dev/null 2>&1; then
    notify-send -u "$urgency" -a "Wallpaper Script" "$title" "$message"
  fi
}

# Function to print detailed API errors
print_api_error() {
  local json_response="$1"
  local http_status="$2"
  local curl_exit_code="$3"

  echo "=== API ERROR DETAILS ===" >&2
  echo "HTTP Status: $http_status" >&2
  echo "Curl Exit Code: $curl_exit_code" >&2

  local error_summary=""
  local error_details=""

  # Check if response is valid JSON
  if echo "$json_response" | jq empty 2>/dev/null; then
    # Extract error information from JSON response
    local error_msg=$(echo "$json_response" | jq -r '.error // empty')
    local api_errors=$(echo "$json_response" | jq -r '.errors[]? // empty')

    if [ -n "$error_msg" ] && [ "$error_msg" != "null" ]; then
      echo "API Error: $error_msg" >&2
      error_summary="$error_msg"
    fi

    if [ -n "$api_errors" ] && [ "$api_errors" != "null" ]; then
      echo "Additional Errors:" >&2
      echo "$api_errors" | while read -r line; do
        echo "  - $line" >&2
      done
    fi
  else
    echo "Response is not valid JSON:" >&2
    echo "${json_response:0:500}" >&2
    error_summary="Invalid API response"
  fi

  # Provide specific suggestions based on common error codes
  case "$http_status" in
  401)
    echo "Suggestion: Check your API key or leave it empty for public access" >&2
    error_details="Invalid API key"
    ;;
  403)
    echo "Suggestion: API key might be invalid or expired" >&2
    error_details="Forbidden - check API key"
    ;;
  429)
    echo "Suggestion: Rate limit exceeded. Wait before trying again" >&2
    error_details="Rate limit exceeded"
    ;;
  500 | 502 | 503 | 504)
    echo "Suggestion: Wallhaven server error. Try again later" >&2
    error_details="Wallhaven server error"
    ;;
  *)
    error_details="HTTP $http_status error"
    ;;
  esac

  echo "========================" >&2

  # Send desktop notification for the error
  if [ -n "$error_summary" ]; then
    send_notification "Wallpaper API Error" "${error_summary}: ${error_details}" "critical"
  else
    send_notification "Wallpaper API Error" "${error_details}" "critical"
  fi
}

# Function to generate parameter hash for cache validation
generate_params_hash() {
  # Create hash of all relevant parameters
  # Use a stable placeholder for API key to ensure cache stability across environments
  local api_key_placeholder="${API_KEY:+KEY}"
  local params="${SORTING}:${AI_ART_FILTER}:${MIN_RESOLUTION}:${RATIO}:${PURITY}:${CATEGORIES}:${api_key_placeholder}:${MAX_PAGES}"
  echo "$params" | sha256sum | cut -d' ' -f1
}

# Function to fetch all pages from 1 to MAX_PAGES
fetch_all_pages_wallpapers() {
  local all_wallpapers_urls=()
  local total_wallpapers=0

  echo "Fetching wallpapers from all pages (1-${MAX_PAGES})..." >&2

  for page_num in $(seq 1 $MAX_PAGES); do
    echo "Fetching page ${page_num}..." >&2

    local api_url="https://wallhaven.cc/api/v1/search"
    local params="?topRange=1M&sorting=${SORTING}&order=desc&page=${page_num}&ratios=${RATIO}&atleast=${MIN_RESOLUTION}&purity=${PURITY}&categories=${CATEGORIES}&ai_art_filter=${AI_ART_FILTER}"

    # Add API key if provided
    if [ -n "$API_KEY" ]; then
      params="${params}&apikey=${API_KEY}"
    fi

    local full_url="${api_url}${params}"

    # Fetch JSON response
    local curl_output
    curl_output=$(curl -s -w "\nHTTP_STATUS:%{http_code}\nCURL_EXIT:%{exitcode}\n" \
      -H "User-Agent: Wallpaper-Script/1.0" \
      "$full_url" 2>/dev/null)

    local curl_exit_code
    curl_exit_code=$(echo "$curl_output" | grep "CURL_EXIT:" | cut -d: -f2)
    local http_status
    http_status=$(echo "$curl_output" | grep "HTTP_STATUS:" | cut -d: -f2)
    # Extract JSON response - only lines starting with { (JSON object start)
    local json_response
    json_response=$(echo "$curl_output" | sed -n '/^{/p')

    # Check for errors
    if [ "$curl_exit_code" != "0" ] || [ "$http_status" != "200" ]; then
      echo "Warning: Failed to fetch page ${page_num} (HTTP ${http_status}, exit ${curl_exit_code})" >&2
      continue
    fi

    # Validate JSON structure
    if ! echo "$json_response" | jq empty 2>/dev/null; then
      echo "Warning: Invalid JSON response from page ${page_num}" >&2
      continue
    fi

    # Validate JSON has expected .data structure
    if ! echo "$json_response" | jq -e '.data | type' >/dev/null 2>&1; then
      echo "Warning: JSON structure invalid for page ${page_num} (missing .data)" >&2
      continue
    fi

    # Extract wallpaper URLs, filtering out invalid entries
    # Use jq to select only paths that start with https://
    local page_wallpapers
    page_wallpapers=$(echo "$json_response" | jq -r '.data[].path | select(. | startswith("https://"))')

    # Add to array
    while IFS= read -r url; do
      # Skip empty or null values
      if [ -z "$url" ] || [ "$url" = "null" ]; then
        continue
      fi

      # Validate URL format - must be full Wallhaven wallpaper URL
      if [[ ! "$url" =~ ^https://w\.wallhaven\.cc/full/ ]]; then
        echo "Warning: Skipping malformed URL: $url" >&2
        continue
      fi

      all_wallpapers_urls+=("$url")
      ((total_wallpapers++))
    done <<<"$page_wallpapers"

    echo "Page ${page_num}: $(echo "$page_wallpapers" | grep -c .) wallpapers" >&2
  done

  echo "Total wallpapers fetched: ${total_wallpapers}" >&2

  # Convert array to JSON and save to cache
  local json_output
  json_output=$(printf '%s\n' "${all_wallpapers_urls[@]}" | jq -R . | jq -s .)

  if [ -n "$json_output" ] && [ "$json_output" != "null" ]; then
    # Save to cache file
    echo "$json_output" >"$API_CACHE_FILE"

    # Save parameter hash
    generate_params_hash >"$PARAMS_HASH_FILE"

    echo "Cached ${total_wallpapers} wallpapers to ${API_CACHE_FILE}" >&2
    echo "${total_wallpapers}"
    return 0
  else
    echo "Error: Failed to create JSON output" >&2
    return 1
  fi
}

# Function to get cached wallpapers or fetch new ones
get_cached_wallpapers() {
  local current_hash
  current_hash=$(generate_params_hash)
  local cached_hash=""

  # Check if cache files exist and are readable
  if [ -f "$PARAMS_HASH_FILE" ] && [ -f "$API_CACHE_FILE" ]; then
    cached_hash=$(cat "$PARAMS_HASH_FILE" 2>/dev/null || echo "")
  fi

  # Compare hashes to determine if we need to refresh cache
  if [ "$current_hash" = "$cached_hash" ] && [ -s "$API_CACHE_FILE" ]; then
    echo "Using cached wallpapers (parameters unchanged)" >&2

    # Get count from cached file
    local wallpaper_count
    wallpaper_count=$(jq 'length' "$API_CACHE_FILE" 2>/dev/null || echo "0")

    if [ "$wallpaper_count" -gt 0 ]; then
      echo "$wallpaper_count"
      return 0
    else
      echo "Cache file is empty or invalid, refetching..." >&2
    fi
  else
    echo "Parameters changed or no cache found, refetching wallpapers..." >&2
  fi

  # Fetch new wallpapers
  fetch_all_pages_wallpapers
}

# Function to get random wallpaper from Wallhaven toplist with cache
get_wallhaven_toplist_wallpaper() {
  local wallpaper_count

  # Get wallpapers (from cache or fetch new)
  if ! wallpaper_count=$(get_cached_wallpapers); then
    echo "Error: Failed to get wallpapers" >&2
    return 1
  fi

  if [ "$wallpaper_count" -eq 0 ]; then
    echo "Error: No wallpapers available" >&2
    return 1
  fi

  # Validate wallpaper_count is a positive integer before arithmetic
  if ! [[ "$wallpaper_count" =~ ^[0-9]+$ ]] || [ "$wallpaper_count" -le 0 ]; then
    echo "Error: Invalid wallpaper count: '$wallpaper_count'" >&2
    return 1
  fi

  # Get random wallpaper from cache
  local selected_index=$((RANDOM % wallpaper_count))
  local selected_wallpaper
  selected_wallpaper=$(jq -r ".[$selected_index]" "$API_CACHE_FILE")

  if [ -n "$selected_wallpaper" ] && [ "$selected_wallpaper" != "null" ]; then
    echo "Selected cached wallpaper: $selected_wallpaper" >&2
    echo "$selected_wallpaper"
    return 0
  else
    echo "Error: Failed to select wallpaper from cache" >&2
    return 1
  fi
}

# Function to download wallpaper
download_wallpaper() {
  local wallpaper_url=$1
  local filename=$(basename "$wallpaper_url")
  local local_path="${WALLPAPER_CACHE_DIR}${filename}"

  # Check if wallpaper already exists in cache
  if [ -f "$local_path" ]; then
    echo "Wallpaper already cached: $local_path" >&2
    send_notification "Wallpaper Download" "Using cached wallpaper: ${filename}" "low"
    echo "$local_path"
    return 0
  fi

  echo "Downloading wallpaper: $wallpaper_url" >&2
  send_notification "Wallpaper Download" "Starting download: ${filename}" "normal"

  # Direct URL download since we now get proper URLs from jq
  echo "Downloading from: $wallpaper_url" >&2
  echo "Saving to: $local_path" >&2

  # Use verbose curl to see what's happening
  if curl -f -L --max-time 30 --progress-bar -H "User-Agent: Wallpaper-Script/1.0" -o "$local_path" "$wallpaper_url"; then
    # Verify the downloaded file is actually an image
    if file "$local_path" | grep -q -E "(JPEG|PNG|GIF|WebP)"; then
      echo "Downloaded successfully: $local_path" >&2
      send_notification "Wallpaper Download" "Successfully downloaded: ${filename}" "normal"
      echo "$local_path"
      return 0
    else
      echo "Downloaded file is not a valid image, removing..." >&2
      send_notification "Wallpaper Download Failed" "Invalid image format: ${filename}" "critical"
      rm -f "$local_path"
      return 1
    fi
  else
    local curl_exit_code=$?
    local error_reason=""
    case "$curl_exit_code" in
    6)
      error_reason="Could not resolve host (network issue)"
      ;;
    7)
      error_reason="Failed to connect to server"
      ;;
    22)
      error_reason="HTTP error - file not found or forbidden"
      ;;
    28)
      error_reason="Download timeout (30s limit exceeded)"
      ;;
    35)
      error_reason="SSL/TLS handshake failed"
      ;;
    *)
      error_reason="Curl error code: $curl_exit_code"
      ;;
    esac
    echo "Error: Failed to download wallpaper from $wallpaper_url" >&2
    echo "Reason: $error_reason" >&2
    send_notification "Wallpaper Download Failed" "Failed to download ${filename}: ${error_reason}" "critical"
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
    echo "Setting wallpaper with swww..." >&2
    check_swww_daemon
    if swww img "$wallpaper" \
      --resize crop \
      --transition-type "$TRANSITION" \
      --transition-fps "$TRANSITION_FPS" \
      --transition-duration "$TRANSITION_DURATION" \
      --transition-step "$TRANSITION_STEP"; then
      echo "Wallpaper set successfully!" >&2
      local filename=$(basename "$wallpaper")
      send_notification "Wallpaper Updated" "Successfully set: ${filename}" "normal"
    else
      echo "Error: Failed to set wallpaper with swww" >&2
      send_notification "Wallpaper Update Failed" "Failed to set wallpaper with swww" "critical"
      return 1
    fi
    ;;
  "x11")
    echo "Setting wallpaper with feh..." >&2
    if feh --bg-fill "$wallpaper"; then
      echo "Wallpaper set successfully!" >&2
      local filename=$(basename "$wallpaper")
      send_notification "Wallpaper Updated" "Successfully set: ${filename}" "normal"
    else
      echo "Error: Failed to set wallpaper with feh" >&2
      send_notification "Wallpaper Update Failed" "Failed to set wallpaper with feh" "critical"
      return 1
    fi
    ;;
  *)
    echo "Error: Unknown session type. Cannot set wallpaper." >&2
    send_notification "Wallpaper Update Failed" "Unknown session type: ${session_type}" "critical"
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
  send_notification "Wallpaper Script" "Starting wallpaper update process..." "low"

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
    send_notification "Wallpaper Script Failed" "Could not fetch wallpaper from API" "critical"
    exit 1
  fi

  if [ -z "$wallpaper_url" ]; then
    echo "Error: No wallpaper URL returned"
    send_notification "Wallpaper Script Failed" "No wallpaper URL received" "critical"
    exit 1
  fi

  # Download wallpaper
  local local_wallpaper
  if ! local_wallpaper=$(download_wallpaper "$wallpaper_url"); then
    echo "Error: Failed to download wallpaper"
    send_notification "Wallpaper Script Failed" "Failed to download wallpaper" "critical"
    exit 1
  fi

  if [ -z "$local_wallpaper" ]; then
    echo "Error: No local wallpaper path returned"
    send_notification "Wallpaper Script Failed" "No local wallpaper path" "critical"
    exit 1
  fi

  # Set wallpaper
  set_wallpaper "$local_wallpaper"

  if [ $? -eq 0 ]; then
    echo "=== Wallpaper update completed successfully! ==="
    send_notification "Wallpaper Script Complete" "Wallpaper updated successfully!" "normal"
  else
    echo "=== Wallpaper update failed! ==="
    send_notification "Wallpaper Script Failed" "Failed to set wallpaper" "critical"
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
