<!-- BEGIN scaffold-project -->
## TUI Architecture

This app is a layered, dependency-injected terminal UI. **These rules are the source of truth** — when generated code and these rules disagree, follow the rules. Reference screen: `{{REFERENCE_SCREEN_PATH}}`.

**Stack:** {{LANGUAGE}} + {{FRAMEWORK}} (state: {{STATE_MECHANISM}}, styling: {{STYLING}}).

### Layering & dependency direction

- The layers are **screen/widget → service → client/repository → I/O**, and dependencies point only in that direction.
  - **Screens** own one full-terminal mode: layout, bindings, and rendering. They call services and render the result. No business logic, no direct I/O.
  - **Widgets** are reusable and dumb. State comes in, messages go out. A widget never reaches for a service, a global, or another widget's internals.
  - **Services** hold business logic and **must not import {{FRAMEWORK}}**. They depend on client/repository **abstractions** ({{INTERFACE_MECHANISM}}), never concrete classes, and are testable with no terminal attached.
  - **Clients/repositories** are the only layer that performs I/O ({{IO_TARGETS}}), hidden behind an abstraction. No business rules here.
  - **View models** are plain data. They carry no widget types; domain models carry no rendering concerns.

### The render loop

- **Never block the event loop.** Anything over ~16 ms — network, disk, subprocess, crypto — runs in {{WORKER_MECHANISM}}. A blocked loop freezes the terminal and the user cannot even quit.
- Every list or pane has **three states**: loading, empty, populated. Render all three.
- `stdout` belongs to the UI. Logs go to {{LOG_SINK}}, never to a bare print.

### Dependency injection

- Dependencies are **received, never constructed**. Wiring lives in **one composition root**: `{{COMPOSITION_ROOT}}`.

### Boundaries & cross-cutting concerns

- Errors map to a **consistent user-facing surface** in one place: {{ERROR_HANDLER}}. Screens raise typed domain errors from `{{ERRORS_MODULE}}`; the handler renders them. A traceback must never reach the raw terminal.
- **Terminal state is global.** Raw mode, the alternate screen, and the cursor are restored on every exit path, including crash and signal.
- **Bindings are declared as data** next to their screen, and the help overlay is generated from that same data. Never hardcode a key comparison inside a handler.
- Configuration is loaded and validated once at startup (`{{CONFIG_LOCATION}}`); fail fast. Never read raw env vars deep in the code.
- Never render a secret unless the user explicitly reveals it. Prefer a clipboard copy with a timeout.

### Terminal compatibility

- Handle resize; stay usable at 80×24. Honour `NO_COLOR` and never signal meaning with colour alone. Keyboard-first — every action has a key. A non-TTY `stdout` must fail clearly or fall back, never hang.

### Adding a new screen

Copy the reference screen's structure: screen, its widgets, the service it calls, its view model, and two tests — one headless service test with a fake client, and one pilot test that drives keypresses and asserts the rendered output.

### Naming

Follow the convention shown in `{{REFERENCE_SCREEN_PATH}}` ({{NAMING_CONVENTION}}).
<!-- END scaffold-project -->
