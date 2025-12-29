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
| No `[P:Group-X]` | Sequential | Execute immediately |
| `[P:Group-X]` | Parallel group | Execute all group tasks concurrently via subagents |

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

1. **Autonomous Execution (no permission needed):**
   - Execute tasks continuously without stopping for permission
   - Only pause when clarification is needed (ambiguous requirements, missing info, conflicting specs)
   - Run `bd ready` to check task status before starting any task

2. **Pre-execution Checks:**
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
   - Mark **parent task** `[x]` once **ALL** subtasks are `[x]`
   - Run full test suite before committing group changes

5. **File Management:**
   - Keep "Relevant Files" section accurate and up to date
   - Add newly discovered tasks with `bd create`
   - Maintain DRY principle and avoid over-complication

6. **Error Handling:**
   - Use test-automator and language-specific subagents for failing tests
   - **DO NOT** proceed to next task/group until all tests pass

## Ralph Wiggum Loops (Iterative Development)

For tasks that require iteration until success (e.g., getting tests to pass, fixing bugs), use the Ralph Wiggum technique - a self-referential loop that keeps iterating until a completion condition is met.

### Prerequisites

**Check if Ralph plugin is installed** before using Ralph commands:
```bash
# Check if /ralph-loop command is available
# If not installed, skip Ralph loops and use manual iteration instead
```

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

When a task requires iteration (especially TDD or bug fixing), start a Ralph loop:

```bash
/ralph-loop "<prompt>" --max-iterations <n> --completion-promise "<text>"
```

**Example for a beads task:**
```bash
/ralph-loop "Implement task BD-123: User authentication.

Requirements from PRD:
- JWT-based auth with refresh tokens
- Password hashing with bcrypt
- Rate limiting on login attempts

Follow TDD:
1. Write failing tests first
2. Implement to make tests pass
3. Refactor if needed
4. Run full test suite

Output <promise>COMPLETE</promise> when:
- All tests passing
- Code reviewed for security
- README updated" --max-iterations 30 --completion-promise "COMPLETE"
```

### Structuring Ralph Prompts

**Include in every Ralph prompt:**
1. **Clear task reference:** Link to beads issue ID and PRD
2. **Success criteria:** Specific, verifiable conditions
3. **Completion promise:** The exact phrase to output when done
4. **Escape hatch:** What to do if stuck after N iterations

**Template:**
```markdown
Implement task <issue-id>: <title>

Requirements:
- [List from PRD]

Acceptance criteria:
- [Testable conditions]

Process:
1. [Step-by-step approach]
2. Run tests after each change
3. If tests fail, debug and fix
4. Repeat until all green

If stuck after 20 iterations:
- Document what's blocking
- List approaches tried
- Suggest alternatives

Output <promise>DONE</promise> when all acceptance criteria met.
```

### Safety: Always Set Max Iterations

**Never run unbounded loops.** Always use `--max-iterations`:

```bash
# Good - bounded loop
/ralph-loop "Fix bug X" --max-iterations 20 --completion-promise "FIXED"

# Dangerous - could loop forever
/ralph-loop "Fix bug X" --completion-promise "FIXED"
```

### Canceling a Ralph Loop

If a loop is running and you need to stop it:

```bash
/cancel-ralph
```

### Ralph + Beads Integration

When using Ralph for a beads task:

1. **Before starting:** Update beads status
   ```bash
   bd update <issue-id> --status in_progress
   bd update <issue-id> --notes "Starting Ralph loop"
   ```

2. **On completion:** Close the task
   ```bash
   bd close <issue-id> --reason "Completed via Ralph loop"
   ```

3. **On failure (max iterations reached):** Mark as blocked
   ```bash
   bd update <issue-id> --status blocked
   bd update <issue-id> --notes "Ralph loop reached max iterations. See iteration log."
   ```

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
