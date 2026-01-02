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

## Implementation

The main logic is extracted into reusable scripts in `$HOME/.claude/scripts/summary/`. The executable command is in `summary.sh`.

## Script Organization

The `/prd:summary` command uses modular scripts:

- **`lib.sh`** - Shared utilities (status display, progress bars, beads helpers)
- **`detect-context.sh`** - Git worktree detection and context setup
- **`prd-discovery.sh`** - Multi-stage PRD auto-discovery algorithm
- **`display-summary.sh`** - Summary display and formatting logic

This organization makes the code:

- **Reusable** - Functions can be shared across other PRD commands
- **Testable** - Each script can be tested independently
- **Maintainable** - Changes to display logic or discovery algorithm are isolated
- **Clean** - The command file focuses on execution, documentation is separate
