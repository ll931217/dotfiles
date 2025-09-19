# Task List Management

Guidelines for managing task lists in markdown files to track progress on completing a PRD

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
    - Read the group coordination file to understand current file usage
    - Verify no file conflicts exist with currently running tasks
    - Check individual task context files for any blockers or dependencies
  - **Phase 2 - Concurrent Execution:** Launch all tasks in the group simultaneously:
    - Use multiple specialized subagents via Task tool with parallel invocations
    - Each subagent works on their assigned files (listed in task description)
    - All subagents update their individual context files and the group coordination file
  - **Phase 3 - Coordination & Monitoring:**
    - Monitor progress via context files and subagent reports
    - Ensure no file conflicts occur during execution
    - Wait for ALL tasks in the group to complete before proceeding
  - **Phase 4 - Post-execution Validation:**
    - Verify all group tasks are completed successfully
    - Update the group coordination file with final status
    - Run tests if applicable before moving to next group/task
- **Completion protocol:**
  - When you finish a **sub-task**, immediately mark it as completed by changing `[ ]` to `[x]`.
  - If **all** sub-tasks underneath a parent task are now `[x]`, follow this sequence:
    - **First**: Run the full test suite (`pytest`, `npm test`, `bin/rails test`, etc.)
    - **Only if all tests pass**: Stage changes (`git add .`)
    - **Clean up**: Remove any temporary files and temporary code before committing
    - **Commit**: Use a descriptive commit message that:
      - Uses conventional commit format (`feat:`, `fix:`, `refactor:`, etc.)
      - Summarizes what was accomplished in the parent task
      - Lists key changes and additions
      - References the task number and PRD context
      - **Formats the message as a single-line command using `-m` flags**, e.g.:

      ```
      git commit -m "feat: add payment validation logic" -m "- Validates card type and expiry" -m "- Adds unit tests for edge cases" -m "Related to T123 in PRD"
      ```

  - Once all the subtasks are marked completed and changes have been committed, mark the **parent task** as completed.

- **Permission Control Summary:**
  - **Sequential tasks**: Stop and ask for user permission before each task
  - **Parallel group start**: Stop and ask for user permission before starting the group
  - **Within parallel group**: NO stopping, execute all group tasks automatically

## Context File Management

**Individual Task Context Files** (`/tasks/context/{task_number}_{description}.md`):

- **Purpose:** Track individual task progress and file modifications
- **Required Content:** Current status, files being modified, blockers, completion notes
- **Update Frequency:** Before starting task, during significant changes, upon completion

**Group Coordination Files** (`/tasks/context/group-{id}_coordination.md`):

- **Purpose:** Coordinate between parallel tasks in the same group
- **Required Content:**
  - List of all tasks in the group
  - Current file usage map (which task is modifying which files)
  - Overall group progress status
  - Inter-task dependencies within the group
- **Update Frequency:** Before group execution, during task completion, after group completion

**File Conflict Prevention Rules:**

- Before modifying a file, check if another task (in any group) is currently modifying it
- Update context files immediately when starting/finishing file modifications
- If conflict detected, coordinate resolution via context files or sequential execution

## Group State Tracking Logic

**Tracking Active Parallel Groups:**
- **Group Detection:** Scan upcoming tasks for `[P:Group-X]` patterns to identify group boundaries
- **State Variables:**
  - `CURRENT_GROUP_ID`: Track which group is currently being processed (null if none)
  - `GROUP_TASK_COUNT`: Number of tasks remaining in current group
  - `GROUP_START_REQUESTED`: Whether permission was already requested for current group

**Group State Management:**
```bash
# Detect if next task starts a new parallel group
detect_task_type() {
  local next_task="$1"
  if echo "$next_task" | grep -q "\[P:Group-"; then
    local group_id=$(echo "$next_task" | grep -o "Group-[^]]*")
    if [[ "$group_id" != "$CURRENT_GROUP_ID" ]]; then
      echo "NEW_GROUP_START"
    else
      echo "GROUP_CONTINUE"
    fi
  else
    echo "SEQUENTIAL"
  fi
}

# Update group state after task completion
update_group_state() {
  local completed_task="$1"
  if [[ "$CURRENT_GROUP_ID" != "" ]]; then
    GROUP_TASK_COUNT=$((GROUP_TASK_COUNT - 1))
    if [[ $GROUP_TASK_COUNT -eq 0 ]]; then
      CURRENT_GROUP_ID=""
      GROUP_START_REQUESTED=false
      echo "Group completed - returning to sequential mode"
    fi
  fi
}
```

**Reference:** Use the context file templates and coordination strategies in `~/.claude/commands/parallel-task-analyzer.md` for detailed implementation guidance.

## Task List Maintenance

1. **Update the task list as you work:**
   - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
   - Add new tasks as they emerge.

2. **Maintain the "Relevant Files" section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.

## AI Instructions

When working with task lists, the AI must:

1. **3-Condition Permission System:**
   - **Condition 1 (Sequential)**: Ask "Ready to start task [TaskID]? (yes/y to proceed)" and wait for confirmation
   - **Condition 2 (New Group)**: Ask "Ready to start parallel group [Group-X] with [N] tasks? (yes/y to proceed)" and wait for confirmation
   - **Condition 3 (Within Group)**: NO permission needed - execute automatically
   - Always check context files before starting any task

2. **Pre-execution Checks (apply task type detection first):**
   - Use `detect_task_type()` function to determine which permission condition applies
   - Read group coordination files to understand current file usage
   - Verify no file conflicts exist with running tasks
   - Check individual context files for blockers or dependencies

3. **During Execution:**
   - Update individual task context files when starting/modifying files
   - Update group coordination files to reflect current file usage
   - Monitor other tasks' progress via context files to avoid conflicts

4. **Completion Protocol:**
   - Mark each finished **sub‑task** `[x]` immediately
   - Update context files with completion status and final file list
   - Use `update_group_state()` to track group completion
   - Mark **parent task** `[x]` once **ALL** subtasks are `[x]`
   - Run full test suite before committing group changes

5. **File Management:**
   - Keep "Relevant Files" section accurate and up to date
   - Add newly discovered tasks as they emerge
   - Maintain DRY principle and avoid over-complication

6. **Error Handling:**
   - Use test-automator and language-specific subagents for failing tests
   - **DO NOT** proceed to next task/group until all tests pass
   - Document any blockers or issues in context files

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
