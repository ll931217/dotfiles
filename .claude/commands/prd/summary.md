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

The main logic is extracted into reusable scripts in `.claude/scripts/summary/`. The command sources these scripts and executes the appropriate workflow.

```bash
# Get the directory containing this command file (works in both repo and global ~/.claude/)
COMMAND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source all helper scripts relative to the command directory
# Navigate up from commands/prd/ to .claude/ (../../) then to scripts/summary/
source "$COMMAND_DIR/../../scripts/summary/lib.sh"
source "$COMMAND_DIR/../../scripts/summary/detect-context.sh"
source "$COMMAND_DIR/../../scripts/summary/prd-discovery.sh"
source "$COMMAND_DIR/../../scripts/summary/display-summary.sh"

# Check beads prerequisite
if ! command -v bd &> /dev/null; then
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
    echo "Run /prd:plan in a worktree to create a PRD"
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
```

## Script Organization

The `/prd:summary` command is now a lightweight wrapper that sources modular scripts:

- **`lib.sh`** - Shared utilities (status display, progress bars, beads helpers)
- **`detect-context.sh`** - Git worktree detection and context setup
- **`prd-discovery.sh`** - Multi-stage PRD auto-discovery algorithm
- **`display-summary.sh`** - Summary display and formatting logic

This organization makes the code:
- **Reusable** - Functions can be shared across other PRD commands
- **Testable** - Each script can be tested independently
- **Maintainable** - Changes to display logic or discovery algorithm are isolated
- **Clean** - The command file focuses on documentation and workflow
