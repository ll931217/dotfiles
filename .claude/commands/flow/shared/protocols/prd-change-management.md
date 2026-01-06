# PRD Change Management Protocol

## Overview

This protocol handles PRD updates during implementation. It categorizes changes by impact and defines workflows for minor, moderate, and major PRD revisions.

**Context Refresh After Changes:**
After ANY PRD version change (minor/moderate/major), execute `/flow:summary` immediately to update your understanding of the changed requirements and task structure.

## Change Triage

When a PRD revision is requested, first categorize the change:

| Change Type | Examples | Impact on Tasks |
|-------------|----------|-----------------|
| **Minor** | Typo fix, clarification, added edge case detail | Can proceed without task regeneration |
| **Moderate** | New requirement within scope, small UX change, additional field | May require task updates, minimal regeneration |
| **Major** | New feature, removed requirement, architectural change, scope expansion | Requires full task regeneration and work migration |

## Minor Changes (No Task Regeneration Needed)

### Workflow

1. Update PRD document directly (increment version: `prd-auth-v2.md` → `prd-auth-v3.md`)
2. Update PRD changelog with version, date, and summary of changes
3. Continue implementation without pausing
4. Incorporate changes into current/subsequent tasks

### Concrete Example

**Current PRD (v2):**
```markdown
Functional Requirements:
1. The system shall allow users to upload profile pictures
```

**Change Request:** "What's the maximum file size allowed?"

**Updated PRD (v3):**
```markdown
Functional Requirements:
1. The system shall allow users to upload profile pictures (maximum 50MB)

Non-Goals (Out of Scope):
- Video uploads (only images: jpg, png, gif, webp)
```

**Action:**
- Continue with current task: "Implement profile picture upload"
- No task regeneration needed
- Include new constraints (50MB, images only) in implementation

## Moderate Changes (Task Updates Required)

### Workflow

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
     - Commit current work with descriptive WIP message
     - Close task with reason about PRD version change

6. **Regenerate task(s) from updated PRD:**
   - Create new tasks with updated requirements and file lists
   - Update task descriptions to reference new PRD version

7. **Update task descriptions with new PRD version reference**

8. **Resume implementation** with regenerated tasks

### Concrete Example

**Current Tasks (v2):**
```
Open tasks:
- proj-abc123: Define user permissions (regular users only)
- proj-def456: Implement permission checks
- proj-ghi789: Write permission tests

In-progress:
- proj-jkl012: Create user role enum [USER]
```

**PRD Change (v3):**
```markdown
Functional Requirements:
5. The system shall support user roles: User and Admin
6. Admin users shall have full access to all resources
```

**Actions:**
1. Pause in-progress task with blocked status
2. Commit WIP with descriptive message
3. Close affected tasks with regeneration reason
4. Regenerate tasks:
   - Define user permissions including Admin role
   - Implement permission checks for all roles
   - Create user and admin role enums
5. Link new tasks to parent epic
6. Resume with regenerated tasks

## Major Changes (Full Regeneration Required)

### Workflow

1. **Checkpoint current progress:**
   - Commit all WIP with comprehensive message including:
     - PRD version change (vN to vN+1)
     - Reason for architectural shift
     - List of completed/in-progress/open tasks
     - Note about tasks that will be regenerated

2. **Create backup directory:**
   ```bash
   mkdir -p .beads/backups/prd-vN-to-vN+1-$(date +%Y%m%d-%H%M%S)
   ```

3. **Save current task state:**
   - Export all task information (full list, by status categories)
   - Export dependency trees for all epics
   - Export detailed information for all tasks
   - All exports saved to backup directory

4. **Create migration map:**
   - Create markdown file documenting:
     - Overview (from/to PRD versions, date, reason)
     - Completed work (tasks that can be reused vs cannot be reused)
     - Open tasks mapping (vN task IDs to vN+1 actions)
     - Decisions made (what gets reused vs regenerated)
     - Notes about the migration

5. **Auto-close all open and in-progress tasks:**
   - Find all open and in-progress tasks
   - Auto-close all with regeneration reason

6. **Completed tasks remain visible** (marked as completed, not closed)

7. **Regenerate from updated PRD:**
   - Follow full `/flow:generate-tasks` workflow
   - Generate new parent epics
   - Generate new sub-issues
   - Create new dependencies

8. **Migrate completed work:**
   - For each completed vN task, determine if vN+1 task covers same functionality
   - **Can reuse:** Mark new task as complete (reference old task ID)
   - **Cannot reuse:** Start fresh (reference backup, not marked complete)

9. **Update all references:**
   - New tasks reference new PRD version
   - Update PRD changelog with full change summary
   - Keep vN tasks visible but completed for reference

10. **Resume implementation:**
    - Show which new tasks are ready to work on

### Concrete Example

**Before Change (v3 - REST API):**
```
Epic: Authentication Endpoints (proj-auth123) [In Progress]
├── proj-db456: Create user table ✓ (completed)
├── proj-svc789: Implement authentication service 🔸 (50% complete)
├── proj-ep012: POST /auth/login (open)
├── proj-ep345: POST /auth/register (open)
└── proj-ep678: POST /auth/refresh (open)
```

**PRD Change (v4 - GraphQL):**
```markdown
Functional Requirements:
1. The system shall provide GraphQL mutations for authentication
2. Mutation: login(email, password) → returns accessToken, refreshToken
3. Mutation: register(email, password) → returns accessToken, refreshToken
4. Mutation: refreshToken(token) → returns accessToken, refreshToken
```

**Actions:**
1. Commit WIP checkpoint with comprehensive message
2. Create backup: `.beads/backups/prd-v3-to-v4-20250116-143022/`
3. Export task state to backup
4. Create migration map documenting decisions
5. Auto-close open/in-progress tasks
6. Keep completed task visible (proj-db456)
7. Regenerate tasks for GraphQL:
   - New epic: GraphQL Authentication Resolvers
   - New sub-tasks with schema, resolvers, etc.
8. Migrate completed work: Mark schema task as complete
9. Resume with new tasks

## Migration Best Practices

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

## Decision Tree

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
└─ Resume from new task structure
```

## Backup Directory Structure

```
.beads/backups/
└── prd-auth-v3-to-v4-20250116-143022/
├── task-list.txt          # All tasks
├── open-tasks.txt         # Tasks needing regeneration
├── in-progress-tasks.txt  # Tasks with WIP
├── completed-tasks.txt    # Tasks to consider for migration
├── dep-tree-proj-auth123.txt  # Dependency tree for epic
├── task-details.txt       # Detailed info for all tasks
└── migration-map.md       # Decisions and mapping
```
