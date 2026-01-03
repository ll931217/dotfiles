#!/usr/bin/env bash
# Feature Summary (/flow:summary)
# Show current feature implementation summary

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

# Source all helper scripts relative to the command directory
source "$SCRIPT_DIR/lib.sh"
source "$SCRIPT_DIR/detect-context.sh"
source "$SCRIPT_DIR/prd-discovery.sh"
source "$SCRIPT_DIR/display-summary.sh"

# Check beads prerequisite
if ! command -v bd &>/dev/null; then
  echo "❌ beads (bd) is not installed or not in PATH"
  echo "Install from: https://github.com/steveyegge/beads"
  exit 1
fi

# Detect worktree context (sets WORKTREE_MODE, CURRENT_BRANCH, BRANCH_WORKTREES)
detect_worktree_context

# Get current worktree path for context matching
CURRENT_WORKTREE=$(get_current_worktree_path)

# Get flow directory
FLOW_DIR="$(git rev-parse --show-toplevel)/.flow"

# Execute based on mode
if [ "$WORKTREE_MODE" = "multi" ]; then
  # Multi-worktree mode: discover PRDs for all worktrees
  discover_prd_multi BRANCH_WORKTREES

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
    exit 0
  fi

  # Display multi-worktree summary
  display_multi_summary
else
  # Single worktree mode: discover the PRD for this worktree
  PRD_FILE=$(discover_prd_single "$FLOW_DIR" "$CURRENT_BRANCH" "$CURRENT_WORKTREE")

  # Check if PRD was found
  if [ -z "$PRD_FILE" ]; then
    show_no_prd_error "$FLOW_DIR" "$CURRENT_BRANCH" "$CURRENT_WORKTREE"
    exit 1
  fi

  # Display single worktree summary
  display_single_summary "$PRD_FILE"
fi
