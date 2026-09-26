# NestJS-style Architecture — canonical reference

This is the language-agnostic definition of the architecture. Every concept below has a concrete syntactic form in each language (see `language-mapping.md`), but the *roles* and *dependency rules* are invariant.

## The layers

```
Entry point (HTTP request / CLI command / queue message / cron tick)
   │
   ▼
Controller ──uses──▶ Service ──uses──▶ Repository ──talks to──▶ Datastore
   │ (DTO in/out)      │ (domain logic)   │ (interface + impl)
   │                   │                  │
   └─ validation       └─ orchestration   └─ persistence detail
```

The entry point doesn't have to be HTTP. A CLI subcommand handler, a queue consumer's message handler, or a cron job's entry function plays exactly the controller role: parse/validate the input into a DTO, call a service, shape the output. All rules below that mention "HTTP" apply to whatever transport the boundary uses.

| Layer | Responsibility | May depend on | Must NOT |
|-------|----------------|---------------|----------|
| **Module** | Groups one feature; declares & wires its providers, controllers, imports/exports | Other modules (explicitly imported) | Reach into another module's internals not exported |
| **Controller** | HTTP boundary only: parse/validate input (DTO), call a service, shape the response | Services (injected) | Contain business logic; touch repositories or the DB directly |
| **Service (Provider)** | Business logic, orchestration, transactions | Repositories, other services (injected via abstractions) | Know about HTTP (no request/response objects); construct its own dependencies |
| **Repository** | Data access behind an abstraction (interface + implementation) | The ORM/driver, the entity | Contain business rules; be skipped by services going straight to the ORM |
| **Entity / Model** | The domain/persistence object | — | Carry HTTP or transport concerns |
| **DTO** | Validated input contract and/or output shape at the boundary | Validation rules | Be reused as the persistence entity (keep transport and storage separate) |

### The cardinal dependency rule

Dependencies point **inward and downward**, never up. Controllers depend on services; services depend on repository *abstractions*; repositories depend on the datastore. Nothing depends on the controller. A service must never import a controller, and a controller must never import a repository. This is what makes the business logic testable in isolation and the persistence layer swappable.

## Dependency injection

Every dependency is **received**, never **constructed**, by the class/function that uses it. A service takes its repository through its constructor (or equivalent); it does not `new` one up. The wiring happens in one place — the **composition root** (the module definitions + bootstrap). This is what lets a unit test pass a fake repository in.

Two non-negotiables:
- **Depend on abstractions.** Services should depend on a repository *interface/protocol/token*, not a concrete class. The concrete implementation is bound in the module/container.
- **Single composition root.** Wiring lives in the module/container definitions, not scattered through the code. Reading the module file should tell you the feature's whole dependency graph.

## Decorators / annotations / metadata

NestJS uses decorators (`@Controller`, `@Get`, `@Injectable`, `@Body`) to attach routing, injection, and validation metadata declaratively. Reproduce the *declarative boundary*, using whatever the language offers:
- Decorators (TS, Python), annotations (Java/Kotlin/C#), attributes (PHP, Rust proc-macros), struct tags + registration (Go).
- The point is that routing, validation, and injection are **declared near the thing they describe**, not assembled imperatively in a giant setup function.

## Cross-cutting concerns

NestJS factors these out so they don't pollute controllers and services. Reproduce as many as the project needs, using the framework's idiomatic mechanism (middleware, decorators, interceptors):

- **Exception filters / error handlers** — one place that turns errors into a consistent error response shape. Controllers throw domain errors; the filter maps them to HTTP status + body.
- **Guards** — authn/authz checks that run before the handler.
- **Interceptors / middleware** — logging, response transformation, timing.
- **Pipes / validators** — DTO validation and transformation at the edge, so handlers receive already-valid data.

A scaffold should at minimum include the **exception filter** and **DTO validation**, because a consistent error shape and validated input are the two things every later feature relies on.

## Canonical directory layout

Organize **by feature, not by layer** — everything for `users` lives together, so a feature can be understood (and deleted) as a unit. Translate file extensions and naming to the language's conventions (`user_service.py`, `user.service.ts`, `service.go`, `UserService.java`).

```
src/
  main.<ext>                 # bootstrap / composition root: build container, mount modules, start server
  app.module.<ext>           # root module: imports feature modules, global filters/config
  config/
    config.<ext>             # typed/validated env loading (fail fast on bad config)
  common/                    # cross-cutting, shared across features
    filters/
      http-exception.filter.<ext>   # centralized error → response mapping
    # guards/ interceptors/ pipes/ as needed
  modules/
    users/                   # one self-contained feature
      users.module.<ext>     # wires this feature's providers + controller
      users.controller.<ext> # HTTP boundary, thin
      users.service.<ext>    # business logic
      users.repository.<ext> # interface + implementation (or two files)
      dto/
        create-user.dto.<ext>
        update-user.dto.<ext>
      entities/
        user.entity.<ext>
      users.service.spec.<ext>   # unit test: service with a mocked repository
test/
  users.e2e.<ext>            # optional: end-to-end through the HTTP layer
```

In languages where one-class-per-file is not idiomatic (Go), collapse sensibly — e.g. a `users` package with `controller.go`, `service.go`, `repository.go`, `dto.go`, `entity.go` — but preserve the layer separation and the dependency rules.

## The reference module, concretely

The single reference module you scaffold should let a reader trace one request end-to-end:

1. `POST /users` hits the controller.
2. The controller validates the body against `CreateUserDTO` and calls `UsersService.create(dto)`.
3. The service applies any rules and calls `UsersRepository.save(entity)` through the injected abstraction.
4. The repository persists and returns the entity.
5. If anything throws (e.g. duplicate email → a domain error), the exception filter maps it to a clean error response.
6. The unit test constructs the service with a fake repository and asserts the business behavior **without a database** — demonstrating the payoff of DI.

If you show that one slice well, every future feature has a pattern to copy.
