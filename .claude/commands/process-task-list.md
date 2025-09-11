# Task List Management

Guidelines for managing task lists in markdown files to track progress on completing a PRD

## Task Implementation

- **One sub-task at a time:**
  - Do **NOT** start the next sub-task until you ask the user for permission and they say "yes" or "y"
  - If the next sub-task is a parallel sub-task, indicated with "[P]", run them all in parallel with their specialized sub-agents.
- Identify parallel execution groups ([P] flags)
- **Execute [P] tasks concurrently** when no dependencies block them
- Parallel execution management:
  - Group [P] tasks within same phase
  - Execute using Task tool with parallel agent invocations
  - Wait for completion before proceeding to next group
  - Update all completed tasks atomically
  - Always update the context file when you have completed a change.
  - Stay up to date with the latest contexts of sub-agents in the current parallel sub-tasks processing group by reading their context files to see if they have worked on files you are using or will be using.
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

- Stop after each sub‑task and wait for the user's go-ahead, unless it is a parallel sub-task.

## Task List Maintenance

1. **Update the task list as you work:**
   - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
   - Add new tasks as they emerge.

2. **Maintain the "Relevant Files" section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.

## AI Instructions

When working with task lists, the AI must:

1. Regularly update the task list file after finishing any significant work.
2. Follow the completion protocol:
   - Mark each finished **sub‑task** `[x]`.
   - Mark the **parent task** `[x]` once **all** its subtasks are `[x]`.
3. Add newly discovered tasks.
4. Keep "Relevant Files" accurate and up to date.
5. Before starting work, check which sub-task is next.
6. After implementing a sub-task, update the file and then pause for user approval.
7. Deploy relevant subagents to help you with tasks and subtasks.
8. Use tests to discover bugs, if tests fail use the test-automator and relevant language subagent to help fix it. **DO NOT** move onto the next task until all tests pass
9. Maintain the DRY (Don't Repeat Yourself) principle.
10. Do not overcomplicate the implementation, it makes it hard for the user to review the changes.
