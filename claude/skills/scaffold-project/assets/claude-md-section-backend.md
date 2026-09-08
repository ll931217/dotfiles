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

### Boundaries & cross-cutting concerns

- Every request body/query is validated against a **DTO** at the boundary using {{VALIDATION_MECHANISM}}; handlers receive already-valid data.
- Errors are mapped to a **consistent response shape** in one place: {{ERROR_HANDLER}}. Throw domain errors from services; let the handler translate them to HTTP.
- Configuration is loaded and validated once at startup ({{CONFIG_LOCATION}}); fail fast on invalid config. Never read raw env vars deep in the code.

### Adding a new feature

Copy the reference module's structure: module, controller, service, repository (abstraction + impl), DTOs, entity, and at least one unit test that exercises the service with a **mocked repository** (this is the payoff of DI — keep it testable without a database).

### Naming

Follow the existing file/class naming convention shown in `{{REFERENCE_MODULE_PATH}}` ({{NAMING_CONVENTION}}).
<!-- END scaffold-project -->
