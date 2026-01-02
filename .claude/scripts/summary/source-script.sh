#!/usr/bin/env bash
# Script sourcing helper with fallback support

# Source a script from the summary scripts directory
# Args: script_name (e.g., "lib.sh")
# Uses: Current script's directory first, then global fallback
source_summary_script() {
  local script_name="$1"

  # Get the directory of the calling script
  local caller_dir
  caller_dir="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"

  # Try local first (co-located with caller)
  if [ -f "$caller_dir/$script_name" ]; then
    source "$caller_dir/$script_name"
    return 0
  fi

  # Fallback to global location
  local global_dir="$HOME/.claude/scripts/summary"
  if [ -f "$global_dir/$script_name" ]; then
    source "$global_dir/$script_name"
    return 0
  fi

  # Not found
  echo "Error: Cannot find $script_name in $caller_dir or $global_dir" >&2
  return 1
}

# Export the function for use in other scripts
export -f source_summary_script
