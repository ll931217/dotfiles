# Extra tracks — library, data pipeline, MCP server

Three shapes that are not a server, a web app, or a TUI. Each reuses the quality block and the parts of the platform contract that apply; none of them get forced into the backend tree.

## Library / SDK track

No entry point, no I/O of its own, consumed by other code.

- **Layers:** `public API surface → internal modules → pure helpers`. One and only one public entry module re-exports everything supported; everything else is internal and may change.
- **No DI container, no repositories.** A library takes its dependencies as constructor/function arguments. It never reads env vars, never constructs a client, never configures logging — the host application does that.
- **No global state, no side effects at import time.** Importing the library must do nothing observable.
- **Errors:** typed error classes the consumer can catch. Never raise a framework error, never swallow and return `null`.
- **What it gets:** the quality CLAUDE.md block, platform contract §7 (config passed in, never read), §8 (dependencies — a library is strict here: minimal deps, wide version ranges). **Skips** health, pagination, versioning-by-path, graceful shutdown, error response shape.
- **Versioning is semver in the package metadata**, plus a `CHANGELOG.md`. A breaking change to the public surface is a major bump, and the public surface is exactly what the entry module exports.
- **Tests:** the public surface only, plus a doc example that is executed by the test suite (`doctest`/`pytest --doctest-modules`/example test) so the README cannot drift.

## Data pipeline / Airflow task track

A batch job, a DAG task, or a scheduled ETL. The unit of work is an image or a script the scheduler invokes — the scheduler is the entry point.

- **Layers:** `task entry (CLI/DAG operator boundary) → pipeline orchestration → extract / transform / load steps → clients (source and sink behind abstractions)`. Transform steps are **pure functions on data**: input dataframe/rows in, output rows out, no I/O inside. That is what makes them testable without the warehouse.
- **The DAG definition is not the logic.** The DAG file wires and schedules; it imports the pipeline and calls it. Business rules never live in a DAG file. Airflow DAGs live in `misc/airflow`, not in this repo's package.
- **Idempotency is the rule, not a feature.** A task re-run for the same logical window produces the same end state: partition-replace or upsert-by-key, never blind append. State a task's grain (the key + the window) in its docstring.
- **Every run is bounded and parameterized by a window** passed in (execution date / interval), never `now()` inside the logic — same injection rule as the quality block, and it is what makes a backfill possible.
- **Data contract at both edges:** validate the input schema before transforming and the output schema before writing. A silently-changed upstream column must fail the task, not produce nulls.
- **Destructive writes get a guard.** A step that deletes or overwrites states its blast radius in the log line before it acts, and a partial-source run never overwrites a full snapshot.
- **What it gets:** quality block, platform contract §6 (structured logging with the run id and the window), §7 (config/secrets), §8. **Skips** HTTP concerns entirely; the "health check" equivalent is a row-count/freshness assertion at the end of the run.
- **Tests:** one test per transform step with literal input rows and expected output rows, plus one test that the pipeline is idempotent — run it twice against a fake sink and assert the sink's final state is identical.

## MCP server track

A tool server an agent talks to over stdio or HTTP.

- **Layers:** `tool definition (the boundary) → service → client/repository`. The tool handler is as thin as a controller: validate the arguments against the tool's input schema, call a service, shape the result.
- **The tool schema is the contract.** Names, descriptions and argument schemas are written for a model to read: say what the tool does, when to use it, and what it returns. A vague description is the same defect as an unnamed error code.
- **stdio is the protocol.** On a stdio server, nothing may write to stdout except protocol frames — logging goes to stderr or a file. This is the exact same rule as the TUI track's frame ownership, and breaking it corrupts the session.
- **Every tool is read-only unless it says otherwise.** A mutating tool declares it, and a destructive one requires an explicit confirmation argument rather than inferring intent.
- **Results are bounded.** Truncate large output and say it was truncated with how to get the rest; an unbounded result blows the caller's context.
- **What it gets:** quality block, platform contract §1 (a typed error returned as a tool error, with a stable code), §6, §7, §8. Health check applies only to the HTTP transport.
- **Tests:** one test per tool that calls the handler with parsed arguments and a fake client, plus one that asserts the tool list and its schemas — the contract an agent depends on.
