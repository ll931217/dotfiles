<!-- BEGIN scaffold-project-quality -->
## Code Quality Rules

Fixed limits, identical in every repo. **These are checkable, not aspirational** — a number here is a review gate, not a suggestion. When generated code and these rules disagree, follow the rules.

### Size limits

| Thing | Limit | On breach |
|---|---|---|
| File | 300 lines | split by responsibility, not by line count |
| Function / method | 50 lines | extract the inner step, name it |
| Function parameters | 4 | pass one object/struct/DTO |
| Nesting depth | 3 | early return, or extract |
| Cyclomatic branches per function | 10 | table/dispatch map instead of a chain |

Generated files, migrations, and lock files are exempt.

**These are lint rules, not prose.** They are configured in `{{LINT_CONFIG}}` and fail `{{CHECK_CMD}}` locally and in CI. A breach is fixed or gets an explicit per-file ignore **with a reason on the same line** — never by lowering a cap.

### YAGNI

- No abstraction until there are **two real** call sites. One implementation behind an interface is allowed **only** where the layer rules require it (repository/client abstractions) — nowhere else.
- No config value for something that never changes. No flag for a case that does not exist yet.
- No file created "for later". Later can create it.

### DRY

- **Third occurrence extracts, not the second.** Two similar blocks are a coincidence; three are a pattern. Extracting at two couples code that was about to diverge.
- Duplication across features goes to `{{SHARED_DIR}}` (`shared/` if this project has no other convention). Never reach into another feature to reuse.
- Copied domain knowledge (a rule, a threshold, a format) is a defect at the *first* duplicate — it must live in exactly one place.

### SOLID, the parts the layer rules do not already cover

The layering rules already give SRP (one layer, one job) and DIP (services depend on abstractions). Additionally:

- **Open/Closed** — new behaviour arrives as a new implementation of an existing abstraction or a new module, not as another `if` in a shared function.
- **Interface Segregation** — an abstraction declares only what its consumer calls. A repository interface with methods only one caller uses gets split.
- **Liskov** — every implementation of an abstraction honours the same contract: same error types, same null/empty semantics, no narrower accepted input. A fake used in tests must obey the contract too, or the test proves nothing.

### Functional or class-based

- **Default to functions and plain data.** A class earns its place only when it holds injected dependencies (services, repositories, clients) or the framework demands one.
- **No class holding only data** — use the language's record/struct/dataclass/`TypedDict`/interface.
- **No class with a single method and no state** — that is a function.
- Data is immutable by default: {{IMMUTABILITY_MECHANISM}}. Mutate a caller's argument never; return a new value.
- **No inheritance for reuse.** Compose, or inject. Inheritance only where the framework's own base class requires it.

### Testability

- Every service is constructible in a test with **zero real I/O** — no database, no network, no terminal, no clock. If it is not, the dependency is being constructed instead of injected.
- **Time, randomness, and the filesystem are injected**, never called directly in logic. `now()` inside a service makes it untestable.
- One unit test per service method with a real branch in it. A test that only asserts a value passed straight through is not a test.
- Test the behaviour through the layer's public surface, not its privates. A test that breaks on a rename of a private helper is a maintenance cost with no value.
- No test touches another test's state. No ordering dependency.

### Dependency direction

The layer rules are enforced mechanically by `{{BOUNDARY_LINTER}}`, not by review memory. A service importing the ORM, a component importing the HTTP client, or a feature importing another feature's internals fails `{{CHECK_CMD}}`.

### Comments

One line, explaining what the code cannot say itself — a unit, a bound, an ordering requirement, or why the obvious version is wrong here. No history, no restating the next line, no multi-paragraph headers.
<!-- END scaffold-project-quality -->
