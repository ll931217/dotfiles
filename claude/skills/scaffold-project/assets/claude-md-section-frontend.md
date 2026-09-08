<!-- BEGIN scaffold-project -->
## Frontend Architecture

This app follows a feature-based, layered frontend architecture. **These rules are the source of truth** — when generated code and these rules disagree, follow the rules. Reference implementation: `{{REFERENCE_FEATURE_PATH}}`.

**Stack:** {{LANGUAGE}} + {{FRAMEWORK}} (data fetching: {{DATA_FETCHING}}, validation: {{VALIDATION_MECHANISM}}).

### Layering & dependency direction

- Organize **by feature**, not by layer. Everything for a feature lives in its own directory under `{{FEATURES_DIR}}`, exporting a small public surface via its `index` file. Cross-feature reuse goes through `{{SHARED_DIR}}` — never import another feature's internals.
- The layers are **route/page → feature components → hooks → API layer**, and dependencies point only in that direction.
  - **Routes/pages** compose feature components and own layout + error/loading boundaries. No feature logic or API calls inline.
  - **Components** render UI and hold local UI state only. They never call `fetch` or the HTTP client directly.
  - **Hooks** ({{HOOKS_CONVENTION}}) own server-state access and feature logic, wrapping the API layer.
  - **The API layer** (`{{API_LAYER_PATH}}`) is the only code that talks to the network. Every response is validated against a schema there; downstream code trusts its types.

### State ownership

- **Server state** lives in {{DATA_FETCHING}} — never copied into a store.
- **Local UI state** lives in the component that owns it.
- **Shareable view state** (filters, pagination, selected tab) lives in the URL.
- **Shared client state** gets a store only when two unrelated features need it — not preemptively.

### Boundaries & cross-cutting concerns

- API responses are validated at the boundary with {{VALIDATION_MECHANISM}}; a bad payload fails in the API layer, not deep in a component.
- Errors surface as a typed API error and are presented by the route-level error boundary / notification layer: {{ERROR_HANDLER}}.
- Env config is read and validated once in `{{CONFIG_LOCATION}}`; never read raw env vars in components.

### Adding a new feature

Copy the reference feature's structure: feature folder with components, hooks, `api` module + schemas, types, and at least one test that renders the feature with the **API layer mocked** — no network in tests.

### Naming

Follow the existing file/component naming convention shown in `{{REFERENCE_FEATURE_PATH}}` ({{NAMING_CONVENTION}}).
<!-- END scaffold-project -->
