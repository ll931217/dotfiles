#!/usr/bin/env bash
# Display summary output for /flow:summary command

# Get the absolute directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source helper function (this file must exist in same directory)
source "$SCRIPT_DIR/source-script.sh"

# Source lib.sh with fallback
source_summary_script "lib.sh"

# Display summary for a single worktree
# Args: prd_file
display_single_summary() {
  local prd_file="$1"
  local overview total closed percent
  local -a OPEN_ISSUES EPIC_GROUPS_KEYS

  # Extract metadata
  extract_prd_metadata "$prd_file"

  # Extract overview
  overview=$(extract_prd_overview "$prd_file")

  # Check if PRD has related issues
  if [ -z "$PRD_RELATED_ISSUES" ] || [ "$PRD_RELATED_ISSUES" = " " ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Feature: $PRD_FEATURE_NAME"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📋 PRD: $(basename "$prd_file") (version: $PRD_VERSION)"
    echo "   Status: $(get_status_display "$PRD_STATUS")"
    echo "   Branch: $PRD_BRANCH"
    echo ""
    echo "ℹ️  No tasks generated yet for this PRD"
    echo "   Run /flow:generate-tasks to create tasks"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return 0
  fi

  # Get issue statuses and count progress
  total=0
  closed=0
  local issue status

  for issue in $PRD_RELATED_ISSUES; do
    total=$((total + 1))
    status=$(get_issue_status "$issue")
    if [ "$status" = "closed" ]; then
      closed=$((closed + 1))
    else
      OPEN_ISSUES+=("$issue")
    fi
  done

  # Group open issues by epic
  declare -A EPIC_GROUPS
  group_issues_by_epic EPIC_GROUPS OPEN_ISSUES

  # Header
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Feature: $PRD_FEATURE_NAME"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  # PRD Metadata
  echo "📋 PRD: $(basename "$prd_file") (version: $PRD_VERSION)"
  echo "   Status: $(get_status_display "$PRD_STATUS")"
  echo "   Branch: $PRD_BRANCH"
  echo ""

  # Feature Overview
  if [ -n "$overview" ]; then
    echo "📝 Overview:"
    echo "$overview" | head -n 5
    echo ""
  fi

  # Progress
  echo "📊 Progress: $closed/$total tasks completed"

  if [ $total -gt 0 ]; then
    percent=$((closed * 100 / total))
    draw_progress_bar "$percent"
  fi
  echo ""

  # What's Left
  if [ ${#OPEN_ISSUES[@]} -gt 0 ]; then
    echo "⏳ What's Left (${#OPEN_ISSUES[@]} tasks):"
    echo ""

    # Get sorted epic keys
    EPIC_GROUPS_KEYS=($(printf '%s\n' "${!EPIC_GROUPS[@]}" | sort))

    for epic in "${EPIC_GROUPS_KEYS[@]}"; do
      echo "   📦 $(format_epic_label "$epic")"
      for issue in ${EPIC_GROUPS[$epic]}; do
        # Get issue title
        local title
        title=$(bd show "$issue" 2>/dev/null | grep "Title:" | cut -d: -f2- | sed 's/^[[:space:]]*//')
        echo "      ⏳ $issue: $title"
      done
      echo ""
    done
  else
    echo "✅ All tasks completed!"
    echo ""
  fi

  # Footer
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Display summary for a single worktree block (used in multi-mode)
# Args: wt_name wt_display_name prd_file feature_name
display_worktree_block() {
  local wt_name="$1"
  local wt_display_name="$2"
  local prd_file="$3"
  local feature_name="$4"

  local wt_version wt_status wt_related_issues
  local wt_total=0 wt_closed=0
  local -a wt_open_issues
  local issue status

  # Extract metadata
  wt_version=$(grep -A3 "^prd:" "$prd_file" | grep "version:" | awk '{print $2}' | tr -d '"')
  wt_status=$(grep -A3 "^prd:" "$prd_file" | grep "status:" | awk '{print $2}' | tr -d '"')
  # Extract related_issues from YAML array format (single-line)
  wt_related_issues=$(awk '
    /^beads:/ { in_beads = 1 }
    in_beads && /related_issues:/ {
      match($0, /\[.*\]/)
      if (RSTART > 0) {
        content = substr($0, RSTART + 1, RLENGTH - 2)
        gsub(/,/, " ", content)
        print content
      }
      exit
    }
  ' "$prd_file" | tr -s '[:space:]' ' ' | sed 's/[[:space:]]*$//')

  # Check if PRD has related issues
  if [ -z "$wt_related_issues" ] || [ "$wt_related_issues" = " " ]; then
    echo "$wt_display_name ─────────────────────────────────────────"
    echo "  Feature: $feature_name"
    echo "  PRD: $(basename "$prd_file") ($wt_version)"
    echo "  Status: $(get_status_display "$wt_status")"
    echo ""
    echo "  ℹ️  No tasks generated yet for this PRD"
    echo "     Run /flow:generate-tasks to create tasks"
    echo ""
    return 0
  fi

  # Get progress for this worktree
  for issue in $wt_related_issues; do
    wt_total=$((wt_total + 1))
    status=$(get_issue_status "$issue")
    if [ "$status" = "closed" ]; then
      wt_closed=$((wt_closed + 1))
    else
      wt_open_issues+=("$issue")
    fi
  done

  # Display worktree header
  echo "$wt_display_name ─────────────────────────────────────────"
  echo "  Feature: $feature_name"
  echo "  PRD: $(basename "$prd_file") (v$wt_version)"
  echo "  Status: $(get_status_display "$wt_status")"
  echo ""

  # Progress
  echo "  Progress: $wt_closed/$wt_total tasks completed"
  if [ $wt_total -gt 0 ]; then
    local percent=$((wt_closed * 100 / wt_total))
    draw_progress_bar "$percent"
  fi
  echo ""

  # What's Left (brief - just count and list epic groups)
  if [ ${#wt_open_issues[@]} -gt 0 ]; then
    # Group by epic
    declare -A wt_epic_groups
    group_issues_by_epic wt_epic_groups wt_open_issues

    local epic count epic_keys
    echo "  ⏳ Remaining: ${#wt_open_issues[@]} tasks"

    # Get sorted epic keys
    epic_keys=($(printf '%s\n' "${!wt_epic_groups[@]}" | sort))
    for epic in "${epic_keys[@]}"; do
      count=$(echo "${wt_epic_groups[$epic]}" | wc -w)
      echo "     • $(format_epic_label "$epic"): $count tasks"
    done
    echo ""
  else
    echo "  ✅ All tasks completed!"
    echo ""
  fi
}

# Display consolidated summary for all worktrees
# Uses: BRANCH_WORKTREES, WORKTREE_PRDS, WORKTREE_NAMES, CURRENT_BRANCH
display_multi_summary() {
  local overall_total=0 overall_closed=0
  local wt_name prd_file feature_name
  local -a wt_keys

  # Header
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Branch: $CURRENT_BRANCH"
  echo "  Multi-Worktree Summary"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  # Check if any PRDs were found
  if [ ${#WORKTREE_PRDS[@]} -eq 0 ]; then
    echo "ℹ️  No PRDs found for any worktree on branch: $CURRENT_BRANCH"
    echo ""
    echo "Available worktrees:"
    for wt_name in "${!BRANCH_WORKTREES[@]}"; do
      echo "  - ${wt_name}: ${BRANCH_WORKTREES[$wt_name]}"
    done
    echo ""
    echo "Run /flow:plan in a worktree to create a PRD"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return 0
  fi

  # Get sorted worktree keys
  wt_keys=($(printf '%s\n' "${!WORKTREE_PRDS[@]}" | sort))

  # Display each worktree's summary
  for wt_name in "${wt_keys[@]}"; do
    prd_file="${WORKTREE_PRDS[$wt_name]}"
    feature_name="${WORKTREE_NAMES[$wt_name]}"

    # Extract related issues count for overall totals
    local wt_related_issues wt_total wt_closed
    # Extract related_issues from YAML array format (single-line)
    wt_related_issues=$(awk '
      /^beads:/ { in_beads = 1 }
      in_beads && /related_issues:/ {
        match($0, /\[.*\]/)
        if (RSTART > 0) {
          content = substr($0, RSTART + 1, RLENGTH - 2)
          gsub(/,/, " ", content)
          print content
        }
        exit
      }
    ' "$prd_file" | tr -s '[:space:]' ' ' | sed 's/[[:space:]]*$//')
    wt_total=0
    wt_closed=0

    for issue in $wt_related_issues; do
      wt_total=$((wt_total + 1))
      if get_issue_status "$issue" | grep -q "closed"; then
        wt_closed=$((wt_closed + 1))
      fi
    done

    overall_total=$((overall_total + wt_total))
    overall_closed=$((overall_closed + wt_closed))

    # Determine display name
    local wt_display_name="$wt_name"
    if [ "$wt_name" = "[main]" ]; then
      wt_display_name="📍 main"
    else
      wt_display_name="🌿 $wt_name"
    fi

    # Display this worktree block (we need to temporarily set related issues for display)
    local saved_issues="$PRD_RELATED_ISSUES"
    PRD_RELATED_ISSUES="$wt_related_issues"
    display_worktree_block "$wt_name" "$wt_display_name" "$prd_file" "$feature_name"
    PRD_RELATED_ISSUES="$saved_issues"
  done

  # Overall summary footer
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Overall Progress: $overall_closed/$overall_total tasks"
  if [ $overall_total -gt 0 ]; then
    local percent=$((overall_closed * 100 / overall_total))
    draw_progress_bar "$percent"
  fi
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}
