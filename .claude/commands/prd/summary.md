---
description: Show current feature implementation summary
---

# Rule: Feature Summary (/prd:summary)

## Goal

Provide a concise summary of the current feature implementation, showing:
- Current PRD (auto-discovered based on git context)
- PRD metadata (name, version, status, branch)
- Feature overview (goal and description from PRD content)
- Related issues with their status (open/closed)
- Progress tracking (X/Y tasks completed)
- What's left to do (list of open issues grouped by epic)

**Multi-Worktree Support**: When run in the main directory (not a worktree), the command shows summaries for ALL worktrees related to the current branch in a distinguishable format.

## Process

### 0. Detect Multi-Worktree Context

First, determine if we're in a worktree or the main directory:

```bash
# Check if in worktree
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir 2>/dev/null)
IS_WORKTREE=$([ "$GIT_DIR" != "$GIT_COMMON_DIR" ] && echo "true" || echo "false")

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$IS_WORKTREE" = "false" ]; then
  # In main directory - find all worktrees for current branch
  WORKTREE_MODE="multi"

  # Get all worktrees and filter by current branch
  declare -A BRANCH_WORKTREES
  while read -r path branch; do
    # Extract branch name from worktree
    wt_branch=$(basename "$branch" | sed 's/refs\/heads\///')
    if [ "$wt_branch" = "$CURRENT_BRANCH" ]; then
      # Main directory also counts as a "worktree"
      if [ "$path" = "$(git rev-parse --show-toplevel)" ]; then
        BRANCH_WORKTREES["[main]"]="$path"
      else
        # Get worktree name from path
        wt_name=$(basename "$path" | sed 's/.*\.git\/worktrees\///')
        BRANCH_WORKTREES["$wt_name"]="$path"
      fi
    fi
  done < <(git worktree list --porcelain | grep -E "^(worktree|branch)" | paste - -)

  # If no worktrees found for current branch, show only main directory
  if [ ${#BRANCH_WORKTREES[@]} -eq 0 ]; then
    BRANCH_WORKTREES["[main]"]=$(git rev-parse --show-toplevel)
  fi
else
  # In a worktree - single worktree mode
  WORKTREE_MODE="single"
fi
```

### 1. Beads Prerequisites Check

Verify beads is available:
```bash
if ! command -v bd &> /dev/null; then
  echo "❌ beads (bd) is not installed or not in PATH"
  echo "Install from: https://github.com/steveyegge/beads"
  exit 1
fi
```

### 2. PRD Auto-Discovery

**For Single Worktree Mode:**

Use the same multi-stage discovery algorithm as generate-tasks:

**Stage 1 - Latest PRD Check:**
```bash
FLOW_DIR="$(git rev-parse --show-toplevel)/.flow"
LATEST_PRD=$(find "$FLOW_DIR" -name "prd-*.md" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
```

**Stage 2 - Context Validation:**
```bash
# Extract PRD metadata
PRD_BRANCH=$(grep -A5 "^git:" "$LATEST_PRD" | grep "branch:" | awk '{print $2}' | tr -d '"')
PRD_WORKTREE_PATH=$(grep -A5 "^worktree:" "$LATEST_PRD" | grep "path:" | awk '{print $2}' | tr -d '"')

# Get current context
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_WORKTREE=$(if [ "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" ]; then git rev-parse --git-dir; else echo ""; fi)

# Validate match
if [ "$PRD_BRANCH" = "$CURRENT_BRANCH" ] && [ "$PRD_WORKTREE_PATH" = "$CURRENT_WORKTREE" ]; then
  PRD_FILE="$LATEST_PRD"
else
  # Stage 3: Fallback search - iterate all PRDs
  for prd in "$FLOW_DIR"/prd-*.md; do
    PRD_BRANCH=$(grep -A5 "^git:" "$prd" | grep "branch:" | awk '{print $2}' | tr -d '"')
    PRD_WORKTREE_PATH=$(grep -A5 "^worktree:" "$prd" | grep "path:" | awk '{print $2}' | tr -d '"')
    if [ "$PRD_BRANCH" = "$CURRENT_BRANCH" ] && [ "$PRD_WORKTREE_PATH" = "$CURRENT_WORKTREE" ]; then
      PRD_FILE="$prd"
      break
    fi
  done
fi
```

**Stage 4 - No Match Found:**
```bash
if [ -z "$PRD_FILE" ]; then
  echo "⚠️  No PRD found matching current context"
  echo ""
  echo "Current Context:"
  echo "- Branch: $CURRENT_BRANCH"
  echo "- Worktree: ${CURRENT_WORKTREE:-none}"
  echo ""
  echo "Available PRDs:"
  for prd in "$FLOW_DIR"/prd-*.md; do
    PRD_BRANCH=$(grep -A5 "^git:" "$prd" | grep "branch:" | awk '{print $2}' | tr -d '"')
    PRD_VERSION=$(grep -A3 "^prd:" "$prd" | grep "version:" | awk '{print $2}' | tr -d '"')
    PRD_STATUS=$(grep -A3 "^prd:" "$prd" | grep "status:" | awk '{print $2}' | tr -d '"')
    echo "- $(basename "$prd") (branch: $PRD_BRANCH, version: $PRD_VERSION, status: $PRD_STATUS)"
  done
  exit 1
fi
```

**For Multi-Worktree Mode:**

When in main directory, discover PRD for each worktree:

```bash
declare -A WORKTREE_PRDS
declare -A WORKTREE_NAMES

for wt_name in "${!BRANCH_WORKTREES[@]}"; do
  wt_path="${BRANCH_WORKTREES[$wt_name]}"

  # Find PRD in this worktree's .flow directory
  wt_flow_dir="$wt_path/.flow"

  # Find PRD matching this worktree
  wt_prd=""
  if [ -d "$wt_flow_dir" ]; then
    for prd in "$wt_flow_dir"/prd-*.md 2>/dev/null; do
      if [ -f "$prd" ]; then
        prd_wt_path=$(grep -A5 "^worktree:" "$prd" | grep "path:" | awk '{print $2}' | tr -d '"')

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
```

### 3. Helper Functions

Define helper functions for status display and issue status checking:

```bash
# Helper function to get status display
get_status_display() {
  local status="$1"
  case "$status" in
    "draft") echo "📝 draft (not yet approved)" ;;
    "approved") echo "✅ approved (ready for implementation)" ;;
    "implemented") echo "✨ implemented (complete)" ;;
    *) echo "❓ $status" ;;
  esac
}

# Helper function to get issue status from beads
get_issue_status() {
  local issue_id="$1"
  if bd show "$issue_id" 2>/dev/null | grep -q "Status: closed"; then
    echo "closed"
  else
    echo "open"
  fi
}

# Function to get epic name for an issue
get_epic_for_issue() {
  local issue_id="$1"
  # Use bd dep to find parent epic
  bd dep show "$issue_id" 2>/dev/null | grep "parent:" | awk '{print $2}' | tr -d '[]'
}
```

### 4. Process Based on Mode

**For Multi-Worktree Mode (when in main directory):**

```bash
# Header
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Branch: $CURRENT_BRANCH"
echo "  Multi-Worktree Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Track totals across all worktrees
OVERALL_TOTAL=0
OVERALL_CLOSED=0

# Check if any PRDs were found
if [ ${#WORKTREE_PRDS[@]} -eq 0 ]; then
  echo "ℹ️  No PRDs found for any worktree on branch: $CURRENT_BRANCH"
  echo ""
  echo "Available worktrees:"
  for wt_name in "${!BRANCH_WORKTREES[@]}"; do
    echo "  - ${wt_name}: ${BRANCH_WORKTREES[$wt_name]}"
  done
  echo ""
  echo "Run /prd:plan in a worktree to create a PRD"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 0
fi

# Display each worktree's summary
for wt_name in "${!WORKTREE_PRDS[@]}"; do
  prd_file="${WORKTREE_PRDS[$wt_name]}"
  feature_name="${WORKTREE_NAMES[$wt_name]}"

  # Extract metadata
  wt_version=$(grep -A3 "^prd:" "$prd_file" | grep "version:" | awk '{print $2}' | tr -d '"')
  wt_status=$(grep -A3 "^prd:" "$prd_file" | grep "status:" | awk '{print $2}' | tr -d '"')
  wt_related_issues=$(grep -A2 "^beads:" "$prd_file" | grep "related_issues:" | sed 's/related_issues: //' | tr -d '[]')

  # Check if PRD has related issues
  if [ -z "$wt_related_issues" ] || [ "$wt_related_issues" = " " ]; then
    # Display worktree header
    wt_display_name="$wt_name"
    if [ "$wt_name" = "[main]" ]; then
      wt_display_name="📍 main"
    else
      wt_display_name="🌿 $wt_name"
    fi

    echo "$wt_display_name ─────────────────────────────────────────"
    echo "  Feature: $feature_name"
    echo "  PRD: $(basename "$prd_file") (v$wt_version)"
    echo "  Status: $(get_status_display "$wt_status")"
    echo ""
    echo "  ℹ️  No tasks generated yet for this PRD"
    echo "     Run /prd:generate-tasks to create tasks"
    echo ""
    continue
  fi

  # Get progress for this worktree
  wt_total=0
  wt_closed=0
  wt_open_issues=()

  for issue in $wt_related_issues; do
    wt_total=$((wt_total + 1))
    status=$(get_issue_status "$issue")
    if [ "$status" = "closed" ]; then
      wt_closed=$((wt_closed + 1))
    else
      wt_open_issues+=("$issue")
    fi
  done

  # Update overall totals
  OVERALL_TOTAL=$((OVERALL_TOTAL + wt_total))
  OVERALL_CLOSED=$((OVERALL_CLOSED + wt_closed))

  # Display worktree header
  wt_display_name="$wt_name"
  if [ "$wt_name" = "[main]" ]; then
    wt_display_name="📍 main"
  else
    wt_display_name="🌿 $wt_name"
  fi

  echo "$wt_display_name ─────────────────────────────────────────"
  echo "  Feature: $feature_name"
  echo "  PRD: $(basename "$prd_file") (v$wt_version)"
  echo "  Status: $(get_status_display "$wt_status")"
  echo ""

  # Progress
  echo "  Progress: $wt_closed/$wt_total tasks completed"
  if [ $wt_total -gt 0 ]; then
    PERCENT=$((wt_closed * 100 / wt_total))
    printf "   ["
    for i in $(seq 1 20); do
      if [ $i -le $((PERCENT / 5)) ]; then
        printf "█"
      else
        printf "░"
      fi
    done
    printf "] %d%%\n" $PERCENT
  fi
  echo ""

  # What's Left (brief - just count and list epic groups)
  if [ ${#wt_open_issues[@]} -gt 0 ]; then
    # Group by epic
    declare -A wt_epic_groups
    for issue in "${wt_open_issues[@]}"; do
      epic=$(get_epic_for_issue "$issue")
      if [ -n "$epic" ]; then
        wt_epic_groups["$epic"]+="$issue "
      fi
    done

    echo "  ⏳ Remaining: ${#wt_open_issues[@]} tasks"
    for epic in "${!wt_epic_groups[@]}"; do
      count=$(echo "${wt_epic_groups[$epic]}" | wc -w)
      echo "     • $epic: $count tasks"
    done
    echo ""
  else
    echo "  ✅ All tasks completed!"
    echo ""
  fi
done

# Overall summary footer
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Overall Progress: $OVERALL_CLOSED/$OVERALL_TOTAL tasks"
if [ $OVERALL_TOTAL -gt 0 ]; then
  PERCENT=$((OVERALL_CLOSED * 100 / OVERALL_TOTAL))
  printf "   ["
  for i in $(seq 1 20); do
    if [ $i -le $((PERCENT / 5)) ]; then
      printf "█"
    else
      printf "░"
    fi
  done
  printf "] %d%%\n" $PERCENT
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

**For Single Worktree Mode:**

```bash
# Extract PRD metadata
PRD_NAME=$(basename "$PRD_FILE" .md | sed 's/^prd-//')
PRD_VERSION=$(grep -A3 "^prd:" "$PRD_FILE" | grep "version:" | awk '{print $2}' | tr -d '"')
PRD_STATUS=$(grep -A3 "^prd:" "$PRD_FILE" | grep "status:" | awk '{print $2}' | tr -d '"')
PRD_FEATURE_NAME=$(grep -A3 "^prd:" "$PRD_FILE" | grep "feature_name:" | awk '{print $2}' | tr -d '"')
PRD_RELATED_ISSUES=$(grep -A2 "^beads:" "$PRD_FILE" | grep "related_issues:" | sed 's/related_issues: //' | tr -d '[]')
PRD_RELATED_EPICS=$(grep -A2 "^beads:" "$PRD_FILE" | grep "related_epics:" | sed 's/related_epics: //' | tr -d '[]')

# Extract overview section (between ## Overview/Introduction and next ## heading)
OVERVIEW=$(sed -n '/^## \(Overview\|Introduction\)/,/^## /p' "$PRD_FILE" | head -n -1 | tail -n +2)

# Check if PRD has related issues
if [ -z "$PRD_RELATED_ISSUES" ] || [ "$PRD_RELATED_ISSUES" = " " ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  Feature: $PRD_FEATURE_NAME"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "📋 PRD: $(basename "$PRD_FILE") (version: $PRD_VERSION)"
  echo "   Status: $(get_status_display "$PRD_STATUS")"
  echo "   Branch: $PRD_BRANCH"
  echo ""
  echo "ℹ️  No tasks generated yet for this PRD"
  echo "   Run /prd:generate-tasks to create tasks"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 0
fi

# Get issue statuses and count progress
TOTAL=0
CLOSED=0
OPEN_ISSUES=()

for issue in $PRD_RELATED_ISSUES; do
  TOTAL=$((TOTAL + 1))
  status=$(get_issue_status "$issue")
  if [ "$status" = "closed" ]; then
    CLOSED=$((CLOSED + 1))
  else
    OPEN_ISSUES+=("$issue")
  fi
done

# Group open issues by epic
declare -A EPIC_GROUPS
for issue in "${OPEN_ISSUES[@]}"; do
  epic=$(get_epic_for_issue "$issue")
  if [ -n "$epic" ]; then
    EPIC_GROUPS["$epic"]+="$issue "
  else
    EPIC_GROUPS["[no epic]"]+="$issue "
  fi
done

# Header
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Feature: $PRD_FEATURE_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# PRD Metadata
echo "📋 PRD: $(basename "$PRD_FILE") (version: $PRD_VERSION)"
echo "   Status: $(get_status_display "$PRD_STATUS")"
echo "   Branch: $PRD_BRANCH"
echo ""

# Feature Overview
if [ -n "$OVERVIEW" ]; then
  echo "📝 Overview:"
  echo "$OVERVIEW" | head -n 5
  echo ""
fi

# Progress
echo "📊 Progress: $CLOSED/$TOTAL tasks completed"

if [ $TOTAL -gt 0 ]; then
  PERCENT=$((CLOSED * 100 / TOTAL))
  printf "   ["
  for i in $(seq 1 20); do
    if [ $i -le $((PERCENT / 5)) ]; then
      printf "█"
    else
      printf "░"
    fi
  done
  printf "] %d%%\n" $PERCENT
fi
echo ""

# What's Left
if [ ${#OPEN_ISSUES[@]} -gt 0 ]; then
  echo "⏳ What's Left (${#OPEN_ISSUES[@]} tasks):"
  echo ""

  for epic in "${!EPIC_GROUPS[@]}"; do
    echo "   📦 $epic"
    for issue in ${EPIC_GROUPS[$epic]}; do
      # Get issue title
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
```
