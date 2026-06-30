# Implementation Plan: CountOrgDeviceEvents Menu Item

**Branch**: `512-mist-count-org-device-events` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/512-mist-count-org-device-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/devices/events/count` (operationId `countOrgDeviceEvents`)
to retrieve a per-distinct-attribute count summary of org-wide device events. The menu
item prompts the user for `org_id`, an optional `distinct` grouping key (defaults to
`type`), and an optional time window (`start`/`end`/`duration`) via `safe_input()`,
invokes the `mistapi` SDK once, flattens the response into one summary row plus N
detail rows (one per element of the `results[]` array), and persists everything through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **195** -- the next sequential slot above the
current destructive cluster ceiling (154-194). If implementation collides with another
in-flight feature branch claiming 195, the next free integer is used; the spec
operation cluster (events at 20-26 and stats at 80-91) is also acceptable if a free
slot opens before task generation.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB +
Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using `MIST_ORG_ID` from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. Heavy /
destructive skip list (14, 18, 63-65, 90-100) is unaffected -- a new item at 195 sits
outside the default safe-test sweep range and will be invoked explicitly in
`--menu 195` smoke runs.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical event
windows; the endpoint returns a count summary (not raw events) so the response is small
(<=`limit` rows in `results[]`, default 100). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; this endpoint is
light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~24 lines) on the existing
`DeviceEventsExportUtils` class (the same class that owns `searchOrgDeviceEvents` used by
menus 13, 15, 83 per the enriched per-endpoint doc), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new CSV/SQLite tables
(`org_device_events_count_summary` and `org_device_events_count_results`), one menu
registration entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories. If `DeviceEventsExportUtils` does not
exist yet, a new class of that name is created -- justified because the count and search
endpoints share input semantics and a shared owner reduces duplication.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_device_events_count()` stays under
  25 lines, takes <=4 parameters (`self`, `org_id`, `distinct`, `time_window`), and
  contains <=5 logical blocks (prompt -> validate -> API call -> flatten summary + flatten
  results -> DataExporter call). Hierarchy is unchanged: one new method on an existing (or
  newly extracted) class. No new packages, modules, or top-level constants are introduced.
  The two output flatteners are inlined as single comprehensions; if either grows past
  five lines during implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `DeviceEventsExportUtils` class (or a new class of that name if no current owner
  exists). No standalone wrapper function is introduced. The menu dispatch in the main
  loop references the class method directly. Variable names use full words
  (`distinct_field`, `event_count_row`, `results_array`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_device_events_count:org_id"`,
  `"org_device_events_count:distinct"`, `"org_device_events_count:duration"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. Org ID is
  validated against the Mist UUID shape before the API call; on validation failure the
  method logs a warning and returns early. The `distinct` value is validated against an
  allow-list of known distinct keys from the OpenAPI doc (model, type, ap, apfw, site_id,
  text, timestamp) to prevent malformed query strings. API token comes from `.env` via the
  existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 195 CountOrgDeviceEvents` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch`
  -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Counting device events for org %s distinct=%s
  duration=%s"); `DEBUG` after the call with summary counts ("Count response: total=%d
  results_rows=%d window=%d-%d"); `WARNING` on 404 / empty `results[]`; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets, tokens, or
  full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing device-events export cluster on
  `DeviceEventsExportUtils`) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with the result count,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write, `logging.debug(...)` after write. The DataExporter
  call already emits its own per-backend log lines; the new method does not duplicate
  them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/512-mist-count-org-device-events/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_device_events.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on DeviceEventsExportUtils class + PK strategy +
                         # menu 195 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 195
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 195
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `DeviceEventsExportUtils` class in `MistHelper.py` (the class that
owns `searchOrgDeviceEvents`, per the enriched per-endpoint doc note that the search
operation backs menus 13, 15, and 83). If that class does not currently exist as a named
unit, it is extracted to own both the search and the new count operations. The menu
number proposal is **195**, the next free integer above the destructive ceiling at 194.
The full menu list is re-verified at task generation time; if 195 collides with an
in-flight feature branch claim, the next free integer is used (candidate fallbacks: a
free slot in the events cluster at 20-26 or the stats cluster at 80-91).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `DeviceEventsExportUtils`.
  No wrappers introduced. Flattening helpers, if needed, are added as private methods on
  the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation and `distinct` allow-list happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
