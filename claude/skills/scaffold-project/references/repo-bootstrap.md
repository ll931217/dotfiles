# Repo bootstrap — day-one files, enforcement, and handoffs

A skeleton is not a repo. This is the fixed set of files and setup steps every scaffolded project gets, so two repos created a year apart still start identical.

## 1. Hygiene files (all tracks)

| File | Content rule |
|---|---|
| `README.md` | What it is (1 line), how to run it, how to test it, how to configure it. Nothing else — no architecture essay, that lives in CLAUDE.md. |
| `CLAUDE.md` | The three managed blocks (track, quality, platform). |
| `.env.example` | Every key the config object reads, with safe placeholders. No real values. |
| `.gitignore` | Language-idiomatic, plus `.env`, `.claude/jira_issues`, local DB files, coverage output. |
| `.editorconfig` | UTF-8, LF, final newline, trim trailing whitespace, indent matching the language's convention. |
| Lint + format config | The ecosystem's standard tool, configured with the enforcement rules in §2. |
| Test config | Runner configured, one command runs everything. |
| `.claude/jira_issues` | Created empty **and gitignored**. A repo missing it fails `wt` worktree dispatch the first time a worktree is created. |

Then `git init` (if needed) and one commit: `chore: scaffold project structure`. Nothing is left uncommitted at the end of a scaffold.

## 2. Enforcement — the quality numbers become lint rules, not prose

The caps in the quality CLAUDE.md block are configured in the linter so a breach fails locally and in CI. Prose the model may forget is not enforcement.

| Language | Where the caps go |
|---|---|
| TypeScript / JS | ESLint: `max-lines: 300`, `max-lines-per-function: 50`, `max-params: 4`, `max-depth: 3`, `complexity: 10`, `no-console`. Biome equivalents if the repo uses Biome. |
| Python | Ruff: `select = ["E","F","I","N","UP","B","C90","PL","RUF"]`, `mccabe.max-complexity = 10`, `pylint.max-args = 4`, `flake8-bugbear`; file length via `PLR0915`/a `check-shape` run. `T201` bans `print`. |
| Go | `golangci-lint`: `funlen` (50 lines), `gocyclo` (10), `nestif` (3), `revive`, `errcheck`, `forbidigo` for `fmt.Print*`. |
| Rust | `clippy` with `#![warn(clippy::pedantic)]`, `cognitive_complexity`, `too_many_arguments`. |
| Java / Kotlin | Checkstyle / detekt: method length 50, params 4, nesting 3, cyclomatic 10. |
| C# / .NET | `.editorconfig` analyzer severities + Roslynator equivalents. |
| PHP | PHPStan level 8 + PHP_CodeSniffer metrics. |

Also add a **dependency-direction check** where the ecosystem has one (`import-linter` for Python, `eslint-plugin-boundaries` / `dependency-cruiser` for TS, `depguard` for Go). This is the only mechanical way to stop "service imports the ORM" or "component calls fetch".

Never lower a cap to make existing code pass. Existing breaches get a baseline file or an explicit per-file ignore with a reason.

## 3. Handoffs — call these skills, don't reimplement them

Run in this order after the skeleton exists:

1. **TypeScript projects** → `setup-effect` (`~/.claude/commands/setup-effect.md`): Effect deps, LSP plugin, tsconfig, its own managed CLAUDE.md section.
2. **Pre-commit** → the `setup-pre-commit` skill: wires the lint/format/type-check commands from §2 as hooks, so a breach never reaches CI.
3. **Issue tracking** → `bd init` (Beads) so the repo can track its own work; `.claude/jira_issues` stays empty until a Jira-tier issue exists.
4. **CI/CD** → the `vici-cicd-onboard` skill. It owns the `.gitlab-ci.yml` include, the deployable-unit decision, Harbor variables and the deploy gate. This skill writes **no** pipeline YAML, no Dockerfile and no Kubernetes manifests.
5. **Observability** → if the service will run on a server, say so and point at the Komodo resource-sync repo for otel-collector onboarding. Do not hand-roll a collector config.

State each handoff you ran, and each one you skipped with the reason.

## 4. Dev server / local run (all tracks)

- A project that serves anything uses **`portless`** for its dev port. No hardcoded port, no "3000 unless taken" logic — hardcoded ports are why two repos cannot run at once.
- One documented command to run, one to test, one to lint. If the language has no task runner, add a `Makefile` or `justfile` with `run`, `test`, `lint`, `check` targets so the command names are the same in every repo.

## 5. Verification before reporting done

A scaffold is not finished until, in this order:

1. The type-checker passes (or you state explicitly that the language has none configured).
2. The linter and formatter pass — including the new caps from §2.
3. The test suite runs and the reference feature's test passes.
4. The thing actually starts: the server boots and `GET /healthz` returns `200`; the CLI prints its help; the TUI renders and exits cleanly; the frontend dev server serves the page (check it in a browser via `chrome-devtools-mcp`).

Report the command you ran for each. A file that was written is not a feature that works.
