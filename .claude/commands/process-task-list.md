# Task List Management

Guidelines for managing task lists in markdown files to track progress on completing a PRD

## Task Implementation

- **Smart Task Execution Strategy:**
  - Do **NOT** start the next sub-task until you ask the user for permission and they say "yes" or "y"
  - **Sequential Tasks:** Execute one at a time, waiting for user confirmation
  - **Parallel Groups:** Execute all tasks within a group concurrently using specialized sub-agents

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

- Stop after each sub‑task and wait for the user's go-ahead, unless it is a parallel group (all [P:Group-X] tasks in the same group execute together).

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

1. **Task Execution Strategy:**
   - For sequential tasks: Execute one at a time, get user approval before proceeding
   - For parallel groups: Execute all tasks in the group simultaneously using multiple subagents
   - Always check context files before starting any task

2. **Pre-execution Checks:**
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
