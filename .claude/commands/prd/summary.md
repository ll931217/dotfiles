---
description: Show current feature implementation summary
---

# Rule: Feature Summary (/prd:summary)

## Goal

Provide a concise summary of the current feature implementation, showing:

- Current PRD (auto-discovered based on git context)
- PRD metadata (name, version, status, branch)
- Feature overview (goal and description from PRD content)
- Related tasks with their status (open/closed)
- Progress tracking (X/Y tasks completed)
- What's left to do (list of open tasks grouped by epic)

**Multi-Worktree Support**: When run in the main directory (not a worktree), the command shows summaries for ALL worktrees related to the current branch in a distinguishable format.

**Task Source:**
- **With beads (`bd`) installed:** Displays issues from the `.beads/` database with full status tracking
- **Without beads:** Displays tasks from the internal TodoWrite state with basic status tracking

## Implementation

The main logic is extracted into reusable scripts in `$HOME/.claude/scripts/summary/`. The executable command is in `summary.sh`.

```bash
# Execute the summary script
exec ~/.claude/scripts/summary/summary.sh
```

## Script Organization

The `/prd:summary` command uses modular scripts:

- **`lib.sh`** - Shared utilities (status display, progress bars, optional beads helpers)
- **`detect-context.sh`** - Git worktree detection and context setup
- **`prd-discovery.sh`** - Multi-stage PRD auto-discovery algorithm
- **`display-summary.sh`** - Summary display and formatting logic

This organization makes the code:

- **Reusable** - Functions can be shared across other PRD commands
- **Testable** - Each script can be tested independently
- **Maintainable** - Changes to display logic or discovery algorithm are isolated
- **Clean** - The command file focuses on execution, documentation is separate

**Beads Integration:**
The scripts detect whether beads (`bd`) is installed and adapt accordingly:
- With beads: Uses `bd` commands to query task status and display detailed progress
- Without beads: Falls back to basic summary display without detailed task status
