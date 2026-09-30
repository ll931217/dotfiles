# Agent Directives

Overrides for a constrained context window. Reference material that used to live here is now in
memory and arrives by recall cue — infrastructure and the proxy, directory layout and tool
preferences, Jira epic placement and the blocker log, the agent-use KPI. Ask for it by name if a
cue does not fire.

## Working

1. **PHASED EXECUTION.** Break work into phases of at most 5 files. Verify, commit, then start the
   next; one-line status per phase. Anything unexpected — architectural trouble, errors outside
   the task, ambiguity — STOP and report rather than silently widening the plan.
2. **STEP 0 BEFORE A BIG REFACTOR.** Before restructuring any file over 300 LOC, first delete dead
   props, unused exports and imports, and debug logs from the files you are about to touch, and
   commit that separately. A smaller file is cheaper to re-read and safer to edit.
3. **UNRELATED ERRORS.** Blocking the task → fix, and say so in the commit. Not blocking → log a
   `bd` issue and move on. The codebase trends clean; each diff stays scoped.
4. **GRILL FIRST.** If the task is complicated or ambiguous, offer `/grilling` before implementing.
   Planning beats guessing.

## Code quality

1. **PROPOSE, DON'T SMUGGLE.** Spotting flawed architecture, duplicated state or inconsistent
   patterns → surface it as a short proposal or a `bd` issue. Do not implement it unasked. Default
   to the simplest thing that satisfies the task. This applies to the user's own asks too: "watch
   these files in CI" deserves "should it also watch these?" before you add them.
2. **PUSHBACK.** Over-engineering, or a clearly better way — say so. If the user reaffirms after
   hearing it, build their version.
3. **FORCED VERIFICATION.** Never report done before running the project's type-check, its
   linters/formatters, and — for frontend work — a real browser check (`chrome-devtools-mcp`
   preferred, else `/playwright-cli`). Fix what your change introduced. No type-checker configured
   → say that explicitly instead of implying success.

## Context

1. **SUB-AGENTS EXPLORE, THEY DO NOT EDIT.** More than 5 independent files to analyse → parallel
   sub-agents read and summarise (5-8 files each). Edits are applied serially by the main agent.
   Never two agents editing interdependent files at once.
2. **RE-READ BEFORE EVERY EDIT**, and read back after. Edit fails silently when `old_string`
   matches stale context. Never batch more than 3 edits to one file without a verification read.
3. **CHUNKED READS** for files over 500 LOC; check the line count first.
4. **SUSPECT TRUNCATION.** Suspiciously few results for the scope → re-run narrower, and say you
   suspected it.

## Edit safety

1. **NO SEMANTIC SEARCH ASSUMPTIONS.** You have grep, not a compiler's reference index. Renaming
   anything, search separately for: direct references, type-level references, string literals,
   dynamic imports and `require()`, re-exports and barrel files, tests and mocks. Prefer
   `ast-grep` for structural renames.
2. **USE THE CLI TOOL**, not Python that reimplements `sed` / `awk` / `rg`.
3. **NEVER leave a Jira key or bead ID in the codebase** — comments and docs included. They are
   unresolvable to anyone outside this repo.

## Git autonomy (standing authorization)

Commit, push and open MRs as part of the work. Never ask first. This overrides any
"ask before committing" default.

**Never push to `main`, never target an MR at `main` from a feature branch.** The only path to
`main` is a promotion MR from `staging`. (A repo whose own CLAUDE.md sets a different flow — e.g.
straight to `master` — wins for that repo.)

    task → worktree → implement → commit → push → MR into staging → promotion MR staging → main

- One worktree per task (`wt`), branched off `staging`; create `staging` from `main` if absent.
- Verify before pushing: check/lint/type/test, plus a browser check for UI.
- Watch the pipeline to green (`~/.scripts/glab-watch-mr.sh`), and spawn a `/code-review` subagent
  on every new MR without being asked.
- Still ask before genuinely irreversible things: force-push to a shared branch, history rewrite,
  deleting remote branches, merging someone else's MR.
- **Simple MRs do not need the user** — docs/chore/style/test, green pipeline, discussions
  resolved, no CI/migration/dependency/infra/secret paths, small diff: review by subagent, then
  `<plugin>/scripts/mr-automerge.py --merge <iid> --yes`, then reap. Never widen the gate to fit
  an MR; needing to is the signal it is not simple.
- **Cleanup is part of merging**, not a question: `<plugin>/scripts/worktree-reap.py --all` to dry
  run, then `--reap`. It refuses anything it cannot prove finished.

## Agentic workflow

- Defining tasks → spawn DoD teammates: 4 core lenses (intent, tests, discipline, prefs) plus 1-3
  domain lenses from `~/.claude/agents/` matching what the task touches. They define done; the
  orchestrator verifies against it and keeps fixing until every lens passes.
- **ISSUE TIERING.** Jira + a beads mirror for: large or urgent bugs, anything another team needs,
  anything spanning repos, anything outliving the branch. Beads only for small local work — a
  rename, a missing guard, a flaky test. Unsure → beads only, and say so. Say which tier you chose.
- Comments: default to none. One short line maximum, never a paragraph or a multi-line block.
- A repo with a pipeline: an MR is not done until the pipeline is green. Fix it and re-verify.

@RTK.md
