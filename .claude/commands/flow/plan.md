---
description: Generating a Product Requirements Document (PRD)
---

# Rule: Generating a Product Requirements Document (PRD)

## Goal

To guide an AI assistant in creating a detailed Product Requirements Document (PRD) in Markdown format, based on an initial user prompt. The PRD should be clear, actionable, and suitable for a junior developer to understand and implement the feature.

## Process

1.  **Check Prerequisites:** Verify that required tools are installed. Check for: `git` (required), `wt` (optional), `bd` (optional).

    For each missing optional tool, offer to install:

    | Tool  | Check       | Installation                                                                                                                              |
    | ----- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
    | `git` | `which git` | Use system package manager (e.g., `sudo apt install git`, `brew install git`)                                                             |
    | `bd`  | `which bd`  | `curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh \| bash` (optional - TodoWrite fallback available) |
    | `wt`  | `which wt`  | `brew install max-sixty/worktrunk/wt` OR `cargo install worktrunk` (optional - git fallback available)                                    |
    - Only `git` is required.
    - If `wt` is missing, the AI will use native git worktree commands.
    - If `bd` is missing, the AI will use the internal TodoWrite tool for task tracking.

⚠️ **Warning about beads (bd):**
Without beads installed, task context may be lost between sessions. Beads provides:

- Persistent task storage across sessions
- Dependency tracking between tasks
- Better visibility into progress and blockers
- Integration with PRD frontmatter for traceability

Consider installing beads for the best experience, especially for larger features with many tasks.

2.  **Verify Git Worktree:** Before proceeding, check if the current directory is a Git worktree. If it is not a worktree, warn the user and offer options.
    - **Warning message should include:**
      - An explanation that PRDs are best created in isolated worktrees for better branch/feature management.
    - **Use AskUserQuestion to offer 3 choices:**

      ```
      AskUserQuestion({
        questions: [
          {
            question: "PRDs work best in isolated worktrees for better branch/feature management. What would you like to do?",
            header: "Worktree",
            options: [
              {
                label: "Create worktree",
                description: "Create a new git worktree and continue PRD planning there (recommended)"
              },
              {
                label: "Continue without worktree",
                description: "Proceed with PRD planning in the current directory"
              },
              {
                label: "Exit",
                description: "Exit the PRD planning process"
              }
            ],
            multiSelect: false
          }
        ]
      })
      ```

      - **If user selects "Create worktree":**
        The AI will:
        - Ask for a feature name using AskUserQuestion (or allow free text input for custom names)
        - Check if `wt` (worktrunk) is installed
        - If `wt` is available: Use `wt switch -c -x claude feature/<name>` to create and start Claude
        - If `wt` is NOT available: Use `git worktree add -b feature/<name> ../repo.<name>` and save the prompt to a file

        **With worktrunk (wt) installed:**
        The AI will create the worktree and launch Claude automatically:

        ```bash
        wt switch -c -x claude feature/<name>
        ```

        **Without worktrunk (git fallback):**
        The AI will:
        1. Create the worktree: `git worktree add -b feature/<name> ../repo.<name>`
        2. Capture the worktree path: `WORKTREE_PATH=$(git worktree list --porcelain | grep "worktree" | tail -1 | cut -d' ' -f2)`
        3. Save the current prompt to: `/tmp/prd-prompt-<timestamp>.txt`
        4. Include worktree context in the prompt file:
           ```
           # Worktree Context
           WORKTREE_PATH="<path-to-new-worktree>"
           FEATURE_NAME="<name>"
           ```
        5. Instruct user to:
           - Exit this Claude Code session
           - Navigate to the new worktree: `cd <WORKTREE_PATH>`
           - Open Claude Code in the new directory
           - Read the prompt file to restore context
           - Continue with `/flow:plan` (which will detect existing worktree and skip creation)

        Example prompt file:

        ```
        # PRD Planning Prompt Saved from Previous Session

        # Worktree Context
        WORKTREE_PATH="/home/user/worktrees/github.com/user/repo/feature-auth"
        FEATURE_NAME="auth"

        Your feature name: auth

        To continue planning your PRD:
        1. You're now in the new worktree created for this feature
        2. Re-run the /flow:plan command to continue (it will skip worktree creation)
        3. Answer the clarifying questions again

        [Original prompt context preserved]
        ```

      - **If user selects "Continue without worktree":** Proceed with the current directory.

      - **If user selects "Exit":** Gracefully exit the process.

**Worktree Context Tracking:**

When a new worktree is created, the AI must track the worktree path for subsequent PRD saving:

- **Variable to track:** `NEW_WORKTREE_PATH`
- **Set when:** User selects "Create worktree" and worktree is successfully created
- **Used by:** Step 6 (Save PRD Draft) to determine save location

**With worktrunk:**
```bash
# After worktree creation, NEW_WORKTREE_PATH is already the current directory
# No additional tracking needed - git rev-parse --show-toplevel returns new worktree
```

**Without worktrunk:**
```bash
# Store the new worktree path for later use
NEW_WORKTREE_PATH="../repo.<name>"  # or actual path from git worktree add output

# Also save to prompt file for user's new session
echo "NEW_WORKTREE_PATH=\"$NEW_WORKTREE_PATH\"" >> /tmp/prd-prompt-<timestamp>.txt
```

2.5 **Detect Git Context:** Gather git metadata for the PRD frontmatter. - Detect current branch name using `git rev-parse --abbrev-ref HEAD` - Determine if in a worktree by comparing `--git-dir` vs `--git-common-dir` - Get worktree name from branch or directory - Capture commit SHA, author, and timestamp - Store all context for frontmatter generation

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

2.75 **Check for Existing PRD (Iteration Detection):**
After detecting git context, check if a PRD already exists for this context: - Search `/.flow/` directory for PRD files (`prd-*.md`) - For each PRD found, read its frontmatter - Compare `git.branch`, `worktree.name`, and `worktree.path` with current context - **Match criteria:** ALL of the following must match - Branch name matches exactly (or both are main/master) - Worktree name matches (if both in worktrees) - Worktree path matches (if both in worktrees)

    **If existing PRD is found (iteration mode):**
    - Display message: `Found existing PRD: [filename] (version: N, status: [status])`
    - Explain: "I'll iterate on this existing PRD. When you provide your updates, I'll increment the version and update the content."
    - Store the existing PRD path and version for later use in step 6

    **If no existing PRD is found (new PRD mode):**
    - Display message: "No existing PRD found for this context. Creating a new PRD."
    - Proceed to create a new PRD file

2.76 **Session State Management:**

When creating a new worktree, the AI must maintain state across the session:

**State Variables:**
- `WORKTREE_CREATED`: Boolean flag indicating if worktree was created this session
- `NEW_WORKTREE_PATH`: Path to the newly created worktree (if applicable)
- `ORIGINAL_DIRECTORY`: Original directory before worktree creation (for fallback)

**State Preservation:**
- With worktrunk: State is implicit - new Claude session in new worktree
- Without worktrunk: State is written to prompt file for user's new session

**Usage:**
- Step 6 (Save PRD Draft) checks these variables to determine save location
- Ensures PRD is saved in the correct worktree regardless of creation method

3.  **Receive Initial Prompt:** The user provides a brief description or request for a new feature or functionality.
4.  **Ask Clarifying Questions:** Before writing the PRD, the AI _must_ ask clarifying questions using the AskUserQuestion tool. This provides an interactive UI where users can select options with keyboard navigation (arrow keys or number keys).
    - Ask **3-5 clarifying questions at a time** to avoid overwhelming the user. Prioritize the most critical unknowns first.
    - **Always use the AskUserQuestion tool** - do NOT use letter/number lists
    - Each question should have 2-4 options with clear descriptions
    - Use multiSelect=true for questions where multiple options can be selected

4.5 **Priority Inference & Collection:** After gathering clarifying answers, infer and collect priorities for each functional requirement.

    **Inference Process:**
    1. AI analyzes each requirement/user story from the clarifying responses
    2. Detects priority level (P0-P4) based on keyword triggers and context
    3. Assigns confidence level (high/medium/low) to each inference
    4. Records rationale for the priority assignment

    **User Confirmation:**
    1. Present inferred priorities in a structured format:
       ```
       Inferred Priorities:
       ┌─────────┬────────────────────────────────┬───────────┬────────────┐
       │ ID      │ Requirement                    │ Priority  │ Confidence │
       ├─────────┼────────────────────────────────┼───────────┼────────────┤
       │ FR-1    │ User authentication            │ P1 (High) │ High       │
       │ FR-2    │ Password reset                │ P2 (Norm) │ Medium     │
       └─────────┴────────────────────────────────┴───────────┴────────────┘
       ```
    2. Ask user to confirm or adjust each priority
    3. Store user-confirmed priorities in frontmatter `priorities.requirements` array

    **Default Handling:**
    - If user doesn't specify, use `default: P2` from frontmatter
    - Mark with `confidence: low` and `user_confirmed: false`

5.  **Generate PRD:** Based on the initial prompt and the user's answers to the clarifying questions, generate a PRD using the structure outlined below.
6.  **Save PRD Draft:**

   **Determine Save Location:**
   - Check if `NEW_WORKTREE_PATH` is set (worktree was created this session)
   - If set:
     - If using worktrunk: Current directory is already the new worktree, use `$(pwd)`
     - If using git fallback: Use stored `NEW_WORKTREE_PATH` and create the `.flow` directory there
   - If not set: Use current repository root (`git rev-parse --show-toplevel`)

   **Ensure .flow Directory Exists:**
   ```bash
   # Determine target directory
   if [ -n "$NEW_WORKTREE_PATH" ]; then
     TARGET_DIR="$NEW_WORKTREE_PATH/.flow"
   else
     TARGET_DIR="$(git rev-parse --show-toplevel)/.flow"
   fi

   # Create directory if it doesn't exist
   mkdir -p "$TARGET_DIR"
   ```

   **Save PRD to Target Location:**
   - Save as `prd-[feature-name]-v1.md` inside the `TARGET_DIR`
   - Update frontmatter `worktree.repo_root` to point to the worktree's root (if in worktree)

   - **First, check for existing PRD in current context:**
      - Search `TARGET_DIR` for PRDs matching current git context (branch, worktree)
      - Check PRD frontmatter for matching `git.branch`, `worktree.path`, etc.
    - **If existing PRD is found (iteration mode):**
      - Read the existing PRD file
      - Increment version: `version: N` → `version: N+1`
      - Update status: If currently `approved` or `implemented`, reset to `draft`
      - Update `updated_at` timestamp and `updated_at_commit`
      - Add changelog entry documenting the iteration
      - **Replace the PRD content** with newly generated content
      - Keep the same filename (e.g., `prd-[feature]-v1.md` stays as `prd-[feature]-v1.md`)
    - **If no existing PRD found (new PRD mode):**
      - Generate YAML frontmatter with detected git context
      - Set initial `version: v1` and `status: draft`
      - Append generated PRD content after frontmatter
      - Save as `prd-[feature-name]-v1.md` inside the `/.flow` directory
    - **Display confirmation message:**
      - For new PRD: `Created PRD: prd-[feature]-v1.md`
      - For iteration: `Updated PRD: prd-[feature]-vN.md (version N → N+1)`

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
    priorities:
      enabled: true
      default: P2
      inference_method: ai_inference_with_review
      requirements:
        - id: FR-1
          text: "Users can authenticate with email/password"
          priority: P1
          confidence: high
          inferred_from: "core authentication feature"
          user_confirmed: true
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
    priorities:
      enabled: true
      default: P2
      inference_method: ai_inference_with_review
      requirements:
        - id: FR-1
          text: "Users can authenticate with email/password"
          priority: P1
          confidence: high
          inferred_from: "core authentication feature"
          user_confirmed: true
        - id: FR-2
          text: "Users can reset password via email link"
          priority: P2
          confidence: medium
          inferred_from: "standard authentication feature"
          user_confirmed: true
    ---
    ```

    **Priority Data Structure:**

    The `priorities` section stores requirement-level priority information:

    ```yaml
    priorities:
      enabled: true # Enable/disable priority system
      default: P2 # Default priority for unspecified requirements
      inference_method: ai_inference_with_review # How priorities are assigned
      requirements: # Array of prioritized requirements
        - id: FR-1 # Requirement identifier
          text: "..." # Full requirement text
          priority: P1 # Priority level (P0-P4)
          confidence: high # AI confidence: high/medium/low
          inferred_from: "..." # Rationale for priority assignment
          user_confirmed: true # Whether user confirmed this priority
    ```

    **Priority Levels:**
    - **P0** - Critical: Blocking issues, security vulnerabilities, must-have features
    - **P1** - High: Important features, urgent bugfixes, key functionality
    - **P2** - Normal: Standard features, expected functionality (default)
    - **P3** - Low: Nice-to-have features, enhancements, optimizations
    - **P4** - Lowest: Backlog items, stretch goals, future considerations

    **Important:** The variables collected in step 2.5 should be used to populate the frontmatter. The feature_name should be derived from the filename (e.g., `prd-authentication.md` → `authentication`).

7.  **PRD Review & Approval Cycle:**

- Present the draft PRD to the user with the PRD Review Checklist (see section below)
- **Use AskUserQuestion to request approval:**

```
AskUserQuestion({
  questions: [
    {
      question: "Does this PRD meet your requirements?",
      header: "Approval",
      options: [
        {
          label: "Yes",
          description: "Approve PRD and proceed to task generation"
        },
        {
          label: "No",
          description: "Restart from clarifying questions"
        },
        {
          label: "Changes",
          description: "Collect feedback and revise"
        }
      ],
      multiSelect: false
    }
  ]
})
```

- **If "Yes":**
  - Update PRD status in frontmatter from `draft` to `approved`
  - Add initial changelog entry (version 1)
  - Proceed to task generation (user will invoke `/flow:generate-tasks`)
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
The AI performs the following steps internally to update the PRD:

1. Read the current version from the frontmatter
2. Increment the version number
3. Update the version, timestamp, and commit SHA in the frontmatter
4. Add an entry to the changelog table

**PRD Iteration Workflow (when editing existing approved/implemented PRD):**

When the user edits an existing PRD that has status `approved` or `implemented`:

1. **Reset status to `draft`**: The updated PRD needs re-approval
2. **Increment version**: Add new version number
3. **Add changelog entry**: Document the changes
4. **Archive existing tasks**: Mark old tasks as superseded
5. **Prompt to regenerate**: Offer to run `/flow:generate-tasks`

The AI performs the following steps:

- Check current PRD status
- If approved or implemented:
  - Reset status to draft
  - Increment version number
  - Update timestamp and commit SHA
  - Archive related tasks by marking them as superseded and closing them
  - Add changelog entry
  - Display success message with next steps

**Archive function for old tasks:**

The AI archives all tasks related to a PRD by:

1. Getting the list of related issues from the PRD frontmatter
2. For each related issue that exists:
   - Adding a "superseded" label
   - Closing the issue
3. Clearing the related_issues and related_epics from the PRD frontmatter
4. Displaying the count of archived tasks

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
2. Run /flow:generate-tasks to create new tasks from updated requirements
3. Approve the PRD to begin implementation

**Use AskUserQuestion to prompt the user:**

```

AskUserQuestion({
questions: [
{
question: "Would you like to run /flow:generate-tasks now to create new tasks from the updated PRD?",
header: "Next Step",
options: [
{
label: "Yes",
description: "Generate tasks from the updated PRD"
},
{
label: "No",
description: "Skip task generation for now"
}
],
multiSelect: false
}
]
})

```

If user selects "Yes", automatically invoke the generate-tasks workflow.

**Next Step After Approval:**

After the user approves the PRD (option "Yes"), display the following message:

```

✅ PRD Approved!

📋 PRD: prd-[feature]-vN.md
Status: draft → approved
Version: N
Branch: [branch-name]

Next steps:
→ Run /flow:generate-tasks to create implementation tasks

````

8.  **Changelog:**

Each PRD includes a changelog section at the bottom tracking all versions:

  ```markdown
  ## Changelog

  | Version | Date             | Summary of Changes                    |
  | ------- | ---------------- | ------------------------------------- |
  | 3       | 2025-01-03 09:15 | Clarified file upload limits           |
  | 2       | 2025-01-02 14:30 | Added Admin role permissions          |
  | 1       | 2025-01-02 10:30 | Initial PRD approved                  |
````

9.  **Task Tracking Reference:** After PRD approval, the user will invoke `/flow:generate-tasks` to create implementation tasks using beads. The PRD file will be referenced in all task descriptions.
10. **Review & Refine (Deprecated):** The approval workflow in step 7 now handles PRD review. Proceed to task generation after approval.

## Clarifying Questions

The AI should use the AskUserQuestion tool for all clarifying questions. Group questions into categories to systematically cover all areas.

### Tool Usage

**Use the AskUserQuestion tool with this structure:**

```
AskUserQuestion({
  questions: [
    {
      question: "What is the primary goal of this feature?",
      header: "Goal",
      options: [
        {
          label: "Solve a specific problem",
          description: "Address an existing pain point"
        },
        {
          label: "Add new capability",
          description: "Enable something not currently possible"
        },
        {
          label: "Improve experience",
          description: "Enhance existing functionality"
        }
      ],
      multiSelect: false
    }
  ]
})
```

**Key Guidelines:**

- **header**: Short label (max 12 chars) displayed as a chip/tag
- **question**: Clear question text ending with a question mark
- **options**: 2-4 options with concise labels and helpful descriptions
- **multiSelect**: Set to `true` when multiple options can apply (e.g., user roles)
- The tool automatically provides an "Other" option for custom input

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

## Priority Inference Rules

The AI infers priority levels (P0-P4) from requirement language using keyword detection:

| Priority | Level    | Keyword Triggers                              | Examples                               |
| -------- | -------- | --------------------------------------------- | -------------------------------------- |
| P0       | Critical | critical, blocking, security, must-have, core | "User authentication is critical"      |
| P1       | High     | urgent, important, primary, main, key         | "Main feature for Q1 release"          |
| P2       | Normal   | should, standard, typical, expected (default) | "Users should be able to upload files" |
| P3       | Low      | nice-to-have, optional, could, enhancement    | "Could add dark mode later"            |
| P4       | Lowest   | eventually, backlog, maybe, stretch           | "Maybe add advanced search"            |

**Inference Guidelines:**

1. Analyze requirement text for keyword presence
2. Consider context and emphasis (e.g., "CRITICAL" vs "critical")
3. Check for negation patterns (e.g., "not critical")
4. Assign confidence based on keyword strength and context
5. When multiple keywords exist, use highest priority match

**Confidence Levels:**

- **High**: Explicit keyword (e.g., "critical", "urgent") with clear context
- **Medium**: Implicit priority from domain context or user emphasis
- **Low**: No clear indicators, using default P2

## Priority Confirmation Workflow

After AI inference, the user must confirm all assigned priorities using the AskUserQuestion tool.

**Confirmation Process:**

1. **Present Inferred Priorities**: Display each requirement with its inferred priority in table format
2. **Use AskUserQuestion for Confirmation**:
   - Ask if user wants to accept all, adjust individually, or redo inference
   - If adjusting, iterate through each requirement offering priority selection
3. **Store Results**: Update frontmatter with confirmed priorities

**Example Interaction:**

```
AI: Based on your responses, I've inferred the following priorities:

┌─────┬───────────────────────────────┬───────────┬────────────┐
│ ID  │ Requirement                   │ Priority  │ Confidence │
├─────┼───────────────────────────────┼───────────┼────────────┤
│ FR-1│ User authentication           │ P1 (High) │ High       │
│ FR-2│ Password reset                │ P2 (Norm) │ Medium     │
│ FR-3│ Social login (OAuth)          │ P3 (Low)  │ Medium     │
└─────┴───────────────────────────────┴───────────┴────────────┘

[AskUserQuestion invoked]
Question: How would you like to proceed?
Options:
- Accept all (Accept all inferred priorities)
- Adjust individually (Review and modify each priority)
- Redo inference (Restart priority inference)

> User selects: Accept all
✓ All priorities confirmed
```

**Update Frontmatter:**

```yaml
priorities:
  requirements:
    - id: FR-1
      priority: P1
      confidence: high
      user_confirmed: true
    - id: FR-2
      priority: P2
      confidence: medium
      user_confirmed: true
    - id: FR-3
      priority: P3
      confidence: medium
      user_confirmed: true
```

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

**Important:** Do not proceed to `/flow:generate-tasks` until explicit approval is received.

## PRD Structure

The generated PRD should include the following sections:

1.  **Introduction/Overview:** Briefly describe the feature and the problem it solves. State the goal.
2.  **Goals:** List the specific, measurable objectives for this feature.
3.  **User Stories:** Detail the user narratives describing feature usage and benefits.
4.  **Functional Requirements:** List the specific functionalities the feature must have. Use clear, concise language (e.g., "The system must allow users to upload a profile picture."). Number these requirements. **Include priority for each requirement in table format:**

    | ID   | Requirement                            | Priority | Notes            |
    | ---- | -------------------------------------- | -------- | ---------------- |
    | FR-1 | Users can authenticate with email/pass | P1       | Core feature     |
    | FR-2 | Users can reset password via email     | P2       | Standard feature |
    | FR-3 | Users can enable 2FA                   | P3       | Nice-to-have     |

    Requirements are derived from the `priorities.requirements` array in frontmatter.

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

After the PRD is approved, invoke `/flow:generate-tasks` to create and track implementation tasks using the beads tool.

All task management is handled through beads integration - no separate task files needed.

## Final instructions

1. Do NOT start implementing the PRD
2. Make sure to ask the user clarifying questions (3-5 at a time)
3. Take the user's answers to the clarifying questions and improve the PRD
4. Use the beads tool (`read_todos`/`write_todos`) for task tracking
5. If the user is satisfied with the PRD, suggest the user to use `/flow:generate-tasks` command
6. DO NOT suggest the user to use the `bd` command, this command is mainly reserved for AI Agents to use.
7. ULTRATHINK
