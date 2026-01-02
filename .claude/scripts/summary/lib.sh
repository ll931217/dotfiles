#!/usr/bin/env bash
# Shared utilities for /prd:summary command

# Convert PRD status to human-readable display with emoji
get_status_display() {
  local status="$1"
  case "$status" in
    "draft") echo "📝 draft (not yet approved)" ;;
    "approved") echo "✅ approved (ready for implementation)" ;;
    "implemented") echo "✨ implemented (complete)" ;;
    *) echo "❓ $status" ;;
  esac
}

# Query beads for issue status (open/closed)
get_issue_status() {
  local issue_id="$1"
  if bd show "$issue_id" 2>/dev/null | grep -q "Status: closed"; then
    echo "closed"
  else
    echo "open"
  fi
}

# Get parent epic name for an issue using beads
get_epic_for_issue() {
  local issue_id="$1"
  bd dep show "$issue_id" 2>/dev/null | grep "parent:" | awk '{print $2}' | tr -d '[]'
}

# Draw a visual progress bar using block characters
# Args: percent (0-100), width (default 20)
draw_progress_bar() {
  local percent=$1
  local width=${2:-20}
  printf "   ["
  for i in $(seq 1 $width); do
    if [ $i -le $((percent * width / 100)) ]; then
      printf "█"
    else
      printf "░"
    fi
  done
  printf "] %d%%\n" $percent
}

# Get current worktree path for context matching
get_current_worktree_path() {
  local git_dir git_common_dir
  git_dir=$(git rev-parse --git-dir 2>/dev/null)
  git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null)

  if [ "$git_dir" != "$git_common_dir" ]; then
    echo "$git_dir"
  else
    echo ""
  fi
}

# Extract overview section from PRD content
extract_prd_overview() {
  local prd_file="$1"
  sed -n '/^## \(Overview\|Introduction\)/,/^## /p' "$prd_file" | head -n -1 | tail -n +2
}

# Group issues by epic and populate associative array
# Args: array_name issue_array_name
group_issues_by_epic() {
  local -n epic_groups=$1
  local -n issues_array=$2
  local issue epic

  for issue in "${issues_array[@]}"; do
    epic=$(get_epic_for_issue "$issue")
    if [ -n "$epic" ]; then
      eval "${epic_groups}[\"$epic\"]+=\"\$issue \""
    else
      eval "${epic_groups}['[no epic]']+=\"\$issue \""
    fi
  done
}
