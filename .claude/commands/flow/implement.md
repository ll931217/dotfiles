# Task List Management

Guidelines for managing task lists to track progress on completing a PRD.

**Task Management Options:**

- **With beads (`bd`) installed:** Full-featured task tracking with dependencies, ready task detection, and persistent storage
- **Without beads:** Basic task tracking using the internal TodoWrite tool (limited features, no persistent storage)

## Current Status

<!-- AUTO-COMPACTION DETECTION ZONE -->

**Last Refresh:** [Initial - Not yet refreshed]

**Instructions for AI Agent:**
If you are reading this workflow and ANY of the following are true:

1. The "Last Refresh" timestamp is more than 30 minutes old
2. You suspect the conversation has been auto-compacted by Claude Code
3. You feel unsure about the current task state or progress
4. You are about to start a [P:Group-X] parallel task group

**Then execute:** `/flow:summary`

After executing `/flow:summary`, replace the content between the `==== LATEST SUMMARY ====` markers below with the new output and update the "Last Refresh" timestamp.

**Current Status Summary:**

==== LATEST SUMMARY ====

<!--
[Paste /flow:summary output here]

Example format:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Feature: User Authentication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PRD: prd-authentication-v2.md (version: 2)
   Status: ✅ approved
   Branch: feature/auth
   Worktree: feature-auth

📝 Overview:
Implement secure user authentication with email/password...

📊 Progress: 3/8 tasks completed
[████████░░░░░░░░░░░░░] 37%

⏳ What's Left (5 tasks):
   📦 Authentication Core
      ⏳ proj-auth.3: Implement login endpoint
      ⏳ proj-auth.4: Implement password hashing
   📦 Session Management
      ⏳ proj-auth.5: Create session storage
      ⏳ proj-auth.6: Implement token refresh
   📦 Testing
      ⏳ proj-auth.7: Write unit tests

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-->

==== END LATEST SUMMARY ====

<!-- END AUTO-COMPACTION DETECTION ZONE -->

## Auto-Compaction Detection Protocol

Claude Code automatically compacts long conversations to manage token limits. This protocol ensures you maintain accurate context about current PRD status and task progress.

### Detection Checklist

**Check these conditions BEFORE starting any task:**

- [ ] **Initial Read:** When first reading this workflow, check "Last Refresh" timestamp
- [ ] **Time Threshold:** Is timestamp > 30 minutes old?
- [ ] **Task Milestone:** Have you completed ~5 tasks since last refresh?
- [ ] **Group Start:** Are you about to start a [P:Group-X] parallel task group?
- [ ] **After Blocker:** Did you just resolve a blocked task?
- [ ] **Context Uncertainty:** Do you feel unsure about current state?

### Refresh Procedure

If ANY checkbox above is checked:

1. **Execute summary command:** Type `/flow:summary` in your response
2. **Wait for output:** The command will execute and return current status
3. **Update this section:**
   - Replace content between `==== LATEST SUMMARY ====` markers
   - Update "Last Refresh" to current timestamp
   - Use format: `YYYY-MM-DD HH:MM UTC`
4. **Verify alignment:** Ensure you're working on correct tasks
5. **Resume workflow:** Continue with your planned task

### Example Agent Response

```
I notice the "Last Refresh" timestamp is 45 minutes old. Let me refresh the context to ensure I have the current state.

/flow:summary

[summary output appears]

Updating Current Status section with latest summary...

Last Refresh updated to: 2026-01-02 14:30 UTC

I can see from the summary that 3/8 tasks are complete and I should continue with proj-auth.3. Let me proceed with implementing the login endpoint.
```

### Integration Points

This protocol integrates with existing workflow sections:

- **PRD Discovery:** Refresh after discovering and validating PRD
- **Parallel Groups:** REQUIRED refresh before starting [P:Group-X]
- **PRD Changes:** REQUIRED refresh if PRD version changes
- **Blocker Resolution:** Refresh after unblocking tasks
- **Completion Check:** Refresh before checking PRD completion status

## Prerequisites Check

Before beginning implementation, check for task tracking availability:

**Automated Check:** The AI should verify whether beads (`bd`) is available:

**With beads (`bd`) installed:**

- The `bd` command is available in the system PATH
- The `.beads` directory exists (initialize with `bd init` if not present)
- Beads database is functional

**Without beads (TodoWrite fallback):**

- The AI will use the internal TodoWrite tool for task tracking
- Note: Task context may be lost between sessions
- Note: No persistent dependency tracking or ready task detection

**Recommendation:** Consider installing beads for the best experience, especially for larger features with many tasks.

## PRD Discovery and Validation

Before beginning implementation, discover and validate the PRD:

**Auto-Discovery:** Use the same discovery algorithm as `/flow:generate-tasks`:

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
- If status is `draft`, use AskUserQuestion to warn the user:

  ```
  AskUserQuestion({
    questions: [
      {
        question: "PRD status is \"draft\" - this PRD has not been approved yet. What would you like to do?",
        header: "PRD Status",
        options: [
          {
            label: "Continue anyway",
            description: "Proceed with implementation despite draft status"
          },
          {
            label: "Run /flow:generate-tasks",
            description: "Generate tasks and approve the PRD first"
          },
          {
            label: "Exit",
            description: "Exit the implementation process"
          }
        ],
        multiSelect: false
      }
    ]
  })
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
- `implementing` = 🔄 implementing (implementation in progress)
- `implemented` = ✨ implemented (complete)

**After PRD Validation:**
Once you've discovered and validated the PRD:
1. Run `/flow:summary` to capture the initial state in the "Current Status" section above. This establishes your baseline context.
2. **Check for `code_references` in PRD frontmatter:**
   - If present: Use these files for initial context (selective reading with line ranges)
   - If absent: Fall back to broader exploration during implementation
3. **Update PRD status** from `approved` to `implementing`:
   - Update `prd.status` field in frontmatter
   - Update `metadata.updated_at` timestamp
   - Update `git.updated_at_commit` with current commit SHA
   - Add changelog entry: "Implementation started"

## Context-Optimized File Reading

When implementing tasks, use selective reading based on `code_references` and issue descriptions to reduce token usage.

### Reading Strategy

1. **Check Issue Description First:**
   - Read the "Relevant Files" table from the beads issue
   - Extract file paths and line ranges

2. **Use Selective Read Tool:**
   - Instead of `Read("src/auth.ts")` (entire file)
   - Use `Read("src/auth.ts", offset=45, limit=75)` (lines 45-120)

3. **Fallback Conditions:**
   - No relevant files in issue → Read full file
   - Line range doesn't provide context → Expand range
   - File modified since PRD → Read full file
   - New file → Read similar files for patterns

### Implementation Example

```python
# Before: Read entire file (500+ tokens)
auth_service = Read("src/services/AuthService.ts")

# After: Read only relevant section (100 tokens)
auth_service = Read("src/services/AuthService.ts", offset=1, limit=50)

# Token savings: ~80%
```

### Token Savings

| Approach | Typical File Size | Tokens Used | Savings |
|----------|------------------|-------------|---------|
| Full file read | 500 lines | ~2,500 | 0% |
| Selective read | 50 lines | ~250 | **90%** |
| Multiple selective reads | 5 files × 30 lines | ~375 | **85%** |

**Overall savings: ~70-85% for typical implementations**

### Reading from PRD code_references

When `code_references` exists in PRD frontmatter:

```yaml
code_references:
  - path: "src/services/AuthService.ts"
    lines: "45-120"
    reason: "Existing authentication patterns to follow"
```

Read selectively using:
```bash
Read("src/services/AuthService.ts", offset=45, limit=75)  # Lines 45-120
```

## Priority Display Format

Tasks are displayed with priority indicators and sorted by priority level (P0 → P4).

**Priority Indicators:**
| Color | Priority | Level | Description |
|-------|----------|----------|--------------------------------|
| 🔴 | P0 | Critical | Urgent, blocking, security |
| 🟠 | P1 | High | Important, urgent functionality |
| 🟢 | P2 | Normal | Standard feature (default) |
| 🔵 | P3 | Low | Nice-to-have, enhancement |
| ⚪ | P4 | Lowest | Backlog, future consideration |

**Display Format (with beads):**

```
Available Ready Tasks (sorted by priority):

🔴 P0 | proj-abc: Critical Security Fix (epic)
  ├─ proj-abc.1: Patch authentication bypass
🟠 P1 | proj-def: User Authentication (epic)
  ├─ proj-def.1: Implement login endpoint
  ├─ proj-def.2: Add password reset flow
🟢 P2 | proj-ghi: Email Notifications (epic)
  ├─ proj-ghi.1: Create email service
```

The AI views tasks sorted by priority level (P0 → P4) using internal beads integration.

**Display Format (without beads - TodoWrite):**

```
Available Tasks (sorted by priority):

🔴 P0 | Epic: Critical Security Fix
  ├─ [Epic: Critical Security Fix] Patch authentication bypass
🟠 P1 | Epic: User Authentication
  ├─ [Epic: User Authentication] Implement login endpoint
  ├─ [Epic: User Authentication] Add password reset flow
🟢 P2 | Epic: Email Notifications
  ├─ [Epic: Email Notifications] Create email service
```

The AI views tasks from the internal TodoWrite state, organized by epic hierarchy.

**PRD Updates During Implementation:**

- When PRD changes are made (see "PRD Change Management"), update frontmatter:
  - Increment version in `prd.version`
  - Update `metadata.updated_at`
  - Update `git.updated_at_commit`
  - Update `metadata.filename`
  - Set `prd.status` to `implemented` when all tasks complete

## PRD Completion Detection

After completing each task, check if all PRD tasks are complete and update the PRD status to `implemented`.

**With beads (`bd`) installed:**

- After closing each task with `bd close`, check if all PRD tasks are complete
- Use the helper function below to verify completion and update status

**Without beads (TodoWrite fallback):**

- After marking each task as completed in TodoWrite, check if all tasks are complete
- Check the internal TodoWrite state for completion
- Note: Manual verification may be needed if context is lost

### Helper Functions

**Function: check_prd_completion (with beads)**

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

  # If all closed, notify user but don't update status yet (cleanup will do that)
  if [ "$all_closed" = true ] && [ $total -gt 0 ]; then
    echo ""
    echo "✨ ──────────────────────────────────────────────────"
    echo "  All PRD Tasks Complete!"
    echo "  PRD: $(basename "$prd_file")"
    echo "  Tasks completed: $closed/$total"
    echo "✨ ──────────────────────────────────────────────────"
    echo ""
    echo "Recommended next steps:"
    echo "1. 🧪 Manually test the implementation to verify everything works"
    echo "2. 📝 If issues found, iterate on fixes (tasks can be reopened)"
    echo "3. 🧹 If satisfied, run /flow:cleanup to finalize:"
    echo "   - Create summary commit"
    echo "   - Update PRD status to 'implemented'"
    echo "   - Add changelog entry"
    echo ""
    echo "Run /flow:cleanup when ready to finalize."
    echo ""
  else
    # Show progress
    echo "📊 Progress: $closed/$total tasks completed"
  fi
}
```

**Function: check_prd_completion_todo (TodoWrite fallback)**

Checks if all TodoWrite tasks for a PRD are complete (manual process).

```
The AI should:
1. Review all TodoWrite items related to the current PRD
2. Check if all tasks have status "completed"
3. If all complete, update the PRD frontmatter:
   - Change status from "approved" to "implemented"
   - Update version, updated_at, updated_at_commit
4. Display completion message to user
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

After closing a task, the AI checks if the PRD is now complete by calling the `check_prd_completion` function with the appropriate PRD file.

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

**Periodic Context Refresh:**
Every 5 completed tasks or 30 minutes of work, execute `/flow:summary` to refresh your context. Update the "Current Status" section with the latest output.

- **Parallel Group Execution ([P:Group-X] flags):**
- **Phase 1 - Pre-execution Analysis:** Before starting any parallel group:
  - Check which tasks are unblocked
  - Verify there are no blocking dependencies
  - Review task details and any blockers

**Pre-Group Refresh (REQUIRED):**
Before starting ANY [P:Group-X] parallel task group, you MUST execute `/flow:summary` to ensure you have the current task state. Parallel groups require accurate context about dependencies and blocking issues.

- **Phase 2 - Concurrent Execution:** Launch all tasks in the group simultaneously:

**Subagent Selection Process:**

For each task in the parallel group:

1. **Read Task Metadata:**
   - Query the beads issue for `subagent_type` metadata
   - Extract `fallback_agents` array if present
   - Extract `applicable_skills` array if present

2. **Select Agent:**
   - Use `subagent_type` as primary agent
   - If primary agent is unavailable, try `fallback_agents` in order
   - If no metadata found, auto-detect by analyzing task description against `.claude/subagent-types.yaml`

3. **Apply Skills (if applicable):**
   - When `applicable_skills` array is present and non-empty
   - For each skill, use the Skill tool before launching the subagent
   - Pass skill context to guide the subagent's approach

**Example Parallel Execution:**

```python
# For a group with 3 tasks launching in parallel:

# Task 1: Frontend component
# Subagent: frontend-developer
# Skill: frontend-design
Task(
  subagent="frontend-developer",
  prompt="Implement React login component with TypeScript...",
  relevant_files=["src/components/Login.tsx", "src/types/auth.ts"]
)

# Task 2: Backend API (parallel)
# Subagent: backend-architect
Task(
  subagent="backend-architect",
  prompt="Implement login POST endpoint with JWT...",
  relevant_files=["src/api/routes.ts", "src/services/AuthService.ts"]
)

# Task 3: Database schema (parallel)
# Subagent: database-admin
Task(
  subagent="database-admin",
  prompt="Create users table with auth fields...",
  relevant_files=["migrations/001_create_users.sql"]
)
```

**Implementation Guidelines:**

- Use multiple specialized subagents via Task tool with parallel invocations
- Each subagent works on their assigned files (listed in task description)
- Update task status to in_progress
- Respect the subagent type metadata for optimal task routing

**Auto-Detection Fallback:**

If task lacks `subagent_type` metadata:
1. Extract task description from beads issue
2. Match against patterns in `.claude/subagent-types.yaml`
3. Assign best-matching subagent type based on priority order
4. Store assignment in task metadata for future reference
5. Proceed with specialized subagent execution

**Skill Integration Example:**

```python
# First apply the skill for guidance
Skill(skill="frontend-design", args="Create distinctive UI for login component")

# Then launch subagent with skill context
Task(
  subagent="frontend-developer",
  prompt="Implement login component following design guidelines...",
  relevant_files=["src/components/Login.tsx"]
)
```

- **Phase 3 - Coordination & Monitoring:**
  - Monitor progress via in-progress task status
  - Use beads database for coordination between parallel tasks
  - Wait for ALL tasks in the group to complete before proceeding
- **Phase 4 - Post-execution Validation:**
  - Verify all group tasks are completed
  - Close completed tasks
  - Run tests if applicable before moving to next group/task
- **Completion protocol:**
  - When you finish a **sub-task**, immediately mark it as completed:
    - Update the task status to closed in beads
    - Update markdown: change `[ ]` to `[x]`
  - If **all** sub-tasks underneath a parent task are now complete, follow this sequence:
    - **First**: Run the full test suite (pytest, npm test, bin/rails test, etc.)
    - **Only if all tests pass**: Stage changes (git add .)
    - **Clean up**: Remove any temporary files and temporary code before committing
    - **Commit**: Use a descriptive commit message that:
      - Uses conventional commit format (`feat:`, `fix:`, `refactor:`, etc.)
      - Summarizes what was accomplished in the parent task
      - Lists key changes and additions
      - References the issue ID and PRD context
      - **Formats the message as a single-line command using `-m` flags**

  - Once all the subtasks are closed and changes have been committed, close the **parent task** in beads.

## PRD Change Management

This section handles what happens when PRD needs updates mid-implementation.

**Context Refresh After Changes:**
After ANY PRD version change (minor/moderate/major), execute `/flow:summary` immediately to update your understanding of the changed requirements and task structure.

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
   - Follow full `/flow:generate-tasks` workflow from Phase1
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
   The AI creates a timestamped backup directory in `.beads/backups/prd-vN-to-vN+1-TIMESTAMP/`

3. **Save current task state:**
   The AI exports all task information to the backup directory:
   - All tasks list
   - Tasks by status (open, in-progress, closed)
   - Dependency trees for all epics
   - Detailed information for all tasks

4. **Create migration map:**
   The AI creates a markdown file documenting:
   - Overview (from/to PRD versions, date, reason)
   - Completed work (tasks that can be reused vs cannot be reused)
   - Open tasks mapping (vN task IDs to vN+1 actions)
   - Decisions made (what gets reused vs regenerated)
   - Notes about the migration

5. **Auto-close all open and in-progress tasks:**
   The AI finds all open and in-progress tasks and closes them with a reason explaining the PRD version change and migration.

6. **Completed tasks remain open** (marked as completed, not closed):
   - Keep visible in beads for reference
   - Use migration map to identify reusable work

7. **Regenerate from updated PRD:**
   - Follow full `/flow:generate-tasks` workflow from Phase 1
   - Generate new parent epics
   - Generate new sub-issues
   - Create new dependencies

8. **Migrate completed work:**
   For each completed vN task, the AI determines if the vN+1 task covers the same functionality by referencing the migration map:
   - **Can reuse**: Mark new task as complete (reference old task ID)
   - **Cannot reuse**: Start fresh (reference backup, not marked complete)

9. **Update all references:**
   - New tasks reference `prd-auth-v4.md`
   - Update `prd-auth-history.md` with full change summary
   - Keep v3 tasks visible but completed for reference

10. **Resume implementation:**
    The AI shows tasks sorted by priority (P0 → P4) to begin implementation.

    **Priority Indicators:**
    - 🔴 P0 = Critical (urgent)
    - 🟠 P1 = High
    - 🟢 P2 = Normal (default)
    - 🔵 P3 = Low
    - ⚪ P4 = Lowest

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
```

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
│ ├─ Pause current task: mark as blocked
│ ├─ Update PRD (vN → vN+1)
│ ├─ Update history file
│ ├─ Identify affected tasks
│ │ ├─ Task NOT started: close with regeneration reason
│ │ └─ Task IN PROGRESS: Commit WIP → close
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
│ └─ Follow full /flow:generate-tasks workflow
├─ Migrate completed work:
│ ├─ Can reuse: Mark new task as complete
│ └─ Cannot reuse: Start fresh, reference backup
└─ Resume from new task structure: view tasks sorted by priority

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
    - DO NOT suggest the user to use the `bd` command, this command is mainly reserved for AI Agents to use.

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

AskUserQuestion({
questions: [
{
question: "Clarification needed for task BD-123: The PRD specifies \"users can upload files\" but doesn't define the maximum file size or allowed file types. Which approach should I use?",
header: "File Upload",
options: [
{
label: "10MB limit, images only",
description: "Restrict to jpg, png, gif formats with 10MB size limit"
},
{
label: "50MB limit, documents",
description: "Allow common documents (pdf, doc, images) with 50MB limit"
},
{
label: "No limit, any type",
description: "Allow any file type with no size restrictions"
}
],
multiSelect: false
}
]
})

```

```
