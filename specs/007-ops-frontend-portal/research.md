# Research: Ops Frontend Portal

**Branch**: `007-ops-frontend-portal` | **Date**: 2026-03-06
**Input**: Technical Context unknowns from [plan.md](plan.md)

---

## R-01: Frontend Framework Selection

**Task**: Evaluate React 19 vs Vue 3 vs Svelte 5 for an operator dashboard consuming ~46 REST endpoints.

### Decision: React 19 with TypeScript

### Rationale
- **Ecosystem maturity**: React has the largest component ecosystem, critical for specialized UI needs (diff viewers, timeline visualizations, data tables with pagination).
- **TypeScript integration**: React 19 has first-class TS support. Strict mode catches API contract mismatches at compile time — essential when consuming 46 typed endpoints.
- **Hiring & knowledge**: React is the most widely known framework, aligning with the NOC engineer audience (lower barrier for internal contributions).
- **TanStack Query**: The best data-fetching library for polling-heavy dashboards (our primary data pattern) is TanStack Query, which is React-first.
- **Concurrent features**: React 19's `use()` hook and transitions enable progressive loading of dashboard cards without blocking the entire UI.

### Alternatives Considered
- **Vue 3**: Comparable capability, smaller ecosystem for specialized components (diff viewers). Composition API is clean but fewer enterprise-grade component libraries.
- **Svelte 5**: Excellent performance, but smaller ecosystem. Production readiness for enterprise dashboards with complex state (rollout timelines, multi-entity navigation context) is less proven. Fewer testing tools.

---

## R-02: State Management

**Task**: Evaluate state management for navigation context persistence, polling state, and form wizards.

### Decision: Zustand 5 for client state + TanStack Query 5 for server state

### Rationale
- **Separation of concerns**: Server state (API data, cache, polling) is managed by TanStack Query. Client state (navigation context, UI preferences, wizard state) is managed by Zustand.
- **Zustand simplicity**: No boilerplate (vs Redux Toolkit). A single store with slices maps cleanly to the Five-Item Rule — each slice is a named concern.
- **Zustand middleware**: Built-in `persist` middleware stores navigation context and timezone preferences in localStorage, surviving page refreshes.
- **TanStack Query polling**: `refetchInterval` natively supports our polling pattern (5s for active operations, 30s for passive monitoring). `staleTime` prevents redundant fetches during navigation.

### Alternatives Considered
- **Redux Toolkit**: More ceremony (slices, reducers, selectors) for the same outcome. Overkill when TanStack Query handles all server state. The Five-Item Rule would be harder to maintain with Redux's file-per-slice convention.
- **Jotai**: Atom-based model is elegant for simple state but navigation context (org → site → device) is a hierarchical object, not independent atoms. Zustand handles this more naturally.

---

## R-03: Data Fetching & Polling Strategy

**Task**: Define patterns for fetching ~46 endpoints with polling, pagination, and cache invalidation.

### Decision: TanStack Query 5 with typed query factories

### Rationale
- **Query factories**: Each API route group (config, audit, deploy, sync, system) gets a query factory that generates typed query keys and fetch functions. This maps to the Five-Item Rule (5 route groups = 5 factory files).
- **Polling**: Active operations (deployment progress, rollout waves) use `refetchInterval: 5000`. Passive views (dashboard counts, sync status) use `refetchInterval: 30000`. Intervals are configurable via Zustand settings store.
- **Pagination**: TanStack Query's `keepPreviousData` flag prevents layout shift during page transitions. The `meta.total_pages` from the API envelope drives the pagination UI.
- **Cache invalidation**: Mutations (approve job, install-from-revision, remediate drift) invalidate related query keys automatically via `onSuccess` callbacks.
- **Error handling**: Global `QueryClient` error handler maps API error codes to human-readable messages (FR-040). No raw stack traces exposed.
- **Retry**: 3 retries with exponential backoff for transient failures. No retry on 4xx errors.

### Alternatives Considered
- **SWR**: Similar capability but less mature mutation support. TanStack Query's `useMutation` with optimistic updates is better suited for deployment approval workflows.
- **Custom fetch wrapper**: Would require reimplementing caching, polling, retry, and deduplication. No benefit over TanStack Query.

---

## R-04: Diff Rendering

**Task**: Find best approach for rendering field-level configuration diffs with color coding (FR-015).

### Decision: Custom diff component using recursive object comparison

### Rationale
- **Not text diff**: Our diffs are structured JSON field-level diffs (from the backend `/api/v1/config/diff` endpoint), not line-by-line text diffs. The API returns `{path, old_value, new_value, change_type}` arrays, not unified diff format.
- **Custom component**: A `DiffViewer` component renders the API's diff response directly — left panel (old) vs right panel (new) with field-level highlighting. Color scheme: red background for removed, green for added, amber for changed (matching FR-015).
- **Reusability**: The same `DiffViewer` is used in 4 contexts: time-travel compare (FR-012), revision diff (FR-015), drift detail (FR-032), and audit record detail (FR-023). One component, four consumers.
- **Accessibility**: Color coding is supplemented with icons (minus, plus, pencil) and text labels for colorblind operators (WCAG 2.1 AA).

### Alternatives Considered
- **react-diff-viewer**: Designed for text/code diffs (unified/split format). Our data is structured objects, not text. Would require converting structured diffs to text format and losing field-level semantics.
- **Monaco diff editor**: Heavyweight (>1 MB), designed for code editing. Overkill for read-only config comparison.

---

## R-05: CSP Compliance with Tailwind CSS

**Task**: Ensure strict Content Security Policy (no inline scripts/styles) works with Tailwind CSS 4.

### Decision: Tailwind CSS 4 with Vite build — CSP-compatible by default

### Rationale
- **Tailwind 4**: Generates utility classes at build time into a single CSS file. No inline styles injected at runtime. The built CSS file is served as a static asset, fully CSP-compliant.
- **No CSS-in-JS**: Libraries like styled-components or Emotion inject inline `<style>` tags at runtime, violating CSP `style-src` restrictions. Tailwind avoids this entirely.
- **CSP headers**: Nginx configuration sets `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'`. No `'unsafe-inline'` directives needed.
- **Nonce not required**: Since all scripts and styles are external files (no inline), we don't need CSP nonces — simplifying the container configuration.

### Alternatives Considered
- **CSS Modules**: CSP-compatible but verbose for utility patterns. Would require more custom CSS for responsive layouts, accessibility states, and color-coded diffs.
- **Vanilla CSS**: Maximum control but high maintenance burden. Tailwind provides design system constraints (spacing scale, color palette) that enforce visual consistency.

---

## R-06: Container Serving Architecture

**Task**: Define Nginx configuration for SPA serving + API reverse proxy.

### Decision: Multi-stage Containerfile (Node.js build → Nginx serve)

### Rationale
- **Build stage**: Node.js 22 Alpine image runs `npm ci && npm run build`, producing static assets in `dist/`.
- **Serve stage**: Nginx 1.27 Alpine image copies `dist/` to `/usr/share/nginx/html/` and serves with:
  - `try_files $uri $uri/ /index.html` for SPA client-side routing
  - `location /api/ { proxy_pass http://api:8000; }` for API reverse proxy
  - CSP, HSTS, X-Frame-Options, X-Content-Type-Options security headers
  - Gzip compression for JS/CSS/JSON
  - Cache-Control: `max-age=31536000, immutable` for hashed assets, `no-cache` for `index.html`
- **No Node.js in production**: Final image contains only Nginx + static files. Image size ~30 MB vs ~300 MB for Node.js runtime.
- **Compose integration**: Added to existing `compose.yml` as `portal` service alongside `api`, `worker`, `db`, `redis`, `minio`, `vault`.

### Alternatives Considered
- **Caddy**: Simpler config syntax but less ecosystem support. Nginx is more widely documented for production SPA serving.
- **Node.js (Express/Fastify)**: Unnecessary runtime overhead. The spec explicitly requires static asset serving with reverse proxy (Clarification Q1).

---

## R-07: Accessibility (WCAG 2.1 AA)

**Task**: Define accessibility strategy for all primary workflows (FR-042, SC-012).

### Decision: Headless UI primitives + ARIA patterns + automated testing

### Rationale
- **Headless UI (@headlessui/react)**: Provides accessible primitives (Dialog, Menu, Listbox, Combobox, Tab) with correct ARIA roles, keyboard navigation, and focus management out of the box. No custom ARIA implementation needed for standard interactive patterns.
- **Custom components**: For non-standard UI (timeline scrubber, rollout visualization, diff viewer), follow WAI-ARIA Authoring Practices with explicit `role`, `aria-label`, `aria-live` attributes.
- **Color contrast**: Tailwind's color palette is audited for 4.5:1 contrast ratio (AA standard). Diff colors (red/green/amber) are supplemented with icons for colorblind accessibility.
- **Keyboard navigation**: All interactive elements reachable via Tab. Destructive confirmation dialogs trap focus. Escape closes modals.
- **Testing**: `@axe-core/playwright` runs automated accessibility audits in E2E tests. `eslint-plugin-jsx-a11y` catches common mistakes at lint time.

### Alternatives Considered
- **Radix UI**: Similar capability to Headless UI with slightly different API. Headless UI is maintained by the Tailwind team, ensuring seamless integration.
- **Full component library (MUI, Ant Design)**: Provides accessible components but imposes design opinions that conflict with our Tailwind-based design system. Heavier bundle size.

---

## R-08: Testing Strategy

**Task**: Define testing approach covering unit, component, and E2E for ~15 views.

### Decision: Three-tier testing with Vitest + React Testing Library + Playwright

### Rationale
- **Vitest (unit)**: Tests pure functions (API response transformers, diff computation helpers, timestamp formatting). Fast, Vite-native, TypeScript-first.
- **React Testing Library (component)**: Tests component behavior — renders components with mock API data, verifies user interactions trigger correct state changes and API calls. Uses MSW (Mock Service Worker) to intercept and mock API requests.
- **Playwright (E2E)**: Tests critical user journeys end-to-end against a running portal + mock API server:
  1. Login → Dashboard → Drill into org → View device
  2. Time-travel: Select device → Pick timestamp → Compare with current
  3. Config: View revisions → Diff two revisions → Install from revision (with confirmation)
  4. Deploy: Create job → Dry run → Submit → Approve
  5. Audit: Filter records → Export CSV
- **Coverage targets**: 80% statement coverage for `src/api/` and `src/hooks/` (business logic). Component tests for all confirmation dialogs (safety-critical).

### Alternatives Considered
- **Jest**: Vitest is faster (Vite-native) and has identical API. No benefit to Jest.
- **Cypress**: Heavier than Playwright, no multi-browser support in free tier. Playwright supports Chrome, Firefox, WebKit natively.

---

## Summary of Technology Decisions

| Area | Decision | Key Reason |
|------|----------|------------|
| Framework | React 19 + TypeScript 5.5 | Largest ecosystem, best TS integration, TanStack Query support |
| Build | Vite 6 | Fast builds, native TS/JSX, HMR for dev |
| Routing | React Router 7 | Standard SPA routing, data loaders, nested layouts |
| Server State | TanStack Query 5 | Polling, caching, pagination, mutations — all built-in |
| Client State | Zustand 5 | Minimal boilerplate, persist middleware, Five-Item Rule alignment |
| Styling | Tailwind CSS 4 | CSP-compliant, utility-first, build-time CSS generation |
| Accessibility | Headless UI + ARIA patterns | Accessible primitives, Tailwind integration |
| Diff Rendering | Custom DiffViewer component | Structured field-level diffs from API, reused in 4 views |
| Testing | Vitest + RTL + Playwright | Fast unit tests, behavioral component tests, E2E journeys |
| Container | Multi-stage Node.js build → Nginx serve | ~30 MB image, CSP headers, reverse proxy, no runtime |
