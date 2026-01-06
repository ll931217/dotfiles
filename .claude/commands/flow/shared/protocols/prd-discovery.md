# PRD Auto-Discovery Protocol

## Overview

This protocol defines the multi-stage algorithm for automatically discovering Product Requirements Documents (PRDs) based on git context (branch, worktree). It is used by `/flow:plan`, `/flow:generate-tasks`, `/flow:cleanup`, and `/flow:summary`.

## Reference Implementation

See: `~/.claude/scripts/summary/prd-discovery.sh` for the shell script implementation.

## Multi-Stage Algorithm

### Stage 1: Latest PRD Check

Find the most recently modified PRD in `/.flow/` directory:

```bash
# Find latest PRD by modification time
LATEST_PRD=$(find /.flow -name "prd-*.md" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
```

Extract metadata from PRD frontmatter:
- `git.branch` - Branch name
- `worktree.name` - Worktree name
- `worktree.path` - Worktree .git path
- `prd.status` - Current PRD status

### Stage 2: Context Validation

Detect current git context:

```bash
# Current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Worktree detection
GIT_DIR=$(git rev-parse --git-dir)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir)
IS_WORKTREE=$([ "$GIT_DIR" != "$GIT_COMMON_DIR" ] && echo "true" || echo "false")

# Current worktree info (if in worktree)
if [ "$IS_WORKTREE" = "true" ]; then
  CURRENT_WORKTREE_NAME=$(git worktree list --porcelain | grep -A1 "^$(git rev-parse --show-toplevel)$" | tail -1 | sed 's/^branch //' | sed 's|refs/heads/||')
  CURRENT_WORKTREE_PATH="$GIT_DIR"
else
  CURRENT_WORKTREE_NAME="main"
  CURRENT_WORKTREE_PATH=""
fi
```

**Match Criteria:** ALL of the following must match
- Branch name matches exactly (or both are main/master)
- Worktree name matches (if both in worktrees)
- Worktree path matches (if both in worktrees)

### Stage 3: Fallback Search

If latest PRD doesn't match current context, search all PRDs in `/.flow/`:

```bash
for prd in /.flow/prd-*.md; do
  # Extract frontmatter
  prd_branch=$(grep "git.branch" "$prd" | awk '{print $2}')
  prd_worktree=$(grep "worktree.name" "$prd" | awk '{print $2}')

  # Compare with current context
  if [ "$prd_branch" = "$CURRENT_BRANCH" ] && [ "$prd_worktree" = "$CURRENT_WORKTREE_NAME" ]; then
    MATCHING_PRD="$prd"
    break
  fi
done
```

### Stage 4: No Match Found

If no PRD matches current context, use `AskUserQuestion` to inform user and offer options:

```
AskUserQuestion({
  questions: [{
    question: "No PRD matches the current context (branch: [branch], worktree: [worktree]). Available PRDs: [list]. What would you like to do?",
    header: "PRD Action",
    options: [
      {
        label: "Create new PRD",
        description: "Run /flow:plan to create a new PRD"
      },
      {
        label: "Select existing PRD",
        description: "Manually select one of the available PRDs"
      },
      {
        label: "Exit",
        description: "Exit the process"
      }
    ],
    multiSelect: false
  }]
})
```

## Git Context Detection

Full context detection for PRD frontmatter:

```bash
# Branch name
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Worktree detection
GIT_DIR=$(git rev-parse --git-dir)
GIT_COMMON_DIR=$(git rev-parse --git-common-dir)
IS_WORKTREE=$([ "$GIT_DIR" != "$GIT_COMMON_DIR" ] && echo "true" || echo "false")

# Worktree name (from git worktree list or branch)
if [ "$IS_WORKTREE" = "true" ]; then
  WORKTREE_NAME=$(git worktree list --porcelain | grep -A1 "^$(git rev-parse --show-toplevel)$" | tail -1 | sed 's/^branch //' | sed 's|refs/heads/||')
  WORKTREE_PATH="$GIT_DIR"
else
  WORKTREE_NAME="main"
  WORKTREE_PATH=""
fi

# Branch type categorization
case "$BRANCH" in
  main|master) BRANCH_TYPE="main" ;;
  develop|dev) BRANCH_TYPE="develop" ;;
  feature/*) BRANCH_TYPE="feature" ;;
  bugfix/*|fix/*) BRANCH_TYPE="bugfix" ;;
  hotfix/*) BRANCH_TYPE="hotfix" ;;
  *) BRANCH_TYPE="other" ;;
esac

# Commit info
COMMIT_SHA=$(git rev-parse HEAD)
AUTHOR_NAME=$(git log -1 --format="%an" HEAD)
AUTHOR_EMAIL=$(git log -1 --format="%ae" HEAD)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
REPO_ROOT=$(git rev-parse --show-toplevel)
```

## Iteration Detection

When a PRD is found for the current context, determine if this is iteration mode:

**Iteration mode triggers:**
- PRD status is `approved` or `implemented` (not `draft`)
- User explicitly requested updates to existing PRD

**Iteration mode actions:**
- Display message: `Found existing PRD: [filename] (version: N, status: [status])`
- Explain: "I'll iterate on this existing PRD. When you provide your updates, I'll increment the version and update the content."
- Store the existing PRD path and version for later use

**New PRD mode actions:**
- Display message: "No existing PRD found for this context. Creating a new PRD."
- Proceed to create a new PRD file

## Usage in Flow Commands

| Command | Step | Usage |
|---------|------|-------|
| `/flow:plan` | Step 2.5 | Detect context, check for existing PRD |
| `/flow:generate-tasks` | Step 1 | Discover PRD for task generation |
| `/flow:cleanup` | Step 1 | Discover PRD for cleanup |
| `/flow:summary` | Auto | Uses `discover_prd_single()` function from script |

## Frontmatter Fields

The PRD frontmatter contains these git-related fields:

```yaml
git:
  branch: feature/auth          # Current branch name
  branch_type: feature          # Categorized branch type
  created_at_commit: abc123...  # Commit SHA when PRD created
  updated_at_commit: def456...  # Commit SHA when PRD last updated
worktree:
  is_worktree: true             # Whether in a worktree
  name: feature-auth            # Worktree name
  path: /path/to/.git/worktrees/feature-auth  # Worktree .git path
  repo_root: /path/to/repo      # Repository root path
```
