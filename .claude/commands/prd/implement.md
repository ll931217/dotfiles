# Task List Management

Guidelines for managing task lists using beads (`bd`) to track progress on completing a PRD

## Beads Prerequisites Check

Before beginning implementation, verify beads is available and initialized:

**Automated Check:** The AI should verify that:

- The `bd` command is available in the system PATH
- The `.beads` directory exists (initialize with beads if not present)
- Beads database is functional

If beads is not available, provide installation instructions and pause execution.

## PRD Discovery and Validation

Before beginning implementation, discover and validate the PRD:

**Auto-Discovery:** Use the same discovery algorithm as `/prd:generate-tasks`:
1. Check latest modified PRD for metadata match
2. Validate branch and worktree context
3. Fallback search if no match
4. Prompt user if no matching PRD found

**Discovery Commands:**
```bash
# Find latest PRD
LATEST_PRD=$(find /.flow -name "prd-*.md" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

# Extract metadata from PRD frontmatter
PRD_BRANCH=$(grep -A5 "^git:" "$LATEST_PRD" | grep "branch:" | awk '{print $2}' | tr -d '"')
PRD_STATUS=$(grep -A3 "^prd:" "$LATEST_PRD" | grep "status:" | awk '{print $2}' | tr -d '"')
PRD_WORKTREE_PATH=$(grep -A5 "^worktree:" "$LATEST_PRD" | grep "path:" | awk '{print $2}' | tr -d '"')
PRD_RELATED_ISSUES=$(grep -A2 "^beads:" "$LATEST_PRD" | grep "related_issues:" | sed 's/related_issues: //' | tr -d '[]')

# Get current context
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_WORKTREE=$(if [ "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" ]; then git rev-parse --git-dir; else echo ""; fi)

# Validate match
if [ "$PRD_BRANCH" = "$CURRENT_BRANCH" ] && [ "$PRD_WORKTREE_PATH" = "$CURRENT_WORKTREE" ]; then
  echo "Match found: $LATEST_PRD"
else
  echo "Searching for matching PRD..."
  # Fallback search logic
fi
```

**Status Validation:** After discovering the PRD:
- Check `prd.status` field in frontmatter
- If status is `draft`, warn user:
  ```
  ⚠️  PRD status is "draft"
  This PRD has not been approved yet.
  Consider running /prd:generate-tasks first, or continue anyway?
  ```
- If status is `approved`, proceed with implementation
- Display PRD metadata summary with status indicator:
  ```
  Using PRD: prd-authentication.md (version: 3)
  - Status: ✅ approved (ready for implementation)
  - Branch: feature/auth
  - Worktree: feature-auth
  - Related Issues: proj-123, proj-456
  - Related Epics: proj-789
  ```

**Status Indicators:**
- `draft` = 📝 draft (not yet approved)
- `approved` = ✅ approved (ready for implementation)
- `implemented` = ✨ implemented (complete)

**PRD Updates During Implementation:**
- When PRD changes are made (see "PRD Change Management"), update frontmatter:
  - Increment version in `prd.version`
  - Update `metadata.updated_at`
  - Update `git.updated_at_commit`
  - Update `metadata.filename`
  - Set `prd.status` to `implemented` when all tasks complete

## PRD Completion Detection

After closing each task with `bd close`, check if all PRD tasks are complete and update the PRD status to `implemented`.

### Helper Functions

**Function: check_prd_completion**

Checks if all tasks for a PRD are complete and updates the PRD status to `implemented` if so.

```bash
# Function to check if all PRD tasks are complete and update status
check_prd_completion() {
  local prd_file="$1"

  # Get current PRD status
  local current_status=$(grep "^  status:" "$prd_file" | awk '{print $2}')

  # Skip if already implemented or not yet approved
  if [ "$current_status" != "approved" ]; then
    return 0
  fi

  # Get all related issues from PRD frontmatter
  local related_issues=$(grep -A2 "^beads:" "$prd_file" | grep "related_issues:" | sed 's/.*: \[\(.*\)\]/\1/')

  # Skip if no related issues
  if [ -z "$related_issues" ] || [ "$related_issues" = "[]" ]; then
    return 0
  fi

  # Clean up the issue list (remove brackets, quotes, commas)
  related_issues=$(echo "$related_issues" | tr -d '[]",' | tr ' ' '\n' | grep -v '^$')

  # Check if all issues are closed
  local all_closed=true
  local total=0
  local closed=0

  for issue in $related_issues; do
    total=$((total + 1))
    # Check issue status using beads
    if bd show "$issue" 2>/dev/null | grep -q "Status: closed"; then
      closed=$((closed + 1))
    else
      all_closed=false
    fi
  done

  # If all closed, update PRD status to implemented
  if [ "$all_closed" = true ] && [ $total -gt 0 ]; then
    local current_version=$(grep "^  version:" "$prd_file" | awk '{print $2}')
    local new_version=$((current_version + 1))

    # Update version, status, timestamp, and commit
    sed -i "s/^  version: $current_version/  version: $new_version/" "$prd_file"
    sed -i 's/^  status: approved/  status: implemented/' "$prd_file"
    sed -i "s/^  updated_at: .*/  updated_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")/" "$prd_file"
    sed -i "s/^  updated_at_commit: .*/  updated_at_commit: $(git rev-parse HEAD)/" "$prd_file"

    # Add entry to changelog
    local changelog_entry="| $new_version | $(date -u +"%Y-%m-%d %H:%M") | All $closed tasks completed - status set to implemented |"

    # Insert changelog entry after the header row
    sed -i "/^| Version |/a $changelog_entry" "$prd_file"

    echo ""
    echo "✨ ──────────────────────────────────────────────────"
    echo "  PRD Implementation Complete!"
    echo "  PRD: $(basename "$prd_file")"
    echo "  Tasks completed: $closed/$total"
    echo "  Status: approved → implemented"
    echo "  Version: $current_version → $new_version"
    echo "✨ ──────────────────────────────────────────────────"
    echo ""
  else
    # Show progress
    echo "📊 Progress: $closed/$total tasks completed"
  fi
}
```

**Function: find_prd_for_issue**

Finds which PRD file contains a given issue in its `related_issues`.

```bash
# Find PRD file that contains the given issue in related_issues
find_prd_for_issue() {
  local issue_id="$1"
  local flow_dir="$(git rev-parse --show-toplevel)/.flow"

  for prd in "$flow_dir"/prd-*.md; do
    if [ -f "$prd" ]; then
      if grep -q "related_issues:" "$prd" && grep "$issue_id" "$prd" >/dev/null 2>&1; then
        echo "$prd"
        return 0
      fi
    fi
  done

  return 1
}
```

### Usage Example

After closing a task with `bd close`, check if the PRD is now complete:

```bash
# After closing a task
bd close "$issue_id"

# Check if PRD is now complete
PRD_FILE=$(find_prd_for_issue "$issue_id")
if [ -n "$PRD_FILE" ]; then
  check_prd_completion "$PRD_FILE"
fi
```

## Beads Integration

All task context is stored in beads' SQLite database. Task management is handled through beads integration - no separate task files needed.

## Task Implementation

- **Autonomous Execution Strategy:**
  - Execute tasks continuously without asking for permission
  - Only stop to ask the user when you discover something that needs clarification:
    - Ambiguous requirements not covered by the PRD
    - Multiple valid implementation approaches where user preference matters
    - Missing information or dependencies
    - Conflicting requirements discovered during implementation
  - When stopping for clarification, clearly explain the issue and provide options

- **Parallel Group Execution ([P:Group-X] flags):**
- **Phase 1 - Pre-execution Analysis:** Before starting any parallel group:
  - Check which tasks are unblocked
  - Use `bd dep tree <issue-id>` to verify no blocking dependencies
  - Run `bd show <issue-id>` to check task details and any blockers
- **Phase 2 - Concurrent Execution:** Launch all tasks in the group simultaneously:
  - Use multiple specialized subagents via Task tool with parallel invocations
  - Each subagent works on their assigned files (listed in task description)
  - Update task status with `bd update <issue-id> --status in_progress`
- **Phase 3 - Coordination & Monitoring:**
  - Monitor progress via `bd list --status in_progress`
  - Use beads database for coordination between parallel tasks
  - Wait for ALL tasks in the group to complete before proceeding
- **Phase 4 - Post-execution Validation:**
  - Verify all group tasks are completed with `bd list`
  - Close completed tasks with `bd close <issue-id>`
  - Run tests if applicable before moving to next group/task
- **Completion protocol:**
  - When you finish a **sub-task**, immediately mark it as completed:
    - Update beads to close the task
    - Update markdown: change `[ ]` to `[x]`
  - If **all** sub-tasks underneath a parent task are now complete, follow this sequence:
    - **First**: Run the full test suite (pytest, npm test, bin/rails test, etc.)
    - **Only if all tests pass**: Stage changes (git add .)
    - **Clean up**: Remove any temporary files and temporary code before committing
    - **Commit**: Use a descriptive commit message that:
      - Uses conventional commit format (`feat:`, `fix:`, `refactor:`, etc.)
      - Summarizes what was accomplished in the parent task
      - Lists key changes and additions
      - References the beads issue ID and PRD context
      - **Formats the message as a single-line command using `-m` flags**

  - Once all the subtasks are closed in beads and changes have been committed, close the **parent task** in beads.

## PRD Change Management

This section handles what happens when PRD needs updates mid-implementation.

### Change Triage

When a PRD revision is requested, first categorize change:

| Change Type  | Examples                                                                | Impact on Tasks                                    |
| ------------ | ----------------------------------------------------------------------- | -------------------------------------------------- |
| **Minor**    | Typo fix, clarification, added edge case detail                         | Can proceed without task regeneration              |
| **Moderate** | New requirement within scope, small UX change, additional field         | May require task updates, minimal regeneration     |
| **Major**    | New feature, removed requirement, architectural change, scope expansion | Requires full task regeneration and work migration |

### Minor Changes (No Task Regeneration Needed)

**Workflow:**

1. Update PRD document directly (increment version: `prd-auth-v2.md` → `prd-auth-v3.md`)
2. Update `prd-auth-history.md` with change log entry for version, date, and summary of changes
3. Continue implementation without pausing
4. Incorporate changes into current/subsequent tasks

**Concrete Example:**

```markdown
# Scenario: PRD v2 clarification needed

**Current PRD (v2):**
```

Functional Requirements:

1. The system shall allow users to upload profile pictures

```

**Change Request:** "What's the maximum file size allowed?"

**Updated PRD (v3):**
```

Functional Requirements:

1. The system shall allow users to upload profile pictures (maximum 50MB)

Non-Goals (Out of Scope):

- Video uploads (only images: jpg, png, gif, webp)

````

**prd-auth-history.md update:**
```markdown
| Version | Date | Approved | Summary of Changes |
|---------|------|----------|-------------------|
| v1 | 2025-01-15 10:30 | Yes | Initial PRD approved |
| v2 | 2025-01-15 14:22 | Yes | Added Admin role permissions |
| v3 | 2025-01-16 09:45 | Yes | Clarified file upload: max 50MB, images only |
````

**Action:**

- Continue with current task: "Implement profile picture upload"
- No task regeneration needed
- Include new constraints (50MB, images only) in implementation

````

### Moderate Changes (Task Updates Required)

**Workflow:**

1. **Pause current implementation:**
   - Find current task that is in progress
   - Update task status to blocked with note explaining PRD version change

2. **Update PRD** (increment version: `prd-auth-v2.md` → `prd-auth-v3.md`)
3. **Update PRD history** with version, date, and summary

4. **Analyze affected tasks:**
   - List all open and in-progress tasks
   - Review task descriptions to identify which reference changed PRD sections

5. **For each affected task:**
   - **If task NOT started** (status: `open`): Close task with reason about PRD version change
   - **If task IN PROGRESS** (status: `in_progress`):
     - Commit current work with descriptive WIP message explaining task ID, title, progress, and PRD version change reason
     - Close task with reason about PRD version change

6. **Regenerate task(s) from updated PRD:**
   - Create new tasks with updated requirements and file lists
   - Update task descriptions to reference new PRD version

7. **Update task descriptions with new PRD version reference**
8. **Resume implementation** with regenerated tasks

**Concrete Example:**

```markdown
# Scenario: PRD v2 → v3 - Added Admin role

**Current Tasks (v2):**
````

Open tasks:

- proj-abc123: Define user permissions (regular users only)
- proj-def456: Implement permission checks
- proj-ghi789: Write permission tests

In-progress:

- proj-jkl012: Create user role enum [USER]

```

**PRD Change (v3):**
```

Functional Requirements: 5. The system shall support user roles: User and Admin 6. Admin users shall have full access to all resources

````

**History Update:**
```markdown
| v3 | 2025-01-16 11:30 | Yes | Added Admin role with full access permissions |
````

**Actions:**

1. Pause in-progress task with blocked status and PRD version change note
2. Commit all work with WIP message explaining task, progress, and PRD version change reason
3. Close affected tasks with regeneration reason
4. Regenerate tasks with updated requirements:
   - Define user permissions including Admin role
   - Implement permission checks for all roles
   - Create user and admin role enums
5. Link new tasks to parent epic
6. Resume with regenerated tasks

**Result:** 4 new tasks regenerated, old tasks closed with clear reason, implementation can resume.

````

### Major Changes (Full Regeneration Required)

**Workflow:**

1. **Checkpoint current progress:**
   - Commit all WIP with comprehensive message including:
     - PRD version change (v3 to v4)
     - Reason for architectural shift
     - List of completed epics, completed tasks, in-progress tasks, and open tasks
     - Note about tasks that will be regenerated

2. **Create backup directory:**
   - Create timestamped backup directory in `.beads/backups/prd-v3-to-v4-TIMESTAMP/`

3. **Save current task state:**
   - Export all task information (full list, by status categories)
   - Export dependency trees for all epics
   - Export detailed information for all tasks
   - All exports saved to backup directory

4. **Create migration map:**
   - Create markdown file documenting:
     - Overview (from/to PRD versions, date, reason)
     - Completed work (tasks that can be reused vs cannot be reused)
     - Open tasks mapping (v3 task IDs to v4 actions)
     - Decisions made (what gets reused vs regenerated)
     - Notes about the migration

5. **Auto-close all open and in-progress tasks:**
   - Find all open and in-progress tasks
   - Auto-close all with regeneration reason explaining PRD version change and migration details

6. **Completed tasks remain visible** (marked as completed, not closed):
   - Keep visible for reference
   - Use migration map to identify reusable work

7. **Regenerate from updated PRD:**
   - Follow full `/prd:generate-tasks` workflow from Phase1
   - Generate new parent epics
   - Generate new sub-issues
   - Create new dependencies

8. **Migrate completed work:**
   - For each completed v3 task, determine if v4 task covers same functionality
   - Reference migration map for decisions
   - Can reuse: Mark new task as complete (reference old task ID)
   - Cannot reuse: Start fresh (reference backup, not marked complete)

9. **Update all references:**
   - New tasks reference new PRD version
   - Update `prd-auth-history.md` with full change summary
   - Keep v3 tasks visible but completed for reference

10. **Resume implementation:**
    - Show which new tasks are ready to work on

2. **Create backup directory:**
   ```bash
   # Create timestamped backup directory
   mkdir -p .beads/backups/prd-v3-to-v4-$(date +%Y%m%d-%H%M%S)

   # Backup directory: .beads/backups/prd-v3-to-v4-20250116-143022/
````

3. **Save current task state:**

   ```bash
   BACKUP_DIR=".beads/backups/prd-v3-to-v4-$(date +%Y%m%d-%H%M%S)"

   # Export all task information
   bd list > "$BACKUP_DIR/task-list.txt"
   bd list --status open > "$BACKUP_DIR/open-tasks.txt"
   bd list --status in_progress > "$BACKUP_DIR/in-progress-tasks.txt"
   bd list --status closed > "$BACKUP_DIR/completed-tasks.txt"

   # Export dependency trees for all epics
   for epic_id in $(bd list --type epic --format "{{.ID}}"); do
     bd dep tree $epic_id > "$BACKUP_DIR/dependency-tree-$epic_id.txt"
   done

   # Export task details
   for task_id in $(bd list --format "{{.ID}}"); do
     echo "=== Task: $task_id ===" >> "$BACKUP_DIR/task-details.txt"
     bd show $task_id >> "$BACKUP_DIR/task-details.txt"
     echo "" >> "$BACKUP_DIR/task-details.txt"
   done
   ```

4. **Create migration map:**

   ```bash
   BACKUP_DIR=".beads/backups/prd-v3-to-v4-$(date +%Y%m%d-%H%M%S)"

   cat > "$BACKUP_DIR/migration-map.md" << 'EOF'
   # PRD v3 to v4 Migration Map

   ## Overview
   - **From:** PRD v3 (REST API architecture)
   - **To:** PRD v4 (GraphQL API architecture)
   - **Date:** 2025-01-16 14:30:22
   - **Reason:** Architectural shift from REST to GraphQL

   ## Completed Work (v3)

   ### Can Reuse in v4
   - **proj-ghi789:** Initialize project structure → ✓ Reuse for GraphQL setup
   - **proj-jkl012:** Create user table → ✓ Reuse (database schema same)

   ### Cannot Reuse (Architecture Mismatch)
   - **proj-mno345:** Implement authentication service (REST) → ✗ Discard (needs GraphQL resolvers)
   - **proj-abc123:** Setup & Configuration → ✗ Partial (update to GraphQL server setup)

   ## Open Tasks (v3 → v4 Mapping)

   | v3 Task ID | v3 Task Title | v4 Action | New v4 Task ID |
   |------------|---------------|-----------|----------------|
   | proj-pqr678 | Create login endpoint | Regenerate as GraphQL mutation | TBD |
   | proj-stu901 | Add rate limiting | Regenerate as GraphQL middleware | TBD |
   | proj-vwx123 | Implement refresh tokens | Regenerate as GraphQL mutation | TBD |
   | proj-yza456 | Write unit tests | Regenerate for GraphQL | TBD |

   ## Decisions Made
   1. Database schema unchanged (reuse completed tasks)
   2. Authentication logic needs GraphQL adaptation (regenerate)
   3. All REST endpoints become GraphQL mutations/queries (regenerate)
   4. Rate limiting middleware adapted for GraphQL context (regenerate)

   ## Notes
   - Save WIP from proj-mno345 as reference for GraphQL resolver implementation
   - User table design is solid, no changes needed
   - GraphQL schema design completed separately before task regeneration
   EOF
   ```

5. **Auto-close all open and in-progress tasks:**

   ```bash
   # Find all open and in-progress tasks
   TASKS_TO_CLOSE=$(bd list --status open,in_progress --format "{{.ID}}")

   # Auto-close with regeneration reason
   for task_id in $TASKS_TO_CLOSE; do
     bd close $task_id --reason "Auto-closed for PRD v4 regeneration: REST to GraphQL migration"
   done

   echo "✓ Closed $(echo $TASKS_TO_CLOSE | wc -w) tasks for regeneration"
   ```

6. **Completed tasks remain open** (marked as completed, not closed):
   - Keep visible in beads for reference
   - Use migration map to identify reusable work

7. **Regenerate from updated PRD:**
   - Follow full `/prd:generate-tasks` workflow from Phase 1
   - Generate new parent epics
   - Generate new sub-issues
   - Create new dependencies

8. **Migrate completed work:**

   ```bash
   # For each completed v3 task, determine if v4 task covers same functionality
   # Reference migration map for decisions

   # Example 1: Database schema (can reuse)
   bd create "Define GraphQL types for User" -p 2 -t task -d "PRD: /.flow/prd-auth-v4.md

   GraphQL types for User entity (reusing database schema from v3).

   Reference: Completed v3 task proj-jkl012 (Create user table)

   Files:
   - src/graphql/types/user.ts"
   # Returns: proj-new123

   # Mark as complete (based on v3 work)
   bd close proj-new123 --reason "Migrated from completed v3 task proj-jkl012 (database schema complete)"

   # Example 2: Authentication service (cannot reuse)
   bd create "Implement authentication GraphQL resolvers" -p 2 -t task -d "PRD: /.flow/prd-auth-v4.md

   GraphQL mutations for login, register, and token refresh.

   Reference: In-progress v3 task proj-mno345 (saved in backup for reference)

   Files:
   - src/graphql/resolvers/auth.ts"
   # Returns: proj-new456

   # Start fresh (not marked complete)
   ```

9. **Update all references:**
   - New tasks reference `prd-auth-v4.md`
   - Update `prd-auth-history.md` with full change summary
   - Keep v3 tasks visible but completed for reference

10. **Resume implementation:**
    ```bash
    bd ready  # Show which new tasks are ready to work on
    ```

**Concrete Example:**

```markdown
# Scenario: PRD v3 → v4 - REST to GraphQL Migration

**Before Change (v3 - REST API):**
```

Epic: Authentication Endpoints (proj-auth123) [In Progress]
├── proj-db456: Create user table ✓ (completed)
├── proj-svc789: Implement authentication service 🔸 (50% complete, in-progress)
├── proj-ep012: POST /auth/login (open)
├── proj-ep345: POST /auth/register (open)
└── proj-ep678: POST /auth/refresh (open)

```

**PRD Change (v4 - GraphQL):**
```

Functional Requirements:

1. The system shall provide GraphQL mutations for authentication
2. Mutation: login(email, password) → returns accessToken, refreshToken
3. Mutation: register(email, password) → returns accessToken, refreshToken
4. Mutation: refreshToken(token) → returns accessToken, refreshToken

````

**History Update:**
```markdown
| v4 | 2025-01-16 14:30 | Yes | Major architectural change: REST → GraphQL API |
````

**Backup Created:**

```
.beads/backups/prd-v3-to-v4-20250116-143022/
├── task-list.txt
├── open-tasks.txt
├── in-progress-tasks.txt
├── completed-tasks.txt
├── dependency-tree-proj-auth123.txt
├── task-details.txt
└── migration-map.md
```

**Auto-Close Tasks:**

- Close open tasks with regeneration reason explaining PRD version change and migration
- Close in-progress task (WIP already committed)

**Completed Tasks Remain:**

- proj-db456: Create user table (completed, kept for reference)

**Regenerate Tasks (v4):**

- New epic: GraphQL Authentication Resolvers
- New sub-tasks:
  - Define GraphQL schema for authentication (references completed v3 task)
  - Implement login mutation resolver (references in-progress v3 task)
  - Implement register mutation resolver
  - Implement refreshToken mutation resolver
- Link new tasks to parent epic
- Migrate completed work: Mark schema task as complete (referencing completed v3 task)

**Result:**

- 4 new tasks generated for GraphQL
- proj-new101 marked complete (reused v3 work)
- proj-new202, 303, 404 start fresh (new GraphQL resolvers)
- All v3 open/in-progress tasks auto-closed with clear reason
- Migration map documents all decisions
- Backup preserves v3 work for reference

```

### PRD Change Decision Tree

```

PRD change request during implementation?
│
├─ Minor change (clarification/typo/edge case)
│ └─ Update PRD (vN → vN+1)
│ └─ Update history file
│ └─ Continue implementation without pausing
│
├─ Moderate change (new requirement within scope/small UX change)
│ ├─ Pause current task: bd update --status blocked
│ ├─ Update PRD (vN → vN+1)
│ ├─ Update history file
│ ├─ Identify affected tasks
│ │ ├─ Task NOT started: bd close --reason "Regenerating"
│ │ └─ Task IN PROGRESS: Commit WIP → bd close
│ ├─ Regenerate affected tasks from updated PRD
│ ├─ Update task descriptions with new PRD version
│ └─ Resume with regenerated tasks
│
└─ Major change (architectural/new feature/scope expansion)
├─ Commit WIP checkpoint with comprehensive message
├─ Create backup: .beads/backups/prd-vN-to-vN+1-TIMESTAMP/
├─ Export task state to backup
├─ Create migration map
├─ Auto-close all open/in-progress tasks
├─ Keep completed tasks visible for reference
├─ Update PRD (vN → vN+1)
├─ Update history file
├─ Regenerate ALL tasks from updated PRD
│ └─ Follow full /prd:generate-tasks workflow
├─ Migrate completed work:
│ ├─ Can reuse: Mark new task as complete
│ └─ Cannot reuse: Start fresh, reference backup
└─ Resume from new task structure: bd ready

```

### Migration Best Practices

1. **Document Everything**
   - Always create migration maps
   - Record why each task was/wasn't migrated
   - Note architecture changes and decisions

2. **Preserve Work**
   - Never delete completed task history
   - Keep backups of all WIP
   - Reference old tasks in new task descriptions

3. **Test Thoroughly**
   - Major changes require full test suite run
   - Run tests before committing regenerated work
   - Verify migrated work still functions

4. **Communicate Clearly**
   - Explain what changed and why
   - Document migration decisions
   - Update PRD history with full change summary

5. **Review Dependencies**
   - Regenerated tasks may have different parallelization opportunities
   - Re-analyze file conflicts after regeneration
   - Update dependency trees accordingly

6. **Use Version Numbers Explicitly**
   - Always reference specific PRD version in task descriptions
   - Use format: `PRD: /.flow/prd-[feature-name]-vN.md`
   - Update history file for every version change

7. **Create Meaningful Commit Messages**
   - WIP commits should explain what was done
   - Regeneration commits should explain what changed
   - Reference PRD version in all commits

### Example Backup Directory Structure

```

.beads/backups/
└── prd-auth-v3-to-v4-20250116-143022/
├── task-list.txt # All tasks
├── open-tasks.txt # Tasks needing regeneration
├── in-progress-tasks.txt # Tasks with WIP
├── completed-tasks.txt # Tasks to consider for migration
├── dep-tree-proj-auth123.txt # Dependency tree for epic
├── dep-tree-proj-test456.txt # Dependency tree for testing
├── task-details.txt # Detailed info for all tasks
└── migration-map.md # Decisions and mapping

```

## Group State Tracking with Beads

Use beads labels to persist parallel group membership in the database (not in-memory variables).

**Tagging tasks with group:**
- Add label indicating parallel group membership

**Finding all tasks in a group:**
- List tasks by specific label

**Checking group completion:**
- List tasks by label and status (open)

**Task Type Detection Logic:**

| Task Pattern | Detection | Action |
|--------------|-----------|--------|
| No `[P:Group-X]` | Sequential | Execute immediately |
| `[P:Group-X]` | Parallel group | Execute all group tasks concurrently via subagents |

**After group completion:**
- All tasks in group closed → Group is complete
- Remove labels if desired
- Return to sequential mode for next task

## Task List Maintenance

1. **Update the task list as you work:**
    - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
    - Close tasks in beads.
    - Add new tasks as they emerge.

2. **Maintain the "Relevant Files" section:**
    - List every file created or modified.
    - Give each file a one‑line description of its purpose.

## AI Instructions

When working with task lists, the AI must:

1. **Autonomous Execution (no permission needed):**
    - Execute tasks continuously without stopping for permission
    - Only pause when clarification is needed (ambiguous requirements, missing info, conflicting specs)
    -

2. **Pre-execution Checks:**
    - Check which tasks are unblocked
    - Verify no blocking dependencies
    - Check task details and blockers

3. **During Execution:**
    - Update task status to in_progress
    - Monitor progress via in-progress status
    - Use beads database for coordination between parallel tasks

4. **Completion Protocol:**
    - Mark each finished **sub‑task** `[x]` immediately
    - Close task in beads
    - Mark **parent task** `[x]` once **ALL** subtasks are `[x]`
    - Run full test suite before committing group changes

5. **File Management:**
    - Keep "Relevant Files" section accurate and up to date
    - Add newly discovered tasks

6. **Error Handling:**
    - Use test-automator and language-specific subagents for failing tests
    - **DO NOT** proceed to next task/group until all tests pass

## Ralph Wiggum Loops (Iterative Development)

For tasks that require iteration until success (e.g., getting tests to pass, fixing bugs), use the Ralph Wiggum technique - a self-referential loop that keeps iterating until a completion condition is met.

### Prerequisites

**Check if Ralph plugin is installed** before using Ralph commands.

If the Ralph plugin is not installed, fall back to manual iterative development:
- Run tests → Fix failures → Run tests again → Repeat until passing
- Do NOT attempt to use `/ralph-loop` or `/cancel-ralph` commands

### When to Use Ralph Loops

| Good For | Not Good For |
|----------|--------------|
| Tasks with clear success criteria | Tasks requiring human judgment |
| Getting tests to pass | Design decisions |
| Bug fixing with automatic verification | Unclear success criteria |
| Greenfield implementation | Production debugging |

### Starting a Ralph Loop

When a task requires iteration (especially TDD or bug fixing), start a Ralph loop.

**Example for a beads task:**
Include task reference, PRD requirements, TDD approach, success criteria, and max iterations with completion promise.

### Structuring Ralph Prompts

**Include in every Ralph prompt:**
1. **Clear task reference:** Link to beads issue ID and PRD
2. **Success criteria:** Specific, verifiable conditions
3. **Completion promise:** The exact phrase to output when done
4. **Escape hatch:** What to do if stuck after N iterations

### Safety: Always Set Max Iterations

**Never run unbounded loops.** Always use `--max-iterations` to set a maximum iteration count.

### Canceling a Ralph Loop

If a loop is running and you need to stop it, use `/cancel-ralph`.

### Ralph + Beads Integration

When using Ralph for a beads task:

1. **Before starting:** Update beads status to in_progress and add notes
2. **On completion:** Close the task
3. **On failure (max iterations reached):** Mark as blocked with notes

## Blocked Task Handling

When a task cannot proceed (test failures, missing dependencies, blockers):

1. **Update beads status:**
    - Update task status to blocked
    - Add notes explaining the reason

2. **Notify user:**
    - Explain what is blocked and why
    - List specific failing tests or missing dependencies
    - Suggest next steps to resolve

3. **Do NOT proceed** to dependent tasks until resolved

4. **Resume workflow:**
    - Fix the blocker
    - Run tests again to verify
    - Update task status to in_progress
    - Continue execution from where it left off

## When to Stop for Clarification

Only pause execution and ask the user when you encounter:

1. **Ambiguous Requirements:**
   - PRD doesn't specify behavior for an edge case
   - Multiple interpretations of a requirement are valid

2. **Implementation Choices:**
   - Multiple valid architectural approaches exist
   - Trade-offs that depend on user preferences (performance vs. simplicity, etc.)

3. **Missing Information:**
   - Required API endpoints or schemas not defined
   - Dependencies on external systems not documented

4. **Conflicts Discovered:**
   - Requirements contradict each other
   - Existing code conflicts with PRD specifications

**Example clarification request:**
```

⚠️ Clarification needed for task BD-123:

The PRD specifies "users can upload files" but doesn't define:

- Maximum file size
- Allowed file types

Options:
a) 10MB limit, images only (jpg, png, gif)
b) 50MB limit, common documents (pdf, doc, images)
c) No limit, any file type

Which approach should I use?

```

```
