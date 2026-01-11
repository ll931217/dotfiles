---
description: Generate tasks from a PRD (using beads if available, otherwise TodoWrite)
---

# Rule: Generating Tasks from a PRD

## Quick Start (5 steps)

1. **Auto-discover PRD** - Matches current git context (branch/worktree)
2. **Check existing tasks** - Detects if PRD was previously processed
3. **Generate epics** - 5-7 high-level parent issues
4. **Generate sub-tasks** - Detailed tasks with dependencies
5. **Wait for "Go"** - User confirmation before generation begins (SKIP in autonomous mode)

**Requirements:** PRD must exist and be `approved` status.

**Full workflow:** See `README.md` for complete flow command usage.

## Autonomous Mode Detection

**CRITICAL:** Before executing, check if this command is running in autonomous mode:

- This command is running autonomously if invoked from `/flow:autonomous`
- When autonomous, **SKIP all AskUserQuestion checkpoints**
- When autonomous, **SKIP all "Wait for Go" confirmations**
- Continue execution through all phases without stopping

**Detection method:**
- Check if the current conversation context indicates autonomous execution
- Look for `[Maestro]` log format or explicit autonomous mode flags
- If uncertain, assume interactive mode (safer default)

## Goal

To guide an AI assistant in creating a detailed, step-by-step task hierarchy based on an existing Product Requirements Document (PRD). The tasks should guide a developer through implementation with proper dependency tracking.

**Task Storage Options:**

- **With beads (`bd`) installed:** Tasks are stored in the `.beads/` database with full dependency tracking
- **Without beads:** Tasks are tracked using the internal TodoWrite tool with basic hierarchical organization

## PRD Update Detection

This command intelligently detects whether a PRD has been previously processed and avoids duplicate task generation.

**Key Behaviors:**

1. **First-Time PRD:** Generates complete task hierarchy (epics + sub-issues)
2. **Updated PRD:** Detects existing tasks and offers update options:
   - Review and update existing tasks (keep completed, update pending)
   - Regenerate all tasks from scratch
   - Show PRD diff to understand changes
   - Cancel operation

3. **Context Awareness:**
   - Checks PRD frontmatter for `beads.related_issues` and `beads.related_epics`
   - Compares `updated_at_commit` to detect PRD modifications
   - Matches tasks to current git branch/worktree context

**Detection Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Auto-discover PRD (match branch/worktree context)        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Check PRD frontmatter for existing task references       │
│    - beads.related_issues: []?                              │
│    - beads.related_epics: []?                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
              ┌──────┴──────┐
              │ Empty/null? │
              └──────┬──────┘
           ┌──────────┴──────────┐
           │ YES                 │ NO
           ▼                     ▼
    ┌──────────────┐    ┌────────────────────────┐
    │ Fresh PRD    │    │ Existing tasks found   │
    │ Full gen     │    │ Compare PRD version    │
    └──────────────┘    └──────────┬─────────────┘
                                   │
                                   ▼
                        ┌────────────────────────┐
                        │ Show user options      │
                        │ a) Update existing     │
                        │ b) Regenerate all      │
                        │ c) Show diff           │
                        │ d) Cancel              │
                        └────────────────────────┘
```

## Output

- **With beads (`bd`) installed:**
  - **Format:** Beads issues in `.beads/` database
  - **Tool:** `bd` (beads dependency-aware issue tracker)
  - **Features:** Dependency tracking, persistent storage, ready task detection

- **Without beads:**
  - **Format:** Internal TodoWrite tool state
  - **Tool:** TodoWrite (built-in AI Agent tool)
  - **Limitations:** Task context may be lost between sessions; no persistent dependency tracking

## Prerequisites

- **Required:** A PRD file created via `/flow:plan` in the current branch/worktree context
- **Optional:** beads (`bd`) - If installed, tasks will be stored persistently in the `.beads/` database
  - Check with: `which bd`
  - Initialize if needed: `bd init` (only if using beads)
  - If beads is not available, the AI will use the internal TodoWrite tool for task tracking

## Process

1. **Auto-Discover PRD:** Automatically find the appropriate PRD based on git context.

   See: `shared/protocols/prd-discovery.md` for the multi-stage discovery algorithm.

   **After PRD Discovery:**
   - Display discovered PRD with its metadata
   - Ask for confirmation: "Using PRD: [name] (branch: [branch], version: [vN])"
   - Proceed with step 2 (Analyze PRD)

2. **Analyze PRD:** The AI reads and analyzes the functional requirements, user stories, and other sections of the specified PRD.

3. **Check Existing Tasks (Update Detection):**
   Before generating new tasks, check if tasks already exist for this PRD context.

   **If beads (`bd`) is installed:**
   - **Step 3a - Query Beads for Existing Tasks:**
     The AI queries the beads database to retrieve all existing issues and filters them by the current git context (branch/worktree).

   - **Step 3b - Identify Related Issues:**
     - Look for issues that reference this PRD by checking PRD filename/version in descriptions
     - Check `beads.related_issues` or `beads.related_epics` in PRD frontmatter:
       ```yaml
       beads:
         related_issues: [proj-123, proj-456, proj-789]
         related_epics: [proj-001, proj-002]
       ```

   - **Step 3c - Compare PRD Version:**
     Compare current PRD `updated_at_commit` with existing task creation time

   - **Step 3d - Update Strategy Decision:**
     Present options to user based on existing tasks:

     ```
     ℹ️  Found existing tasks for this PRD:
     Options:
     a) Review and update existing tasks (keep completed tasks, update pending ones)
     b) Regenerate all tasks (archive existing, create new from scratch)
     c) Show diff of PRD changes to understand what needs updating
     d) Cancel
     ```

   - **Step 3e - Intelligent Task Update:**
     If user chooses option (a):
     - Parse existing issues from beads using `bd show <issue-id>`
     - Compare with PRD requirements
     - Keep completed tasks, update pending ones, generate new tasks

   - **Step 3f - No Existing Tasks:**
     If `beads.related_issues` and `beads.related_epics` are empty or null, proceed to full task generation

   **If beads is NOT installed (TodoWrite fallback):**
   - Check internal TodoWrite state for existing tasks related to current PRD
   - Compare PRD version `updated_at_commit` with last task generation
   - Present similar update options (review, regenerate, show diff, cancel)
   - If no existing TodoWrite state, proceed to full task generation
   - Note: Without beads, task history between sessions is limited

4. **Assess Current State:** Review the existing codebase to understand existing infrastructure, architectural patterns and conventions. Also, identify any existing components or features that already exist and could be relevant to the PRD requirements. Then, identify existing related files, components, and utilities that can be leveraged or need modification.

4.5 **Context Discovery:** For each epic/sub-issue, identify and document relevant files with specific line ranges.

**Discovery Process:**

1. **Launch Explore Agents (1-2 parallel) to find relevant files:**

   **Agent 1: Feature-Related Files**

   Explore the codebase to find files relevant to: [EPIC/TASK_DESCRIPTION]

   Search for:
   1. Existing implementations of similar functionality
   2. Configuration files (schemas, types, routes)
   3. Service layer patterns
   4. Utilities and helpers

   For each relevant file found, report:
   - File path (relative to repo root)
   - Specific line ranges (e.g., "45-120" for a function)
   - Why it's relevant to this task

   Use medium thoroughness.

   **Agent 2: Test Patterns** (optional, skip for test-related tasks)

   Find testing patterns for: [FEATURE_TYPE]

   Locate:
   1. Test files for similar features
   2. Test utilities and fixtures
   3. Mock or stub patterns

   Report with file paths, line ranges, and relevance.
   Use quick thoroughness.

2. **Organize findings per task:**

   Create a mapping for each epic/sub-issue:
   ```
   proj-auth.1: Implement login endpoint
     relevant_files:
       - src/api/routes.ts:45-80 (existing route patterns)
       - src/services/AuthService.ts:1-50 (auth interface to follow)
       - src/types/user.ts:10-30 (User type definitions)
       - tests/auth.test.ts:1-40 (test patterns to follow)
   ```

3. **Store in beads issue description:**

   Add a "Relevant Files" section to each issue:
   ```
   ### Relevant Files

   | File | Lines | Purpose |
   |------|-------|---------|
   | `src/api/routes.ts` | 45-80 | Existing route patterns to follow |
   | `src/services/AuthService.ts` | 1-50 | Auth service interface |
   | `src/types/user.ts` | 10-30 | User type definitions |
   | `tests/auth.test.ts` | 1-40 | Test patterns |
   ```

**Benefits:**
- `/flow:implement` can read only specific line ranges vs entire files
- Reduces token usage by ~70% for typical implementations
- Provides clear guidance on what code to review
- Helps agents understand codebase patterns quickly

**Fallback for new projects:**
- If no relevant files found, use: `No existing files found (new feature area)`

4.6 **Determine Subagent Types:** For each epic/sub-issue, determine the most appropriate subagent type using the subagent type taxonomy.

**Subagent Type Detection Process:**

1. **Analyze Task Description:**
   - Extract keywords and patterns from task title and description
   - Identify primary technical domain (frontend/backend/data/etc)
   - Detect language-specific requirements (Python, TypeScript, SQL, etc.)
   - Look for domain-specific keywords (auth, testing, deployment, etc.)

2. **Match to Subagent Type:**
   - Consult `.claude/subagent-types.yaml` taxonomy
   - Find best-matching task category based on pattern matching
   - Use priority order from taxonomy (security > testing > frontend > etc.)
   - Assign primary subagent type
   - Identify fallback subagents if needed

3. **Skill Detection:**
   - Check task description and category against skill_mappings in `.claude/subagent-types.yaml`
   - Match trigger patterns for each available skill:
     - **frontend-design**: UI components, styling, layout, visual design
     - **mcp-builder**: External API integrations, MCP server creation
     - **skill-creator**: Custom skill definition requests
     - **webapp-testing**: Browser testing, E2E testing, UI verification
     - **document-skills**: API docs, user guides, technical documentation
   - Associate all applicable skills with the task (multiple skills allowed)

4. **Store in Issue Metadata:**
   - Add `subagent_type` field to beads issue
   - Add `fallback_agents` array for alternatives
   - Add `applicable_skills` array if skills detected
   - Store skill-specific context for later use

**Example Output:**

For task "Implement React login component with TypeScript":

```yaml
subagent_type: frontend-developer
fallback_agents:
  - react-pro
  - typescript-pro
applicable_skills:
  - frontend-design
  - webapp-testing
```

**Skill Assignment Examples:**

| Task Description | Category | Skills Assigned |
|-----------------|----------|-----------------|
| "Create responsive UI for dashboard" | frontend | `frontend-design`, `webapp-testing` |
| "Build MCP server for GitHub integration" | backend | `mcp-builder` |
| "Generate API documentation from endpoints" | documentation | `document-skills` |
| "Add E2E tests for checkout flow" | testing | `webapp-testing` |
| "Create custom skill for code review" | ai | `skill-creator` |

**Storage in beads:**
```bash
bd create \
  --title "Implement React login component" \
  --description "..." \
  --metadata "subagent_type=frontend-developer" \
  --metadata "fallback_agents=react-pro,typescript-pro" \
  --metadata "applicable_skills=frontend-design,webapp-testing"
```

**Auto-Detection Fallback:**

If automatic detection fails:
1. Use `general-purpose` as default subagent type
2. Continue with task creation
3. Log detection failure for review
4. Manual agent selection still available during implementation

5. **Phase 1: Generate Parent Issues (Epics) - For New or Updated Requirements Only:**
   - If this is a fresh PRD (no existing tasks): Generate all parent epics
   - If this is an updated PRD: Only generate NEW or MODIFIED epics
   - Skip generation of completed/unchanged epics

   **With beads (`bd`) installed:**
   - Use `bd create` to create epic issues
   - Set epic properties (title, description, priority, labels)
   - Store epic IDs for later reference

   **Without beads (TodoWrite fallback):**
   - Use TodoWrite tool to track epics internally
   - Each epic is a todo item with status "pending"
   - Use epic naming convention: "Epic: [title]" for clarity

   **Generation Strategy for Updates:**
   - Compare PRD requirements with existing epic descriptions
   - For each requirement area:
     - If matching epic exists and is incomplete: Update description
     - If matching epic exists and is done: Skip
     - If no matching epic exists: Create new epic
   - Present both existing (kept) and new epics to user for review

   Based on the PRD analysis and current state assessment, create the main, high-level issues required to implement the feature. Use your judgement on how many high-level issues to use. It's likely to be about 5. These parent issues should each be full features that can be tested where the user will only proceed to next parent issue until satisfied. Present these issues to the user.

   **AUTONOMOUS MODE CHECK:**
   - If this command was invoked from `/flow:autonomous`, **SKIP the confirmation checkpoint**
   - Proceed directly to Phase 2 (sub-issue generation) without waiting
   - Detect autonomous mode by checking if the parent workflow is autonomous

   **INTERACTIVE MODE (default):**
   - Inform the user (Using AskUserQuestion tool): "I have generated the high-level issues based on the PRD. Ready to generate the sub-issues? Respond with 'Go' to proceed."

6. **Phase 1.5: Assign Priorities to Epics:**
   - Read priorities from PRD frontmatter `priorities.requirements` array
   - Map each epic to its associated requirements
   - **Epic Priority Rule:** Use the **highest** requirement priority in epic (P0 > P1 > P2 > P3 > P4)
   - Present epic priorities to user for confirmation
   - User can adjust epic priorities if needed

   **Example Mapping:**

   ```
   PRD Requirements with Priorities:
   - FR-1: User login (P1)
   - FR-2: Password reset (P2)
   - FR-3: Email notifications (P3)
   - FR-4: Admin dashboard (P4)

   Generated Epics with Mapped Priorities:
   ┌────────────────────────────┬─────────────┬──────────────────────┐
   │ Epic                       │ Requirements │ Priority (Highest)   │
   ├────────────────────────────┼─────────────┼──────────────────────┤
   │ User Authentication        │ FR-1, FR-2  │ P1 (from FR-1)       │
   │ Email Notifications        │ FR-3        │ P3 (from FR-3)       │
   │ Admin Dashboard            │ FR-4        │ P4 (from FR-4)       │
   └────────────────────────────┴─────────────┴──────────────────────┘
   ```

7. **Wait for Confirmation (INTERACTIVE MODE ONLY):**

   **AUTONOMOUS MODE:** Skip this checkpoint entirely - proceed directly to Phase 2.

   **INTERACTIVE MODE:** Pause and wait for the user to respond with "Go".

8. **Phase 2: Generate Sub-Issues - For New or Updated Epics Only:** Once the user confirms, break down each parent issue into smaller, actionable sub-issues necessary to complete the parent issue.

   **With beads (`bd`) installed:**
   - Use `bd create` to create sub-issues
   - Link each sub-issue to its parent epic using parent-child relationship
   - Set dependencies between sub-issues based on file conflicts
   - Use `bd add-blocked-by` or `bd add-depends-on` as needed

   **Without beads (TodoWrite fallback):**
   - Use TodoWrite tool to create sub-tasks
   - Name sub-tasks with parent epic prefix: "[Epic Title] Sub-task: specific task"
   - Mark sub-tasks as status "pending"
   - Note: Dependency tracking is limited with TodoWrite

   **For updated PRDs:** Only generate sub-issues for epics that are new or modified. Skip sub-issue generation for completed/unchanged epics.

9. **Phase 3: Intelligent Parallel Issue Analysis and Dependencies**
   - **Phase 3a - File Dependency Analysis:** For each sub-issue, use the discovered relevant files from Step 4.5:
     - Files already identified during Context Discovery
     - Additional files for new/modified files
     - Include line ranges where possible for precision
   - **Phase 3b - Conflict Detection:** Analyze the file dependency map to identify sub-issues that modify the same files (these cannot run in parallel and need blocking dependencies).
   - **Phase 3c - Dependency Assignment:**
     - Issues that can run in parallel (different files) = no blocking dependencies between them
     - Issues that must be sequential (same files) = add blocking dependency
     - Use `related` type for soft connections between related but not dependent issues

   **File Conflict Rules:**
   - Sub-issues modifying the same files = add blocking dependency
   - Sub-issues modifying different files = can run in parallel (no blocking dependency)
   - Test files and source files are considered separate for conflict purposes
   - Configuration files (package.json, etc.) should have blocking dependencies if multiple issues modify them

   **With beads (`bd`) installed:**
   - Use `bd add-depends-on` to add blocking dependencies
   - Use `bd add-related` for soft connections
   - Run `bd ready` to identify tasks ready to start (no blockers)

   **Without beads (TodoWrite fallback):**
   - Note dependencies in task descriptions
   - Manual ordering required when executing tasks
   - No automatic "ready" task detection

10. **Task Priority Inheritance:** When creating sub-issues, assign priorities based on inheritance rules:
    - **Default Rule:** Sub-tasks inherit parent epic priority
    - **Exception 1:** Documentation tasks default to P3 unless epic is P0
    - **Exception 2:** Refactoring tasks default to P3 unless epic is P0
    - **User Override:** User can specify different priority if needed

11. **Add Relevant Files to Issue Descriptions:** Attach discovered file context to each issue.

   **Format for Issue Description:**

   ```markdown
   ## Task: [Task Title]

   [Task description...]

   ### Agent Assignment
   - **Primary Subagent:** `frontend-developer`
   - **Fallback Agents:** `react-pro`, `typescript-pro`
   - **Applicable Skills:** `frontend-design`, `webapp-testing`

   ### Relevant Files

   | File | Lines | Purpose |
   |------|-------|---------|
   | `path/to/file.ts` | 45-120 | Brief description |
   | `path/to/other.ts` | 1-30 | Brief description |

   ### Context Notes
   - [Any additional context about file structure]
   - [Patterns to follow or avoid]
   ```

   **With beads (`bd`) installed:**

   When creating issues with `bd create`, include the relevant files table in the description along with agent assignment:

   ```bash
   bd create --title "Implement login endpoint" \
     --description "## Task: Implement login endpoint

   Create a POST endpoint for user authentication.

   ### Agent Assignment
   - **Primary Subagent:** `backend-architect`
   - **Fallback Agents:** `api-documenter`
   - **Applicable Skills:** (none for this task)

   ### Relevant Files

   | File | Lines | Purpose |
   |------|-------|---------|
   | \`src/api/routes.ts\` | 45-80 | Existing route patterns |
   | \`src/services/AuthService.ts\` | 1-50 | Auth interface |
   | \`src/types/user.ts\` | 10-30 | User types |" \
     --priority "P1" \
     --labels "feature,auth" \
     --metadata "subagent_type=backend-architect" \
     --metadata "fallback_agents=api-documenter"
   ```

   **Frontend task example with skills:**

   ```bash
   bd create --title "Implement React login component" \
     --description "## Task: Implement React login component

   Create a responsive login form with email/password inputs.

   ### Agent Assignment
   - **Primary Subagent:** `frontend-developer`
   - **Fallback Agents:** `react-pro`, `typescript-pro`
   - **Applicable Skills:** `frontend-design`, `webapp-testing`

   ### Relevant Files

   | File | Lines | Purpose |
   |------|-------|---------|
   | \`src/components/Login.tsx\` | 1-50 | Component structure |
   | \`src/styles/auth.css\` | 10-30 | Styling patterns |" \
     --priority "P1" \
     --labels "feature,auth,frontend" \
     --metadata "subagent_type=frontend-developer" \
     --metadata "fallback_agents=react-pro,typescript-pro" \
     --metadata "applicable_skills=frontend-design,webapp-testing"
   ```

   **Without beads (TodoWrite fallback):**

   Include the same relevant files table in the task description stored in TodoWrite.

   **Context Storage Strategy:**

   - Store **file paths** and **line ranges** (not full file contents)
   - Implement command will use these to read selective sections
   - If line numbers change, store function/class names instead

12. **Merge Updated Issues with Existing Issues:**
    - For updated PRDs: Merge newly created issues with existing kept issues
    - Update PRD frontmatter with combined issue list (kept + new)
    - Ensure dependencies are correctly set between old and new issues
    - Archive obsolete issues if user chose option (b) "Regenerate all"

13. **Verify Issue Structure:** After creating all issues, verify the structure.

    **With beads (`bd`) installed:**
    - Use `bd list` to view all issues
    - Use `bd show <issue-id>` to view specific issue details
    - Use `bd ready` to identify tasks ready to start (no blockers)
    - Review dependency trees to ensure correct relationships

    **Without beads (TodoWrite fallback):**
    - Review the internal TodoWrite state
    - Verify all epics and sub-tasks are created
    - Check task descriptions for completeness

14. **Update PRD Metadata:** After creating tasks, update the PRD frontmatter.
    - Update `updated_at` timestamp
    - Update `updated_at_commit` with current commit SHA
    - Change status from `draft` to `approved` if not already (only if current status is draft)

    **With beads (`bd`) installed:**
    - Add newly created issue IDs to `beads.related_issues`
    - Add epic IDs to `beads.related_epics`

    **Without beads (TodoWrite fallback):**
    - Set `beads.related_issues: []` (empty array, since beads is not installed)
    - Set `beads.related_epics: []` (empty array)
    - Note: Tasks are tracked internally via TodoWrite

    **Update Process:**

    The AI updates the PRD frontmatter by:
    1. Updating the `updated_at` timestamp to the current UTC time
    2. Updating the `updated_at_commit` to the current git HEAD SHA
    3. Changing status from `draft` to `approved` (only if current status is draft)
    4. Adding issue/epic IDs to beads frontmatter (if beads is installed)

    **Example Updated Frontmatter (with beads):**

    ```yaml
    ---
    prd:
      version: 1
      feature_name: authentication
      status: approved # Changed from draft
    beads:
      related_issues: [proj-123, proj-456, proj-789] # Added
      related_epics: [proj-001, proj-002] # Added
    ...
    ```

    **Example Updated Frontmatter (without beads):**

    ```yaml
    ---
    prd:
      version: 1
      feature_name: authentication
      status: approved # Changed from draft
    beads:
      related_issues: [] # Empty - beads not installed, using TodoWrite
      related_epics: [] # Empty - beads not installed, using TodoWrite
    ...
    ```

15. **Next Steps After Task Generation:**

After successfully creating all tasks, display the following message to guide the user:

```
✅ Tasks Generated Successfully!

📋 PRD: prd-[feature]-vN.md
   Status: approved
   Branch: [branch-name]

📊 Tasks Created:
   Epics: X
   Sub-tasks: Y
   Total: Z

Next steps:
→ Run /flow:summary to view all tasks and their status
→ Run /flow:implement to start implementation
```

This guides the user to either review the tasks first or dive straight into implementation.

DO NOT suggest the user to use the `bd` command, this command is mainly reserved for AI Agents to use.

## Issue Structure

### With beads (`bd`) installed:

Issues are stored in the `.beads/` database with the following hierarchy:

#### Epic (Parent Issue)

High-level issue grouping multiple related tasks. Should include:

- Epic description with clear purpose
- Files to be created/modified
- Reference to PRD version

#### Task (Sub-Issue)

Individual actionable tasks that complete epic requirements. Should include:

- Task description with specific deliverable
- Files to be created/modified
- Link to parent epic (parent-child relationship)

### Without beads (TodoWrite fallback):

Tasks are tracked internally using the TodoWrite tool:

#### Epic (Parent Todo Item)

High-level task grouping multiple related sub-tasks. Should include:

- Epic description with clear purpose
- Status: "pending", "in_progress", or "completed"
- Active form: "[Verb]-ing [epic title]"

#### Task (Sub-Todo Item)

Individual actionable tasks that complete epic requirements. Should include:

- Task description with specific deliverable
- Status: "pending", "in_progress", or "completed"
- Parent epic name in the task title for hierarchy: "[Epic Title] Sub-task: specific task"

### Dependency Types

- **`blocks`**: Task B must complete before Task A can start
- **`parent-child`**: Hierarchical relationship (epic → task)
- **`related`**: Soft connection, informational only

### Example Issue Hierarchy

```
Epic: User Authentication System
├── Implement login endpoint [parent-child]
├── Implement registration endpoint [parent-child]
│   └── blocked by: Implement login endpoint [blocks]
├── Add password hashing utility [parent-child]
└── Write authentication tests [parent-child]
    └── blocked by: Implement login endpoint, Implement registration endpoint [blocks]
```

### Notes

- The first epic should always be the core system architecture, functional enough for a minimal viable system.
- **Always include a "Testing Strategy" epic** as one of the parent issues with comprehensive test coverage description

  **Testing Epic Dependency Rules (Sequential Testing - DEFAULT):**

  The Testing Strategy epic should block on ALL core implementation epics using blocking dependencies.

  **Exception - Setup/Configuration Epics:**
  - Testing epic does NOT block on "Setup" or "Configuration" epics
  - These can run in parallel or before implementation

  **Example Dependency Tree:**

  ```
  Epic: Setup & Configuration
      ├── Sub-task: Initialize project structure
      ├── Sub-task: Install dependencies

  Epic: Core Architecture
      ├── Sub-task: Define database schema
      ├── Sub-task: Create base services

  Epic: Feature Implementation
      ├── Sub-task: Implement authentication endpoints
      ├── Sub-task: Add rate limiting

  Epic: Testing Strategy [blocks: Core Architecture, Feature Implementation]
      ├── Sub-task: Write unit tests
      ├── Sub-task: Write integration tests
      └── Sub-task: Write E2E tests
  ```

- Unit tests should typically be placed in the `tests` directory unless otherwise specified.
- Maintain the DRY (Don't Repeat Yourself) principle.
- Do not overcomplicate the implementation, it makes it hard for the user to review the changes.
- Include relevant files in issue descriptions for clarity.

## Context Discovery Helper Functions

### Function: extract_relevant_files

Extracts relevant files with line ranges for a given task description.

**Usage:**

```bash
# Pseudocode for the AI agent
extract_relevant_files(task_description, codebase_context) {
  results = []

  # Use Explore agent to find files
  explore(task_description) -> files_found

  # For each file, identify relevant sections
  for file in files_found:
    if has_specific_function(file):
      results.append({
        path: file,
        lines: find_function_range(file, function_name),
        reason: "Contains pattern to follow"
      })
    else:
      results.append({
        path: file,
        lines: "1-50",  # First 50 lines as preview
        reason: "General context"
      })

  return results
}
```

**Output Format:**

```markdown
| File | Lines | Purpose |
|------|-------|---------|
| `src/auth.ts` | 45-120 | Existing auth patterns |
| `types/user.ts` | 1-30 | Type definitions |
```

**Fallback Strategies:**

- **Line numbers unknown:** Use `1-50` (first 50 lines) or function name search
- **New file type:** Note "New file, no existing reference"
- **Multiple sections:** List multiple entries for same file with different ranges

## Interaction Model

The process explicitly requires a pause after generating parent tasks to get user confirmation ("Go", using AskUserQuestion tool if using Claude Code) before proceeding to generate the detailed sub-tasks. This ensures the high-level plan aligns with user expectations before diving into details.

## Target Audience

Assume the primary reader of the task list is a **senior engineer** who will implement the feature with awareness of the existing codebase context and architectural patterns.

## Testing Strategy Approaches

### Sequential Testing (DEFAULT)

**When to Use:** Most projects (default approach unless PRD explicitly specifies otherwise)

**How it Works:**

- Testing Strategy epic is created and blocks on ALL implementation epics
- Implementation epics complete first, then testing begins
- Simple, straightforward dependency management

**Concrete Example:**

**Epic Structure:**

```
Epic: Core Authentication Architecture
Epic: Authentication Endpoints
Epic: Testing Strategy [blocks: Core Authentication Architecture, Authentication Endpoints]
```

**Result:** Testing epic will NOT appear as ready until both implementation epics are complete.

### Incremental Testing (TDD Approach)

**When to Use:** PRD explicitly requests test-driven development or wants tests written alongside implementation

**How it Works:**

- For each implementation task, create a corresponding test task
- Use `related` dependencies (not blocking) between implementation and test pairs
- Implementation and its tests can be worked on in parallel or sequentially

**Concrete Example:**

**Epic Structure:**

```
Epic: Authentication Endpoints
    ├── Implement login endpoint [parent-child]
    ├── Write tests for login endpoint [parent-child] [related: login endpoint]
    ├── Implement registration endpoint [parent-child]
    └── Write tests for registration endpoint [parent-child] [related: registration endpoint]
```

**Result:** Implementation and test tasks appear together in ready list. Developer can choose to implement first, test first, or work on them in parallel.

### Parallel Testing

**When to Use:** Very simple features, fast iteration needed, PRD explicitly requests minimal testing overhead

**How it Works:**

- No dependencies between testing and implementation
- Both can be worked on immediately
- Fastest iteration, highest risk of integration issues

**Concrete Example:**

**Epic Structure:**

```
Epic: Simple UI Component
    ├── Implement button component [parent-child]
    └── Write tests for button component [parent-child]
```

**Result:** No blocking dependencies - both tasks appear in ready list immediately. Developer can work on them in any order.

## Testing Strategy Decision Matrix

| Approach                | When to Use                           | Dependency Pattern                                 | Ready Tasks Behavior                                                                     |
| ----------------------- | ------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **Sequential testing**  | **DEFAULT** - most projects           | Testing epic `blocks` on all implementation epics  | Implementation tasks appear first, then testing tasks after all implementations complete |
| **Incremental testing** | TDD workflow, PRD explicitly requests | `related` dependencies between impl + test pairs   | Implementation and test tasks appear together                                            |
| **TDD (Test-Driven Development) Approach - DEFAULT:**

When a PRD explicitly requests TDD or indicates test-driven development, use the following approach:

**How it Works:**
- For each implementation task, create a corresponding test task
- Use `related` dependencies (not blocking) between implementation and test pairs
- Implementation and its tests can be worked on in parallel or sequentially
- Tests are written FIRST (before implementation) and will fail initially
- Feature is implemented only when its tests pass
- **Always prioritize test writing** over implementation tasks
- **No implementation task begins without a corresponding test that can validate it

**Task Structure:**
- Epic: Testing Strategy [blocks on ALL implementation epics]
- For each feature task: `Epic: [Feature] Sub-task: Write tests for [Feature]` [related: [Feature implementation]]
- Tests follow the same priority as their implementation counterparts

**When to Use:**
- PRD explicitly requests "TDD approach" or "write tests first" or "test-driven development"
- Project requires strict test-first workflow
- Team wants tests written before implementation

**Behavioral Difference from Sequential/Parallel Testing:**
- Tests appear **before** implementation (not after)
- Tests are **paired** 1:1 with implementation tasks via `related` dependencies
- Ready tasks show both implementation and test tasks together
- Implementation blocked until its corresponding tests pass

**Quality Gate:**
- **ALL tests MUST pass** before any implementation task is marked complete
- Test failures MUST be fixed before continuing to next task
- No feature is considered complete without passing its tests

**Example Dependency Tree:**
```
Epic: Testing Strategy [blocks: Feature Implementation, Database Schema]
    ├── Write tests for authentication flow [parent-child]
    │   └── related: Implement authentication flow [related: auth]
    ├── Write tests for database schema [parent-child]
    │   └── related: Implement database schema [related: db]
    └── blocked by: Write tests for authentication flow
```

**Default Behavior (without explicit TDD request):**
- Use Sequential Testing approach (default behavior)
- Testing epic blocks on all implementation epics

**Autonomous Mode:**
- If invoked from `/flow:autonomous`, auto-detect TDD approach from PRD
- Apply TDD rules without confirmation

**Priority Assignment:**
- Test creation tasks inherit implementation task priority
- Test epics block on implementation epics using blocking dependencies

**Implementation Notes:**
- Developers write failing tests first (RED), then implement to make them pass (GREEN)
- This ensures tests exist for verification during development
- Test failures should be addressed immediately - do not proceed with implementation until tests pass

## Default Behavior

**Use Sequential testing unless the PRD explicitly specifies otherwise.**

When the PRD includes statements like:

- "Follow TDD approach"
- "Write tests alongside implementation"
- "Test-driven development"

Then use Incremental Testing approach with `related` dependencies.

Otherwise, default to Sequential Testing with blocking dependencies.

ULTRATHINK
