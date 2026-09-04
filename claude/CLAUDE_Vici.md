# Agent Directives: Mechanical Overrides

You are operating within a constrained context window. To produce production-grade code, adhere to these overrides:

## Brain-first protocol

You have a knowledge brain connected over MCP (gbrain and dept-brain). Before answering any question
about people, companies, decisions, projects, or past context:

1. **Search first.** Call `search` (or `query` for a synthesized answer) against
   the brain BEFORE answering from memory or asking me. If the brain has the
   answer, use it. Never ask "who is X?" or "what did we decide about Y?" before
   searching — the brain probably already knows.
2. **Write back.** When I make a decision, mention a new person/company, or land
   on an idea worth keeping, write it to the brain with `put_page` (entity pages
   under people/, companies/; decisions under decisions/ or notes/). One insight,
   one page, linked.
3. **Cite.** When you answer from the brain, name the page you used.

## Pre-Work

1. THE "STEP 0" RULE: Before ANY structural refactor on a file >300 LOC, first remove all dead props, unused exports, unused imports, and debug logs from the files you are about to touch. Commit this cleanup separately before starting the real work. A smaller file is cheaper to re-read and safer to edit. Check /jira for any issues that could be related to what I am working on and keep that issue up to date, jira should never drift from the codebase. If an issue doesn't exist there are rules to how to create a new jira issue:

- Check if the work is related to some issue then create a subtask, otherwise create it as a task
- We have epics for each half of a year (H1, H2), make sure to create tickets under those epics
- We have a dedicated epic for maintenance work which does not belong to the Epics that are the main goals of the H1 or H2. Make sure maintenance work is under those epics for better tracking.
- Tracked jira issues should be in `<repo_root>/.claude/jira_issues` — this file lists the in-progress **Jira** issues for this repo. Beads-only issues do NOT belong in it; see the tiering rule under Agentic Workflow.

1. PHASED EXECUTION: Break work into explicit phases. Each phase touches no more than 5 files. Complete the phase, run verification, and commit before starting the next. After each phase, post a one-line status report. If a phase surfaces anything unexpected (architectural problems, errors outside the task's scope, ambiguity in requirements), STOP and report to the user before continuing — do not silently expand the plan.

2. UNRELATED ERRORS: If you encounter pre-existing or unrelated errors:
   - If they block the current task, fix them and note it in the commit message.
   - If they don't block the task, log them as `bd` (Beads) issues and move on. Do NOT expand the diff to fix them in-band.
     The codebase trajectory should always be toward clean and error-free, but each task's diff stays scoped to that task.

3. GRILL THE USER: Before implementation, if the task is complicated or ambiguous, ask the user if they want to run `/grilling` to align on what needs to be implemented. Planning with the user is always preferred over guessing.

## Code Quality

1. PROPOSE, DON'T SMUGGLE: If you spot flawed architecture, duplicated state, or inconsistent patterns while working, ask: "What would a senior, perfectionist dev flag in code review?" Then SURFACE those findings to the user — as a short proposal or `bd` issues — rather than implementing them unasked. Default to the simplest implementation that satisfies the task; structural fixes happen only after the user agrees. This applies to the user's prompts too:
   - "update a CI job to only trigger on these files" → check what other files should plausibly be watched and ask the user to confirm before adding them.
   - "add permission guards for a certain account role" → push back or suggest improvements if the design seems off.

2. PUSHBACK: If you think the user is over-engineering, or there is a clearly better way, say so and suggest the alternative. If the user insists on their approach after hearing it, follow their approach.

3. FORCED VERIFICATION: A successful file write does not mean working code. You are FORBIDDEN from reporting a task as complete until you have:
   - Run `npx tsc --noEmit` (or the project's equivalent type-check)
   - Run the configured linters/formatters: `npx eslint . --quiet`, `vp lint`, `biome check`, `ruff check`, `ruff format`
   - For frontend work, verified in a browser via `/playwright-cli` or `chrome-devtools-mcp` (`chrome-devtools-mcp` preferred — it gets an authenticated Chrome instance)
   - Fixed all errors _introduced by your changes_ (pre-existing errors follow rule 3)
     If no type-checker is configured, state that explicitly instead of claiming success.

## Context Management

1. SUB-AGENTS FOR EXPLORATION, NOT PARALLEL EDITS: For tasks requiring analysis of >5 independent files, launch parallel sub-agents to read, search, and summarize (5-8 files per agent) — each gets a fresh context window. EDITS are then applied serially by the main agent using those summaries. Never have multiple agents editing interdependent files concurrently.

2. RE-READ BEFORE EVERY EDIT: Before EVERY file edit, re-read the file (or at least the region being edited). After editing, read it again to confirm the change applied. Do not trust your memory of file contents — context may have been compacted, and the Edit tool fails silently when old_string doesn't match stale context. Never batch more than 3 edits to the same file without a verification read. This applies with extra force after 10+ messages in a conversation.

3. CHUNKED READS: For files over 500 LOC, read in sequential chunks using offset/limit parameters. Never assume a single read showed you the complete file — check the line count first.

4. SUSPECT TRUNCATION: Large tool results may be truncated. If a search or command returns suspiciously few results for its scope, re-run it with a narrower scope (single directory, stricter glob) and state that you suspected truncation.

5. AST GREP: `ast-grep` can search the codebase by AST structure instead of text (`ast-grep --help` for query syntax). Use it when text grep is too noisy.

## Edit Safety

1. NO SEMANTIC SEARCH ASSUMPTIONS: You have grep, not a compiler's reference index. When renaming or changing any function/type/variable, search separately for:

- Direct calls and references
- Type-level references (interfaces, generics)
- String literals containing the name
- Dynamic imports and require() calls
- Re-exports and barrel file entries
- Test files and mocks
  Do not assume a single grep caught everything. Prefer `ast-grep` for structural renames.

1. ALWAYS use CLI tools available in your arsenal instead of writing Python code that does exactly what CLI tools are meant for, such as `sed`, `awk` or the ones listed in the [tools](#tools) section

# Git Autonomy (standing authorization)

Committing, pushing, and opening merge requests are NOT gated — do them automatically as part of
the work, never ask first. This overrides any "conservative / ask before committing" default in a
repo's Beads block or tool instructions.

**Never push to `main`. Never target an MR at `main` from a feature branch.** The only path to
`main` is a promotion MR from `staging`.

The flow, always, no shortcuts:

    task → worktree → implement → commit → push → MR into `staging` → promotion MR `staging` → `main`

- One worktree per task (`wt`), branched off `staging`.
- Verify before pushing: the project's check/lint/type/test command, plus a browser check for UI work.
- The feature MR targets `staging`. Promoting `staging` to `main` is its own MR, opened separately.
- If a repo has no `staging` branch, create it from `main` before opening the MR.
- Still ask before genuinely destructive or irreversible things (force-push to a shared branch,
  history rewrite, deleting remote branches, merging someone else's MR).
- After each MR exists, watch the pipeline to green (`~/.scripts/glab-watch-mr.sh`).
- **Simple MRs do not need the user.** A docs / chore / style / test MR that passes the
  eligibility gate (green pipeline, discussions resolved, no CI / migration / dependency /
  infra / secret paths touched, small diff) gets reviewed by a subagent and merged via
  `<plugin>/scripts/mr-automerge.py --merge <iid> --yes`, then reaped. Everything else still
  goes to the user. Never widen the gate to fit a particular MR — that is the signal it is
  not simple.
- **Once an MR merges, clean up after it in the same breath**: remove the worktree, delete the
  local branch, and drop any MR-watch cron entry for it. Use
  `<plugin>/scripts/worktree-reap.py --all` (dry run) then `--reap`. It only
  touches branches whose MRs are all merged, with a clean tree and nothing unpushed — anything
  it cannot prove is finished it keeps and reports. A squash-merged branch needs `-D`; the
  script does that itself, only after those checks pass.

# Agentic Workflow

- When defining tasks, spawn DoD teammates: 4 core lenses always (intent, tests, discipline, prefs) plus 1-3 domain lenses chosen from the agent pool in `~/.claude/agents/` to match what the task touches (UI work gets frontend/UX reviewers, backend gets architect, SQL gets sql-pro, auth gets security-reviewer, and so on). They define the definition of done (DoD); the orchestrator asks them to verify the implementation matches it, and keeps fixing until every lens passes.
- Subagents are used to do research.
- ISSUE TIERING — not every issue needs Jira. Decide by size and urgency, and say which tier you picked:
  - **Jira + beads** — a large bug, an urgent bug, anything another person or team needs to see, anything spanning more than one repo, or anything that will outlive the current branch. Mirror it in beads and add it to `<repo_root>/.claude/jira_issues`.
  - **beads only** — small, local, self-contained work: a rename, a missing guard, a flaky test, a cleanup found in passing. Do not create Jira noise for these.
  - Unsure → beads only, and say so. Promoting a beads issue to Jira later is cheap; a backlog full of trivia is not.
- THE LINK IS DIRECTIONAL, and this is what keeps Jira from drifting:
  - **Every Jira key in `.claude/jira_issues` MUST have a beads mirror labelled `jira:<key>`.** That mirror is where the work happens, so Jira status follows it. A Jira key with no labelled bead is an orphan — nothing will ever update it; create the mirror or drop the key.
  - **The reverse does not hold.** A beads issue with no `jira:` label is complete on its own — it is not "unmapped" and needs no Jira parent.
  - A mirrored bead carries the link **twice, for two different readers**: the `jira:<key>` label (machine — queryable, what an audit keys on) AND a first line in its description carrying the key _with the parent's title_, e.g. `Jira: DE-1765 — [ROM] release tags should reach the remote before the branch push`. A bare key in the body only moves the lookup; the title removes it. If the label and the body disagree, that is a copy-paste error — trust the label and fix the body.
  - Do NOT write bead IDs into Jira. They are repo-local, so `master-cl6` is unresolvable for a teammate — a worse link than none. The MR URL is the return path.
  - When a Jira issue closes, remove its key from `.claude/jira_issues`; the file lists _in-progress_ work, not history.
- ISSUE TITLE FORMAT — `[SYSTEM] <subject/condition> should <expected behaviour>`, e.g. `[AMS] IsFINI = true accounts should be excluded from the nightly settlement run`. A reader must know the system and the condition without opening the ticket. No bare "fix bug" / "update logic" titles.
- ISSUE DESCRIPTION — cover **why, what, where, when, how** (4W1H), one short line each, no essays:
  - **Why** — the impact if left alone; what broke or what it costs
  - **What** — the current behaviour vs the expected behaviour
  - **Where** — system, repo, file or table
  - **When** — when it triggers (which condition, which schedule, since which change)
  - **How** — the intended fix or the next investigative step
- When a task is parked as blocked, log it: `~/.scripts/blocker-log.py block --task <key> --title <short title> --class access|decision|dependency|premise|external|flake|other --reason <why>`. Log `clear --task <key> --by <who>` the moment it frees up — the wait time is the cost number. `report` groups by class; a class with 2+ hits is a process fix, not a ticket fix. Log: `<global-memory>/blocker_log.tsv`.
- If a beads issue grows past the tiering line (turns out large, urgent, or someone else needs it), ask whether to promote it to Jira — and if a related task/subtask already exists, offer to attach it there instead of opening a new one.
- Never write an entire story in comments, keep it simple, structured and to the point. We don't need some background of what this code-block or file is about
- Never leave jira or bead issue IDs in the codebase, including docs and comments
- Default to writing no comments. Never write multi-paragraph docstrings or multi-line comment blocks — one short line max.
- When there is a PR/MR for the branch, please make sure that you verify E2E, this means that if the pipeline fails then you are required to fix the pipeline and verify again until the pipeline is green
- Remove all mannered prose

# VICI Company Internal Infrastructure

## Firewall

Our company has a corporate firewall that blocks all access to the external network unless we explicitly open a ticket to have access to the internet or access certain services using our internal proxy server. Here is the envs for our proxy server:

```bash
export NO_PROXY="172.21.0.0/16,harbor.vidi.com:8081,.anthropic.com,.viciholdings.com,.vici.corp,.vidi.com,localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/20,192.168.0.0/16,huggingface.co"
export http_proxy="http://172.21.10.22:8888/"
export https_proxy="http://172.21.10.22:8888/"
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$https_proxy"
export ELECTRON_GET_USE_PROXY="$https_proxy"
```

I have the above envs setup as `proxied` zsh function.

I have opened access to [HuggingFace](huggingface.co), so at least we have that access available.

## Docker

We can reach 2 external registries with the proxy enabled:

- ghcr
- Docker Hub

We can also use our local Harbor registries:

- harbor.vidi.com:8081: this will be deprecated since this was originally hosted by our team
- harbor.vici.corp: this is the official company wide registry, we are migrating to this registry

## Sonatype Nexus Repository

Our packages are routed through Sonatype Nexus Repository — package installation failures (pypi/npm unreachable) are usually firewall/Nexus routing; use the `vici-infra-reference` skill for the Nexus API query.

## GitLab

We use a self-hosted GitLab instance that can be accessed at [GitLab](https://gitlab.data.vici.corp), our GitLab server is hosted on 172.21.10.106.

## Network Infrastructure

We currently have 2 nginx instances that are responsible for routing network requests:

- 172.21.10.133: This is the main nginx, it is newly setup to route all requests, all routing configuration are located at `/etc/nginx/sites-available/`. All `*.data.vici.corp` URLs are routed through this nginx instance, it also has a custom self-signed certificate loaded.
- 172.21.10.106: This is the old nginx instance, it serves on `*.vidi.com` which we are trying to deprecate but didn't have the time to do so.

## Komodo

We have recently started using Komodo to get our system setup, use the `/komodo` skill to learn how to interact with Komodo if you need to, it should have information about all our servers, as well as the containers that are available in each server. If you discover that a system (container or stack) isn't in Komodo, please suggest adding to improve observability (local dev services should not be included in Komodo, unless it is for personal use).

## HyperDX

We have recently started using HyperDX (Part of ClickStack) to store our logs, it has a 30-days TTL set in the table schema. Invoke `/hyperdx` skill when wanting to get logs of a docker container or create dashboards for certain use-cases. We have implemented a Komodo Resource Sync inside <https://gitlab.data.vici.corp/infra/komodo>, which handles otel-collector setup for different servers, if a server is not found, suggest to the user to onboard the server with the Komodo repository.

# My Development Preferences

For coding conventions please follow `/scaffold-project` skill.

## Directories

- ~/GitHub/: Stores all GitHub cloned repos, libraries that I want to take a look at etc
- ~/Projects/: Main projects directory, all project repos I work on will be located here.
- ~/Services/: Most services I use or manage are placed here
- ~/testing/: This is mainly my testing directory

## Tools

These are tools I prefer to use during development. If you think a tool is a great fit for a project, feel free to suggest integrating it.

- `tmux` — use tmux commands to find the window the dev server is started in
- `portless` — any project requiring a dev server should use it to prevent port conflicts
- `wt` (Worktrunk CLI) — manage worktrees
- `bd` (Beads) — track issues instead of the TaskList in Claude Code
- `http` (HTTPie) — request testing instead of `curl`
- `~/.scripts/glab-watch-mr.sh` — watch a GitLab MR + its pipeline; notifies on every state change and again when it merges/closes. Use this whenever I ask to monitor/watch an MR or its pipeline (run from inside the repo). `glab-watch-mr.sh [<iid>|<branch>]`, `--once` for a single status, `INTERVAL=<sec>` to change poll rate.
- `rg` — instead of `grep`
- `ast-grep` — structural codebase search
- `gopass` - use this to get tokens, keys, and passwords for various services I maintain. For example my authentik credentials are `liangshih.lin` and password is `liang_pw` from gopass

## VICI Related

One of our KPI sections are about:

- How we use agents?
- Did we use agents?

Reason behind this is to let LLM and AI agents help us with our work, such as:

- Automate repetitive work
- Use agents to improve our workflow
- Use agents to increase our productivity
- Use agents to improve our code quality
- Use agents to find solutions that can have a great impact on the company

Whenever you work on something, you should think about all of this, you can get more context of the company or of what I have worked on in gbrain. When you have suggestions, feel free to let me know, lets improve together, help me get a high KPI score.

@RTK.md

# graphify

- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
  When the user types `/graphify`, invoke the Skill tool with `skill: "graphify"` before doing anything else.
