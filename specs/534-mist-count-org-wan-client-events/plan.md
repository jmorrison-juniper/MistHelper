# Implementation Plan: countOrgWanClientEvents Menu Item

**Branch**: `534-mist-count-org-wan-client-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/534-mist-count-org-wan-client-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/wan_client/events/count` (operationId
`countOrgWanClientEvents`) to retrieve aggregated counts of WAN client events
grouped by a distinct attribute (event type, MAC, gateway, etc.) over a
user-supplied time window. The menu item prompts the user for `org_id`,
`distinct`, optional `type`, and a time range (`start`/`end` or `duration`) via
`safe_input()`, invokes the `mistapi` SDK, flattens the summary envelope plus
the `results[]` array into rows, and persists everything through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs.
The new operation is proposed as menu number **195** -- the next sequential
free slot above the existing destructive cluster (154-194), tagged in the safe
org-exports category.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
only permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode against the `.env`-configured org. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The destructive skip list (14, 18,
63-65, 90-100) is unaffected; menu 195 is safe-read-only and stays inside the
default test sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a 1-day
window at default `limit=100`. The endpoint is a server-side aggregation, so
the payload is bounded (one envelope + up to `limit` result rows). Adaptive
delay metrics in `delay_metrics.json` and `tuning_data.json` continue to
govern back-off; no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
WAN-clients export class (confirmed in Phase 0 research), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new SQLite tables
(`org_wan_client_events_count_summary` and
`org_wan_client_events_count_results`), one menu registration line, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new modules,
no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_wan_client_events_count()` stays under 25 lines, takes <=5
  parameters (`self`, `org_id`, `distinct`, `event_type`, `time_window`), and
  contains <=5 logical blocks (collect prompts -> validate inputs -> API call
  -> flatten summary + results -> DataExporter call). Hierarchy is unchanged:
  one new method on an existing class. No new packages, modules, or top-level
  constants are introduced. The results-array flattener is a single
  comprehension; if it grows past 5 lines during implementation it is
  extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  WAN-clients export class (`OrgWanClientExportUtils` is the working name;
  Phase 0 confirms the exact existing class housing the wan_client list /
  search methods). No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable
  names use full words (`distinct_attr`, `event_type_filter`, `time_window`)
  -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings
  (`"wan_client_events_count:org_id"`,
  `"wan_client_events_count:distinct"`,
  `"wan_client_events_count:type"`,
  `"wan_client_events_count:duration"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. `org_id` is validated
  against the Mist UUID shape before the API call; `distinct` is validated
  against the documented allowed values; on validation failure the method
  logs a warning and returns early. API token comes from `.env` via the
  existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 195 countOrgWanClientEvents` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Counting WAN client events for org
  %s distinct=%s"); `DEBUG` after the call with summary counts ("WAN client
  event count: total=%d results=%d window=%s..%s"); `WARNING` on 404 / empty
  payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  surrounding WAN-clients export cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a result count, `logging.info(...)` before
  flatten, `logging.debug(...)` after flatten, `logging.info(...)` before
  write, `logging.debug(...)` after write. The DataExporter call already
  emits its own per-backend log lines; the new method does not duplicate
  them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/534-mist-count-org-wan-client-events/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── count_org_wan_client_events.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgWanClientExportUtils (or chosen
                         # host class confirmed in Phase 0) + PK strategy
                         # entry + menu 195 registration. No new modules;
                         # same single-file monolith.
README.md                # Operation count bump + new row in the menu table
                         # for op 195
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing
                         # menu 195 addition
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the two new SQLite tables
                         # created on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing WAN-clients export class in `MistHelper.py`.
Phase 0 research confirms the exact host class (`OrgWanClientExportUtils` is
the working name; if no such class exists the closest match is the org-clients
export class housing the existing wan_client search / list methods). The menu
number proposal is **195**, chosen because the existing menu space 1-194 is
fully allocated per the AI-Agent Instructions menu map (1-59 Safe Org Exports,
60-96 Interactive Safe, 97-101+153 Resource Intensive, 102-123 WebSocket,
124-150 Interactive, 151-152 Continuous, 154-194 Destructive). Operation 195
is the next free integer; the README menu table is updated to record it under
the Safe Org Exports / Org Clients (WAN) category. If 195 collides with
another in-flight feature branch at task-generation time, the next free
integer is used and the README/CHANGELOG are updated to match.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` insert is a single dictionary entry
  (existing structure), so no level-5 hierarchy explosion. The two-table
  flatten pattern (summary + results) is the same idiom already used by
  `GetOrgLicenseAsyncClaimStatus` (spec 500), so no new structural risk.
- **Principle II (Class-Based)**: PASS -- All work lives on the chosen host
  class. No wrappers introduced. The results-row flattener, if needed beyond
  one comprehension, is added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID validation and distinct-value validation
  happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or full
  request URLs.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompts, validate,
  API call, flatten summary, flatten results, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
