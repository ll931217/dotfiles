# Rule: Generating a Task List from a PRD

## Goal

To guide an AI assistant in creating a detailed, step-by-step task list in Markdown format based on an existing Product Requirements Document (PRD). The task list should guide a developer through implementation.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `tasks-[prd-file-name].md` (e.g., `tasks-prd-user-profile-editing.md`)

## Process

1. **Receive PRD Reference:** The user points the AI to a specific PRD file
2. **Analyze PRD:** The AI reads and analyzes the functional requirements, user stories, and other sections of the specified PRD.
3. **Assess Current State:** Review the existing codebase to understand existing infrastructre, architectural patterns and conventions. Also, identify any existing components or features that already exist and could be relevant to the PRD requirements. Then, identify existing related files, components, and utilities that can be leveraged or need modification.
4. **Phase 1: Generate Parent Tasks:** Based on the PRD analysis and current state assessment, create the file and generate the main, high-level tasks required to implement the feature. Use your judgement on how many high-level tasks to use. It's likely to be about 5. These parent tasks should each be full features that can be tested where the user will only proceed to next parent task until satisfied. Present these tasks to the user in the specified format (without sub-tasks yet). Inform the user: "I have generated the high-level tasks based on the PRD. Ready to generate the sub-tasks? Respond with 'Go' to proceed."
5. **Wait for Confirmation:** Pause and wait for the user to respond with "Go".
6. **Phase 2: Generate Sub-Tasks:** Once the user confirms, break down each parent task into smaller, actionable sub-tasks necessary to complete the parent task. Ensure sub-tasks logically follow from the parent task, cover the implementation details implied by the PRD, and consider existing codebase patterns where relevant without being constrained by them.
7. **Phase 3: Intelligent Parallel Task Analysis and Grouping**
   - **Phase 3a - File Dependency Analysis:** For each sub-task, identify all files that will be created, modified, or read. Create a file dependency map showing which sub-tasks interact with which files.
   - **Phase 3b - Conflict Detection:** Analyze the file dependency map to identify sub-tasks that modify the same files (these cannot run in parallel). Group sub-tasks into conflict-free execution groups.
   - **Phase 3c - Parallel Group Assignment:** Mark sub-tasks that can run in parallel with `[P:Group-X]` notation, where X is the group identifier (A, B, C, etc.). Tasks in the same group can run concurrently because they don't modify the same files.
   - **Phase 3d - Context File Generation:** For each parallel group, create a group coordination context file at `/tasks/context/group-{group-id}_coordination.md` that tracks file modifications and progress. Individual task context files are named: `/tasks/context/{subtask_number}_{subtask_description}.md`

   **File Conflict Rules:**
   - Sub-tasks modifying the same files = different groups or sequential execution
   - Sub-tasks modifying different files = same parallel group
   - Test files and source files are considered separate for conflict purposes
   - Configuration files (package.json, etc.) should be handled sequentially if multiple tasks modify them

   **Reference:** Use the algorithms and templates in `~/.claude/commands/parallel-task-analyzer.md` for detailed conflict detection and group assignment logic.

8. **Identify Relevant Files:** Based on the tasks and PRD, identify potential files that will need to be created or modified. List these under the `Relevant Files` section, including corresponding test files if applicable.
9. **Generate Final Output:** Combine the parent tasks, sub-tasks, relevant files, and notes into the final Markdown structure.
10. **Save Task List:** Save the generated document in the `/tasks/` directory with the filename `tasks-[prd-file-name].md`, where `[prd-file-name]` matches the base name of the input PRD file (e.g., if the input was `prd-user-profile-editing.md`, the output is `tasks-prd-user-profile-editing.md`).

## Output Format

The generated task list _must_ follow this structure:

```markdown
## Relevant Files

- `path/to/potential/file1.ts` - Brief description of why this file is relevant (e.g., Contains the main component for this feature).
- `path/to/file1.test.ts` - Unit tests for `file1.ts`.
- `path/to/another/file.tsx` - Brief description (e.g., API route handler for data submission).
- `path/to/another/file.test.tsx` - Unit tests for `another/file.tsx`.
- `lib/utils/helpers.ts` - Brief description (e.g., Utility functions needed for calculations).
- `lib/utils/helpers.test.ts` - Unit tests for `helpers.ts`.

### Notes

- Unit tests should typically be placed in the `tests` directory unless otherwise specified or unless if there is a test directory.
- Maintain the DRY (Don't Repeat Yourself) principle.
- Do not overcomplicate the implementation, it makes it hard for the user to review the changes.
- Keep "Relevant Files" accurate and up to date.
- Add newly discovered tasks.
- Deploy relevant subagents to help you with tasks and subtasks.
- Use tests to discover bugs, if tests fail use the test-automator and relevant language subagent to help fix it.
- When processing parallel tasks (Tasks marked with "[P:Group-X]"), please:
  - Use relevant sub-agents for tasks within the same group
  - Check the group coordination file before starting to see current file usage status
  - Update your individual task context file and the group coordination file when you complete changes
  - Only work on files that aren't currently being modified by other tasks in different groups
  - Coordinate with other agents in your group via the group coordination context file

## Tasks

- [ ] 1.0 Parent Task Title
  - [ ] 1.1 [Sub-task description 1.1]
  - [ ] 1.2 [Sub-task description 1.2]
- [ ] 2.0 Parent Task Title
  - [ ] 2.1 [Sub-task description 2.1]
  - [ ] 2.2 [Sub-task description 2.2]
    - [ ] 2.2.1 [P:Group-A] [Parallel sub-task description 2.2.1] [Files: src/component.tsx, src/component.test.tsx] [Context: /tasks/context/2.2.1_component_task.md]
    - [ ] 2.2.2 [P:Group-A] [Parallel sub-task description 2.2.2] [Files: src/utils.ts, src/utils.test.ts] [Context: /tasks/context/2.2.2_utils_task.md]
    - [ ] 2.2.3 [P:Group-B] [Parallel sub-task description 2.2.3] [Files: src/api.ts, src/api.test.ts] [Context: /tasks/context/2.2.3_api_task.md]
  - [ ] 2.3 [Sequential sub-task that depends on Group-A and Group-B completion]
- [ ] 3.0 Parent Task Title (may not require sub-tasks if purely structural or configuration)
```

## Enhanced Parallel Task Format

Each parallel task now includes detailed information for conflict detection and coordination:

**Format:** `- [ ] X.Y.Z [P:Group-ID] [Task Description] [Files: file1.ext, file2.ext] [Context: /path/to/context.md]`

**Components:**

- `[P:Group-ID]`: Parallel group identifier (Group-A, Group-B, etc.)
- `[Files: ...]`: List of files this task will create, modify, or read
- `[Context: ...]`: Path to individual task context file for detailed coordination

**Group Coordination Files:**

- `/tasks/context/group-a_coordination.md` - Tracks all Group-A tasks and file usage
- `/tasks/context/group-b_coordination.md` - Tracks all Group-B tasks and file usage

## Interaction Model

The process explicitly requires a pause after generating parent tasks to get user confirmation ("Go") before proceeding to generate the detailed sub-tasks. This ensures the high-level plan aligns with user expectations before diving into details.

## Target Audience

Assume the primary reader of the task list is a **junior developer** who will implement the feature with awareness of the existing codebase context.

ULTRATHINK
