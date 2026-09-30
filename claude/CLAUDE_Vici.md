# Agent Directives

Overrides for a constrained context window. Reference material that used to live here is now in
memory and arrives by recall cue — infrastructure and the proxy, directory layout and tool
preferences, Jira epic placement and the blocker log, the agent-use KPI. Ask for it by name if a
cue does not fire. Anything the agent-discipline plugin already enforces (verification, tracker
IDs, comment density, subagent edits, pipeline watch, reap, automerge, DoD lenses) lives in its
`rules/` and hooks, not here.

## Working

1. **PHASED EXECUTION.** Break work into phases of at most 5 files. Verify, commit, then start the
   next; one-line status per phase. Anything unexpected — architectural trouble, errors outside
   the task, ambiguity — STOP and report rather than silently widening the plan.
2. **STEP 0 BEFORE A BIG REFACTOR.** Before restructuring any file over 300 LOC, first delete dead
   props, unused exports and imports, and debug logs from the files you are about to touch, and
   commit that separately.
3. **UNRELATED ERRORS.** Blocking the task → fix, and say so in the commit. Not blocking → log a
   `bd` issue and move on.
4. **GRILL FIRST.** If the task is complicated or ambiguous, offer `/grilling` before implementing.

## Code quality

1. **PROPOSE, DON'T SMUGGLE.** Spotting flawed architecture, duplicated state or inconsistent
   patterns → surface it as a short proposal or a `bd` issue. Do not implement it unasked. This
   applies to the user's own asks too: "watch these files in CI" deserves "should it also watch
   these?" before you add them.
2. **PUSHBACK.** Over-engineering, or a clearly better way — say so. If the user reaffirms after
   hearing it, build their version.
3. **BROWSER CHECK** for frontend work: `chrome-devtools-mcp` preferred, else `/playwright-cli`.
   No type-checker configured → say that explicitly instead of implying success.

## Context and edit safety

1. **SUSPECT TRUNCATION.** Suspiciously few results for the scope → re-run narrower, and say you
   suspected it.
2. **NO SEMANTIC SEARCH ASSUMPTIONS.** You have grep, not a compiler's reference index. Renaming
   anything, search separately for: direct references, type-level references, string literals,
   dynamic imports and `require()`, re-exports and barrel files, tests and mocks. Prefer
   `ast-grep` for structural renames.
3. **USE THE CLI TOOL**, not Python that reimplements `sed` / `awk` / `rg`.

## Git autonomy (standing authorization)

Commit, push and open MRs as part of the work. Never ask first. This overrides any
"ask before committing" default.

- **Never push to `main`, never target an MR at `main` from a feature branch.** The only path to
  `main` is a promotion MR from `staging`. A repo whose own CLAUDE.md sets a different flow wins.
- Spawn a `/code-review` subagent on every new MR without being asked.
- Still ask before genuinely irreversible things: force-push to a shared branch, history rewrite,
  deleting remote branches, merging someone else's MR.

## Issue tiering

Jira + a beads mirror for: large or urgent bugs, anything another team needs, anything spanning
repos, anything outliving the branch. Beads only for small local work — a rename, a missing
guard, a flaky test. Unsure → beads only, and say so. Say which tier you chose.

@RTK.md
