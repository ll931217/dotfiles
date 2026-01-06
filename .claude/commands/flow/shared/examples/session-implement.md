# Implementation Session Examples

## Overview

Complete examples showing the `/flow:implement` command workflow, including autonomous execution, parallel task execution, and Ralph Wiggum iterative development.

---

## Example 1: Autonomous Execution Pattern

This example shows the autonomous execution mode where tasks are executed continuously without asking for permission.

```
AI: /flow:implement

Discovering PRD for current context...
✓ Found: prd-authentication-v2.md
   Status: ✅ approved (ready for implementation)
   Branch: feature/auth
   Worktree: feature-auth

📊 Available Ready Tasks (sorted by priority):

🟠 P1 | proj-auth.1: Implement login endpoint
🟠 P1 | proj-auth.2: Implement registration endpoint
🟢 P2 | proj-auth.3: Add password hashing utility
🔵 P3 | proj-auth.4: Create session storage

Starting autonomous execution...
[No permission requested - proceeding continuously]

Working on: proj-auth.1: Implement login endpoint

[Reading relevant files selectively]
- src/api/routes.ts (lines 45-80) - Existing route patterns
- src/services/AuthService.ts (lines 1-50) - Auth interface
- src/types/user.ts (lines 10-30) - User type definitions

[Implementing...]
✓ Created POST /auth/login endpoint
✓ Added JWT token generation
✓ Added error handling for invalid credentials

Running tests...
✓ All tests passing

Committing changes...
git add src/api/routes.ts src/services/AuthService.ts
git commit -m "feat(auth): implement login endpoint

- Add POST /auth/login endpoint with email/password authentication
- Generate JWT tokens on successful login
- Handle invalid credentials with appropriate error messages

Closes: proj-auth.1"

✓ Closed task: proj-auth.1

Moving to next ready task: proj-auth.2: Implement registration endpoint

[... autonomous execution continues ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Progress: 2/4 tasks complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Example 2: Parallel Task Execution ([P:Group-X])

This example shows parallel execution of tasks marked with `[P:Group-X]` flags.

```
AI: /flow:implement

Discovering PRD...
✓ Found: prd-authentication-v2.md
   Status: ✅ approved

Refreshing context before parallel group...
/flow:summary

[Summary output...]
Last Refresh updated to: 2026-01-02 14:30 UTC

📊 Ready Tasks:

[P:Group-1] Parallel Group (3 tasks):
├─ proj-auth.5: Implement React login component
├─ proj-auth.6: Implement login POST endpoint
└─ proj-auth.7: Create users table schema

Starting parallel execution...

[Analyzing task metadata]
proj-auth.5: subagent_type=frontend-developer, skill=frontend-design
proj-auth.6: subagent_type=backend-architect
proj-auth.7: subagent_type=database-admin

Launching 3 tasks in parallel...

[Task 1/3] Frontend component
Skill applied: frontend-design
Subagent: frontend-developer
Files: src/components/Login.tsx, src/types/auth.ts
Status: ⏳ In progress

[Task 2/3] Backend API
Subagent: backend-architect
Files: src/api/routes.ts, src/services/AuthService.ts
Status: ⏳ In progress

[Task 3/3] Database schema
Subagent: database-admin
Files: migrations/001_create_users.sql
Status: ⏳ In progress

[Monitoring parallel progress...]
Task 1/3: ✓ Completed
Task 2/3: ✓ Completed
Task 3/3: ✓ Completed

All parallel tasks complete. Running test suite...
pytest, npm test
✓ All tests passing

Committing group changes...
git add .
git commit -m "feat(auth): implement login system (frontend + backend + database)

[P:Group-1] Parallel execution complete:
- React login component with form validation
- POST /auth/login endpoint with JWT authentication
- Users table with email, password_hash, created_at

Closes: proj-auth.5, proj-auth.6, proj-auth.7"

✓ Closed 3 tasks

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Progress: 7/8 tasks complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Example 3: Ralph Wiggum Iterative Development

This example shows using Ralph Wiggum loops for iterative tasks like getting tests to pass.

```
AI: /flow:implement

Working on: proj-auth.9: Add comprehensive error handling

[Initial implementation]
✓ Added try-catch blocks to auth service
✓ Added error logging
✓ Added user-friendly error messages

Running tests...
✗ 3 tests failing:
   - Should handle network errors
   - Should handle timeout errors
   - Should handle invalid JSON responses

[Starting Ralph Wiggum loop]
/ralph-loop

Ralph prompt:
```
Task: proj-auth.9 - Add comprehensive error handling

Keep iterating until ALL tests pass:
- Should handle network errors
- Should handle timeout errors
- Should handle invalid JSON responses

For each iteration:
1. Run tests to identify failures
2. Fix the failing test
3. Run tests again
4. If all pass, output: "RALPH COMPLETE: All error handling tests passing"

Max iterations: 10
```

[Ralph iteration 1]
Running tests... 3 failing
Fixed: Added network error detection
Tests... 2 failing

[Ralph iteration 2]
Running tests... 2 failing
Fixed: Added timeout handling with axios interceptors
Tests... 1 failing

[Ralph iteration 3]
Running tests... 1 failing
Fixed: Added JSON parsing error handling
Tests... All passing ✓

RALPH COMPLETE: All error handling tests passing

[Ralph loop exited]
✓ Task proj-auth.9 complete

Committing changes...
git commit -m "feat(auth): add comprehensive error handling

- Network error detection with retry logic
- Timeout handling with configurable limits
- JSON parsing error handling
- All error scenarios now tested and passing

Closes: proj-auth.9"
```

---

## Example 4: Clarification Request

This example shows stopping for clarification when requirements are ambiguous.

```
AI: /flow:implement

Working on: proj-auth.10: Add password reset functionality

[Reading task description...]
Task says: "Users should be able to reset their password via email"

[Analyzing requirements]
⚠️  Clarification needed:

The PRD specifies "users can reset password via email link" but doesn't define:
- Token expiration time
- Whether old tokens should be invalidated
- Maximum number of reset attempts per hour

[Asking user for clarification]

AskUserQuestion({
  questions: [{
    question: "What should be the token expiration time for password reset links?",
    header: "Token Expiry",
    options: [
      { label: "15 minutes", description: "Short-lived tokens for security" },
      { label: "1 hour", description: "Standard expiration time" },
      { label: "24 hours", description: "Long-lived tokens for convenience" }
    ],
    multiSelect: false
  }]
})

User selects: "1 hour"

[Clarification received - continuing implementation]
✓ Implementing password reset with 1-hour token expiration
✓ Old tokens invalidated on new request
✓ Rate limiting: 3 attempts per hour per email

[Implementation continues...]
```

---

## Example 5: Blocked Task Handling

This example shows handling a blocked task when dependencies are not met.

```
AI: /flow:implement

Working on: proj-auth.11: Integrate with OAuth providers

[Analyzing dependencies]
⚠️  Task blocked!

Missing dependencies:
- OAuth provider credentials not configured
- Environment variables OAUTH_GOOGLE_CLIENT_ID, OAUTH_GITHUB_CLIENT_ID not set
- OAuth callback URL not registered with providers

[Updating task status in beads]
Task: proj-auth.11
Status: blocked
Notes: OAuth credentials not configured. User needs to:
1. Create OAuth applications in Google Cloud Console
2. Create OAuth application in GitHub Developer Settings
3. Add credentials to environment configuration

[Notifying user]
❌ Task proj-auth.11 is BLOCKED

Required action: Configure OAuth provider credentials

See task notes for setup instructions.

[Continuing with other unblocked tasks...]
Moving to: proj-auth.12: Write documentation

✓ Task proj-auth.11 marked as blocked (not proceeding)
```

---

## Subagent Type Selection

Tasks are routed to specialized subagents based on metadata:

| Task Type | Subagent | Fallback Agents | Skills |
|-----------|----------|-----------------|--------|
| React component | `frontend-developer` | `react-pro`, `typescript-pro` | `frontend-design` |
| Backend API | `backend-architect` | `api-documenter` | - |
| Database migration | `database-admin` | `sql-pro` | - |
| Tests | `test-automator` | `language-specific` | - |

---

## Completion Protocol

When completing tasks:

1. **Sub-task completion:**
   - Mark task as completed in beads
   - Continue with next ready task

2. **Parent epic completion:**
   - Verify all sub-tasks are complete
   - Run full test suite
   - Stage changes (`git add .`)
   - Create commit with conventional commit message
   - Close parent epic in beads

3. **PRD completion:**
   - Check if all tasks are complete
   - Display completion message
   - Suggest running `/flow:cleanup`
