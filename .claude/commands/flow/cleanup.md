---
description: Clean up after implementation - close issues, commit changes, update PRD status
---

# Rule: Implementation Cleanup (/flow:cleanup)

## Goal

To guide an AI assistant in performing post-implementation cleanup after all PRD tasks are complete. This includes:

- Verifying all tasks are completed
- Closing completed beads issues (if using beads)
- Creating a summary commit grouping all implementation changes
- Updating PRD status from `approved` to `implemented`
- Adding changelog entry to PRD

**Task Management Options:**

- **With beads (`bd`) installed:** Issues are managed in the `.beads/` database with full cleanup support
- **Without beads:** Basic verification of TodoWrite task completion

## Prerequisites

- **Required:** All PRD tasks must be completed (all issues closed in beads, or all TodoWrite items marked completed)
- **Required:** An approved PRD in `/.flow/` directory with `status: approved`
- **Optional:** beads (`bd`) - If installed, issues will be verified and committed
- **Optional:** Clean working directory (no uncommitted changes) - required for worktree merge operation

## Process

1. **Auto-Discover PRD:** Automatically find the appropriate PRD based on git context.

   **Stage 1 - Latest PRD Check:**
   - Find the most recently modified PRD in `/.flow/` directory
   - Read its YAML frontmatter
   - Extract branch, worktree name, and worktree path

   **Stage 2 - Context Validation:**
   - Detect current git context (branch, worktree)
   - Compare current context with PRD metadata
   - **Match criteria:** ALL of the following must match
     - Branch name matches exactly (or both are main/master)
     - Worktree name matches (if both in worktrees)
     - Worktree path matches (if both in worktrees)

   **Stage 3 - Fallback Search:**
   - If latest PRD doesn't match, search all PRDs in `/.flow/`
   - For each PRD, check if metadata matches current context
   - Return first matching PRD

   **Stage 4 - No Match Found:**
   - If no PRD matches current context, use AskUserQuestion to inform user and offer options:
     ```
     AskUserQuestion({
       questions: [
         {
           question: "No PRD matches the current context. Available PRDs: [list]. What would you like to do?",
           header: "PRD Action",
           options: [
             {
               label: "Create new PRD",
               description: "Run /flow:plan to create a new PRD"
             },
             {
               label: "Select existing PRD",
               description: "Manually select one of the available PRDs"
             },
             {
               label: "Exit",
               description: "Exit the cleanup process"
             }
           ],
           multiSelect: false
         }
       ]
     })
     ```

2. **Verify Implementation Complete:** Check that all PRD tasks are completed before cleanup.

   **With beads (`bd`) installed:**
   - **Step 2a - Query Beads for Related Issues:**
     - Read `beads.related_issues` from PRD frontmatter
     - For each issue, query its status using `bd show <issue-id>`

   - **Step 2b - Completion Check:**
     - Verify ALL related issues have status `closed`
     - If any issues are NOT closed, use AskUserQuestion to present options:
       ```
       AskUserQuestion({
         questions: [
           {
             question: "Not all tasks are complete yet. Open/In-Progress Issues: [list]. What would you like to do?",
             header: "Cleanup",
             options: [
               {
                 label: "Continue anyway",
                 description: "Cleanup only completed tasks"
               },
               {
                 label: "Exit",
                 description: "Complete remaining tasks first"
               }
             ],
             multiSelect: false
           }
         ]
       })
       ```
     - If user selects "Exit", exit cleanup and suggest running `/flow:implement`
     - If user selects "Continue anyway", proceed with partial cleanup

   - **Step 2c - Task Summary:**
     - Display completion summary:
       ```
       📊 Task Completion Status:
       Total tasks: X
       Completed: Y
       In Progress: Z
       Open: W
       ```

   **Without beads (TodoWrite fallback):**
   - Check internal TodoWrite state for all PRD-related tasks
   - Verify all tasks have status "completed"
   - If any tasks are incomplete, show warning and offer options
   - Note: Manual verification may be needed if context is incomplete

3. **Check for Worktree Cleanup:** Determine if current directory is a worktree and offer merge/cleanup.

   **Step 3a - Worktree Detection:**
   - Read `worktree.is_worktree` from PRD frontmatter
   - If `false`, skip to step 4 (summary commit)

   **Step 3b - Pre-Merge Validation:**
   - Verify clean working directory: `git status --porcelain` returns empty
   - Verify we're not in main repo: `worktree.name != "main"`

   **Step 3c - Determine Merge Target:**
   - Read PRD frontmatter for target branch info:
     - Check if `git.parent_branch` exists in PRD frontmatter
     - If not found, try to infer from branch naming patterns:
       - `feature/*` → merge to `main` or `master` (whichever exists)
       - `bugfix/*`, `hotfix/*` → merge to `main` or `master`
       - Other branches → ask user
   - If target cannot be determined, prompt user via AskUserQuestion

   **Step 3d - User Confirmation:**
   - Use AskUserQuestion to present options:
     ```
     AskUserQuestion({
       questions: [
         {
           question: "Worktree detected: [worktree-name]. Merge to [target-branch] and cleanup? This will merge the branch, remove the worktree, and delete the feature branch.",
           header: "Worktree Cleanup",
           options: [
             {
               label: "Merge and cleanup worktree",
               description: "Merge branch to target, remove worktree, and delete feature branch"
             },
             {
               label: "Skip worktree cleanup",
               description: "Only create summary commit, leave worktree intact for manual cleanup"
             },
             {
               label: "Exit",
               description: "Abort cleanup to handle worktree merge manually"
             }
           ],
           multiSelect: false
         }
       ]
     })
     ```

   **Step 3e - Execute Merge (if approved):**

   **With worktrunk (`wt`) installed:**

   ```bash
   # Switch to target branch and merge current worktree branch
   wt switch "$target_branch"
   git merge --no-ff -m "feat([scope]): merge [feature] - complete

   Implements all requirements from PRD:
   - prd-[feature]-vN.md

   Closes: [issue IDs]
   PRD: prd-[feature]-vN.md" "$current_branch"

   # Remove worktree and delete branch
   wt remove
   ```

   **Without worktrunk (fallback):**

   ```bash
   # Store current worktree info
   current_branch=$(git rev-parse --abbrev-ref HEAD)
   worktree_path=$(git rev-parse --show-toplevel)

   # Switch to main repository and target branch
   repo_root=$(sed 's|/worktrees/[^/]*||' <<< "$worktree_path")
   cd "$repo_root"
   git checkout "$target_branch"

   # Merge feature branch with conventional commit message
   git merge --no-ff -m "feat([scope]): merge [feature] - complete

   Implements all requirements from PRD:
   - prd-[feature]-vN.md

   Changes:
   - [Epic 1 summary]
   - [Epic 2 summary]

   Closes: [issue IDs]
   PRD: prd-[feature]-vN.md" "$current_branch"

   # Remove worktree
   git worktree remove "$worktree_path"

   # Delete merged branch
   git branch -d "$current_branch"
   ```

   **Step 3f - Verify Success:**
   - Check merge exit code (0 = success)
   - Verify worktree no longer exists: `git worktree list`
   - Display merge commit SHA for reference

   **Step 3g - Handle Merge Failure:**
   - If merge failed due to conflicts:
     - Inform user of merge conflicts
     - Keep worktree intact for manual resolution
     - Suggest running `git status` to see conflicts
     - Offer to keep worktree for manual cleanup
   - If worktree removal failed:
     - Provide manual cleanup instructions
     - Show commands to remove worktree and branch

4. **Create Summary Commit (if not already merged):** Group all implementation changes into a single summary commit.

   **Skip if:** Worktree merge was performed in step 3 (commit created by merge operation)

   **Only create commit if:** Still in worktree (user skipped merge) or in main repo

   **Commit Message Format:**

   Use conventional commit format with comprehensive summary:

   ```
   feat([scope]): implement [feature-name] - complete

   Implements all requirements from PRD:
   - prd-[feature]-vN.md

   Changes:
   - [Summary of epic 1 - e.g., Core authentication system]
   - [Summary of epic 2 - e.g., User registration flow]
   - [Summary of epic 3 - e.g., Password reset functionality]
   - [Testing complete - unit, integration, e2e tests]

   Closes: [list of all issue IDs]
   PRD: prd-[feature]-vN.md
   Branch: [branch-name]
   ```

   **Commit Creation:**
   - Stage all changes: `git add .`
   - Create commit with formatted message: `git commit -m "[message]"`
   - Display commit SHA for reference

   **Example Commit:**

   ```
   feat(auth): implement user authentication - complete

   Implements all requirements from PRD:
   - prd-authentication-v3.md

   Changes:
   - Core authentication system with JWT tokens
   - User registration with email verification
   - Password reset via email link
   - Session management and token refresh
   - Unit, integration, and E2E tests complete

   Closes: proj-auth-1, proj-auth-2, proj-auth-3, proj-auth-4, proj-auth-5
   PRD: prd-authentication-v3.md
   Branch: feature/user-auth
   ```

5. **Update PRD Status:** Mark the PRD as implemented in the frontmatter.

   **Updates to PRD Frontmatter:**
   - **Increment version:** `version: N` → `version: N+1`
   - **Update status:** `status: approved` → `status: implemented`
   - **Update timestamp:** `updated_at: [current ISO 8601 timestamp]`
   - **Update commit SHA:** `updated_at_commit: [current commit SHA]`
   - **Add changelog entry:** Insert at top of changelog table

   **Changelog Entry Format:**

   For worktree merge:

   ```markdown
   | N+1 | YYYY-MM-DD HH:MM | Implementation complete - merged to [target-branch], worktree removed |
   ```

   For non-worktree (main repo):

   ```markdown
   | N+1 | YYYY-MM-DD HH:MM | Implementation complete - all X tasks closed |
   ```

   **Example Changelog Update (with worktree merge):**

   ```markdown
   ## Changelog

   | Version | Date             | Summary of Changes                                           |
   | ------- | ---------------- | ------------------------------------------------------------ |
   | 4       | 2025-01-03 14:30 | Implementation complete - merged to master, worktree removed |
   | 3       | 2025-01-02 16:45 | Updated priority for password reset requirement              |
   | 2       | 2025-01-02 14:22 | Added Admin role permissions                                 |
   | 1       | 2025-01-02 10:30 | Initial PRD approved                                         |
   ```

6. **Display Cleanup Summary:** Show the user what was accomplished.

   **Output Format (with worktree merge):**

   ```
   🧹 Implementation Cleanup Complete!

   📋 PRD: prd-[feature]-vN.md
      Status: approved → implemented
      Version: N → N+1

   📊 Worktree: [worktree-name]
      ✓ Merged to [target-branch]
      ✓ Worktree removed
      ✓ Branch deleted

   📊 Tasks: X/X completed
      ✓ All issues closed

   📝 Merge Commit:
      Commit: [commit SHA]
      Message: feat([scope]): merge [feature] - complete

   ✨ PRD implemented and merged!
   ```

   **Output Format (without worktree merge):**

   ```
   🧹 Implementation Cleanup Complete!

   📋 PRD: prd-[feature]-vN.md
      Status: approved → implemented
      Version: N → N+1
      Branch: [branch-name]

   📊 Tasks: X/X completed
      ✓ All issues closed

   📝 Summary Commit:
      Commit: [commit SHA]
      Message: feat([scope]): implement [feature] - complete

   ✨ PRD is now marked as implemented!
   ```

7. **Optional Next Step:** Suggest running `/flow:summary` to view the final implementation summary.

   **Suggestion:**

   ```
   Optional next step:
   → Run /flow:summary to view the final implementation summary
   ```

## With beads (`bd`) installed:

All task context is stored in beads' SQLite database. Task verification and cleanup is handled through beads integration.

### Helper Function: verify_all_tasks_complete

```bash
# Function to verify all PRD tasks are complete
verify_all_tasks_complete() {
  local prd_file="$1"
  local related_issues=$(grep -A2 "^beads:" "$prd_file" | grep "related_issues:" | sed 's/.*: \[\(.*\)\]/\1/')

  # Clean up the issue list
  related_issues=$(echo "$related_issues" | tr -d '[]",' | tr ' ' '\n' | grep -v '^$')

  local all_closed=true
  local total=0
  local closed=0

  for issue in $related_issues; do
    total=$((total + 1))
    if bd show "$issue" 2>/dev/null | grep -q "Status: closed"; then
      closed=$((closed + 1))
    else
      all_closed=false
      echo "- $issue: $(bd show "$issue" 2>/dev/null | grep "^Title:" | sed 's/Title: //') ($(bd show "$issue" 2>/dev/null | grep "^Status:" | sed 's/Status: //'))"
    fi
  done

  if [ "$all_closed" = true ]; then
    return 0
  else
    echo ""
    echo "⚠️  Not all tasks are complete yet ($closed/$total closed)"
    return 1
  fi
}
```

## Without beads (TodoWrite fallback):

Task completion is verified through internal TodoWrite state. Note: Context may be lost between sessions, so manual verification may be needed.

## Cleanup Safety Checks

Before performing cleanup, the following safety checks are performed:

1. **PRD Status Check:** Verify PRD status is `approved` (not `draft` or already `implemented`)
2. **Git Status Check:** Ensure there are uncommitted changes to commit
3. **Branch Check:** Verify current branch matches PRD's git context
4. **Task Completion Check:** Verify all tasks are marked as completed
5. **Worktree Clean State Check:** If in worktree, ensure no uncommitted changes before merge

If any safety check fails, the AI will:

- Display the specific issue
- Offer options to resolve or continue anyway
- Document the decision in the commit message if continuing

## Error Handling

**Common Errors and Resolutions:**

| Error                           | Cause                               | Resolution                                             |
| ------------------------------- | ----------------------------------- | ------------------------------------------------------ |
| No PRD found                    | No matching PRD for current context | Offer to create new PRD or select manually             |
| Tasks not complete              | Some issues still open/in-progress  | Show incomplete tasks, offer to exit or continue       |
| No git changes                  | Nothing to commit                   | Verify if work was done, may skip commit step          |
| Beads not available             | `bd` command not found              | Fall back to TodoWrite verification                    |
| PRD already implemented         | Status already `implemented`        | Inform user, exit with message                         |
| Merge conflicts                 | Merge failed due to conflicts       | Show conflict resolution steps, offer to keep worktree |
| Worktree removal failed         | Cannot delete worktree              | Manual cleanup required, provide instructions          |
| Uncommitted changes in worktree | Working directory not clean         | Warn user, require commit or stash before merge        |

## Example Session

**Example with Worktree Merge:**

```
User: /flow:cleanup

AI: 🧹 Implementation Cleanup

Discovering PRD for current context...
✓ Found: prd-authentication-v3.md
   Status: approved
   Branch: feature/user-auth
   Worktree: feature-user-auth

Verifying task completion...
📊 Task Completion Status:
   Total tasks: 8
   Completed: 8
   In Progress: 0
   Open: 0
   ✓ All tasks complete

🔍 Worktree detected: feature-user-auth
   Current branch: feature/user-auth
   Target branch: master (inferred from PRD git context)

⚠️  Worktree cleanup required before completion.
   This will:
   - Merge feature/user-auth → master
   - Remove worktree: /worktrees/.../feature-user-auth
   - Delete branch: feature/user-auth

What would you like to do?

User selects: "Merge and cleanup worktree"

Executing merge...
✓ Switched to main repository
✓ Merged feature/user-auth into master
✓ Removed worktree
✓ Deleted branch

Merge commit: def456ghi

Updating PRD status...
✓ Version: 3 → 4
✓ Status: approved → implemented
✓ Updated: 2025-01-03T14:30:00Z
✓ Changelog entry added

🧹 Implementation Cleanup Complete!

📋 PRD: prd-authentication-v3.md
   Status: approved → implemented
   Version: 3 → 4

📊 Worktree: feature-user-auth
   ✓ Merged to master
   ✓ Worktree removed
   ✓ Branch deleted

📊 Tasks: 8/8 completed
   ✓ All issues closed

📝 Merge Commit:
   Commit: def456ghi
   Message: feat(auth): merge user authentication - complete

✨ PRD implemented and merged!

Optional next step:
→ Run /flow:summary to view the final implementation summary
```

**Example without Worktree (main repo):**

```
User: /flow:cleanup

AI: 🧹 Implementation Cleanup

Discovering PRD for current context...
✓ Found: prd-authentication-v3.md
   Status: approved
   Branch: feature/user-auth
   Worktree: main

Verifying task completion...
📊 Task Completion Status:
   Total tasks: 8
   Completed: 8
   In Progress: 0
   Open: 0
   ✓ All tasks complete

Creating summary commit...
✓ Staged all changes
✓ Created commit: abc123def

Commit message:
feat(auth): implement user authentication - complete

Implements all requirements from PRD:
- prd-authentication-v3.md

Changes:
- Core authentication system with JWT tokens
- User registration with email verification
- Password reset via email link
- Session management and token refresh
- Unit, integration, and E2E tests complete

Closes: proj-auth-1, proj-auth-2, proj-auth-3, proj-auth-4, proj-auth-5, proj-auth-6, proj-auth-7, proj-auth-8
PRD: prd-authentication-v3.md
Branch: feature/user-auth

Updating PRD status...
✓ Version: 3 → 4
✓ Status: approved → implemented
✓ Updated: 2025-01-03T14:30:00Z
✓ Changelog entry added

🧹 Implementation Cleanup Complete!

📋 PRD: prd-authentication-v3.md
   Status: approved → implemented
   Version: 3 → 4
   Branch: feature/user-auth

📊 Tasks: 8/8 completed
   ✓ All issues closed

📝 Summary Commit:
   Commit: abc123def
   Message: feat(auth): implement user authentication - complete

✨ PRD is now marked as implemented!

Optional next step:
→ Run /flow:summary to view the final implementation summary
```

## Key Design Decisions

1. **Reuse existing PRD discovery logic** - Consistent with other PRD commands
2. **Optional beads support** - Works with or without beads installed
3. **Safety first** - Multiple checks before cleanup, warns if incomplete
4. **Single atomic commit** - Groups all implementation changes for easy review
5. **Conventional commit format** - Follows project standards for commit messages
6. **Comprehensive commit message** - Includes PRD reference, epic summaries, and closed issues

## Notes

- The cleanup command should only be run after ALL implementation tasks are complete
- Manual testing is recommended before cleanup to verify the implementation works correctly
- The summary commit can be amended if needed: `git commit --amend`
- PRD can be reverted from `implemented` to `approved` if additional work is needed
