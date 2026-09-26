# Frontend architecture — canonical reference

The frontend equivalent of the backend's layered architecture. The roles and dependency rules are invariant across frameworks; only the spelling changes. This is **not** controller/service/repository transplanted into the browser — a frontend's layers follow how data and UI actually flow.

## The layers

```
User interaction
   │
   ▼
Route/Page ──renders──▶ Feature components ──use──▶ Hooks/composables ──call──▶ API layer ──▶ Backend
   │ (composition)         │ (UI + local state)        │ (server state,          │ (typed client,
   │                       │                           │  feature logic)         │  validated responses)
   └─ layout, error        └─ presentation             └─ orchestration          └─ transport detail
      boundary
```

| Layer | Responsibility | May depend on | Must NOT |
|-------|----------------|---------------|----------|
| **Route/Page** | Compose a screen from feature components; own layout, route params, error/loading boundaries | Feature components, shared layout | Contain feature logic or API calls inline |
| **Feature component** | Render one feature's UI; local/ephemeral UI state | Its feature's hooks, shared UI components | Call `fetch`/the HTTP client directly; import another feature's internals |
| **Hook / composable** | Feature logic and server-state access (query/mutation wrappers, derived state) | The API layer, state libs | Render JSX/markup; know about routing internals |
| **API layer** | The only place that talks to the network: typed client, endpoint functions, response validation | HTTP client, schema/types | Contain UI or feature branching logic |
| **Types/schemas** | Contracts for API data, validated at the boundary | — | Be hand-drifted copies of backend types when generation/sharing is available |

### The cardinal dependency rules

- **Components never touch the network.** All requests go through the API layer, via hooks. This is the frontend's "controllers never touch repositories."
- **Features don't reach into each other's internals.** A feature exports a small public surface (its page/main components, maybe a hook); everything else is private to its folder. Cross-feature reuse goes through `shared/`.
- **Validate at the boundary.** API responses are parsed against a schema (zod / valibot / `effect/Schema`) or generated types in the API layer, so everything downstream is typed and trusted.

## State ownership

Decide where state lives by what kind of state it is — this is the most common source of frontend mess:

- **Server state** (data from the API): the data-fetching layer owns it — TanStack Query, SWR, RTK Query, or the framework's loader (Next.js/Nuxt/SvelteKit). Never copy server data into a global store "for convenience."
- **Local UI state** (open/closed, input values): `useState`/`ref` in the component that owns it.
- **Shared client state** (theme, auth session, cart): context or a small store (zustand/pinia) — added only when two unrelated features actually need it, not preemptively.
- **URL state** (filters, pagination, selected tab): the URL. If a user would want to share or refresh into it, it belongs in query params, not a store.

## Cross-cutting concerns

- **Error handling** — one error boundary at the route level plus a consistent API-error shape surfaced by the API layer (a typed `ApiError`, not raw fetch failures). Feature code throws/returns domain errors; the boundary and toast/notification layer present them.
- **Config** — env vars read and validated in one `config` module at startup (`import.meta.env` / `process.env` behind a typed export). Never read raw env vars deep in components.
- **Loading states** — handled by the data-fetching layer's primitives (suspense boundaries, `isPending`), not hand-rolled flags.

## Canonical directory layout

Organize **by feature, not by layer** — same principle as the backend. Everything for `users` lives together and can be understood (and deleted) as a unit.

```
src/
  main.<ext>                 # bootstrap: mount app, providers, router
  app/                       # app shell: router config, providers, global error boundary
    router.<ext>
    providers.<ext>
  config/
    config.<ext>             # typed/validated env loading (fail fast on bad config)
  lib/
    api-client.<ext>         # the HTTP client instance: base URL, auth header, error mapping
  shared/                    # cross-feature building blocks
    components/              # design-system-ish primitives (Button, Modal, ...)
    hooks/
  features/
    users/                   # one self-contained feature
      index.<ext>            # the feature's public surface (re-exports)
      components/
        UserList.<ext>
        UserForm.<ext>
      hooks/
        useUsers.<ext>       # query/mutation hooks wrapping the API layer
      api.<ext>              # endpoint functions + response schemas for this feature
      types.<ext>
      users.test.<ext>       # component/hook test with the API layer mocked
```

Framework-router conventions (Next.js `app/`, SvelteKit `routes/`, Nuxt `pages/`) replace the `app/router` piece — route files stay thin and delegate to `features/`. Don't fight the framework's file conventions; keep the feature-folder rule for everything the router doesn't mandate.

## Framework mapping

Pick the idiomatic default and proceed (the user can override):

| Request | Default | Data fetching | Validation | Test setup |
|---------|---------|---------------|------------|------------|
| **React SPA** (default when unspecified) | Vite + React + TypeScript | TanStack Query | zod (or `effect/Schema` when Effect is set up) | Vitest + Testing Library, API mocked via MSW or a mocked api module |
| **React with SSR/routing needs** | Next.js (App Router) | Server components + TanStack Query for client state | zod / `effect/Schema` | Vitest + Testing Library |
| **Vue** | Vite + Vue 3 + TypeScript (Nuxt if SSR) | TanStack Query (vue-query) or Nuxt `useFetch` | zod / valibot | Vitest + Vue Testing Library |
| **Svelte** | SvelteKit | `load` functions + TanStack Query where client-side | zod | Vitest + Testing Library |

For TypeScript frontends, the `setup-effect` step from the workflow applies: `effect/Schema` is the preferred boundary validator and Effect can back the API layer — but keep components framework-idiomatic; Effect lives below the hooks, not inside JSX.

## The reference feature, concretely

The single reference feature you scaffold should let a reader trace one interaction end-to-end:

1. The `users` route renders `UserList` inside the route's error boundary.
2. `UserList` calls `useUsers()` — no fetch in sight.
3. `useUsers` wraps a query around `features/users/api.ts#listUsers()`.
4. `listUsers` calls the shared api-client and parses the response against `UserSchema`; a bad payload fails loudly here, not three components deep.
5. A failed request surfaces as a typed `ApiError`, presented by the boundary/notification layer.
6. The test renders `UserList` with the api module mocked and asserts the UI — no network required.

If you show that one slice well, every future feature has a pattern to copy.
