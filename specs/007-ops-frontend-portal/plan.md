# Implementation Plan: Ops Frontend Portal

**Branch**: `007-ops-frontend-portal` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-ops-frontend-portal/spec.md`

## Summary

Build a production-grade operator-facing web portal that consumes the existing Mist Ops Platform REST API (~46 endpoints under `/api/v1/`) and provides dashboards, time-travel investigation, configuration versioning/diff/rollback, scheduled deployments, audit/compliance reporting, phased rollouts, and drift detection/remediation. The portal is deployed as a separate container serving pre-built static assets via Nginx reverse proxy — no server-side runtime in production.

## Technical Context

**Language/Version**: TypeScript 5.5+ (strict mode)
**Primary Dependencies**: React 19, React Router 7, TanStack Query 5, Zustand 5, Tailwind CSS 4, Vite 6
**Storage**: N/A (browser-only; all persistence via backend API)
**Testing**: Vitest (unit), Playwright (E2E), React Testing Library (component)
**Target Platform**: Modern desktop browsers (Chrome, Firefox, Edge — latest 2 stable versions)
**Project Type**: Single-page web application (SPA) served as static assets
**Performance Goals**: Dashboard render <3s on 10 Mbps, view transitions <1s, diff render <3s for 50 KB configs
**Constraints**: Strict CSP (no inline scripts/styles), no server-side runtime, accessible (WCAG 2.1 AA)
**Scale/Scope**: 50 concurrent operators, ~15 views/pages, ~46 API endpoints consumed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate (Initial)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | Frontend directory structure planned with max 5 children per level. Components organized by feature domain. Functions will respect 25-line / 5-param limits. |
| II. Class-Based Architecture | ADAPTED | TypeScript/React uses functional components with hooks as the idiomatic pattern. The spirit of "no standalone wrappers" is maintained: all logic lives in named custom hooks or service classes — never in bare utility functions that delegate. |
| III. Safety-First | PASS | All destructive operations (install-from-revision, remediate, rollback, firmware upgrade) require explicit confirmation dialogs with typed confirmation keywords. API-sourced data sanitized before render. CSP enforced. |
| IV. Full Deployment Pipeline | ADAPTED | Frontend has its own CI pipeline: lint + type-check + test + build + container push. Separate from MistHelper.py pipeline but follows same principle of "no skipping steps." |
| V. Observability & Logging | PASS | Client-side error capture and performance metrics reported to backend. Structured console logging in development. ASCII-only in log output. |

**Adaptation Justifications**:
- **Principle II**: React's functional component + hooks paradigm is the TypeScript/React equivalent of class-based architecture. Custom hooks (`useTimeTravelQuery`, `useDriftAlerts`) provide the same ownership, discoverability, and testability as classes. Standalone wrapper functions are still prohibited.
- **Principle IV**: The frontend is a separate deployable artifact with its own container image. Its pipeline mirrors the MistHelper pipeline structurally (validate → commit → push → CI build → pull image → restart → verify) but targets the frontend container.

### Post-Design Gate (After Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | `src/` has 5 children (api, components, features, hooks, pages). Each query factory file covers 1 route group. Data model has 5 domains + 1 shared. Route structure has 7 top-level sections (justified: mirrors 7 nav items from FR-001). |
| II. Class-Based Architecture | PASS | `ApiClient` is a proper class. Query factories are named objects (not standalone functions). Custom hooks (`useNavigationContext`, `usePollingConfig`) encapsulate reusable logic. `DiffViewer`, `ConfirmationDialog`, `PaginatedTable`, `ProgressTracker` are named components. |
| III. Safety-First | PASS | 5 destructive operations mapped with confirmation keywords in contracts. CSP header defined. Data sanitization rules documented. `dangerouslySetInnerHTML` prohibited. Token storage is memory-only (no localStorage for secrets). |
| IV. Full Deployment Pipeline | PASS | Pipeline defined: lint → typecheck → test → build → container push → pull → restart → verify. Container build is multi-stage (Node build → Nginx serve). |
| V. Observability & Logging | PASS | Client-side telemetry (FR-043) reports JS errors, API failures, page load times to backend metrics endpoint. Error code mapping ensures human-readable messages (FR-040). |

**Post-Design Violations**: None. All principles pass or have documented adaptations.

## Project Structure

### Documentation (this feature)

```text
specs/007-ops-frontend-portal/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (frontend-specific)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
ops-portal/
├── src/
│   ├── api/             # API client, types, query hooks
│   ├── components/      # Shared UI components (max 5 subdirs)
│   ├── features/        # Feature modules (max 5 subdirs per feature)
│   ├── hooks/           # Shared custom hooks
│   └── pages/           # Route-level page components
├── tests/
│   ├── e2e/             # Playwright end-to-end tests
│   └── unit/            # Vitest unit + component tests
├── public/              # Static assets (favicon, manifest)
├── nginx/               # Nginx config for container serving
├── Containerfile         # Multi-stage build (node build + nginx serve)
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.ts
```

**Structure Decision**: Standalone `ops-portal/` directory at repository root — separate from `mist-ops-platform/` (backend). This mirrors the 3-layer architecture: the portal is an independent deployable that communicates with the application layer exclusively via the REST API. The Five-Item Rule is enforced: `src/` has exactly 5 children; each feature module has at most 5 internal directories.

## Complexity Tracking

> **Principle II adaptation documented above. No other violations.**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Functional components + hooks instead of classes (Principle II) | React 19 / TypeScript idiom — classes are deprecated in React ecosystem | Class components lack hook support, are verbose, and diverge from all modern React libraries and documentation |
| `pages/` has 7 subdirectories (Principle I) | Each directory maps 1:1 to a primary nav section per FR-001. Shell pages (RootLayout, LoginPage) are isolated in `pages/shell/`. | Merging directories (e.g., drift/ into config/) breaks the direct mapping between nav items and page directories, making the codebase harder to navigate |
