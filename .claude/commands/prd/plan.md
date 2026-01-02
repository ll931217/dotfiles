---
description: Generating a Product Requirements Document (PRD)
---

# Rule: Generating a Product Requirements Document (PRD)

## Goal

To guide an AI assistant in creating a detailed Product Requirements Document (PRD) in Markdown format, based on an initial user prompt. The PRD should be clear, actionable, and suitable for a junior developer to understand and implement the feature.

## Process

1.  **Check Prerequisites:** Verify that required tools are installed. Check for: `git`, `gwq`, `bd`.

    For each missing tool, offer to install:

    | Tool  | Check       | Installation                                                                                    |
    | ----- | ----------- | ----------------------------------------------------------------------------------------------- |
    | `git` | `which git` | Use system package manager (e.g., `sudo apt install git`, `brew install git`)                   |
    | `bd`  | `which bd`  | `curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh \| bash` |
    | `gwq` | `which gwq` | Download from latest release, extract, and add to PATH                                          |
    - If any tool is missing, show the installation command and ask user to confirm before running.
    - If user declines installation, warn that some features may not work and ask if they want to continue anyway.
    - Only proceed to step 2 when all tools are available or user explicitly chooses to continue.

2.  **Verify Git Worktree:** Before proceeding, check if the current directory is a Git worktree. If it is not a worktree, warn the user and offer options.
    - **Warning message should include:**
      - An explanation that PRDs are best created in isolated worktrees for better branch/feature management.
    - **Offer 3 choices:**
      1. **Create worktree now** - Ask for a feature name, create the worktree, then instruct user to start a new session:
         ```bash
         gwq add -b feature/<user-provided-name>
         ```
         After creation, tell the user:
         - Exit this Claude Code session
         - Run `gwq exec feature/<name> -- claude` to open Claude Code in the new worktree
         - Then re-run `/prd:plan` to continue
      2. **Continue without worktree** - Proceed with the current directory.
      3. **Exit** - Gracefully exit the process.
    - Example interaction:

      ```
      ⚠️  Not in a git worktree. PRDs work best in isolated worktrees.

      Options:
      a) Create worktree now (recommended)
      b) Continue without worktree
      c) Exit

      > a
      Enter feature name: auth

      ✓ Created worktree: feature/auth

      To continue in the new worktree:
      1. Exit this Claude Code session (Ctrl+C or type 'exit')
      2. Run: gwq exec feature/auth -- claude
      3. Then run: /prd:plan

      Goodbye!
      ```

2.5 **Detect Git Context:** Gather git metadata for the PRD frontmatter.
    - Detect current branch name using `git rev-parse --abbrev-ref HEAD`
    - Determine if in a worktree by comparing `--git-dir` vs `--git-common-dir`
    - Get worktree name from branch or directory
    - Capture commit SHA, author, and timestamp
    - Store all context for frontmatter generation

    **Detection Commands:**
    ```bash
    # Branch name
    BRANCH=$(git rev-parse --abbrev-ref HEAD)

    # Worktree detection
    GIT_DIR=$(git rev-parse --git-dir)
    GIT_COMMON_DIR=$(git rev-parse --git-common-dir)
    IS_WORKTREE=$([ "$GIT_DIR" != "$GIT_COMMON_DIR" ] && echo "true" || echo "false")

    # Worktree name (from git worktree list or branch)
    if [ "$IS_WORKTREE" = "true" ]; then
      WORKTREE_NAME=$(git worktree list --porcelain | grep -A1 "^$(git rev-parse --show-toplevel)$" | tail -1 | sed 's/^branch //' | sed 's|refs/heads/||')
      WORKTREE_PATH="$GIT_DIR"
    else
      WORKTREE_NAME="main"
      WORKTREE_PATH=""
    fi

    # Branch type categorization
    case "$BRANCH" in
      main|master) BRANCH_TYPE="main" ;;
      develop|dev) BRANCH_TYPE="develop" ;;
      feature/*) BRANCH_TYPE="feature" ;;
      bugfix/*|fix/*) BRANCH_TYPE="bugfix" ;;
      hotfix/*) BRANCH_TYPE="hotfix" ;;
      *) BRANCH_TYPE="other" ;;
    esac

    # Commit info
    COMMIT_SHA=$(git rev-parse HEAD)
    AUTHOR_NAME=$(git log -1 --format="%an" HEAD)
    AUTHOR_EMAIL=$(git log -1 --format="%ae" HEAD)
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    REPO_ROOT=$(git rev-parse --show-toplevel)
    ```

3.  **Receive Initial Prompt:** The user provides a brief description or request for a new feature or functionality.
4.  **Ask Clarifying Questions:** Before writing the PRD, the AI _must_ ask clarifying questions to gather sufficient detail. The goal is to understand the "what" and "why" of the feature, not necessarily the "how" (which the developer will figure out). Make sure to provide options in letter/number lists so I can respond easily with my selections.
    - Ask **3-5 clarifying questions at a time** to avoid overwhelming the user. Prioritize the most critical unknowns first.
    - Use the AskUserQuestions tool, this provides a better user experience. (NOTE: Only available with Claude Code)
5.  **Generate PRD:** Based on the initial prompt and the user's answers to the clarifying questions, generate a PRD using the structure outlined below.
6.  **Save PRD Draft:**
    - Generate YAML frontmatter with detected git context
    - Append generated PRD content after frontmatter
    - Save as `prd-[feature-name]-v1.md` inside the `/.flow` directory

    **Frontmatter Format:**
    ```yaml
    ---
    prd:
      version: v1
      feature_name: [derived from filename]
      status: draft
    git:
      branch: [detected branch name]
      branch_type: [feature/bugfix/main/etc]
      created_at_commit: [current commit SHA]
      updated_at_commit: [current commit SHA]
    worktree:
      is_worktree: [true/false]
      name: [worktree name or "main"]
      path: [worktree .git path or empty]
      repo_root: [repository root path]
    metadata:
      created_at: [ISO 8601 timestamp]
      updated_at: [ISO 8601 timestamp]
      created_by: [git user.name <user.email>]
      filename: [prd-name-v1.md]
    beads:
      related_issues: []
      related_epics: []
    ---
    ```

    **Example Frontmatter:**
    ```yaml
    ---
    prd:
      version: v1
      feature_name: authentication
      status: draft
    git:
      branch: feature/auth
      branch_type: feature
      created_at_commit: abc123def4567890
      updated_at_commit: abc123def4567890
    worktree:
      is_worktree: true
      name: feature-auth
      path: /home/user/project/.git/worktrees/feature-auth
      repo_root: /home/user/project
    metadata:
      created_at: 2025-01-02T10:30:00Z
      updated_at: 2025-01-02T10:30:00Z
      created_by: John Doe <john@example.com>
      filename: prd-authentication-v1.md
    beads:
      related_issues: []
      related_epics: []
    ---
    ```

    **Important:** The variables collected in step 2.5 should be used to populate the frontmatter. The feature_name should be derived from the filename (e.g., `prd-authentication.md` → `authentication`).
7.  **PRD Review & Approval Cycle:**

- Present the draft PRD to the user with the PRD Review Checklist (see section below)
- **Use AskUserQuestion to request approval:**
  - Question: "Does this PRD meet your requirements?"
  - Options:
    - "Yes" (Approve PRD and proceed to task generation)
    - "No" (Restart from clarifying questions)
    - "Changes" (Collect feedback and revise)
- **If "Yes":**
  - Update PRD status in frontmatter from `draft` to `approved`
  - Add initial changelog entry (version 1)
  - Proceed to task generation (user will invoke `/prd:generate-tasks`)
- **If "No":**
  - Restart from clarifying questions (step 4)
- **If "Changes":**
  - Collect specific feedback on what needs to change
  - **Increment version number in frontmatter** (`version: 1` → `version: 2`)
  - **Update the same PRD file** (no new file created)
  - Update `updated_at` timestamp and `updated_at_commit`
  - **Add entry to changelog** at bottom of PRD
  - Present revised PRD and repeat approval cycle
- **Critical:** Do NOT proceed to task generation without explicit approval

**PRD Update Process (when changes are requested):**
```bash
# Read current version
CURRENT_VERSION=$(grep "^  version:" "$PRD_FILE" | awk '{print $2}')
NEW_VERSION=$((CURRENT_VERSION + 1))

# Update version in frontmatter
sed -i "s/^  version: $CURRENT_VERSION/  version: $NEW_VERSION/" "$PRD_FILE"

# Update timestamps and commit
sed -i "s/updated_at: .*/updated_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")/" "$PRD_FILE"
sed -i "s/updated_at_commit: .*/updated_at_commit: $(git rev-parse HEAD)/" "$PRD_FILE"

# Add entry to changelog
NEW_CHANGELOG_ENTRY="| $NEW_VERSION | $(date -u +"%Y-%m-%d %H:%M") | [Summary of changes] |"
# Insert this entry in the changelog table
```

**PRD Iteration Workflow (when editing existing approved/implemented PRD):**

When the user edits an existing PRD that has status `approved` or `implemented`:

1. **Reset status to `draft`**: The updated PRD needs re-approval
2. **Increment version**: Add new version number
3. **Add changelog entry**: Document the changes
4. **Archive existing tasks**: Mark old tasks as superseded
5. **Prompt to regenerate**: Offer to run `/prd:generate-tasks`

```bash
# Check current status before updating PRD
CURRENT_STATUS=$(grep "^  status:" "$PRD_FILE" | awk '{print $2}')

# If approved or implemented, handle iteration workflow
if [ "$CURRENT_STATUS" = "approved" ] || [ "$CURRENT_STATUS" = "implemented" ]; then
  # Reset to draft
  sed -i "s/^  status: $CURRENT_STATUS/  status: draft/" "$PRD_FILE"

  # Get current version and increment
  CURRENT_VERSION=$(grep "^  version:" "$PRD_FILE" | awk '{print $2}')
  NEW_VERSION=$((CURRENT_VERSION + 1))
  sed -i "s/^  version: $CURRENT_VERSION/  version: $NEW_VERSION/" "$PRD_FILE"

  # Update timestamp
  sed -i "s/^  updated_at: .*/  updated_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")/" "$PRD_FILE"
  sed -i "s/^  updated_at_commit: .*/  updated_at_commit: $(git rev-parse HEAD)/" "$PRD_FILE"

  # Archive related tasks
  archive_prd_tasks "$PRD_FILE"

  # Add changelog entry
  CHANGELOG_ENTRY="| $NEW_VERSION | $(date -u +"%Y-%m-%d %H:%M") | PRD updated - status reset to draft, tasks archived |"
  sed -i "/^| Version |/a $CHANGELOG_ENTRY" "$PRD_FILE"

  echo "⚠️  PRD updated - status reset to draft"
  echo "   Existing tasks have been archived"
  echo "   Run '/prd:generate-tasks' to create new tasks"
fi
```

**Archive function for old tasks:**

```bash
# Archive all tasks related to a PRD
archive_prd_tasks() {
  local prd_file="$1"

  # Get related issues
  local related_issues=$(grep -A2 "^beads:" "$prd_file" | grep "related_issues:" | sed 's/.*: \[\(.*\)\]/\1/')
  related_issues=$(echo "$related_issues" | tr -d '[]",' | tr ' ' '\n' | grep -v '^$')

  local archived_count=0
  for issue in $related_issues; do
    if bd show "$issue" >/dev/null 2>&1; then
      # Add "superseded" label and close
      bd label add "$issue" superseded 2>/dev/null || true
      bd close "$issue" 2>/dev/null || true
      archived_count=$((archived_count + 1))
    fi
  done

  # Clear related_issues from PRD
  sed -i 's/^  related_issues: .*/  related_issues: []/' "$prd_file"
  sed -i 's/^  related_epics: .*/  related_epics: []/' "$prd_file"

  echo "   Archived $archived_count tasks from previous PRD version"
}
```

**Auto-Regeneration Prompt:**

After PRD update and archival, prompt the user:

```
✅ PRD Updated Successfully!

Changes:
- Status: approved → draft (needs re-approval)
- Version: N → N+1
- Previous tasks: archived (X tasks closed with "superseded" label)

Next Steps:
1. Review your updated PRD content
2. Run /prd:generate-tasks to create new tasks from updated requirements
3. Approve the PRD to begin implementation

Would you like to run /prd:generate-tasks now? [Y/n]
```

If user confirms, automatically invoke the generate-tasks workflow.

8.  **Changelog:**

Each PRD includes a changelog section at the bottom tracking all versions:

  ```markdown
  ## Changelog

  | Version | Date             | Summary of Changes                    |
  | ------- | ---------------- | ------------------------------------- |
  | 3       | 2025-01-03 09:15 | Clarified file upload limits           |
  | 2       | 2025-01-02 14:30 | Added Admin role permissions          |
  | 1       | 2025-01-02 10:30 | Initial PRD approved                  |
  ```

9.  **Task Tracking Reference:** After PRD approval, the user will invoke `/prd:generate-tasks` to create implementation tasks using beads. The PRD file will be referenced in all task descriptions.
10. **Review & Refine (Deprecated):** The approval workflow in step 7 now handles PRD review. Proceed to task generation after approval.

## Clarifying Questions

The AI should adapt its questions based on the prompt. Group questions into categories to systematically cover all areas:

### Business Context

- **Problem/Goal:** "What problem does this feature solve for the user?" or "What is the main goal we want to achieve with this feature?"
- **Target User:** "Who is the primary user of this feature?"
- **Priority/Timeline:** "What is the priority or target timeline for this feature?"
- **Similar Features:** "Are there any existing features similar to this we should reference?"

### Functional Scope

- **Core Functionality:** "Can you describe the key actions a user should be able to perform with this feature?"
- **User Stories:** "Could you provide a few user stories? (e.g., As a [type of user], I want to [perform an action] so that [benefit].)"
- **Acceptance Criteria:** "How will we know when this feature is successfully implemented? What are the key success criteria?"
- **Scope/Boundaries:** "Are there any specific things this feature _should not_ do (non-goals)?"
- **Edge Cases:** "Are there any potential edge cases or error conditions we should consider?"

### Technical Context

- **Data Requirements:** "What kind of data does this feature need to display or manipulate?"
- **Existing Systems:** "Are there existing systems, APIs, or modules this should integrate with?"
- **Constraints:** "Are there any known technical constraints or dependencies?"

### UX/Design

- **Design/UI:** "Are there any existing design mockups or UI guidelines to follow?" or "Can you describe the desired look and feel?"
- **Accessibility:** "Are there accessibility requirements to consider?"
- **Responsive/Mobile:** "Does this need to work on mobile or different screen sizes?"

### Non-Functional Requirements

- **Performance:** "Are there any performance requirements or expectations?"
- **Security/Privacy:** "Are there security or privacy considerations?"
- **Internationalization:** "Does this need to support multiple languages?"

## PRD Review Checklist

When presenting a PRD for review, verify all items are complete:

- [ ] **Clarity:** All clarifying questions have been addressed in the PRD
- [ ] **Business Goals:** Goals are clear, specific, and measurable
- [ ] **User Stories:** Stories follow format "As a [user], I want [action], so that [benefit]"
- [ ] **Functional Requirements:** Requirements are unambiguous and testable
- [ ] **Non-Goals:** Out-of-scope items are clearly defined
- [ ] **Acceptance Criteria:** Criteria are specific, measurable, and testable
- [ ] **Dependencies:** All external dependencies are documented
- [ ] **Technical Constraints:** Technical limitations are reasonable given codebase
- [ ] **Risks:** Potential blockers have been identified with mitigation strategies
- [ ] **Success Metrics:** Success can be objectively measured

### Approval Process

1. Present PRD draft with checklist completed
2. User reviews checklist and PRD content
3. User responds with: "Yes" (approve), "Changes: [feedback]" (revise), or "No" (restart)
4. Iterate until "Yes" is received
5. Create history file and mark approved

## Approval Workflow

```
Initial Prompt
     ↓
Ask 3-5 Clarifying Questions
     ↓
Generate PRD v1
     ↓
Present for Review + Checklist
     ↓
     ├─ Yes → Create History File → Ready for Task Generation
     │
     ├─ No → Restart from Clarifying Questions
     │
     └─ Changes: [feedback]
           ↓
           Update PRD (v1 → v2)
           ↓
           Present for Review + Checklist
           └─ (loop until Yes)
```

**Important:** Do not proceed to `/prd:generate-tasks` until explicit approval is received.

## PRD Structure

The generated PRD should include the following sections:

1.  **Introduction/Overview:** Briefly describe the feature and the problem it solves. State the goal.
2.  **Goals:** List the specific, measurable objectives for this feature.
3.  **User Stories:** Detail the user narratives describing feature usage and benefits.
4.  **Functional Requirements:** List the specific functionalities the feature must have. Use clear, concise language (e.g., "The system must allow users to upload a profile picture."). Number these requirements.
5.  **Non-Goals (Out of Scope):** Clearly state what this feature will _not_ include to manage scope.
6.  **Assumptions:** Document what you're taking for granted (e.g., "User is already authenticated").
7.  **Dependencies:** List any features, systems, or APIs this feature relies on.
8.  **Acceptance Criteria:** Detailed, testable criteria for each functional requirement.
9.  **Design Considerations (Optional):** Link to mockups, describe UI/UX requirements, or mention relevant components/styles if applicable.
10. **Technical Considerations (Optional):** Mention any known technical constraints, dependencies, or suggestions (e.g., "Should integrate with the existing Auth module").
11. **Risks & Mitigations:** Identify potential blockers and how to address them.
12. **Success Metrics:** How will the success of this feature be measured? (e.g., "Increase user engagement by 10%", "Reduce support tickets related to X").
13. **Priority/Timeline:** Indicate urgency or target release if known.
14. **Open Questions:** List any remaining questions or areas needing further clarification.
15. **Glossary (Optional):** Define technical terms, especially helpful for junior developers.
16. **Changelog:** A table tracking all PRD versions with dates and change summaries.

## Complexity Guidance

- **Simple features:** Keep the PRD concise (1-2 pages). Focus on core sections.
- **Complex features:** Be more thorough (3-5 pages). Include all optional sections.

## Target Audience

Assume the primary reader of the PRD is a **junior developer**. Therefore, requirements should be explicit, unambiguous, and avoid jargon where possible. Provide enough detail for them to understand the feature's purpose and core logic.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/.flow/`
- **Filename Pattern:** `prd-[feature-name].md` (single file, version tracked in frontmatter)
- **History:** Tracked in changelog section at bottom of PRD file

## Task Tracking

After the PRD is approved, invoke `/prd:generate-tasks` to create and track implementation tasks using the beads tool.

All task management is handled through beads integration - no separate task files needed.

## Final instructions

1. Do NOT start implementing the PRD
2. Make sure to ask the user clarifying questions (3-5 at a time)
3. Take the user's answers to the clarifying questions and improve the PRD
4. Use the beads tool (`read_todos`/`write_todos`) for task tracking
5. If the user is satisfied with the PRD, suggest the user to use `/prd:generate-tasks` command
6. ULTRATHINK
