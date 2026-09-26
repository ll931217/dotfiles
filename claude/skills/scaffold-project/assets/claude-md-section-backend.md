<!-- BEGIN scaffold-project -->
## Backend Architecture (NestJS-style)

This service follows a layered, dependency-injected architecture. **These rules are the source of truth** — when generated code and these rules disagree, follow the rules. Reference implementation: `{{REFERENCE_MODULE_PATH}}`.

**Stack:** {{LANGUAGE}} + {{FRAMEWORK}} (DI: {{DI_MECHANISM}}).

### Layering & dependency direction

- Organize **by feature**, not by layer. Everything for a feature lives in its own module directory under `{{MODULES_DIR}}`.
- The layers are **controller → service → repository → datastore**, and dependencies point only in that direction.
  - **Controllers** are thin: validate input via a DTO, call a service, shape the response. No business logic. Never touch a repository or the datastore directly.
  - **Services** hold business logic. They receive repositories and other services via injection and depend on **abstractions** ({{INTERFACE_MECHANISM}}), never concrete classes. Services know nothing about HTTP.
  - **Repositories** are the only layer that talks to the datastore, hidden behind an abstraction. Persistence uses {{ORM}}; the ORM is imported **only** inside repository implementations — never in services or controllers. No business rules live here. Schema changes go through migrations ({{MIGRATIONS}}).
  - **Entities/models** carry no transport concerns; **DTOs** carry no persistence concerns. Never reuse one as the other.

### Dependency injection

- Dependencies are **received, never constructed**. Do not instantiate a dependency inside the code that uses it.
- Wiring lives in **one composition root** ({{COMPOSITION_ROOT}}). Reading a feature's module definition should reveal its full dependency graph.

### Transactions

- **The service owns the transaction boundary**, because only the service knows what must succeed together. A repository method is never the unit of atomicity when two writes must commit as one.
- A service spans multiple repositories without importing the ORM: it takes a **unit-of-work / transaction-runner abstraction** ({{UNIT_OF_WORK}}) and calls repositories inside it. The concrete implementation is the only place that knows about the ORM's session or transaction object.
- No transaction is held open across a network call to another service. Commit, then call.
- A test substitutes a fake unit of work that just runs the block — the business rule is still tested without a database.

### Authentication & authorization

- **Authentication** (who is calling) happens at the boundary in middleware/guards, before the handler, and produces a typed principal on the request context.
- **Authorization** (may they do this) lives in the **service**, taking the principal as an argument. A rule like "only the owner or an admin may delete" is a business rule, not a routing concern, and putting it in the controller means the next caller — a CLI, a job, another service — bypasses it.
- Route-level guards may reject a whole role/scope up front, but they are a coarse filter, never the only check.
- A service that needs the principal receives it explicitly. Never read the current user from a global or an ambient request context.

### Boundaries & cross-cutting concerns

- Every request body/query is validated against a **DTO** at the boundary using {{VALIDATION_MECHANISM}}; handlers receive already-valid data.
- Errors are mapped to a **consistent response shape** in one place: {{ERROR_HANDLER}}. Throw domain errors from services; let the handler translate them to HTTP. The shape, the status mapping and the error-code catalogue are fixed by the Platform Contract section below — do not invent a per-endpoint shape.
- Configuration is loaded and validated once at startup ({{CONFIG_LOCATION}}); fail fast on invalid config. Never read raw env vars deep in the code.

### Adding a new feature

Copy the reference module's structure: module, controller, service, repository (abstraction + impl), DTOs, entity, and at least one unit test that exercises the service with a **mocked repository** (this is the payoff of DI — keep it testable without a database).

### Naming

Follow the existing file/class naming convention shown in `{{REFERENCE_MODULE_PATH}}` ({{NAMING_CONVENTION}}).
<!-- END scaffold-project -->
