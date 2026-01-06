# Cleanup Session Examples

## Overview

Complete session transcripts showing the `/flow:cleanup` command in action.

---

## Example 1: Cleanup with Worktree Merge

This example shows cleanup when working in a git worktree with automatic merge and worktree removal.

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

[AskUserQuestion presented with options]
User selects: "Merge and cleanup worktree"

Executing merge...
✓ Switched to main repository
✓ Merged feature/user-auth into master
✓ Removed worktree
✓ Deleted branch

Merge commit: def456ghi

Updating PRD status...
✓ Version: 3 → 4
✓ Status: implementing → implemented
✓ Updated: 2025-01-03T14:30:00Z
✓ Changelog entry added

🧹 Implementation Cleanup Complete!

📋 PRD: prd-authentication-v3.md
   Status: implementing → implemented
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

---

## Example 2: Cleanup without Worktree (Main Repo)

This example shows cleanup when working directly in the main repository (not a worktree).

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
✓ Status: implementing → implemented
✓ Updated: 2025-01-03T14:30:00Z
✓ Changelog entry added

🧹 Implementation Cleanup Complete!

📋 PRD: prd-authentication-v3.md
   Status: implementing → implemented
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

---

## Key Differences

| Aspect | Worktree Cleanup | Main Repo Cleanup |
|--------|------------------|-------------------|
| **Merge** | Yes, to target branch | No, already on branch |
| **Worktree removal** | Yes | N/A |
| **Branch deletion** | Yes (feature branch) | No |
| **Commit type** | Merge commit | Summary commit |
| **Final state** | Back on main branch | Stays on feature branch |

---

## Error Handling Examples

### Incomplete Tasks

```
AI: Verifying task completion...
📊 Task Completion Status:
   Total tasks: 8
   Completed: 5
   In Progress: 1
   Open: 2
   ⚠️  Not all tasks complete

Open tasks:
- proj-auth.6: Implement token refresh
- proj-auth.7: Write unit tests

In Progress:
- proj-auth.5: Create session storage

[AskUserQuestion - Not all tasks are complete yet]
User selects: "Exit"

AI: Please complete the remaining tasks first. Run /flow:implement to continue.
```

### Merge Conflicts

```
AI: Executing merge...
✗ Merge failed due to conflicts

Conflicting files:
- src/services/AuthService.ts
- src/types/user.ts

The worktree has been kept intact for manual resolution.

Suggested next steps:
1. Resolve conflicts in the listed files
2. Run tests to verify resolution
3. Complete merge with: git commit
4. Re-run /flow:cleanup to finalize
```

### Uncommitted Changes

```
AI: ⚠️  Worktree has uncommitted changes:
   M  src/components/Login.tsx
   ??  tests/auth.test.ts

Cannot proceed with merge. Please commit or stash changes first.

[AskUserQuestion - Uncommitted changes detected]
Options:
- Commit changes now
- Stash changes and proceed
- Exit to handle manually
```
