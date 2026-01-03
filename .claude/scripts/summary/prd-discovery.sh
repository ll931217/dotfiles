#!/usr/bin/env bash
# PRD auto-discovery for /flow:summary command

# Get the absolute directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source helper function (this file must exist in same directory)
source "$SCRIPT_DIR/source-script.sh"

# Source lib.sh with fallback
source_summary_script "lib.sh"

# Discover PRD for single worktree mode using multi-stage algorithm
# Args: flow_dir current_branch current_worktree
# Outputs: PRD file path or empty string if not found
discover_prd_single() {
  local flow_dir="$1"
  local current_branch="$2"
  local current_worktree="$3"

  # Stage 1: Latest PRD Check
  local latest_prd
  latest_prd=$(find "$flow_dir" -name "prd-*.md" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

  if [ -z "$latest_prd" ]; then
    return 1
  fi

  # Stage 2: Context Validation
  local prd_branch prd_wt_path
  prd_branch=$(grep -A5 "^git:" "$latest_prd" | grep "branch:" | awk '{print $2}' | tr -d '"')
  prd_wt_path=$(grep -A5 "^worktree:" "$latest_prd" | head -6 | grep -E "^  path:" | awk '{print $2}' | tr -d '"')

  if [ "$prd_branch" = "$current_branch" ] && [ "$prd_wt_path" = "$current_worktree" ]; then
    echo "$latest_prd"
    return 0
  fi

  # Stage 3: Fallback search - iterate all PRDs
  local prd
  for prd in "$flow_dir"/prd-*.md; do
    prd_branch=$(grep -A5 "^git:" "$prd" | grep "branch:" | awk '{print $2}' | tr -d '"')
    prd_wt_path=$(grep -A5 "^worktree:" "$prd" | head -6 | grep -E "^  path:" | awk '{print $2}' | tr -d '"')
    if [ "$prd_branch" = "$current_branch" ] && [ "$prd_wt_path" = "$current_worktree" ]; then
      echo "$prd"
      return 0
    fi
  done

  return 1
}

# Discover PRDs for all worktrees (multi-worktree mode)
# Args: branch_worktrees associative array (passed by reference)
# Outputs: WORKTREE_PRDS and WORKTREE_NAMES associative arrays
discover_prd_multi() {
  local -n branch_wts=$1
  local wt_name wt_path wt_flow_dir wt_prd prd prd_wt_path wt_feature

  declare -gA WORKTREE_PRDS
  declare -gA WORKTREE_NAMES

  for wt_name in "${!branch_wts[@]}"; do
    wt_path="${branch_wts[$wt_name]}"
    wt_flow_dir="$wt_path/.flow"

    # Find PRD matching this worktree
    wt_prd=""
    if [ -d "$wt_flow_dir" ]; then
      for prd in "$wt_flow_dir"/prd-*.md; do
        [ -f "$prd" ] || continue
        if [ -f "$prd" ]; then
          prd_wt_path=$(grep -A5 "^worktree:" "$prd" | head -6 | grep -E "^  path:" | awk '{print $2}' | tr -d '"')

          # Match based on worktree path or empty (for main)
          if [ "$wt_name" = "[main]" ] && [ -z "$prd_wt_path" ]; then
            wt_prd="$prd"
            break
          elif [ -n "$prd_wt_path" ] && [[ "$prd_wt_path" == *"$wt_name"* ]]; then
            wt_prd="$prd"
            break
          fi
        fi
      done
    fi

    if [ -n "$wt_prd" ]; then
      WORKTREE_PRDS["$wt_name"]="$wt_prd"
      # Get feature name from PRD
      wt_feature=$(grep -A3 "^prd:" "$wt_prd" | grep "feature_name:" | awk '{print $2}' | tr -d '"')
      WORKTREE_NAMES["$wt_name"]="$wt_feature"
    fi
  done
}

# Extract metadata from PRD file and set as environment variables
# Args: prd_file
# Outputs: PRD_VERSION, PRD_STATUS, PRD_FEATURE_NAME, PRD_RELATED_ISSUES, PRD_BRANCH
extract_prd_metadata() {
  local prd_file="$1"
  PRD_VERSION=$(grep -A3 "^prd:" "$prd_file" | grep "version:" | awk '{print $2}' | tr -d '"')
  PRD_STATUS=$(grep -A3 "^prd:" "$prd_file" | grep "status:" | awk '{print $2}' | tr -d '"')
  PRD_FEATURE_NAME=$(grep -A3 "^prd:" "$prd_file" | grep "feature_name:" | awk '{print $2}' | tr -d '"')
  # Extract related_issues from multiline YAML array format
  # Pattern: captures everything from "related_issues:" to closing "]" on its own line
  PRD_RELATED_ISSUES=$(awk '
    BEGIN { found = 0 }
    /^beads:/ {
      if (found == 0) in_beads = 1
    }
    in_beads && /related_issues:/ { in_issues = 1; next }
    in_issues && /^\s*\]/ { found = 1; exit }
    in_issues && /flow-/ { gsub(/[\s,]/, " ", $0); gsub(/"/, "", $0); printf "%s ", $0 }
  ' "$prd_file" | sed 's/[[:space:]]*$//')

  # related_epics is typically on one line, use original grep approach
  PRD_RELATED_EPICS=$(grep -A2 "^beads:" "$prd_file" | grep "related_epics:" | sed 's/related_epics: //' | tr -d '[]')
  PRD_BRANCH=$(grep -A5 "^git:" "$prd_file" | grep "branch:" | awk '{print $2}' | tr -d '"')
  export PRD_VERSION PRD_STATUS PRD_FEATURE_NAME PRD_RELATED_ISSUES PRD_RELATED_EPICS PRD_BRANCH
}

# Show error when no PRD is found matching current context
show_no_prd_error() {
  local flow_dir="$1"
  local current_branch="$2"
  local current_worktree="$3"
  local prd prd_branch prd_version prd_status

  echo "⚠️  No PRD found matching current context"
  echo ""
  echo "Current Context:"
  echo "- Branch: $current_branch"
  echo "- Worktree: ${current_worktree:-none}"
  echo ""
  echo "Available PRDs:"
  for prd in "$flow_dir"/prd-*.md; do
    prd_branch=$(grep -A5 "^git:" "$prd" | grep "branch:" | awk '{print $2}' | tr -d '"')
    prd_version=$(grep -A3 "^prd:" "$prd" | grep "version:" | awk '{print $2}' | tr -d '"')
    prd_status=$(grep -A3 "^prd:" "$prd" | grep "status:" | awk '{print $2}' | tr -d '"')
    echo "- $(basename "$prd") (branch: $prd_branch, version: $prd_version, status: $prd_status)"
  done
}
