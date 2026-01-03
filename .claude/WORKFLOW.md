# Workflow Guide

This guide documents the core workflows used in this repository for AI-assisted development using Claude Code, beads, and worktrunk.

---

## Table of Contents

1. [Beads (bd) Issue Tracking](#beads-bd-issue-tracking)
2. [Worktrunk (wt) Git Worktrees](#worktrunk-wt-git-worktrees)
3. [PRD Development Workflow](#prd-development-workflow)
4. [Multi-Agent Coordination](#multi-agent-coordination)
5. [Session Best Practices](#session-best-practices)

---

## Beads (bd) Issue Tracking

This project uses [beads](https://github.com/steveyegge/beads) for distributed, git-backed issue tracking. Beads provides persistent task memory with dependency-aware graph tracking.

### Why Beads?

- **Git-native storage**: Issues stored in `.beads/issues.jsonl`, versioned with your code
- **Dependency-aware**: Track `blocks`, `related`, `parent-child`, and `discovered-from` relationships
- **Conflict-free**: Hash-based IDs prevent merge collisions in multi-branch workflows
- **Agent-optimized**: JSON output on all commands, ~10ms ready-work detection via SQLite

### Essential Commands

| Command                               | Purpose                                              |
| ------------------------------------- | ---------------------------------------------------- |
| `bd ready`                            | **Most important**: Find tasks with no open blockers |
| `bd show <id>`                        | View issue details, audit trail, and dependencies    |
| `bd create "Title" -p 0`              | Create P0 (urgent) task                              |
| `bd create "Title" -t epic`           | Create epic (parent task)                            |
| `bd update <id> --status in_progress` | Claim work on a task                                 |
| `bd update <id> --assignee <agent>`   | Assign task to specific agent                        |
| `bd close <id> --reason "Done"`       | Complete task with reason                            |
| `bd dep add <child> <parent>`         | Link tasks (default: blocks)                         |
| `bd dep tree <id>`                    | View dependency hierarchy                            |
| `bd sync`                             | Export DB → JSONL, commit, and push (MANDATORY)      |
| `bd stats`                            | Show project statistics and progress                 |

### Dependency Types

```bash
# Task A blocks Task B (B cannot start until A completes)
bd dep add bd-a1b2 bd-c3d4  # bd-c3d4 blocks bd-a1b2

# Related tasks (connected but don't block)
bd dep add bd-a1b2 bd-c3d4 -t related

# Parent-child relationship (epics)
bd dep add bd-a1b2 bd-c3d4 -t parent-child

# Discovered from (agent found this while working on parent)
bd dep add bd-a1b2 bd-c3d4 -t discovered-from
```

### Hierarchical IDs (Epics)

```bash
# Create epic
bd create "Auth System" -t epic -p 1
# Returns: bd-a3f8e9

# Create children (automatically gets hierarchical ID)
bd create "Login UI" -p 1
# Returns: bd-a3f8e9.1

bd create "Password validation" -p 1
# Returns: bd-a3f8e9.2

# View hierarchy
bd dep tree bd-a3f8e9
```

### Query Examples

```bash
# List ready work for specific assignee
bd ready --assignee agent-1

# Filter by priority
bd ready --priority 0

# Filter by label
bd ready --label backend

# Show all open issues
bd list --status open

# Show issues in progress
bd list --status in_progress
```

### Git Hooks

Beads installs git hooks automatically during `bd init`:

- **pre-commit**: Flushes SQLite DB → JSONL before commit
- **post-merge**: Imports JSONL → DB after pull
- **pre-push**: Exports DB → JSONL before push
- **post-checkout**: Imports JSONL → DB after branch switch

### Rules

- Whenever the user suggests changes, no matter in which mode, you should create tasks in `beads` before, confirm with the user before proceeding with implementing those changes.
- If there is a PRD available at `.flow/prd-*.md`, make sure to update the current PRD. Check the frontmatter of the file for the current PRD, if you can't find one then ignore this rule.
- **Always run `bd sync` before ending a session** to ensure changes are committed and pushed.

---

## Worktrunk (wt) Git Worktrees

This project uses [worktrunk](https://worktrunk.dev/) for managing git worktrees, enabling parallel AI agent workflows.

### Why Worktrunk?

- **Isolated workspaces**: Each agent gets its own working directory
- **Clean interface**: Simpler than raw `git worktree` commands
- **Lifecycle hooks**: Automate setup/teardown on worktree create/merge
- **Parallel agents**: Scale agents by scaling branches

### Installation

```bash
# Homebrew (macOS & Linux)
brew install max-sixty/worktrunk/wt
wt config shell install  # enables cd behavior

# Cargo
cargo install worktrunk
wt config shell install
```

### Core Commands

| Task                  | Worktrunk                     | Plain git                                                  |
| --------------------- | ----------------------------- | ---------------------------------------------------------- |
| Switch worktrees      | `wt switch feat`              | `cd ../repo.feat`                                          |
| Create + switch       | `wt switch -c feat`           | `git worktree add -b feat ../repo.feat && cd ../repo.feat` |
| Create + start Claude | `wt switch -c -x claude feat` | _(multiple commands)_                                      |
| List with status      | `wt list`                     | `git worktree list` _(no status)_                          |
| Clean up              | `wt remove`                   | `git worktree remove && git branch -d`                     |
| Merge back            | `wt merge`                    | _(complex manual process)_                                 |

### Workflow Examples

```bash
# List all worktrees with git status
wt list

# Create new worktree for feature and switch to it
wt switch -c feat/add-login

# Create and immediately start Claude Code
wt switch -c -x claude feat/add-login

# Return to main worktree
wt switch master  # or just `wt switch` for default

# Merge feature branch back and clean up
wt merge
```

### Multi-Agent Pattern

```bash
# Agent 1: Create isolated workspace
wt switch -c agent-1/auth-system
cd ../dotfiles.agent-1
# ... work ...

# Agent 2: Different workspace (simultaneously)
wt switch -c agent-2/database-migration
cd ../dotfiles.agent-2
# ... work ...

# Both agents can work independently without conflicts
```

### Configuration

Project-specific hooks can be defined in `.worktrunk.yml`:

```yaml
# Run on worktree creation
hooks:
  create:
    - "npm install"
    - "bd sync" # Ensure beads is synced

  # Run before merging
  pre-merge:
    - "npm test"
    - "bd ready" # Check if any tasks remain

  # Run after merge
  post-merge:
    - "bd sync"
    - "wt remove" # Clean up worktree
```

---

## PRD Development Workflow

This repository uses a structured Product Requirements Document (PRD) workflow for requirements-driven development.

### Custom Commands

| Command               | Purpose                              |
| --------------------- | ------------------------------------ |
| `/flow:plan`           | Create PRD with auto-generated tasks |
| `/flow:implement`      | Implement approved PRD               |
| `/flow:generate-tasks` | Generate tasks from approved PRD     |
| `/flow:summary`        | Show PRD status and history          |

### PRD Structure

PRDs are stored with YAML frontmatter containing:

```yaml
---
title: "Feature Name"
author: "author-name"
date: 2024-01-15
status: approved  # draft, review, approved, implemented
priority: 1  # 0-4 (P0 = urgent, P4 = low)
assignee: unassigned
prd_id: PRD-001
branch: feat/feature-name
related_issues:
  - bd-a1b2
  - bd-c3d4
---

## Summary
[One-paragraph overview]

## Requirements
### Functional Requirements
- FR-1: Description...
- FR-2: Description...

### Non-Functional Requirements
- NFR-1: Performance requirement...
- NFR-2: Security requirement...

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Implementation Tasks
Generated via `/flow:generate-tasks`

## Testing Strategy
[Describe testing approach]

## Dependencies
[External or internal dependencies]
```

### Workflow Steps

1. **Create PRD**: Use `/flow:plan` to generate requirements document
2. **Review**: PRD is marked as `review` status
3. **Approve**: After review, mark as `approved`
4. **Generate Tasks**: Use `/flow:generate-tasks` to create beads issues
5. **Implement**: Use `/flow:implement` to begin implementation
6. **Track**: Use `/flow:summary` to monitor progress

### Priority Levels

| Priority | Description       | Response Time   |
| -------- | ----------------- | --------------- |
| P0       | Critical/Blocking | Immediate       |
| P1       | High Priority     | Within 24 hours |
| P2       | Medium Priority   | Within 1 week   |
| P3       | Low Priority      | Within 1 month  |
| P4       | Backlog           | When available  |

---

## Multi-Agent Coordination

When working with multiple AI agents simultaneously:

### Coordination Pattern

```bash
# Agent 1 claims backend work
bd ready --assignee agent-1 --json
bd update bd-a1b2 --status in_progress --assignee agent-1

# Agent 2 claims different work
bd ready --assignee agent-2 --json
bd update bd-c3d4 --status in_progress --assignee agent-2

# Both sync via git
git pull  # Get other agent's changes
bd sync   # Push your own changes
```

### Best Practices

1. **Use assignee field**: Prevents duplicate work
2. **Sync frequently**: Reduces merge conflicts
3. **Create separate worktrees**: Each agent gets isolated workspace
4. **Use dependencies**: Mark blocking relationships explicitly
5. **Review git diffs**: See what other agents changed

### Conflict Resolution

Beads uses hash-based IDs to minimize conflicts:

```bash
# If merge conflict occurs in .beads/issues.jsonl:
git checkout --ours .beads/issues.jsonl   # Keep your changes
# OR
git checkout --theirs .beads/issues.jsonl  # Take remote changes
# OR
# Edit manually, then:
bd import -i .beads/issues.jsonl
```

---

## Session Best Practices

### Starting a Session

```bash
# 1. Pull latest changes
git pull
bd import -i .beads/issues.jsonl

# 2. Check for available work
bd ready

# 3. If starting new feature, create worktree
wt switch -c feat/my-feature

# 4. Claim work
bd update <id> --status in_progress --assignee claude
```

### During a Session

```bash
# Update task as you work
bd update <id> --status in_progress

# Create discovered issues
bd create "Found edge case" -t bug -p 1 --deps discovered-from:bd-parent

# Check progress
bd stats
```

### Ending a Session

```bash
# 1. Complete current task
bd close <id> --reason "Completed implementation"

# 2. Sync beads (MANDATORY)
bd sync

# 3. Commit and push code
git add .
git commit -m "feat: implement feature (bd-abc)"
git push

# 4. Return to main if using worktree
wt switch master
```

### Golden Rules

1. **Always `bd sync` before ending** - Ensures tasks are committed and pushed
2. **Never create "test" issues** in production DB - Use `BEADS_DB=/tmp/test.db`
3. **Use `--json` flags** in scripts - Programmatic output
4. **Claim work with assignee** - Prevents duplicate work
5. **Review `bd ready` first** - Know what's available before starting

---

## Quick Reference

### Beads Cheatsheet

```bash
bd ready                              # Find available work
bd show <id>                          # View task details
bd create "Title" -p 0                # Create urgent task
bd update <id> --status in_progress   # Claim work
bd close <id>                         # Complete task
bd dep add <a> <b>                    # Link tasks
bd sync                               # Commit & push
```

### Worktrunk Cheatsheet

```bash
wt list                               # List worktrees
wt switch -c feat                     # Create & switch
wt switch feat                        # Switch to existing
wt merge                              # Merge & cleanup
wt remove                             # Remove worktree
```

### Combined Workflow

```bash
# Start new feature
wt switch -c feat/new-feature
bd create "Implement feature" -p 1
bd update bd-xxx --status in_progress

# Work...

# Complete and sync
bd close bd-xxx --reason "Done"
bd sync
git add . && git commit -m "feat: ... (bd-xxx)"
git push
```

---

## Additional Resources

- [Beads Documentation](https://github.com/steveyegge/beads)
- [Worktrunk Documentation](https://worktrunk.dev/)
- [Claude Code Best Practices](https://docs.anthropic.com/claude-code)
- [Git Worktree Documentation](https://git-scm.com/docs/git-worktree)
