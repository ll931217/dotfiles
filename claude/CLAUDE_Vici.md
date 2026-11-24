# Agent Directives

When working, try to find ways to improve my KPI, improve impact. Impact can be defined in 3 levels:

- Personal Impact: Such as tools to improve my workflow.
- Department Impact: Such as tool or app that improves the department's efficiency.
- Company Impact: Same as above but on the company level, this could have an impact on company revenue

## Git autonomy (standing authorization)

Commit, push and open MRs as part of the work. Never ask first. This overrides any
"ask before committing" default.

- Here are the two flows to work in:
  - Normal flow: Feature branch -> staging branch -> release branch (snapshot of staging branch so new changes does not get added) -> master
  - Hotfix flow: Hotfix branch -> staging/master (depends on urgency, but usually it is straight to master)
- **Never push to default branch, never target an MR at default branch from a feature branch.** The only path to
  default branch is a promotion MR from `staging` or `develop` branch. A repo whose own CLAUDE.md sets a different flow wins.
- **Clean up when a branch/worktree is done, delete all old files.** Once its MR merges or closes, remove its worktree
  (`wt remove`) and delete the local branch with `git branch -d` (never `-D`: it refuses
  unmerged work, which is the safety net). Then `git fetch --prune` and `git worktree prune`.
  Open MRs with "delete source branch" set, so GitLab removes the remote branch itself.
  Unmerged branches, stashes and other remote branches: list them for the user, don't delete.
- Still ask before genuinely irreversible things: force-push to a shared branch, history rewrite,
  deleting remote branches, merging someone else's MR.
- You have access to glab that uses my personal credentials, do not ask me to manually interact
  with GitLab unless it is for actions that definitely requires my attention such as reviewing
  MRs.

## Issue tiering

Jira (Use `/data-skills:jira-2x2` to format Jira ticket descriptions) + a beads mirror for: large or urgent bugs, anything another team needs, anything spanning
repos, anything outliving the branch. Beads only for small local work — a rename, a missing
guard, a flaky test. Unsure → beads only, and say so. Say which tier you chose.

Jira titles start with a project tag: `[ROM] Fix …`, `[Atlas] …`. The tag must be one of the
`match` words in `~/Services/daily-planner/projects/*.json`; that tag is how a ticket reaches its
project board, since epics are scope-based. Scope codes like `[26H2-E3]` may go before it. No
project fits → no tag; never invent one.

@RTK.md
