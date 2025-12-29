---
description: Generate tasks in beads (`bd`)
---
# Rule: Generating Issues from a PRD using Beads

## Goal

To guide an AI assistant in creating a detailed, step-by-step issue hierarchy using the `bd` (beads) tool based on an existing Product Requirements Document (PRD). The issues should guide a developer through implementation with proper dependency tracking.

## Output

- **Format:** Beads issues in `.beads/` database
- **Tool:** `bd` (beads dependency-aware issue tracker)

## Prerequisites

Ensure beads is initialized in the project. If not, run:
```bash
bd init
```

## Process

1. **Receive PRD Reference:** The user points the AI to a specific PRD file
2. **Analyze PRD:** The AI reads and analyzes the functional requirements, user stories, and other sections of the specified PRD.
3. **Assess Current State:** Review the existing codebase to understand existing infrastructure, architectural patterns and conventions. Also, identify any existing components or features that already exist and could be relevant to the PRD requirements. Then, identify existing related files, components, and utilities that can be leveraged or need modification.
4. **Phase 1: Generate Parent Issues (Epics):** Based on the PRD analysis and current state assessment, create the main, high-level issues required to implement the feature. Use your judgement on how many high-level issues to use. It's likely to be about 5. These parent issues should each be full features that can be tested where the user will only proceed to next parent issue until satisfied. Present these issues to the user. Inform the user: "I have generated the high-level issues based on the PRD. Ready to generate the sub-issues? Respond with 'Go' to proceed."

   **Create parent issues using:**
   ```bash
   bd create "Epic: [Parent Task Title]" -p 1 -t epic
   ```

5. **Wait for Confirmation:** Pause and wait for the user to respond with "Go".
6. **Phase 2: Generate Sub-Issues:** Once the user confirms, break down each parent issue into smaller, actionable sub-issues necessary to complete the parent issue. Ensure sub-issues logically follow from the parent issue, cover the implementation details implied by the PRD, and consider existing codebase patterns where relevant without being constrained by them.

   **Create sub-issues and link to parent:**
   ```bash
   bd create "[Sub-task description]" -p 2 -t task
   bd dep add <sub-issue-id> <parent-issue-id> --type parent-child
   ```

7. **Phase 3: Intelligent Parallel Issue Analysis and Dependencies**
   - **Phase 3a - File Dependency Analysis:** For each sub-issue, identify all files that will be created, modified, or read. Include this in the issue description.
   - **Phase 3b - Conflict Detection:** Analyze the file dependency map to identify sub-issues that modify the same files (these cannot run in parallel and need blocking dependencies).
   - **Phase 3c - Dependency Assignment:**
     - Issues that can run in parallel (different files) = no blocking dependencies between them
     - Issues that must be sequential (same files) = add blocking dependency with `bd dep add <blocked-issue> <blocking-issue>`
     - Use `related` type for soft connections: `bd dep add <issue1> <issue2> --type related`

   **File Conflict Rules:**
   - Sub-issues modifying the same files = add blocking dependency
   - Sub-issues modifying different files = can run in parallel (no blocking dependency)
   - Test files and source files are considered separate for conflict purposes
   - Configuration files (package.json, etc.) should have blocking dependencies if multiple issues modify them

8. **Add Relevant Files to Issue Descriptions:** When creating issues, include the relevant files in the description using the `-d` flag:
   ```bash
   bd create "[Task description]" -p 2 -t task -d "Files: src/component.tsx, src/component.test.ts"
   ```

9. **Verify Issue Structure:** After creating all issues, verify the structure:
   ```bash
   bd list                    # View all issues
   bd dep tree <epic-id>      # Visualize dependency tree for each epic
   bd ready                   # Show issues ready to work on
   ```

## Issue Structure

Issues are stored in the `.beads/` database with the following hierarchy:

### Epic (Parent Issue)
```bash
bd create "Epic: User Authentication System" -p 1 -t epic -d "Implement complete user authentication including login, registration, and session management.

Files:
- src/auth/auth.service.ts
- src/auth/auth.controller.ts
- src/auth/auth.module.ts"
```

### Task (Sub-Issue)
```bash
bd create "Implement login endpoint" -p 2 -t task -d "Create POST /auth/login endpoint with JWT token generation.

Files:
- src/auth/auth.controller.ts
- src/auth/auth.service.ts
- src/auth/dto/login.dto.ts"

# Link to parent epic
bd dep add <task-id> <epic-id> --type parent-child
```

### Dependency Types

- **`blocks`**: Task B must complete before Task A can start
  ```bash
  bd dep add <blocked-task> <blocking-task>
  ```

- **`parent-child`**: Hierarchical relationship (epic → task)
  ```bash
  bd dep add <child-id> <parent-id> --type parent-child
  ```

- **`related`**: Soft connection, informational only
  ```bash
  bd dep add <issue1> <issue2> --type related
  ```

### Example Issue Hierarchy

```
Epic: User Authentication System (proj-abc123)
├── Implement login endpoint (proj-def456) [parent-child]
├── Implement registration endpoint (proj-ghi789) [parent-child]
│   └── blocked by: Implement login endpoint [blocks]
├── Add password hashing utility (proj-jkl012) [parent-child]
└── Write authentication tests (proj-mno345) [parent-child]
    └── blocked by: Implement login endpoint, Implement registration endpoint [blocks]
```

### Notes

- The first epic should always be the core system architecture, functional enough for a minimal viable system.
- Unit tests should typically be placed in the `tests` directory unless otherwise specified.
- Maintain the DRY (Don't Repeat Yourself) principle.
- Do not overcomplicate the implementation, it makes it hard for the user to review the changes.
- Include relevant files in issue descriptions for clarity.
- Use `bd ready` to find issues that are unblocked and ready to work on.
- Use `bd dep tree <epic-id>` to visualize the dependency structure.
- When multiple issues can run in parallel (no file conflicts), they will appear in `bd ready` simultaneously.

## Interaction Model

The process explicitly requires a pause after generating parent tasks to get user confirmation ("Go") before proceeding to generate the detailed sub-tasks. This ensures the high-level plan aligns with user expectations before diving into details.

## Target Audience

Assume the primary reader of the task list is a **junior developer** who will implement the feature with awareness of the existing codebase context.

ULTRATHINK
