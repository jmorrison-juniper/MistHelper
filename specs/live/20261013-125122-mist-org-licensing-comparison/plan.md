# Implementation Plan: Mist Organization Licensing Comparison

**Branch**: `jmorrison-jnpr-4197-mistorglicensingcomparison-integrat` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/live/20261013-125122-mist-org-licensing-comparison/spec.md`

## Summary

Add the source dashboard layout and workflow as a page in the current MistHelper Flask portal. Use its shared Mist session, supported SDK calls, and existing data services. Keep manual rows and purchased values in browser session storage. Add no service, database, Redis instance, server, or public port.

## Technical Context

**Language/Version**: Python 3.13 or newer with the existing HTML, CSS, and JavaScript.

**Primary Dependencies**: Existing Flask portal, Jinja templates, Bootstrap assets, `mistapi>=0.64.0,<0.65`, and `DataExporter`.

**Storage**: Browser `sessionStorage` for manual rows and purchased amounts. Use the existing data directory and `DataExporter` only for an operator-requested CSV export. Add no persistent store.

**Testing**: Pytest with synthetic Mist responses, Flask test clients, the installed SDK contract guard, and existing portal end-to-end tests.

**Target Platform**: The existing MistHelper web portal on port 8055.

**Project Type**: Page and API routes in the existing Flask application.

**Performance Goals**: Use `RateLimitingUtils` for baseline pacing. Send one Mist request at a time. After HTTP 429, wait 60 seconds per token and retry once. Do not retry other HTTP failures.

**Constraints**: Preserve the source dashboard workflow and CC BY-NC-SA 4.0 attribution. Use the existing `APISESSION` and data services. Do not add a database, Redis service, separate frontend, server, or public port.

**Scale/Scope**: Compare multiple organizations available to the active Mist session. Do not add a new fixed organization limit.

## Constitution Check

- **Structure**: Place new feature code in `src/interfaces/portals/licensing_comparison/`. This parent currently has two direct children. Keep the feature package at five direct children or fewer.
- **Existing portal**: Register one blueprint in `web_portal/app.py` and add one navigation link in `web_portal/templates/base.html`. Do not add a route or template to the over-limit `web_portal/routes/` or `web_portal/templates/` directories.
- **Tests**: Add `tests/integration/web_portal/licensing_comparison/` under the existing portal integration test directory. Extend the existing `tests/e2e/web_portal/test_portal_smoke.py` file for page and selector checks. Add no new direct child to a test directory that already exceeds five children.
- **Browser state tests**: Add `tests/e2e/licensing_comparison/test_session_state.py` under a feature-specific directory. Do not add a browser test to the over-limit `tests/e2e/web_portal/` directory.
- **Process-folder debt**: The process baseline lists 792 grandfathered direct children under `specs/` and four managed roots. This feature adds one timestamp record under `specs/live/`. A separate future process change must move one grandfathered record into a managed root.
- **Mist access**: Use supported `mistapi` methods with the shared portal session. Do not add direct REST calls or an owned WebSocket.
- **Data and safety**: Keep manual input in browser session storage. Write only an explicit CSV export through the shared data service. Do not turn API failures into successful zero values.
- **Class-based design**: Put behavior in named classes. Do not add standalone wrapper functions. Keep each function within the constitution limits for parameters, logical blocks, and lines.
- **Code comments and logs**: Add an explanatory inline comment to each executable line. Use ASCII, machine-parseable logs through `structlog` or an equivalent. Log each meaningful action before and after it. Redact secrets at the logging boundary.
- **Constitution review**: Verify all seven core principles before the implementation pull request. Treat inline comments and action logging as required gates.
- **Commit and pull request**: Use a Conventional Commit title and preserve the repository pull request template. This branch contains planning artifacts only.

## Implementation Delivery

After implementation, run every applicable local gate. Build the feature manifest and stage only its explicit files. Commit with a Conventional Commit subject, rebase on `origin/main`, and rerun affected gates. Push the branch and open an implementation pull request that closes issue #4197. Wait for required CI, then squash merge after approval. Wait for the main container build. Verify that the image revision equals the merged commit. After release approval, deploy the approved image and check container and portal health.

**Pre-design gate**: Pass with the structure and storage constraints above. The exact requested branch is already checked out in another worktree. This session uses its own branch from `main`.

## Phase 0: Research

See [research.md](research.md). The local portal shares its Mist session through `APISESSION`. Its operations page reads MSP privileges with `getSelf`. The Mist API reference names the organization, license, and inventory SDK methods.

## Phase 1: Design

See [data-model.md](data-model.md), [contracts/licensing-comparison.md](contracts/licensing-comparison.md), and [quickstart.md](quickstart.md). Keep presentation, route handling, and comparison rules inside the new feature package. Reuse the current app factory, navigation, rate-limit service, exporter, and data-directory download path.

### Project Structure

```text
src/interfaces/portals/licensing_comparison/
├── __init__.py
├── routes.py
├── service.py
├── templates/
│   └── licensing_comparison.html
└── static/
    ├── licensing_comparison.css
    └── licensing_comparison.js

web_portal/
├── app.py                         # Register the feature blueprint.
└── templates/base.html            # Add the page link to the existing navigation.

tests/integration/web_portal/
└── licensing_comparison/
    ├── test_routes.py
    ├── test_service.py
    └── test_export.py

tests/e2e/web_portal/test_portal_smoke.py  # Add the page and selector checks.

tests/e2e/licensing_comparison/
└── test_session_state.py
```

The new feature package has five direct children. Its `service.py` owns the comparison records and calculations, so the package needs no extra model module. The route template and assets preserve the source dashboard layout and use the existing application process.

## Complexity Tracking

No constitution exception is requested. The branch-name conflict and unavailable PowerShell setup script are workflow limits, not product-design exceptions.
