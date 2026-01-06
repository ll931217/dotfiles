# Auto-Compaction Detection Protocol

## Overview

Claude Code automatically compacts long conversations to manage token limits. This protocol ensures you maintain accurate context about current PRD status and task progress.

## Detection Checklist

**Check these conditions BEFORE starting any task:**

- [ ] **Initial Read:** When first reading the workflow, check "Last Refresh" timestamp
- [ ] **Time Threshold:** Is timestamp > 30 minutes old?
- [ ] **Task Milestone:** Have you completed ~5 tasks since last refresh?
- [ ] **Group Start:** Are you about to start a [P:Group-X] parallel task group?
- [ ] **After Blocker:** Did you just resolve a blocked task?
- [ ] **Context Uncertainty:** Do you feel unsure about current state?

## Refresh Procedure

If ANY checkbox above is checked:

1. **Execute summary command:** Type `/flow:summary` in your response
2. **Wait for output:** The command will execute and return current status
3. **Update the status section:**
   - Replace content between `==== LATEST SUMMARY ====` markers
   - Update "Last Refresh" to current timestamp
   - Use format: `YYYY-MM-DD HH:MM UTC`
4. **Verify alignment:** Ensure you're working on correct tasks
5. **Resume workflow:** Continue with your planned task

## Example Agent Response

```
I notice the "Last Refresh" timestamp is 45 minutes old. Let me refresh the context to ensure I have the current state.

/flow:summary

[summary output appears]

Updating Current Status section with latest summary...

Last Refresh updated to: 2026-01-02 14:30 UTC

I can see from the summary that 3/8 tasks are complete and I should continue with proj-auth.3. Let me proceed with implementing the login endpoint.
```

## Integration Points

This protocol integrates with existing workflow sections:

| Integration Point | When to Refresh |
|------------------|-----------------|
| **PRD Discovery** | Refresh after discovering and validating PRD |
| **Parallel Groups** | REQUIRED refresh before starting [P:Group-X] |
| **PRD Changes** | REQUIRED refresh if PRD version changes |
| **Blocker Resolution** | Refresh after unblocking tasks |
| **Completion Check** | Refresh before checking PRD completion status |

## Status Section Format

The status section should be placed at the top of the implementation workflow:

```markdown
## Current Status

<!-- AUTO-COMPACTION DETECTION ZONE -->

**Last Refresh:** [Initial - Not yet refreshed]

**Instructions for AI Agent:**
If you are reading this workflow and ANY of the following are true:

1. The "Last Refresh" timestamp is more than 30 minutes old
2. You suspect the conversation has been auto-compacted by Claude Code
3. You feel unsure about the current task state or progress
4. You are about to start a [P:Group-X] parallel task group

**Then execute:** `/flow:summary`

After executing `/flow:summary`, replace the content between the `==== LATEST SUMMARY ====` markers below with the new output and update the "Last Refresh" timestamp.

**Current Status Summary:**

==== LATEST SUMMARY ====

<!--
[Paste /flow:summary output here]

Example format:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Feature: User Authentication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 PRD: prd-authentication-v2.md (version: 2)
   Status: ✅ approved
   Branch: feature/auth
   Worktree: feature-auth

📝 Overview:
Implement secure user authentication with email/password...

📊 Progress: 3/8 tasks completed
[████████░░░░░░░░░░░░░] 37%

⏳ What's Left (5 tasks):
   📦 Authentication Core
      ⏳ proj-auth.3: Implement login endpoint
      ⏳ proj-auth.4: Implement password hashing
   📦 Session Management
      ⏳ proj-auth.5: Create session storage
      ⏳ proj-auth.6: Implement token refresh
   📦 Testing
      ⏳ proj-auth.7: Write unit tests

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-->

==== END LATEST SUMMARY ====

<!-- END AUTO-COMPACTION DETECTION ZONE -->
```

## Critical Refresh Points

### Before Parallel Groups (REQUIRED)

Before starting ANY [P:Group-X] parallel task group, you MUST execute `/flow:summary` to ensure you have the current task state. Parallel groups require accurate context about dependencies and blocking issues.

### After PRD Changes (REQUIRED)

Execute `/flow:summary` immediately after ANY PRD version change to update your understanding of the changed requirements and task structure.

### Periodic Refresh (Recommended)

Every 5 completed tasks or 30 minutes of work, execute `/flow:summary` to refresh your context and update the "Current Status" section.

## Context Loss Indicators

Watch for these signs that context may have been lost:

- Task IDs don't match current beads database
- PRD references point to non-existent versions
- Summary shows completed tasks you don't remember
- Blocking dependencies don't make sense

When any of these occur, immediately execute `/flow:summary`.
