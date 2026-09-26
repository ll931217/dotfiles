# TUI Architecture — canonical reference

A TUI (terminal user interface) is a **backend track with a screen bolted on**. The layers from
`architecture.md` are unchanged; the *boundary* is a screen/widget instead of an HTTP controller,
and one extra hard rule applies: **the render loop is single-threaded and must never block**.

Read `architecture.md` first. This file only states what changes.

## The layers

```
Terminal (keypress / mouse / resize / paste)
   │
   ▼
Screen / Widget ──uses──▶ Service ──uses──▶ Repository / Client ──talks to──▶ API, DB, subprocess
   │ (renders state)         │ (domain logic)     │ (I/O detail)
   │                         │                    │
   └─ bindings, layout       └─ orchestration     └─ transport, retries, auth
```

| Layer | Responsibility | May depend on | Must NOT |
|-------|----------------|---------------|----------|
| **App** | Composition root. Builds services, installs screens, registers global bindings, owns the theme | Everything (it wires it) | Contain domain logic |
| **Screen** | One full-terminal mode (list, detail, form, modal). Owns its layout and its bindings | Widgets, services (injected) | Perform blocking I/O; hold business rules |
| **Widget** | One reusable piece of UI. Renders the state it is given; emits messages | Its own state only | Reach for a service, a global, or another widget's internals |
| **View model / State** | The plain data a screen renders. Serializable, no widget types in it | Domain models | Import the TUI framework |
| **Service** | Business logic and orchestration, exactly as in `architecture.md` | Repository abstractions | Import the TUI framework, print, or read keys |
| **Repository / Client** | I/O behind an abstraction: HTTP, DB, subprocess, filesystem | The driver/SDK | Contain business rules |

### The cardinal rules

1. **Dependencies point inward.** Same as `architecture.md`. A service must never import the TUI
   framework. Test the service headless, with no terminal.
2. **Never block the event loop.** Any call that can take more than ~16 ms — network, disk,
   subprocess, crypto — runs in the framework's worker/async mechanism. A blocked loop freezes the
   whole terminal and the user cannot even quit. This is the single most common TUI defect.
3. **Data flows down, messages flow up.** A parent passes state into a child; the child emits a
   message and never calls back into the parent or mutates shared state.

## Framework mapping

| Language | Default framework | Reactive/state mechanism | Styling | Test harness |
|----------|-------------------|--------------------------|---------|--------------|
| **Python** | **Textual** | `reactive` attributes + `@work` workers | Textual CSS (`.tcss`) | `App.run_test()` pilot; `pytest-textual-snapshot` |
| **TypeScript / JS** | **Ink** (React for the terminal) | React hooks | `<Box>` flexbox props | `ink-testing-library` |
| **Go** | **Bubble Tea** (+ Bubbles, Lip Gloss) | Elm-style `Model`/`Update`/`View` | Lip Gloss | `teatest` |
| **Rust** | **Ratatui** (+ Crossterm) | Explicit app struct, immediate mode | Style structs | `TestBackend` buffer assertions |
| **C# / .NET** | **Terminal.Gui** | Views + data binding | Color schemes | Fake driver |
| **Java / Kotlin** | **Lanterna** | Explicit screen buffer | `SGR` styles | Virtual screen |

If the framework is **immediate-mode** (Bubble Tea, Ratatui), the "screen" is the `Model` + its
`View` function. The layer rules are the same: `Update` dispatches to a service and stores the
result; it does not do the work itself.

## Directory layout

```
src/<pkg>/
  __main__.<ext>             # entry point: parse argv, build the App, run it
  app.<ext>                  # composition root: wires services, installs screens, global bindings
  config.<ext>               # typed/validated env + config-file loading, fail fast
  theme.tcss                 # styling, kept out of the widget code
  screens/
    resource_list.<ext>      # one screen per mode
    resource_detail.<ext>
  widgets/
    search_bar.<ext>         # reusable, dumb, state-in / message-out
  services/
    resource_service.<ext>   # business logic, framework-free
  clients/
    api_client.<ext>         # abstraction + implementation for each I/O boundary
  models/
    resource.<ext>           # domain types and view models
  errors.<ext>               # the error taxonomy the error handler maps from
tests/
  test_resource_service.<ext>  # headless: service with a fake client
  test_app.<ext>               # pilot: keypresses in, rendered output asserted
```

## Cross-cutting concerns

Every TUI scaffold must include these five. They are what a terminal app fails on, and every later
screen depends on them.

- **Error surface.** One handler turns a domain error into a status-bar line, a toast, or a modal.
  A traceback printed into a raw-mode terminal corrupts the display and hides the cause. Screens
  raise typed domain errors; the handler maps them to a message the user can act on.
- **Terminal restore.** Raw mode, the alternate screen, and the cursor are **process-global state**.
  Restore them on every exit path, including a crash and a signal. Use the framework's context
  manager or `finally`; never rely on the happy path.
- **A declared keymap.** Bindings are declared as data next to the screen they belong to, and the
  help overlay is generated from that same data. Never hardcode a key comparison inside a handler —
  the help then drifts from the behavior.
- **Loading and empty states.** Because every I/O call is async, every list has three renderable
  states: loading, empty, and populated. Design all three; a blank pane is not "loading".
- **Config and secrets.** Load and validate config once at startup. Never echo a secret to the
  screen or into the scrollback unless the user explicitly reveals it, and prefer a clipboard copy
  with a clear timeout over rendering it.

## Non-negotiables for a terminal

- **Resize is an event, not an edge case.** Handle it, and keep the layout usable at 80×24.
- **Do not depend on color alone.** Honour `NO_COLOR`, and pair every colour cue with a glyph or
  text label. Assume a 16-colour terminal may be all the user has.
- **Keep it keyboard-first.** Mouse support is a bonus. Every action needs a key.
- **`stdout` belongs to the UI.** Logs go to a file or `stderr`, never to `print`. One stray write
  corrupts the frame.
- **Non-TTY must not hang.** If `stdout` is a pipe or the process is in CI, either refuse with a
  clear message or fall back to a plain, non-interactive output path.

## The reference screen, concretely

Scaffold **one** screen a reader can trace end-to-end:

1. The app starts, `config` is validated, and `app.<ext>` constructs `ResourceService` with a real
   `ApiClient` and pushes `ResourceListScreen`.
2. The screen mounts and starts a **worker** that calls `ResourceService.list()`. It renders the
   loading state at once — it does not await inline.
3. The worker returns; the screen writes the result to reactive state and the table re-renders.
   If the list is empty, the empty state renders instead.
4. The user presses `enter`. A declared binding pushes `ResourceDetailScreen` with the selected id.
5. A failure raises a typed error; the central handler renders it in the status bar and the app
   stays alive.
6. `test_resource_service` proves the business behavior with a **fake client and no terminal**;
   `test_app` drives the same flow through the pilot and asserts the rendered output.

If that one slice is right, every later screen has a pattern to copy.
