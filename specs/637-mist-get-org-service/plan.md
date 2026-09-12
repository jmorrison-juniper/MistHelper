# Implementation Plan: Mist API Read Operation -- getOrgService

**Branch**: `637-mist-get-org-service` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/637-mist-get-org-service/spec.md`

## Summary

Add a new MistHelper menu item that reads a single Mist Org Service definition by UUID via
`mistapi.api.v1.orgs.services.getOrgService(apisession, org_id, service_id)`. The menu prompts the
NOC engineer for the `service_id` (org_id is loaded from `.env`), invokes the SDK, and persists the
single-object JSON payload through `DataExporter.write_with_format_selection` so CSV, SQLite, and
ArangoDB+Redis backends all upsert consistently. Because the endpoint returns exactly one service
definition with a stable API-provided `id`, the operation registers a `natural_pk` strategy in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` and reuses the existing `listOrgServices` SQLite table
`org_services` for storage. Proposed menu number: **195** (first slot immediately after the
destructive-operation block 154-194, keeping this safe read grouped with the "single-item detail
viewer" pattern established for peer read-by-id endpoints).

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: mistapi 0.59+ (Thomas Munzer SDK), python-dotenv, requests (transitive),
Podman container runtime for deployment
**Storage**: SQLite (`data/mist_data.db`, table `org_services`) plus CSV fallback plus optional
ArangoDB+Redis polyglot backend, all routed through `DataExporter.write_with_format_selection`
**Testing**: `python MistHelper.py --test` interactive-skip harness (this menu number added to the
safe-invocation set), plus `python -m py_compile`, `python -m ruff check MistHelper.py`, and
`python -m black --check MistHelper.py`
**Target Platform**: Windows 11 developer venv (`.venv\Scripts\Activate.ps1`) and Linux Podman
container image `ghcr.io/jmorrison-juniper/misthelper:latest`, also reachable via SSH on port 2200
**Project Type**: CLI monolith -- one file, `MistHelper.py` (~28K lines) containing all menu logic
**Performance Goals**: Single-object GET completes in <=5s p95 under normal load; adaptive delay
system tolerates 429 without user intervention
**Constraints**: Single HTTP round trip (endpoint is not paginated per enriched doc); ASCII-only
logging; no secrets in log output; `safe_input()` mandatory for both prompts
**Scale/Scope**: 1 new menu item, 1 new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry (`getOrgService`),
1 new static method on the existing `OrgServicesReader` category class (or the nearest existing
"Templates/Services" reader class; see Structure Decision), 1 README menu-table row, 1 CHANGELOG
entry, 0 schema migrations (reuses `org_services` table).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `get_org_service_detail()` fits in <=25 lines, uses <=5
  parameters (`apisession`, `org_id`, `service_id`, `data_format`, `filename`), <=5 logical blocks
  (prompt, log-info, SDK call, log-debug, export), and adds only 1 child to the chosen class
  (`OrgServicesReader`), staying under the 5-children limit at every hierarchy level.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- Implementation lives as a static method on the existing services-reader
  class -- no standalone wrapper function. Menu dispatch routes directly to
  `OrgServicesReader.get_org_service_detail()`.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- Both prompts (org_id override, service_id) go through `safe_input(prompt,
  context="get_org_service")` so SSH/container EOF exits 0 without traceback. Endpoint is
  read-only (GET), so no destructive-confirmation gate is required. 404 on unknown service_id is
  caught and surfaced as `logging.warning` per the acceptance scenarios.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After code lands: `py_compile` + `ruff` + `black --check`, commit with
  `version YY.MM.DD.HH.MM`, push, container-build workflow runs, `podman pull` and container
  restart to verify. No pipeline changes required for this feature.

### Principle V: Observability & Logging

- **STATUS: PASS** -- ASCII-only logging. `logging.info` before the SDK call reports the
  operation and target `service_id`; `logging.debug` after logs the record count (0 or 1) and
  bytes written. API token never logged. Exceptions logged with `logging.exception` inside a
  bounded try/except.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line of the new method and the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry receives a same-line inline comment describing *why*
  the line exists (not merely what it does). Menu registration row also commented.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- Pattern is `logging.info("Fetching service %s from org %s", service_id,
  org_id)` immediately before `mistapi.api.v1.orgs.services.getOrgService(...)`, followed by
  `logging.debug("getOrgService returned %d field(s); persisted to %s", len(data or {}),
  output_path)` immediately after. Matches the reference `listOrgServices` pattern in
  MistHelper.py.

### Pre-Phase 0 Gate: PASS

All seven principles cleared with explicit PASS verdicts; no exceptions requested.

## Project Structure

### Documentation (this feature)

```text
specs/637-mist-get-org-service/
├── spec.md                        # Feature specification (input, not edited here)
├── plan.md                        # This file
├── research.md                    # Phase 0 -- decisions and grounding
├── data-model.md                  # Phase 1 -- entity model + SQLite DDL
├── quickstart.md                  # Phase 1 -- dev quickstart
└── contracts/
    └── get_org_service.md         # Phase 1 -- HTTP + SDK contract
```

### Source Code (repository root)

```text
MistHelper.py
  |-- ENDPOINT_PRIMARY_KEY_STRATEGIES  (add "getOrgService" entry, natural_pk on "id")
  |-- class OrgServicesReader          (extend: new static get_org_service_detail method)
  |-- MAIN_MENU dispatch               (register menu 195 -> OrgServicesReader.get_org_service_detail)
README.md
  |-- Menu category table              (add row "195 | Get Org Service (single) | safe read")
CHANGELOG.md
  |-- New entry "version YY.MM.DD.HH.MM -- add menu 195 getOrgService single-service detail"
```

**Structure Decision**: Single-file monolith (unchanged). The new capability extends the existing
`OrgServicesReader` class (peer of `listOrgServices` at MistHelper.py line ~6371). If that exact
class name is not present the implementer MUST reuse the nearest existing class that owns the
`mistapi.api.v1.orgs.services` namespace rather than introduce a new one -- creating a new
one-method class would violate Principle II (Class-Based Architecture, no wrappers) and inflate
the class count under Principle I. The new method sits alongside the plural `list_org_services`
method as the singular-detail counterpart.

## Post-Phase 1 Re-Check

Re-evaluating all seven principles after research.md, data-model.md, quickstart.md, and
contracts/get_org_service.md were produced:

- **Principle I (Five-Item Rule)**: PASS -- data-model.md confirms one entity (`Service`), one
  table (`org_services`), one new method. No hierarchy level exceeds five children.
- **Principle II (Class-Based)**: PASS -- contract binds the operation to the existing services
  reader class; no wrapper function introduced.
- **Principle III (Safety-First)**: PASS -- quickstart.md documents the exact `safe_input()`
  prompts and the SSH/container EOF exit path.
- **Principle IV (Pipeline)**: PASS -- quickstart.md lists all four quality-gate commands and the
  post-merge container refresh.
- **Principle V (Observability)**: PASS -- contract enumerates the two log statements (INFO
  before, DEBUG after) plus the 401/403/404/429 handling.
- **Principle VI (Inline Comments)**: PASS -- data-model.md DDL and quickstart.md example include
  the mandated inline-comment style for the implementer.
- **Principle VII (Action Logging)**: PASS -- contract specifies the exact log lines matching the
  `listOrgServices` precedent.

### Post-Phase 1 Gate: PASS

## Complexity Tracking

> Not required -- no Constitution exceptions requested. Table intentionally empty.

| Principle | Status | Justification |
|-----------|--------|---------------|
| (none) | (none) | No exceptions requested; all seven principles PASS. |
