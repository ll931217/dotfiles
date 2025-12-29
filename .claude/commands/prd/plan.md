---
description: Generating a Product Requirements Document (PRD)
---
# Rule: Generating a Product Requirements Document (PRD)

## Goal

To guide an AI assistant in creating a detailed Product Requirements Document (PRD) in Markdown format, based on an initial user prompt. The PRD should be clear, actionable, and suitable for a junior developer to understand and implement the feature.

## Process

1.  **Check Prerequisites:** Verify that required tools are installed. Check for: `git`, `gwq`, `bd`.

    For each missing tool, offer to install:

    | Tool | Check | Installation |
    |------|-------|--------------|
    | `git` | `which git` | Use system package manager (e.g., `sudo apt install git`, `brew install git`) |
    | `bd` | `which bd` | `curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh \| bash` |
    | `gwq` | `which gwq` | Download from latest release, extract, and add to PATH |

    **gwq installation steps:**
    ```bash
    # Download latest release (Linux x86_64)
    curl -fsSL https://github.com/d-kuro/gwq/releases/download/v0.0.5/gwq_Linux_x86_64.tar.gz -o /tmp/gwq.tar.gz
    # Extract
    tar -xzf /tmp/gwq.tar.gz -C /tmp
    # Move to PATH
    sudo mv /tmp/gwq /usr/local/bin/gwq
    # Cleanup
    rm /tmp/gwq.tar.gz
    ```

    - If any tool is missing, show the installation command and ask user to confirm before running.
    - If user declines installation, warn that some features may not work and ask if they want to continue anyway.
    - Only proceed to step 2 when all tools are available or user explicitly chooses to continue.

2.  **Verify Git Worktree:** Before proceeding, check if the current directory is a Git worktree. If it is not a worktree, warn the user and offer options.
    - **Warning message should include:**
      - An explanation that PRDs are best created in isolated worktrees for better branch/feature management.
    - **Offer 3 choices:**
      1. **Create worktree now** - Ask for a feature name, then show and confirm the command:
         ```bash
         gwq add -b feature/<user-provided-name>
         ```
         Only run if user confirms. After creation, continue with the PRD process.
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

      Will run: gwq add -b feature/auth
      Proceed? (y/n)
      ```

3.  **Receive Initial Prompt:** The user provides a brief description or request for a new feature or functionality.
4.  **Ask Clarifying Questions:** Before writing the PRD, the AI *must* ask clarifying questions to gather sufficient detail. The goal is to understand the "what" and "why" of the feature, not necessarily the "how" (which the developer will figure out). Make sure to provide options in letter/number lists so I can respond easily with my selections.
    - Ask **3-5 clarifying questions at a time** to avoid overwhelming the user. Prioritize the most critical unknowns first.
5.  **Generate PRD:** Based on the initial prompt and the user's answers to the clarifying questions, generate a PRD using the structure outlined below.
6.  **Save PRD:** Save the generated document as `prd-[feature-name].md` inside the `/tasks` directory.
7.  **Track Tasks with Beads:** Use the **beads tool** (`read_todos` and `write_todos`) to track implementation tasks derived from the PRD. Do NOT create a separate tasks markdown file.
8.  **Review & Refine:** Present the draft PRD to the user for feedback. Iterate on the document until the user approves it.

## Clarifying Questions

The AI should adapt its questions based on the prompt. Group questions into categories to systematically cover all areas:

### Business Context
*   **Problem/Goal:** "What problem does this feature solve for the user?" or "What is the main goal we want to achieve with this feature?"
*   **Target User:** "Who is the primary user of this feature?"
*   **Priority/Timeline:** "What is the priority or target timeline for this feature?"
*   **Similar Features:** "Are there any existing features similar to this we should reference?"

### Functional Scope
*   **Core Functionality:** "Can you describe the key actions a user should be able to perform with this feature?"
*   **User Stories:** "Could you provide a few user stories? (e.g., As a [type of user], I want to [perform an action] so that [benefit].)"
*   **Acceptance Criteria:** "How will we know when this feature is successfully implemented? What are the key success criteria?"
*   **Scope/Boundaries:** "Are there any specific things this feature *should not* do (non-goals)?"
*   **Edge Cases:** "Are there any potential edge cases or error conditions we should consider?"

### Technical Context
*   **Data Requirements:** "What kind of data does this feature need to display or manipulate?"
*   **Existing Systems:** "Are there existing systems, APIs, or modules this should integrate with?"
*   **Constraints:** "Are there any known technical constraints or dependencies?"

### UX/Design
*   **Design/UI:** "Are there any existing design mockups or UI guidelines to follow?" or "Can you describe the desired look and feel?"
*   **Accessibility:** "Are there accessibility requirements to consider?"
*   **Responsive/Mobile:** "Does this need to work on mobile or different screen sizes?"

### Non-Functional Requirements
*   **Performance:** "Are there any performance requirements or expectations?"
*   **Security/Privacy:** "Are there security or privacy considerations?"
*   **Internationalization:** "Does this need to support multiple languages?"

## PRD Structure

The generated PRD should include the following sections:

1.  **Introduction/Overview:** Briefly describe the feature and the problem it solves. State the goal.
2.  **Goals:** List the specific, measurable objectives for this feature.
3.  **User Stories:** Detail the user narratives describing feature usage and benefits.
4.  **Functional Requirements:** List the specific functionalities the feature must have. Use clear, concise language (e.g., "The system must allow users to upload a profile picture."). Number these requirements.
5.  **Non-Goals (Out of Scope):** Clearly state what this feature will *not* include to manage scope.
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

## Complexity Guidance

- **Simple features:** Keep the PRD concise (1-2 pages). Focus on core sections.
- **Complex features:** Be more thorough (3-5 pages). Include all optional sections.

## Target Audience

Assume the primary reader of the PRD is a **junior developer**. Therefore, requirements should be explicit, unambiguous, and avoid jargon where possible. Provide enough detail for them to understand the feature's purpose and core logic.

## Output

*   **Format:** Markdown (`.md`)
*   **Location:** `/tasks/`
*   **Filename:** `prd-[feature-name].md`

## Task Tracking

After the PRD is approved, use the **beads tool** to create and track implementation tasks:

1. **Create epics with PRD reference:**
   ```bash
   bd create "Epic: [Feature Name]" -p 1 -t epic --external-ref "prd-[feature-name].md"
   ```

2. **Use beads commands for task management:**
   - `bd list` - View all tasks
   - `bd ready` - Show unblocked tasks ready for work
   - `bd update <id> --status in_progress` - Mark task as in progress
   - `bd close <id>` - Complete a task

3. **Update PRD with beads reference:**
   After creating epics, add a "Beads Reference" section to the PRD noting the epic ID(s).

**Do NOT create a separate tasks markdown file.** The beads tool provides built-in task management with dependency tracking.

## Final instructions

1. Do NOT start implementing the PRD
2. Make sure to ask the user clarifying questions (3-5 at a time)
3. Take the user's answers to the clarifying questions and improve the PRD
4. Use the beads tool (`read_todos`/`write_todos`) for task tracking
5. ULTRATHINK
