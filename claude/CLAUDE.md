# Agent Directives: Mechanical Overrides

You are operating within a constrained context window. To produce production-grade code, adhere to these overrides:

## Pre-Work

1. THE "STEP 0" RULE: Before ANY structural refactor on a file >300 LOC, first remove all dead props, unused exports, unused imports, and debug logs from the files you are about to touch. Commit this cleanup separately before starting the real work. A smaller file is cheaper to re-read and safer to edit.

2. PHASED EXECUTION: Break work into explicit phases. Each phase touches no more than 5 files. Complete the phase, run verification, and commit before starting the next. After each phase, post a one-line status report. If a phase surfaces anything unexpected (architectural problems, errors outside the task's scope, ambiguity in requirements), STOP and report to the user before continuing — do not silently expand the plan.

3. UNRELATED ERRORS: If you encounter pre-existing or unrelated errors:
   - If they block the current task, fix them and note it in the commit message.
   - If they don't block the task, log them as `bd` (Beads) issues and move on. Do NOT expand the diff to fix them in-band.
     The codebase trajectory should always be toward clean and error-free, but each task's diff stays scoped to that task.

4. GRILL THE USER: Before implementation, if the task is complicated or ambiguous, ask the user if they want to run `/grill-me` or `/grill-with-docs` to align on what needs to be implemented. Planning with the user is always preferred over guessing.

## Code Quality

5. PROPOSE, DON'T SMUGGLE: If you spot flawed architecture, duplicated state, or inconsistent patterns while working, ask: "What would a senior, perfectionist dev flag in code review?" Then SURFACE those findings to the user — as a short proposal or `bd` issues — rather than implementing them unasked. Default to the simplest implementation that satisfies the task; structural fixes happen only after the user agrees. This applies to the user's prompts too:
   - "update a CI job to only trigger on these files" → check what other files should plausibly be watched and ask the user to confirm before adding them.
   - "add permission guards for a certain account role" → push back or suggest improvements if the design seems off.

6. PUSHBACK: If you think the user is over-engineering, or there is a clearly better way, say so and suggest the alternative. If the user insists on their approach after hearing it, follow their approach.

7. FORCED VERIFICATION: A successful file write does not mean working code. You are FORBIDDEN from reporting a task as complete until you have:
   - Run `npx tsc --noEmit` (or the project's equivalent type-check)
   - Run the configured linters/formatters: `npx eslint . --quiet`, `vp lint`, `biome check`, `ruff check`, `ruff format`
   - For frontend work, verified in a browser via `/playwright-cli` or `chrome-devtools-mcp` (`chrome-devtools-mcp` preferred — it gets an authenticated Chrome instance)
   - Fixed all errors _introduced by your changes_ (pre-existing errors follow rule 3)
     If no type-checker is configured, state that explicitly instead of claiming success.

## Context Management

8. SUB-AGENTS FOR EXPLORATION, NOT PARALLEL EDITS: For tasks requiring analysis of >5 independent files, launch parallel sub-agents to read, search, and summarize (5-8 files per agent) — each gets a fresh context window. EDITS are then applied serially by the main agent using those summaries. Never have multiple agents editing interdependent files concurrently.

9. RE-READ BEFORE EVERY EDIT: Before EVERY file edit, re-read the file (or at least the region being edited). After editing, read it again to confirm the change applied. Do not trust your memory of file contents — context may have been compacted, and the Edit tool fails silently when old_string doesn't match stale context. Never batch more than 3 edits to the same file without a verification read. This applies with extra force after 10+ messages in a conversation.

10. CHUNKED READS: For files over 500 LOC, read in sequential chunks using offset/limit parameters. Never assume a single read showed you the complete file — check the line count first.

11. SUSPECT TRUNCATION: Large tool results may be truncated. If a search or command returns suspiciously few results for its scope, re-run it with a narrower scope (single directory, stricter glob) and state that you suspected truncation.

12. AST GREP: `ast-grep` can search the codebase by AST structure instead of text. Use the `/ast-grep` skill to learn its query syntax when text grep is too noisy.

## Edit Safety

13. NO SEMANTIC SEARCH ASSUMPTIONS: You have grep, not a compiler's reference index. When renaming or changing any function/type/variable, search separately for:
    - Direct calls and references
    - Type-level references (interfaces, generics)
    - String literals containing the name
    - Dynamic imports and require() calls
    - Re-exports and barrel file entries
    - Test files and mocks
      Do not assume a single grep caught everything. Prefer `ast-grep` for structural renames.

# Development Tool Preferences

These are tools I prefer to use during development. If you think a tool is a great fit for a project, feel free to suggest integrating it.

- `tmux` — use tmux commands to find the window the dev server is started in
- `portless` — any project requiring a dev server should use it to prevent port conflicts
- `wt` (Worktrunk CLI) — manage worktrees
- `bd` (Beads) — track issues instead of the TaskList in Claude Code
- `http` (HTTPie) — request testing instead of `curl`
- `rg` — instead of `grep`
- `ast-grep` — structural codebase search

@RTK.md
