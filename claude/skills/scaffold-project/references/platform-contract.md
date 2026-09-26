# Platform contract — the parts that must be byte-identical across repos

These are the answers the layer rules leave open. "Centralize the error handler" without saying *what shape it emits* produces twelve different shapes in twelve repos. Everything here is fixed; fill in only the language-specific spelling.

Applies to the **backend** track in full, and to the **frontend**/**TUI** tracks where marked.

## 1. Error response shape (backend; frontend consumes it)

Every error, every endpoint, one shape:

```json
{
  "error": {
    "code": "USER_EMAIL_TAKEN",
    "message": "A user with that email already exists.",
    "details": [{ "field": "email", "issue": "already_taken" }],
    "request_id": "01J8ZK7T3QK9V2M4S8XZ1H0BQR"
  }
}
```

- `code` — `SCREAMING_SNAKE_CASE`, stable, part of the API contract. Never renamed once shipped; a new meaning gets a new code.
- `message` — human-readable, safe to show a user. Never a stack trace, never a SQL string, never an internal hostname or path.
- `details` — present only for validation errors; one entry per offending field.
- `request_id` — always present, and the same id that appears in the logs for that request.
- The codes live in **one catalogue module** per service (`errors/catalogue.*`), not scattered as string literals. A domain error class maps to exactly one code, and that mapping lives in the central handler.

HTTP status mapping, fixed: `400` malformed/validation, `401` unauthenticated, `403` authenticated-but-forbidden, `404` not found, `409` conflict/duplicate, `422` semantically invalid but well-formed, `429` rate limited, `500` unexpected. An unhandled exception is always `500` with code `INTERNAL_ERROR` and a generic message — the detail goes to the log, never to the client.

**Frontend track:** the API layer parses this shape into one typed `ApiError { code, message, details, requestId }`. Components branch on `code`, never on `message` text.

## 2. Pagination (backend)

Cursor-based, one shape, for every list endpoint:

Request: `?limit=<1..100, default 20>&cursor=<opaque>`
Response: `{ "data": [...], "page": { "next_cursor": "...|null", "limit": 20 } }`

- The cursor is opaque to the client (encode the sort key, don't expose an offset).
- Never return an unbounded list. A list endpoint with no pagination is a defect.
- Offset pagination only where the client genuinely needs page numbers, and then the shape is `{ "data": [...], "page": { "offset": 0, "limit": 20, "total": 137 } }`.

## 3. Versioning (backend)

- Path prefix: `/v1/...`. Every route sits under a version, from the first commit.
- A breaking change means `/v2`, not a flag. Additive fields are not breaking.
- The version lives in the route registration, never inside a controller's logic.

## 4. Health and readiness (backend; skip for one-shot CLIs)

Two endpoints, unauthenticated, never behind the API version prefix:

- `GET /healthz` — liveness. Answers "the process is up" with **no dependency checks**. Must not touch the DB; a slow database must never get the pod killed.
- `GET /readyz` — readiness. Checks each critical dependency with a short timeout and returns `{ "status": "ok|degraded", "checks": { "db": "ok", ... } }`, status `200` or `503`.

## 5. Graceful shutdown (backend; TUI: the equivalent is terminal restore)

- Handle `SIGTERM`: stop accepting new work, let in-flight requests finish inside a bounded drain window (default 15s, from config), close DB pools and consumers, then exit `0`.
- A queue consumer must not lose the message it is holding. Ack after the work commits, never before.
- The shutdown path is wired in the composition root, not in a handler.

## 6. Logging and tracing (all tracks)

- **Structured only.** One JSON object per line to stdout: `timestamp`, `level`, `message`, `service`, plus fields. No `print`, no string-concatenated log lines, no multi-line messages.
- The logger is **injected** like any other dependency. A service does not reach for a module-level global logger.
- Every log line inside a request carries the same `request_id`/`trace_id` as the error response. Generate it at the boundary if the caller did not send one; propagate the incoming `traceparent` header when present.
- **Never log** a secret, a token, a password, a full auth header, or a whole request body containing user data. Redact by field name at the logger, not at each call site.
- Levels mean something fixed: `error` = a human must look, `warn` = degraded but handled, `info` = a state change worth an audit line, `debug` = off in production.
- Emit OpenTelemetry traces via OTLP to the collector endpoint from config (`OTEL_EXPORTER_OTLP_ENDPOINT`). No endpoint set → the exporter is a no-op; the app still runs. Instrumentation is wired once in the composition root.
- **TUI track:** stdout belongs to the frame, so the log sink is a file or a socket — never stdout.

## 7. Config and secrets (all tracks)

- One typed, validated config object, loaded and frozen at startup; invalid config fails the process immediately with a message naming the offending key.
- Nothing deep in the code reads an env var. If a value is needed three layers down, it is passed in.
- `.env` is **never committed**. `.env.example` is committed, lists every key with a safe placeholder, and is the single source of truth for what the service needs.
- Real values come from `gopass` locally and from CI/CD variables in the pipeline. A secret literal in a source file, a test fixture, or a committed config is a defect.

## 8. Dependencies

- A lockfile is committed, always. Direct dependencies are pinned or range-pinned deliberately; transitive resolution is the lockfile's job.
- Adding a dependency needs a one-line reason in the commit body. A dependency that saves fewer than ~20 lines does not get added.

## 9. API documentation (backend, HTTP only)

- The framework's schema generation is enabled and served (`/docs` or equivalent) in non-production. DTOs are the source of the schema — never a hand-maintained spec file that can drift.
- Every endpoint's error codes are documented from the catalogue module, so the contract in §1 is discoverable.
