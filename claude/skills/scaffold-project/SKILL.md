---
name: scaffold-project
description: >-
  Scaffold the project structure for a new codebase — backend/REST/HTTP API
  services, workers, CLIs, queue consumers, or frontend apps. Use whenever a
  user wants to start, set up, lay out, or bootstrap a new project and asks for
  clean, layered organization: thin entry-point handlers, business logic in
  injectable services, data access behind repositories or interfaces, validated
  DTOs, central error handling, and dependency-injection wiring (backend); or
  feature-based folders, a typed API layer, and clear state boundaries
  (frontend); or screens/widgets over framework-free services, non-blocking
  workers, a declared keymap, and safe terminal restore (TUI). Trigger on
  phrases like "lay out the project," "set up the project skeleton," "create
  the initial folder structure," "scaffold a [framework] api/app," "scaffold
  a TUI," "build a terminal UI," "module/service/repository separation,"
  "properly layered not one big main file," or "architected like NestJS/Spring
  Boot/clean architecture." Works for any language or framework — Express,
  NestJS, FastAPI, Go/gin, Rust/axum, C#/EF Core, Java/Spring, Ruby, PHP,
  React, Next.js, Vue, Svelte, Textual, Ink, Bubble Tea, Ratatui. Also writes
  the conventions into CLAUDE.md. Also use it to bring an EXISTING codebase
  onto the same shape, since the point is that every repo has the identical
  structure and identical quality rules — "make this repo match my other
  repos," "conform this project to my conventions," "refactor this into the
  standard layout," "restructure this repo," "this repo is laid out
  differently," "add the architecture rules to this project," "split this god
  file into layers." Do NOT use for: Dockerfiles/deployment, debugging DI
  errors, or adding an ordinary feature to an already-conforming project.
---

# scaffold-project

This skill scaffolds a new project with a clear architectural shape, **regardless of the implementation language**, and writes the conventions into `CLAUDE.md` so they outlive the scaffolding session.

Three tracks share the same workflow:

- **Backend track** — services with an entry point (HTTP routes, CLI commands, queue consumers, cron jobs). Reproduces the properties popularized by NestJS/Spring: clear feature boundaries, a thin boundary layer, business logic isolated in injectable services, data access hidden behind repository abstractions, validated DTOs at the edge, centralized error handling, all wired with dependency injection. Canonical reference: `references/architecture.md`.
- **Frontend track** — SPA/SSR web apps. Feature-based folders, a typed API layer validated at the boundary, clear state ownership, centralized error handling. Canonical reference: `references/frontend-architecture.md`.
- **TUI track** — interactive terminal apps (Textual, Ink, Bubble Tea, Ratatui). The backend layers with a screen as the boundary, plus the terminal's own hard rules: never block the render loop, framework-free services, a declared keymap, guaranteed terminal restore. Canonical reference: `references/tui-architecture.md`.

The skill produces two things:

1. **A skeleton + one fully-worked reference feature** in the target language/framework, so there's a concrete pattern to copy for every future feature.
2. **A managed `## Architecture` section in `CLAUDE.md`**, so the conventions guide all later code.

## Why this matters

A skeleton rots the moment someone adds a feature that doesn't match it. The CLAUDE.md rules are what keep the architecture honest over time — they're the durable artifact. Treat the generated code as an *example of the rules*, and the rules as the source of truth. When they ever disagree, the rules win.

## Workflow

### 0. Route: new project, or conform an existing one

An **empty or near-empty directory** → scaffold mode, steps 1-5 below.
An **existing codebase** → **conform mode**: steps 1, 2 and 4 unchanged, but step 3 is replaced by "Conform an existing codebase" further down. The target shape is the same either way — that is the entire point. Never invent a different layout because a repo already has one.

### 1. Establish track, language, and framework

Determine the track first: backend (a server-side entry point — HTTP, worker, or a non-interactive CLI), frontend (browser app), or TUI (an *interactive* terminal app that owns the screen and reads keys). A one-shot CLI that prints and exits is backend track; the moment it takes over the terminal and stays running, it is TUI track.

Then establish the language/framework if it isn't already clear. Pick the **idiomatic default framework + wiring approach** from `references/language-mapping.md` (backend), the framework table in `references/frontend-architecture.md` (frontend), or the framework table in `references/tui-architecture.md` (TUI), and state your choice in one line, e.g. *"I'll use FastAPI with `dependency-injector` for Python — say the word if you'd rather use Litestar or Django."* Proceed with the default unless the user redirects. Don't make the user choose from a menu; recommend and move.

If the language isn't in the mapping table, derive the idiomatic equivalent on the fly using the **mapping principles** at the bottom of `references/language-mapping.md`. The architecture is language-agnostic; only the syntax for "decorator," "injectable," and "module" changes.

### 2. Internalize the architecture

Read the track's reference — `references/architecture.md` (backend), `references/frontend-architecture.md` (frontend), or `references/tui-architecture.md` (TUI, which builds on the backend one — read both). It defines the canonical layers and the rules that govern how they may depend on each other. This is what you'll encode in both the skeleton and CLAUDE.md. Don't skip it — the dependency rules (e.g. "controllers never touch repositories directly", "components never call fetch directly", "services never import the TUI framework") are the whole point.

### 3. Scaffold the skeleton and ONE reference feature

Create the directory layout (see the track's reference for the canonical tree) and implement a single, complete reference feature — use the user's domain if they named one (e.g. `users`, `orders`), otherwise default to `users`.

**Backend track** — the reference module must demonstrate all layers:

- **Module/controller/service/repository** with real DI wiring through the composition root. For non-HTTP entry points (CLI command, queue consumer, cron handler), the "controller" is the boundary adapter — same thinness rule.
- **DTOs with validation** at the request boundary.
- **Error handling** via a centralized exception filter/handler and a consistent error response shape.
- **A real persistence layer.** Bind the repository abstraction to a concrete implementation backed by the language's idiomatic ORM/data-access library (see `references/language-mapping.md`). Include the entity↔table mapping, the datasource/connection wiring, and a migration setup if the ORM expects one. Default the connection to a local SQLite/Postgres via env config. The service still depends only on the interface, so the real DB stays swappable and the unit test doesn't touch it.
- **Config + a test** — typed/validated env config loading, and one unit test that demonstrates how to mock the injected repository.

**Frontend track** — the reference feature must demonstrate:

- **One feature folder** with its components, hooks, and API calls colocated.
- **A typed API layer** — API responses validated/typed at the boundary; components never call `fetch` directly.
- **Clear state ownership** — server state via the framework's idiomatic data-fetching layer, local UI state in components; no global store unless warranted.
- **Centralized error handling** — error boundary + consistent API-error surface.
- **Config + a test** — validated env config, and one component or hook test with the API layer mocked.

**TUI track** — the reference screen must demonstrate:

- **One screen + one dumb widget** over a **framework-free service** and a client abstraction, wired in the app's composition root. The service must be importable with no terminal attached.
- **Non-blocking I/O** — the screen dispatches to a worker/async task and renders a loading state immediately. Never await I/O inline in a handler.
- **All three list states** — loading, empty, populated.
- **A declared keymap** — bindings as data next to the screen, with the help overlay generated from that same data.
- **A central error surface + guaranteed terminal restore** — typed domain errors rendered in the UI, and raw mode / alternate screen / cursor restored on every exit path including crash and signal.
- **Config + two tests** — validated config, one headless service test with a fake client, and one pilot test that sends keypresses and asserts the rendered output.

**TypeScript projects (either track):** after scaffolding, also run the `setup-effect` command (`~/.claude/commands/setup-effect.md`) to configure Effect — dependencies, language-service plugin, tsconfig, and its own managed CLAUDE.md section. Where the scaffold has service-layer logic, use Effect idiomatically for it (services/layers, typed errors, `effect/Schema` for DTO validation) rather than ad-hoc equivalents; consult `effect-solutions show <topic>` before writing Effect code.

Keep the reference feature genuinely idiomatic for the language/framework — use the ecosystem's real decorators/annotations/registration mechanism, not a contrived imitation. A Go scaffold should look like good Go; a React scaffold should look like good React, not a NestJS port.

Match the surrounding project if one already exists: reuse its package manager, lint config, and naming style rather than imposing new ones.

### 4. Write the managed CLAUDE.md sections

**Two blocks, always both.** The track block is track-specific; the quality block is identical in every repo — that sameness is the point, so never trim it to fit a project.

Read the track's template — `assets/claude-md-section-backend.md`, `assets/claude-md-section-frontend.md`, or `assets/claude-md-section-tui.md` — **and** `assets/claude-md-section-quality.md` (fixed size limits, YAGNI/DRY thresholds, the SOLID parts the layer rules miss, functional-over-class default, testability and comment rules). Fill in the language/framework specifics, then write both into the project's `CLAUDE.md` **between their managed markers**:

```
<!-- BEGIN scaffold-project -->
...track section...
<!-- END scaffold-project -->

<!-- BEGIN scaffold-project-quality -->
...quality section...
<!-- END scaffold-project-quality -->
```

The quality block's numbers are **not negotiable per project** — do not soften a limit because existing code breaches it. A breach is a finding to record (step 3b), not a reason to raise the number. The only editable placeholders in it are `{{SHARED_DIR}}` and `{{IMMUTABILITY_MECHANISM}}`.

Idempotency rule: each block is replaced in place if its markers already exist. Legacy `<!-- BEGIN scaffold-backend -->` markers are the track block — replace them (and rename the markers) rather than adding a second section. If `CLAUDE.md` exists but has no markers, append the blocks at the end. If there's no `CLAUDE.md`, create one. Never duplicate a section or clobber unrelated content.

### 5. Report

Give a short summary: track and language/framework chosen, the directory tree created, the reference feature's files, and confirmation that both CLAUDE.md sections were written or updated. Point the user at the reference feature as the template to copy for the next one.

## Conform an existing codebase

Replaces step 3 when the repo already has code. The goal is the **same** tree, the same layer rules and the same quality numbers as a freshly scaffolded repo — the deliverable is that a reader cannot tell which repos were scaffolded and which were conformed.

### 3a. Read the repo before proposing anything

Map what exists: entry points, where business logic currently lives, where I/O happens, existing tests, package manager, lint config, naming style. Keep the repo's package manager and lint config; conform the *architecture*, not the toolchain.

### 3b. Produce a conformance report first, and stop

Write the gap list before editing. One line per gap, each naming the file and the rule it breaks:

- **Structural gaps** — logic in a handler, a component calling `fetch`, a service importing the ORM or the TUI framework, a dependency constructed instead of injected, no composition root, validation missing at the boundary, errors handled per-site instead of centrally, features organized by layer instead of by feature.
- **Quality gaps** — every breach of the fixed numbers in `assets/claude-md-section-quality.md` (file >300 lines, function >50, >4 params, nesting >3), plus classes that are only data, single-method stateless classes, inheritance used for reuse, `now()`/`random()`/filesystem called inside logic, untestable services.

Then propose an **ordered, phased plan** — each phase touches at most 5 files, ends green, and is committed on its own. Suggested order, cheapest first: (1) write the CLAUDE.md sections, (2) move files into the canonical tree with no logic changes, (3) introduce the composition root and inject existing dependencies, (4) extract logic out of the boundary layer into services, (5) put I/O behind repository/client abstractions, (6) add boundary validation and the central error handler, (7) the size/testability cleanups. **Show the plan and wait for the user before phase 2** — a structural refactor of working code is the user's call, not yours.

### 3c. Refactor behaviour-preservingly

- **No behaviour change.** A conformance refactor that also fixes a bug is two changes in one diff; log the bug and leave it.
- **Test first where there is no test.** Before moving logic out of a handler, get one test that pins its current behaviour. If a phase cannot be pinned by a test, say so and let the user decide.
- Renaming a symbol means searching every channel: direct calls, type references, string literals, dynamic imports, re-exports/barrels, tests and mocks. Prefer `ast-grep` for structural renames.
- Re-run the project's type-check, lint and tests after **every** phase. A phase is not done until they pass.
- The reference feature still matters: pick the feature you conformed most completely and name it in CLAUDE.md as the template for the rest.

### 3d. What not to conform

- A repo whose track you cannot determine — ask rather than guess.
- Generated code, vendored code, migrations.
- A library with no entry point and no I/O; the layers do not apply. Write the quality block only.
- A file the user marked off-limits.

## What NOT to do

- Don't generate every module the user might eventually need. One excellent reference feature beats ten shallow ones — the rest get built later by following the rules.
- Don't invent a bespoke DI framework when the language has an idiomatic one. Use the ecosystem's tools.
- Don't bury logic in controllers or components. The thin-boundary rule is the most commonly violated one; the scaffold should model the right thing.
- Don't force backend layers onto a frontend. React has no repositories; the frontend track has its own reference for a reason.
- Don't put I/O, business logic, or a bare `print` inside a screen or widget. A blocking call freezes the whole terminal, and a stray write to `stdout` corrupts the frame.
- Don't soften a quality number, drop the quality block, or reorder the tree because a particular repo "is different". Determinism across repos is the deliverable; a per-repo exception destroys it. A genuine mismatch is a change to the template, made once, applied everywhere.
- Don't mix a conformance refactor with a feature or a bug fix in the same diff.
- Don't write the CLAUDE.md rules as a vague essay. They should be specific, checkable conventions (file naming, dependency direction, where validation lives) — see the templates.
