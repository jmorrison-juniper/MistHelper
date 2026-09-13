# Implementation Plan: countOrgSystemEvents

**Branch**: `530-mist-count-org-system-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/530-mist-count-org-system-events/spec.md`

## Summary

Add a new safe, read-only MistHelper menu item that wraps the Mist API
`GET /api/v1/orgs/{org_id}/events/system/count` endpoint via the
`mistapi.api.v1.orgs.events.countOrgSystemEvents()` SDK call. The menu
collects the org_id (default from `.env`) and optional time-range / distinct
filters using `safe_input()`, invokes the SDK once, and persists the
aggregated count result through
`DataExporter.write_with_format_selection(...)` so the CSV, SQLite, and
ArangoDB+Redis backends all receive consistent rows. The new operationId
is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` with an
`auto_increment_with_unique` strategy keyed on
`(org_id, distinct, start_epoch, end_epoch)`, because the count payload
has no stable server-assigned identifier. Proposed menu number: **195**
(next sequential after the destructive 154-194 range, placed alongside
adjacent safe org event exports such as 20-26).

## Technical Context

**Language/Version**: Python 3.13 or newer (required by repository).
**Primary Dependencies**: mistapi 0.59+ (Thomas Munzer's SDK), python-dotenv,
requests, tabulate, rich (already pinned in `requirements.txt`).
**Storage**: Multi-backend via `DataExporter` -- CSV files in `data/`,
SQLite at `data/mist_data.db`, optional ArangoDB+Redis containers.
**Testing**: `python MistHelper.py --test` for menu smoke tests; pytest +
Hypothesis for unit/property tests; quality gates `python -m py_compile`,
`python -m ruff check`, `python -m black --check`.
**Target Platform**: Windows 11 host (developer workstation) and Podman
container `ghcr.io/jmorrison-juniper/misthelper:latest` running on Linux.
**Project Type**: Single-file CLI monolith (~28K-line `MistHelper.py`)
with menu-driven and `--menu N` automation entry points.
**Performance Goals**: Single-page count request returns <=5s under
nominal Mist API latency; respects adaptive rate limiter (default 1000
items per page; configurable via `MIST_PAGE_LIMIT`). The count endpoint
returns a single aggregation document, so pagination is rare but
supported.
**Constraints**: 5-Item Rule (<=5 params, <=5 blocks, <=25 lines per
function); ASCII-only logging; no Unicode/emoji; inline comment on every
new executable line; `safe_input()` for all prompts; `INSERT OR REPLACE`
semantics for SQLite upserts.
**Scale/Scope**: One new menu method (~20-25 lines) on the existing
`OrgEventsExporter` (or comparable) class, one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one README menu-table row, one
CHANGELOG entry. No new external dependencies.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Verdict | Justification |
|---|-----------|---------|---------------|
| I | Five-Item Rule (Structural Discipline) | PASS | The new method is a single ~22-line implementation: prompt collection, SDK call, normalization, export, summary log. Well within <=25 lines, <=5 params, <=5 blocks. |
| II | Class-Based Architecture (No Wrappers) | PASS | The new method attaches to the existing org-events exporter class. No standalone wrapper function is added. If no suitable class exists at integration time, the menu is added to `OrgExportManager` (the established host for org-scoped GET endpoints). |
| III | Multi-Backend Output Discipline | PASS | All persistence flows through `DataExporter.write_with_format_selection(data, filename, api_function_name="countOrgSystemEvents")`. CSV, SQLite, and ArangoDB+Redis backends are exercised by the same call site. |
| IV | Safety-First Input | PASS | Every prompt uses `safe_input(prompt, context="count_org_system_events")` so EOF and disconnected SSH sessions exit 0 cleanly. The operation is read-only, so no destructive confirmation prompt is required. |
| V | Observability & Logging | PASS | ASCII-only `logging.info()` before the SDK call (with org_id, distinct, start, end, duration) and `logging.debug()` after with row counts and elapsed time. Rate-limit and retry paths reuse existing adapters which emit their own logs. |
| VI | Inline Comments (NON-NEGOTIABLE) | PASS | Every executable line in the new method receives a same-line `# ...` comment explaining the why. The `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry and the menu registration line are also commented. |
| VII | Action Logging (NON-NEGOTIABLE) | PASS | A `logging.info()` precedes the API call (intent + parameters) and a `logging.debug()` follows it (result count + duration). The export call also wraps its action in info/debug pair per existing convention. |

**Pre-Phase 0 Gate Verdict**: **PASS** -- all seven principles satisfied
without exception. No entries required in the Complexity Tracking table.

## Project Structure

### Documentation (this feature)

```text
specs/530-mist-count-org-system-events/
├── spec.md                              # Feature specification (already present)
├── plan.md                              # This file (Phase 0/1 output)
├── research.md                          # Phase 0 research
├── data-model.md                        # Phase 1 entity & state model
├── quickstart.md                        # Phase 1 dev quickstart
└── contracts/
    └── count_org_system_events.md       # Phase 1 HTTP/SDK contract
```

### Source Code (repository root)

```text
MistHelper.worktrees/copilot-openapi-mist-api-endpoint-cataloging/
├── MistHelper.py                        # ~28K-line monolith -- add new menu method
│                                        # (target class: OrgEventsExporter, fallback OrgExportManager)
│                                        # Sections touched:
│                                        #   - ENDPOINT_PRIMARY_KEY_STRATEGIES dict (~line 1672)
│                                        #   - Class definition: new method
│                                        #       count_org_system_events(self) -> None
│                                        #   - Menu registry: new entry "195 -> count_org_system_events"
├── README.md                            # Update menu table to list operation 195
├── CHANGELOG.md                         # Add "version YY.MM.DD.HH.MM" entry
├── data/                                # Runtime outputs (gitignored)
│   ├── mist_data.db                     # SQLite, new table count_org_system_events
│   └── count_org_system_events.csv      # CSV when that backend is selected
└── documentation/api/orgs/
    └── GET_orgs_org_id_events_system_count.md  # Enriched OpenAPI doc (reference only)
```

**Structure Decision**: Extend the existing monolith. The endpoint is a
single safe GET that fits the established org-events exporter pattern.
The new method lives on `OrgEventsExporter` if present (the class that
already hosts adjacent system-event search menus); otherwise it joins
`OrgExportManager` to preserve the no-wrapper rule from Principle II.
No new module is created -- a separate file for one ~22-line method
would violate the 5-Item Rule's preference for keeping closely related
behavior co-located, and would not meet the project's class-based
architecture convention.

## Post-Phase 1 Re-Check

After completing Phase 1 (data-model, quickstart, contracts), the
implementation footprint is confirmed minimal and the seven-principle
check still holds:

| # | Principle | Verdict | Notes |
|---|-----------|---------|-------|
| I | Five-Item Rule | PASS | Method projected at ~22 lines / 4 blocks / 1 param (`self`). |
| II | Class-Based Architecture | PASS | Method attaches to an existing class -- no new wrapper or top-level function. |
| III | Multi-Backend Output | PASS | `DataExporter.write_with_format_selection` is the sole persistence call. |
| IV | Safety-First Input | PASS | All three optional prompts (`distinct`, time range, limit) use `safe_input()`. |
| V | Observability & Logging | PASS | info-before, debug-after, ASCII only. |
| VI | Inline Comments | PASS | Verified in pseudocode in `quickstart.md` and the contract. |
| VII | Action Logging | PASS | Pair around the SDK call and the export call. |

**Post-Phase 1 Gate Verdict**: **PASS** -- no design drift detected, no
new violations introduced. Implementation may proceed to `/speckit.tasks`.

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| (none)    | (none)     | (none)                               |

No violations -- table intentionally empty.
