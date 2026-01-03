---
description: Generate tasks in beads (`bd`)
---

# Rule: Generating Issues from a PRD using Beads

## Goal

To guide an AI assistant in creating a detailed, step-by-step issue hierarchy using the `bd` (beads) tool based on an existing Product Requirements Document (PRD). The issues should guide a developer through implementation with proper dependency tracking.

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

- **Format:** Beads issues in `.beads/` database
- **Tool:** `bd` (beads dependency-aware issue tracker)

## Prerequisites

Ensure beads is initialized in the project. If not, initialize beads.

## Process

1. **Auto-Discover PRD:** Automatically find the appropriate PRD based on git context.
   - **Stage 1 - Latest PRD Check:**
     - Find the most recently modified PRD in `/.flow/` directory
     - Read its YAML frontmatter
     - Extract branch, worktree name, and worktree path

   - **Stage 2 - Context Validation:**
     - Detect current git context (branch, worktree)
     - Compare current context with PRD metadata
     - **Match criteria:** ALL of the following must match
       - Branch name matches exactly (or both are main/master)
       - Worktree name matches (if both in worktrees)
       - Worktree path matches (if both in worktrees)

   - **Stage 3 - Fallback Search:**
     - If latest PRD doesn't match, search all PRDs in `/.flow/`
     - For each PRD, check if metadata matches current context
     - Return first matching PRD

   - **Stage 4 - No Match Found:**
     - If no PRD matches current context, inform user
     - List available PRDs with their metadata
     - Offer options:
       a) Create new PRD (run `/prd:plan`)
       b) Select existing PRD manually
       c) Exit

   **Discovery Commands:**

   ```bash
   # Find latest PRD
   LATEST_PRD=$(find /.flow -name "prd-*.md" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

   # Extract branch from PRD frontmatter
   PRD_BRANCH=$(grep -A5 "^git:" "$LATEST_PRD" | grep "branch:" | awk '{print $2}' | tr -d '"')

   # Get current branch
   CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

   # Check worktree
   PRD_WORKTREE_PATH=$(grep -A5 "^worktree:" "$LATEST_PRD" | grep "path:" | awk '{print $2}' | tr -d '"')
   CURRENT_WORKTREE=$(if [ "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" ]; then git rev-parse --git-dir; else echo ""; fi)

   # Validate match
   if [ "$PRD_BRANCH" = "$CURRENT_BRANCH" ] && [ "$PRD_WORKTREE_PATH" = "$CURRENT_WORKTREE" ]; then
     echo "Match found: $LATEST_PRD"
   else
     echo "Searching for matching PRD..."
   fi
   ```

   **User Interaction Example:**

   ```
   ⚠️  No PRD found matching current context

   Current Context:
   - Branch: feature/user-auth
   - Worktree: /home/user/project/.git/worktrees/feature-user-auth

   Available PRDs:
   - prd-authentication-v1.md (branch: main, worktree: none)
   - prd-user-profile-v2.md (branch: feature/profile, worktree: /home/user/project/.git/worktrees/feature-profile)

   Options:
   a) Create new PRD with /prd:plan
   b) Use existing PRD (specify which)
   c) Exit
   ```

   **After PRD Discovery:**
   - Display discovered PRD with its metadata
   - Ask for confirmation: "Using PRD: [name] (branch: [branch], version: [vN])"
   - Proceed with step 2 (Analyze PRD)

2. **Analyze PRD:** The AI reads and analyzes the functional requirements, user stories, and other sections of the specified PRD.

3. **Check Existing Beads Tasks (Update Detection):**
   Before generating new tasks, check if tasks already exist for this PRD context.
   - **Step 3a - Query Beads for Existing Tasks:**

     ```bash
     # Get all issues in beads database
     bd list --format json

     # Filter issues by current git context (branch/worktree)
     # Issues may have PRD reference in description or tags
     ```

   - **Step 3b - Identify Related Issues:**
     - Look for issues that reference this PRD by:
       - Checking PRD filename in issue descriptions
       - Checking PRD version in issue descriptions
       - Checking `beads.related_issues` or `beads.related_epics` in PRD frontmatter
     - Extract issue IDs and their status from PRD frontmatter:
       ```yaml
       beads:
         related_issues: [proj-123, proj-456, proj-789]
         related_epics: [proj-001, proj-002]
       ```

   - **Step 3c - Compare PRD Version:**
     - Compare current PRD `updated_at_commit` with existing task creation time
     - Determine if PRD has been significantly updated:

       ```bash
       # Get commit when tasks were last generated
       PRD_UPDATED_COMMIT=$(grep "^  updated_at_commit:" "$PRD_FILE" | awk '{print $2}')

       # Get current HEAD commit
       CURRENT_COMMIT=$(git rev-parse HEAD)

       # Check if there are new commits since last task generation
       if [ "$PRD_UPDATED_COMMIT" != "$CURRENT_COMMIT" ]; then
         # Check if PRD file itself was modified
         git log "$PRD_UPDATED_COMMIT..HEAD" --oneline "$PRD_FILE" | grep -q .
         if [ $? -eq 0 ]; then
           echo "PRD has been updated since last task generation"
         fi
       fi
       ```

   - **Step 3d - Update Strategy Decision:**
     Present options to user based on existing tasks:

     ```
     ℹ️  Found existing tasks for this PRD:
     - PRD: prd-authentication.md (version: 2)
     - Last updated: commit abc123d (2025-01-02)
     - Existing epics: 3
     - Existing tasks: 15

     Options:
     a) Review and update existing tasks (keep completed tasks, update pending ones)
     b) Regenerate all tasks (archive existing, create new from scratch)
     c) Show diff of PRD changes to understand what needs updating
     d) Cancel
     ```

   - **Step 3e - Intelligent Task Update:**
     If user chooses option (a) "Review and update":
     - Parse existing issues from beads using `bd show <issue-id>`
     - Compare existing issue descriptions with PRD requirements
     - Identify:
       - Completed tasks - mark as done, don't regenerate
       - Obsolete tasks - mark for archival or deletion
       - New requirements - generate new tasks
       - Modified requirements - update existing task descriptions

     **Update Logic:**

     ```bash
     # For each existing epic
     for epic_id in "${existing_epics[@]}"; do
       epic_status=$(bd show "$epic_id" | grep "Status:" | awk '{print $2}')

       if [ "$epic_status" = "done" ]; then
         # Skip - epic already completed
         continue
       fi

       # Check if epic still relevant to updated PRD
       # If yes: keep and potentially update description
       # If no: mark as obsolete
     done
     ```

   - **Step 3f - No Existing Tasks:**
     If `beads.related_issues` and `beads.related_epics` are empty or null:
     - Proceed to full task generation (skip to step 4)
     - This is a fresh PRD or first-time task generation

4. **Assess Current State:** Review the existing codebase to understand existing infrastructure, architectural patterns and conventions. Also, identify any existing components or features that already exist and could be relevant to the PRD requirements. Then, identify existing related files, components, and utilities that can be leveraged or need modification.

5. **Phase 1: Generate Parent Issues (Epics) - For New or Updated Requirements Only:**
   - If this is a fresh PRD (no existing tasks): Generate all parent epics as before
   - If this is an updated PRD: Only generate NEW or MODIFIED epics
   - Skip generation of completed/unchanged epics

   **Generation Strategy for Updates:**
   - Compare PRD requirements with existing epic descriptions
   - For each requirement area:
     - If matching epic exists and is incomplete: Update description
     - If matching epic exists and is done: Skip
     - If no matching epic exists: Create new epic
   - Present both existing (kept) and new epics to user for review

   Based on the PRD analysis and current state assessment, create the main, high-level issues required to implement the feature. Use your judgement on how many high-level issues to use. It's likely to be about 5. These parent issues should each be full features that can be tested where the user will only proceed to next parent issue until satisfied. Present these issues to the user. Inform the user (Using AskUserQuestion tool): "I have generated the high-level issues based on the PRD. Ready to generate the sub-issues? Respond with 'Go' to proceed."

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

7. **Wait for Confirmation:** Pause and wait for the user to respond with "Go".

8. **Phase 2: Generate Sub-Issues - For New or Updated Epics Only:** Once the user confirms, break down each parent issue into smaller, actionable sub-issues necessary to complete the parent issue. Ensure sub-issues logically follow from the parent issue, cover the implementation details implied by the PRD, and consider existing codebase patterns where relevant without being constrained by them.

   **For updated PRDs:** Only generate sub-issues for epics that are new or modified. Skip sub-issue generation for completed/unchanged epics.

9. **Phase 3: Intelligent Parallel Issue Analysis and Dependencies**
   - **Phase 3a - File Dependency Analysis:** For each sub-issue, identify all files that will be created, modified, or read. Include this in the issue description.
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

10. **Task Priority Inheritance:** When creating sub-issues, assign priorities based on inheritance rules:
    - **Default Rule:** Sub-tasks inherit parent epic priority
    - **Exception 1:** Documentation tasks default to P3 unless epic is P0
    - **Exception 2:** Refactoring tasks default to P3 unless epic is P0
    - **User Override:** User can specify different priority if needed

11. **Add Relevant Files to Issue Descriptions:** When creating issues, include the relevant files in the issue description.

12. **Merge Updated Issues with Existing Issues:**
    - For updated PRDs: Merge newly created issues with existing kept issues
    - Update PRD frontmatter with combined issue list (kept + new)
    - Ensure dependencies are correctly set between old and new issues
    - Archive obsolete issues if user chose option (b) "Regenerate all"

13. **Verify Issue Structure:** After creating all issues, verify the structure using beads to view issues, dependency trees, and ready tasks.

14. **Update PRD Metadata:** After creating beads issues, update the PRD frontmatter.
    - Update `updated_at` timestamp
    - Update `updated_at_commit` with current commit SHA
    - Add newly created issue IDs to `beads.related_issues`
    - Add epic IDs to `beads.related_epics`
    - Change status from `draft` to `approved` if not already (only if current status is draft)

    **Update Commands:**

    ```bash
    # Update timestamp and commit
    sed -i "s/^  updated_at: .*/  updated_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")/" "$PRD_FILE"
    sed -i "s/^  updated_at_commit: .*/  updated_at_commit: $(git rev-parse HEAD)/" "$PRD_FILE"

    # Update status (only if currently draft)
    CURRENT_STATUS=$(grep "^  status:" "$PRD_FILE" | awk '{print $2}')
    if [ "$CURRENT_STATUS" = "draft" ]; then
      sed -i 's/^  status: draft/  status: approved/' "$PRD_FILE"
      echo "✓ PRD status updated: draft → approved"
    else
      echo "  PRD status is '$CURRENT_STATUS' - leaving as-is"
    fi

    # Note: Adding issue IDs to beads section requires parsing the output
    # of bd create commands or using a YAML parser like yq
    ```

    **Example Updated Frontmatter:**

    ```yaml
    ---
    prd:
      version: 1
      feature_name: authentication
      status: approved # Changed from draft
    git:
      branch: feature/auth
      branch_type: feature
      created_at_commit: abc123def4567890
      updated_at_commit: def789ghi0123456 # Updated
    worktree:
      is_worktree: true
      name: feature-auth
      path: /home/user/project/.git/worktrees/feature-auth
      repo_root: /home/user/project
    metadata:
      created_at: 2025-01-02T10:30:00Z
      updated_at: 2025-01-02T14:45:00Z # Updated
      created_by: John Doe <john@example.com>
      filename: prd-authentication.md
    beads:
      related_issues: [proj-123, proj-456, proj-789] # Added
      related_epics: [proj-001, proj-002] # Added
    ---
    ```

15. Once all tasks are completed, suggest to the user to use the `/prd:implement` slash command

## Issue Structure

Issues are stored in the `.beads/` database with the following hierarchy:

### Epic (Parent Issue)

High-level issue grouping multiple related tasks. Should include:

- Epic description with clear purpose
- Files to be created/modified
- Reference to PRD version

### Task (Sub-Issue)

Individual actionable tasks that complete epic requirements. Should include:

- Task description with specific deliverable
- Files to be created/modified
- Link to parent epic (parent-child relationship)

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

## Interaction Model

The process explicitly requires a pause after generating parent tasks to get user confirmation ("Go", using AskUserQuestion tool if using Claude Code) before proceeding to generate the detailed sub-tasks. This ensures the high-level plan aligns with user expectations before diving into details.

## Target Audience

Assume the primary reader of the task list is a **junior developer** who will implement the feature with awareness of the existing codebase context.

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
| **Parallel testing**    | Very simple features, fast iteration  | No dependencies between testing and implementation | All tasks appear immediately                                                             |

## Default Behavior

**Use Sequential testing unless the PRD explicitly specifies otherwise.**

When the PRD includes statements like:

- "Follow TDD approach"
- "Write tests alongside implementation"
- "Test-driven development"

Then use Incremental Testing approach with `related` dependencies.

Otherwise, default to Sequential Testing with blocking dependencies.

ULTRATHINK
