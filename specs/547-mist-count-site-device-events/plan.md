# Implementation Plan: countSiteDeviceEvents Menu Item

**Branch**: `547-mist-count-site-device-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/547-mist-count-site-device-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/devices/events/count` (operationId
`countSiteDeviceEvents`) to return a count of device-event-history rows at a
site, grouped by a caller-chosen `distinct` field (for example `model`,
`type`, or `device_id`). The menu prompts the NOC engineer for a `site_id`
via `safe_input()`, then for optional filters (`distinct`, `model`, `type`,
`type_code`, `start`, `end`, `duration`, `limit`), invokes the `mistapi`
SDK, flattens the aggregate envelope (`distinct`, `start`, `end`, `limit`,
`total`, plus the `results[]` array of `count_result` rows) into one row per
distinct-value bucket, and persists the flattened rows through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB +
Redis backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs.
The new operation is proposed as menu number **89** -- the next available
slot in the Stats / Site-level cluster (80-91), adjacent to the existing
site-device statistics operations and below the Viewers cluster at 92-96.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK --
the sole permitted interface to Mist Cloud); `requests` (transport,
transitive); `python-dotenv` (for `.env` loading of `MIST_HOST` and
`MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache
backend.
**Testing**: `python MistHelper.py --test` exercises the new menu item in
non-interactive mode using a known `site_id` from `.env`. Local quality
gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item **89** sits inside the
default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the
CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a
typical site whose distinct cardinality is well below the default `limit=100`.
Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json`
continue to govern back-off; this aggregate endpoint is light enough that
no special tuning is required. Worst case (full one-day window across a
high-event-volume site, `distinct=device_id`) is still well below the 5
second target since the Mist Cloud computes the aggregation server side.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); `--fast` mode honored (concurrency cap +
retry cap unchanged for a single endpoint call).
**Scale/Scope**: One new public menu method (~20 lines) on the existing
site-device statistics export class, one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV / SQLite table
(`site_device_events_count`), one menu registration entry, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new
modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_site_device_events_count()` stays under 25 lines, takes <=5
  parameters (`self`, `site_id`, `distinct`, `time_window`, `extra_filters`)
  and contains <=5 logical blocks (prompt -> filter assembly -> API call ->
  flatten -> DataExporter call). Hierarchy is unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are
  introduced. The flatten step is one comprehension; if it grows past 5
  lines during implementation it is extracted to a private helper on the
  same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  site-device statistics export class in `MistHelper.py` (the same class
  that owns adjacent site-device search and statistics exports). No
  standalone wrapper function is introduced. The menu dispatch in the main
  loop references the class method directly. Variable names use full words
  (`distinct_field`, `count_row`, `time_window_args`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()`
  with explicit `context=` strings
  (`"site_device_events_count:site_id"`,
  `"site_device_events_count:distinct"`,
  `"site_device_events_count:time_window"`,
  `"site_device_events_count:filters"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate is required. Site
  ID is validated against the Mist UUID shape before the API call; on
  validation failure the method logs a warning and returns early. API token
  comes from `.env` via the existing `mistapi.APISession` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `ruff check` -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 89 countSiteDeviceEvents` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs
  -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style
  formatting. `INFO` is emitted before the API call ("Counting site %s
  device events grouped by %s"); `DEBUG` after the call with summary counts
  ("Count response: total=%d buckets=%d window_start=%d window_end=%d");
  `WARNING` on 404 / 400 / empty payload; `ERROR` on unexpected exception
  with full traceback via `logging.exception`. No secrets, tokens, or full
  request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing site-device statistics export cluster) get comments added in the
  same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a result count, `logging.info(...)`
  before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write, `logging.debug(...)` after write. The
  `DataExporter` call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in
the Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/547-mist-count-site-device-events/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_device_events.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the site-device statistics export class
                         # + new PK strategy + menu 89 registration. No new modules;
                         # same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 89
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 89 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as
a new public method on the existing site-device statistics export class in
`MistHelper.py` (the same class that owns adjacent site-device search and
statistics operations). If no such class exists in the current source under
that name, the new method is attached instead to the closest semantic
neighbor (the class that already owns `searchSiteDeviceEvents` or the
site-device statistics exports). A new wrapper class is NOT created, per
Principle II. The menu number proposal is **89**, chosen because operations
80-91 are the Stats cluster and 89 is the next available integer below the
Viewers cluster at 92-96. The full menu list is re-verified at task
generation time; if 89 collides with an in-flight feature branch, the next
free integer in the same cluster (80-91) is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/count_site_device_events.md`), the seven
principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on an existing
  site-device statistics export class. No wrappers introduced. Flattening
  helpers, if needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design
  are ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
