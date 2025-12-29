# Task List Management

Guidelines for managing task lists using beads (`bd`) to track progress on completing a PRD

## Beads Integration

All task context is stored in beads' SQLite database. Use `bd` commands for task management:

```bash
# Initialize beads in project (if not already done)
bd init

# Create tasks from PRD
bd create "Task description" -p <priority> -t <type>

# View ready tasks (no blocking dependencies)
bd ready

# Update task status
bd update <issue-id> --status in_progress
bd update <issue-id> --status open

# Close completed tasks
bd close <issue-id> --reason "Completed"

# Manage dependencies
bd dep add <blocked-by> <blocker>  # blocker must complete first
bd dep tree <issue-id>             # visualize dependencies

# View task details
bd show <issue-id>
bd list --status open
```

## Task Implementation

- **Smart Task Execution Strategy with 3-Condition Permission Logic:**

  **Condition 1 - Sequential Tasks (no parallel flags):**
  - Ask user for permission before starting: "Ready to start task [TaskID]? (yes/y to proceed)"
  - Wait for user confirmation ("yes" or "y") before proceeding
  - Execute one task at a time

  **Condition 2 - Parallel Group Start ([P:Group-X] flags):**
  - When encountering the **first task** in a new parallel group, ask for permission: "Ready to start parallel group [Group-X] with [N] tasks? (yes/y to proceed)"
  - Wait for user confirmation ("yes" or "y") before starting the entire group
  - Once confirmed, execute ALL tasks in the group concurrently using specialized sub-agents

  **Condition 3 - Within Active Parallel Group:**
  - **NO permission needed** for subsequent tasks within the same group
  - All tasks in the group execute automatically once group permission is granted
  - Continue until all tasks in the group are completed

- **Parallel Group Execution ([P:Group-X] flags):**
  - **Phase 1 - Pre-execution Analysis:** Before starting any parallel group:
    - Run `bd ready` to check which tasks are unblocked
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
    - Update beads: `bd close <issue-id> --reason "Completed"`
    - Update markdown: change `[ ]` to `[x]`
  - If **all** sub-tasks underneath a parent task are now complete, follow this sequence:
    - **First**: Run the full test suite (`pytest`, `npm test`, `bin/rails test`, etc.)
    - **Only if all tests pass**: Stage changes (`git add .`)
    - **Clean up**: Remove any temporary files and temporary code before committing
    - **Commit**: Use a descriptive commit message that:
      - Uses conventional commit format (`feat:`, `fix:`, `refactor:`, etc.)
      - Summarizes what was accomplished in the parent task
      - Lists key changes and additions
      - References the beads issue ID and PRD context
      - **Formats the message as a single-line command using `-m` flags**, e.g.:

      ```
      git commit -m "feat: add payment validation logic" -m "- Validates card type and expiry" -m "- Adds unit tests for edge cases" -m "Closes bd-a3f2dd"
      ```

  - Once all the subtasks are closed in beads and changes have been committed, close the **parent task** in beads.

- **Permission Control Summary:**
  - **Sequential tasks**: Stop and ask for user permission before each task
  - **Parallel group start**: Stop and ask for user permission before starting the group
  - **Within parallel group**: NO stopping, execute all group tasks automatically

## Group State Tracking with Beads

Use beads labels to persist parallel group membership in the database (not in-memory variables).

**Tagging tasks with group:**
```bash
bd label add <issue-id> "parallel:Group-A"
```

**Finding all tasks in a group:**
```bash
bd list --label "parallel:Group-A"
```

**Checking group completion:**
```bash
bd list --label "parallel:Group-A" --status open
# If empty, all group tasks are complete
```

**Task Type Detection Logic:**

| Task Pattern | Detection | Action |
|--------------|-----------|--------|
| No `[P:Group-X]` | Sequential | Ask permission before each task |
| `[P:Group-X]` with new group | New group start | Ask permission to start entire group |
| `[P:Group-X]` with active group | Group continue | No permission needed, execute automatically |

**After group completion:**
- All tasks in group closed → Group is complete
- Remove labels if desired: `bd label remove <issue-id> "parallel:Group-A"`
- Return to sequential mode for next task

## Task List Maintenance

1. **Update the task list as you work:**
   - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
   - Close tasks in beads with `bd close <issue-id>`.
   - Add new tasks as they emerge using `bd create`.

2. **Maintain the "Relevant Files" section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.

## AI Instructions

When working with task lists, the AI must:

1. **3-Condition Permission System:**
   - **Condition 1 (Sequential)**: Ask "Ready to start task [TaskID]? (yes/y to proceed)" and wait for confirmation
   - **Condition 2 (New Group)**: Ask "Ready to start parallel group [Group-X] with [N] tasks? (yes/y to proceed)" and wait for confirmation
   - **Condition 3 (Within Group)**: NO permission needed - execute automatically
   - Always run `bd ready` to check task status before starting any task

2. **Pre-execution Checks (apply task type detection first):**
   - Use `detect_task_type()` function to determine which permission condition applies
   - Run `bd ready` to see which tasks are unblocked
   - Use `bd dep tree <issue-id>` to verify no blocking dependencies
   - Run `bd show <issue-id>` to check task details and blockers

3. **During Execution:**
   - Update task status with `bd update <issue-id> --status in_progress`
   - Monitor progress via `bd list --status in_progress`
   - Use beads database for coordination between parallel tasks

4. **Completion Protocol:**
   - Mark each finished **sub‑task** `[x]` immediately
   - Close task in beads: `bd close <issue-id> --reason "Completed"`
   - Use `update_group_state()` to track group completion
   - Mark **parent task** `[x]` once **ALL** subtasks are `[x]`
   - Run full test suite before committing group changes

5. **File Management:**
   - Keep "Relevant Files" section accurate and up to date
   - Add newly discovered tasks with `bd create`
   - Maintain DRY principle and avoid over-complication

6. **Error Handling:**
   - Use test-automator and language-specific subagents for failing tests
   - **DO NOT** proceed to next task/group until all tests pass

## Blocked Task Handling

When a task cannot proceed (test failures, missing dependencies, blockers):

1. **Update beads status:**
   ```bash
   bd update <issue-id> --status blocked
   bd update <issue-id> --notes "Blocked: [reason]"
   ```

2. **Notify user:**
   - Explain what is blocked and why
   - List specific failing tests or missing dependencies
   - Suggest next steps to resolve

3. **Do NOT proceed** to dependent tasks until resolved

4. **Resume workflow:**
   - Fix the blocker
   - Run tests again to verify
   - Update status: `bd update <issue-id> --status in_progress`
   - Continue execution from where it left off

## Permission Logic Examples & Decision Tree

### Task Type Detection Examples
```bash
# Example task list entries:
# - [ ] 1.1 Setup database schema                    # Sequential - ask permission
# - [ ] 1.2 [P:Group-A] Create User model           # New group - ask permission  
# - [ ] 1.3 [P:Group-A] Create Auth service         # Same group - no permission
# - [ ] 1.4 [P:Group-A] Create API endpoints        # Same group - no permission
# - [ ] 1.5 Integration testing                     # Sequential - ask permission

# Detection logic in action:
TASK_1_1="Setup database schema"                    # detect_task_type() → "SEQUENTIAL"
TASK_1_2="[P:Group-A] Create User model"           # detect_task_type() → "NEW_GROUP_START"  
TASK_1_3="[P:Group-A] Create Auth service"         # detect_task_type() → "GROUP_CONTINUE"
TASK_1_4="[P:Group-A] Create API endpoints"        # detect_task_type() → "GROUP_CONTINUE"
TASK_1_5="Integration testing"                     # detect_task_type() → "SEQUENTIAL"
```

### Permission Decision Tree
```
┌─ Next Task Available
│
├─ detect_task_type(next_task)
│  │
│  ├─ "SEQUENTIAL"
│  │  └─ Ask: "Ready to start task [TaskID]? (yes/y to proceed)"
│  │     └─ Wait for user input → Execute single task
│  │
│  ├─ "NEW_GROUP_START"  
│  │  └─ Count tasks in group → Ask: "Ready to start parallel group [Group-X] with [N] tasks? (yes/y to proceed)"
│  │     └─ Wait for user input → Set CURRENT_GROUP_ID → Execute all group tasks concurrently
│  │
│  └─ "GROUP_CONTINUE"
│     └─ NO permission needed → Execute task automatically (part of approved group)
│
└─ After task completion
   └─ update_group_state() → Reset group if all tasks complete → Continue to next task
```

### Practical Implementation Flow
```bash
# Before each task execution:
next_task=$(get_next_pending_task)
task_type=$(detect_task_type "$next_task")

case $task_type in
  "SEQUENTIAL")
    echo "Ready to start task $next_task? (yes/y to proceed)"
    read user_input
    if [[ "$user_input" =~ ^[Yy]([Ee][Ss])?$ ]]; then
      execute_single_task "$next_task"
    fi
    ;;
  "NEW_GROUP_START")
    group_id=$(extract_group_id "$next_task")
    task_count=$(count_group_tasks "$group_id")
    echo "Ready to start parallel group $group_id with $task_count tasks? (yes/y to proceed)"
    read user_input
    if [[ "$user_input" =~ ^[Yy]([Ee][Ss])?$ ]]; then
      CURRENT_GROUP_ID="$group_id"
      GROUP_TASK_COUNT="$task_count"
      execute_parallel_group "$group_id"
    fi
    ;;
  "GROUP_CONTINUE")
    # No permission needed - execute automatically
    execute_group_task "$next_task"
    ;;
esac

# After completion:
update_group_state "$completed_task"
```
