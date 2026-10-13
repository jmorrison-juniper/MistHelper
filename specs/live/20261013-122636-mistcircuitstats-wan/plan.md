# Implementation Plan: MistCircuitStats WAN Dashboard

**Branch**: `feat/4195-mistcircuitstats-wan-dashboard` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

**Input**: Timestamp feature specification in `specs/live/20261013-122636-mistcircuitstats-wan/spec.md`

## Summary

Add the MistCircuitStats WAN dashboard as a tab in MistHelper's existing Flask portal on port 8055. Preserve the source dashboard's operator journeys and page layout. Use MistHelper's existing Mist session, portal security, data services, compose group, and Redis service. Add no database, Redis service, application server, or public port.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Existing Flask portal, `mistapi>=0.64.0,<0.65`, existing Redis client and Redis Stack service

**Storage**: No new persistent store. Use namespaced, expiring entries in the existing shared Redis service for data that needs a shared cache. Keep live telemetry out of the existing SQLite and ArangoDB stores unless a later product requirement defines durable history.

**Testing**: `pytest`, Flask test client end-to-end checks, manual browser comparison, and the existing Mist API SDK compatibility checks

**Target Platform**: MistHelper host deployment and existing Podman compose group on Windows, macOS, and Linux

**Project Type**: Portal feature in the existing Flask application

**Performance Goals**: Preserve the source's bounded request patterns, full pagination, 300-second site cache, and 600-second profile and template caches. Record the source and integrated page latency with the same synthetic organization before setting a new target.

**Constraints**: Use `mistapi` for every Mist REST request. Preserve organization access checks, token handling, bounded rate-limit waits, cache TTLs, and safe stale-data notices. Reuse the current portal and one shared Redis service. Add no database, Redis process, web server, or published port.

**Scale/Scope**: One WAN dashboard tab for the active authorized organization. Support all paginated sites and gateways, four traffic ranges, five insight ranges, per-port details, and two CSV export workflows.

## Constitution Check

| Gate | Result | Evidence or action |
|---|---|---|
| Five-item hierarchy | Pass with design constraint | Keep the source and test packages at five or fewer direct children. Add no direct child under the crowded `tests/integration` or `tests/e2e/web_portal` folders. |
| Existing portal ownership | Pass | Register one blueprint in `web_portal/app.py` and add a navigation link in `web_portal/templates/base.html`. Keep the page template and assets inside the new feature package. |
| Mist API transport | Pass with contract gate | Use the installed Mist SDK methods listed in the spec. Add compatibility, authentication, endpoint-parity, error, output, and secret-redaction tests before implementation. |
| Data and service consolidation | Pass | Use existing configuration, compose group, Redis service, and persistence boundaries. Add no database or Redis service. Keep dashboard telemetry transient. |
| Safety and security | Pass with test gate | This feature is read-only. Reuse portal security middleware, validate route values, escape Mist data, neutralize spreadsheet formulas, and never log credentials. |
| License and attribution | Pass | Both repositories publish CC BY-NC-SA 4.0. Retain attribution, identify the source, and record modifications. |
| Managed process records | Pass | Store this feature under the managed `specs/live/` root. Add no new unmanaged root or process-folder child. Existing baseline debt remains unchanged. |
| Quality gates | Required before merge | Run the changed-file tests, portal end-to-end tests, Ruff, Black, mypy, Bandit, and STE checks that apply. Run relevant menu and full repository guardrails after implementation. |

**Existing process-folder debt**: Preserve all current `specs/` entries. Use only the managed `specs/live/` root for this feature record.

**Separate remediation action**: Keep the existing process-folder baseline guard ratchet active. Remediate legacy unmanaged entries in separate issue-scoped changes.

**Existing test-folder debt**: `tests/integration` has 23 direct children, and `tests/e2e/web_portal` has 22. This feature adds no direct child to either folder. Add the integration test package under the existing `tests/integration/web_portal` folder, which has one direct child. Keep the new package to five entries: `__init__.py` and four test modules. Add one end-to-end case to the existing `TestDashboardPage` class in `tests/e2e/web_portal/test_portal_smoke.py`. That class has four methods, so keep the added method to five or fewer class members.

**Separate test-folder remediation action**: Track a separate issue to reduce the existing test-folder excess. Do not move unrelated test files in this feature.

## Phase 0: Research

See [research.md](research.md). It records the portal boundary, Mist transport, shared cache, licensing, failure behavior, and alternatives.

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/wan-dashboard.md](contracts/wan-dashboard.md), and [quickstart.md](quickstart.md).

The dashboard is a read-only portal feature. It reads Mist organization, inventory, device, port, peer-path, insight, and SLE data. It holds no independent persistent telemetry database. Cache records use a feature namespace, the shared Redis service, and bounded TTLs.

## Project Structure

### Documentation (this feature)

```text
specs/live/20261013-122636-mistcircuitstats-wan/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── wan-dashboard.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
web_portal/
├── app.py                         # Register the feature blueprint.
└── templates/
    └── base.html                  # Add the dashboard navigation tab.

src/interfaces/portals/wan_dashboard/
├── __init__.py                    # Expose the portal blueprint.
├── routes.py                      # Define the page and read-only endpoints.
├── services.py                    # Collect and prepare Mist data.
├── templates/
│   └── wan_dashboard/
│       └── dashboard.html         # Avoid a collision with the shared portal template.
└── static/
    ├── dashboard.css              # Preserve responsive page styling.
    └── dashboard.js               # Render tables, charts, and exports.

tests/integration/web_portal/wan_dashboard/
├── __init__.py
├── test_services.py
├── test_routes.py
├── test_exports.py
└── test_mistapi_contract.py

tests/e2e/web_portal/
└── test_portal_smoke.py  # Add one WAN dashboard end-to-end case to the existing dashboard test class.
```

**Structure Decision**: Put feature behavior and page assets in one compliant package under `src/interfaces/portals/`. Place integration tests under the existing web-portal integration folder and extend one existing Flask test-client case. Use manual browser comparison for visual preservation. The existing web portal registers the package blueprint and exposes its navigation link. Keep the current React `ops-portal` unchanged. Add no separate app, service, port, or database.

## Complexity Tracking

No constitution exception is proposed. The source package has five direct entries. The new integration test package has five direct entries, and no new child is added under the noncompliant test folders listed above. T044 records the performance baseline. Track existing folder excess for separate remediation.
