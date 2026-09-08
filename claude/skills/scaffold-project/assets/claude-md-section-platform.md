<!-- BEGIN scaffold-project-platform -->
## Platform Contract

Fixed across every repo. These are contracts, not preferences — a different error shape or a different pagination envelope in this repo is a defect even if it works. Full rationale: the `scaffold-project` skill's `references/platform-contract.md`.

### Error responses

Every error, every endpoint:

```json
{ "error": { "code": "USER_EMAIL_TAKEN", "message": "safe for a user to read", "details": [{ "field": "email", "issue": "already_taken" }], "request_id": "..." } }
```

- `code` is `SCREAMING_SNAKE_CASE` and stable forever; new meaning means a new code. All codes live in `{{ERROR_CATALOGUE}}` — never a string literal at a throw site.
- `details` only for validation errors. `request_id` always, and it matches the logs.
- `message` never carries a stack trace, SQL, hostname, path, or secret.
- Status mapping: `400` malformed, `401` unauthenticated, `403` forbidden, `404` missing, `409` conflict, `422` semantically invalid, `429` rate-limited, `500` unexpected. Unhandled → `500` + `INTERNAL_ERROR` + generic message; the detail goes to the log only.
- Mapping domain error → code → status happens in one place: `{{ERROR_HANDLER}}`.

### Lists and versioning

- Every list endpoint is paginated: `?limit=<1..100, default 20>&cursor=<opaque>` → `{ "data": [...], "page": { "next_cursor": "...|null", "limit": 20 } }`. An unbounded list response is a defect.
- Every route lives under `/v1/...` from the first commit. Breaking change → `/v2`, never a flag.

### Health and shutdown

- `GET /healthz` — liveness, **no dependency checks**, never touches the database.
- `GET /readyz` — readiness, checks critical dependencies with short timeouts, `200` or `503` with a per-check body.
- `SIGTERM` drains in-flight work within `{{DRAIN_TIMEOUT}}`, closes pools and consumers, exits `0`. Wired in the composition root. A consumer acks **after** the work commits.

### Logging and tracing

- Structured JSON, one object per line, to `{{LOG_SINK}}`. No `print`, no concatenated messages.
- The logger is **injected**, never a module-level global reached for inside a service.
- Every line in a request carries the same `request_id` / `trace_id` as the error response; an inbound `traceparent` is propagated.
- Levels: `error` = a human must look, `warn` = degraded but handled, `info` = an auditable state change, `debug` = off in production.
- Redaction is configured **at the logger** by field name. Never log a token, password, auth header, or a whole user-data body.
- OTLP traces go to `OTEL_EXPORTER_OTLP_ENDPOINT`; unset means a no-op exporter and the app still runs. Instrumented once in the composition root.

### Config and secrets

- One typed config object, validated and frozen at startup; invalid config kills the process with the offending key named. Nothing reads an env var deeper than `{{CONFIG_LOCATION}}` — values are passed in.
- `.env` is never committed; `.env.example` lists every key with a placeholder and is the source of truth for what this service needs. Real values come from `gopass` locally and CI variables in the pipeline. A secret literal anywhere in the repo — including tests and fixtures — is a defect.

### Dependencies

- The lockfile is committed. A new dependency needs a one-line reason in the commit body, and one that saves under ~20 lines does not get added.

### Local commands

- `{{RUN_CMD}}` runs it, `{{TEST_CMD}}` tests it, `{{LINT_CMD}}` lints it, `{{CHECK_CMD}}` does all checks. Same four names in every repo.
- The dev server takes its port from **`portless`**. No hardcoded port.
<!-- END scaffold-project-platform -->
