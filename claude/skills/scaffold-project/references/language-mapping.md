# Language & framework mapping

Pick the **idiomatic default** for the requested language and proceed (the user can override). Each row is a known-good combination that can express modules, DI, declarative routing, and repositories naturally. None of these are mandatory — they're the path of least resistance.

| Language | Default framework | DI mechanism | Declarative boundary | ORM / persistence (default) |
|----------|-------------------|--------------|----------------------|-----------------------------|
| **TypeScript / JS** | **NestJS** (it *is* this architecture); or **Effect** (`@effect/platform` HTTP, `@effect/cli` for CLIs) if the user prefers Effect-native | Built-in IoC container (NestJS) / Effect services + Layers | Decorators (`@Controller`, `@Injectable`, `@Get`) / `HttpApi` definitions | **TypeORM** (or Prisma); entity + datasource, repo class behind the interface/token |
| **Python** | **FastAPI** | `dependency-injector` container, or FastAPI `Depends` for lighter needs | Path-operation decorators; Pydantic models for DTOs | **SQLAlchemy** (+ Alembic migrations); concrete repo implementing the Protocol |
| **Go** | **Echo** or **Gin** + **Uber fx** (or `google/wire`) | `fx` modules / `wire` providers | Route registration funcs; struct tags for validation | **GORM** (or `sqlc`/`sqlx`); struct impl satisfying the repository interface |
| **Java / Kotlin** | **Spring Boot** | Spring IoC (`@Autowired` / constructor) | Annotations (`@RestController`, `@Service`, `@Repository`) | **Spring Data JPA** (Hibernate); `@Repository` interface + entity |
| **C# / .NET** | **ASP.NET Core** | Built-in `IServiceCollection` | Attributes (`[ApiController]`, `[HttpGet]`) | **EF Core**; `DbContext` + repo impl registered in `Program.cs` |
| **Rust** | **Axum** | Manual via `State`, or `shaku` for a container | Handler fns; `validator` derive macros for DTOs | **Diesel** or **SeaORM**; impl satisfying the repository trait |
| **Ruby** | **Hanami** (or Rails) | `dry-system` / `dry-container` | DSL + dry-validation contracts | **ROM** (Hanami) / **ActiveRecord** (Rails) behind a repository object |
| **PHP** | **Symfony** | Symfony DI container (autowiring) | Attributes (`#[Route]`), Validator constraints | **Doctrine**; repository interface + impl + entity mapping |

**Persistence is wired for real by default.** Bind the repository abstraction to a concrete ORM-backed implementation with the entity↔table mapping, a connection configured from env (default to local SQLite or Postgres), and migrations where the ORM expects them. The service must still depend only on the repository abstraction — never import the ORM into the service — so the production binding can be a real database while the unit test substitutes a fake. If the user explicitly wants something dependency-free, an in-memory implementation of the same interface is the documented fallback, but the default is a real ORM.

If FastAPI's `Depends` is enough for the project's scale, prefer it over pulling in `dependency-injector` — but still depend on a repository **protocol**, not the concrete class, so tests can substitute a fake.

## Mapping principles (for languages not in the table)

The architecture survives in any language; only the spelling changes. To derive the idiomatic form, answer these four questions:

1. **How does this language declare an HTTP route near its handler?** (decorator, annotation, attribute, macro, or an explicit registration function). Use that for controllers.
2. **What's the idiomatic "interface" mechanism?** (interface, trait, protocol, abstract base, duck typing). Services depend on *that* for repositories — never on a concrete type.
3. **What's the idiomatic DI / wiring mechanism?** (a container library, constructor injection wired in a composition root, a provider/registration function). Use one composition root; never `new` a dependency inside the code that uses it.
4. **What's the idiomatic validation layer?** (schema objects like Pydantic, derive macros, struct tags, validator libraries). DTO validation lives at the boundary.

If the language has no decorator/annotation facility at all (e.g. Go, C), don't fake one — use explicit registration in the composition root. The declarative *feel* matters less than the dependency rules from `architecture.md`. Keep the layer separation and the inward-pointing dependencies, and the result will be recognizably "NestJS-style" even without decorators.

## Choosing well

- Favor the framework the language community already reaches for; a scaffold that fights the ecosystem is worse than a slightly less "Nest-like" one that feels native.
- Prefer a real DI container only when the project is large enough to need it. For small services, constructor injection wired by hand in the composition root is cleaner than a heavyweight container — and still fully testable.
- State your choice and the one-line reason, then proceed.

## Immutability mechanism (`{{IMMUTABILITY_MECHANISM}}` in the quality block)

| Language | Fill in with |
|----------|--------------|
| TypeScript / JS | `readonly` fields, `as const`, spread instead of mutation (`Object.freeze` only at real boundaries) |
| Python | frozen `@dataclass(frozen=True)` / `NamedTuple`; never mutate a passed list or dict |
| Go | value receivers and copies; return a new struct rather than mutating a pointer field |
| Java / Kotlin | `record` / `data class` with `val`; `List.copyOf` |
| C# / .NET | `record` types, `init` setters, `ImmutableArray` |
| Rust | the borrow checker already enforces it — take `&self`, return owned values |
| Ruby | `Data.define` / frozen value objects, `dup` before mutating |
| PHP | `readonly` promoted constructor properties |

If the language has no immutability facility, fill in "copy on write by convention — never mutate an argument".
