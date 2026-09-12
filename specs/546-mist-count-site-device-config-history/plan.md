# Implementation Plan: countSiteDeviceConfigHistory Menu Item

**Branch**: `546-mist-count-site-device-config-history` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/546-mist-count-site-device-config-history/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/devices/config_history/count` (operationId
`countSiteDeviceConfigHistory`) to retrieve aggregated counts of device
configuration history entries grouped by a caller-selected distinct field (e.g.
`mac`). The menu item prompts the user for a `site_id` and an optional set of
filters (`distinct`, `mac`, `start`, `end`, `duration`, `limit`) via
`safe_input()`, invokes the `mistapi` SDK, flattens the response into one
summary row plus one row per `results[]` entry, and persists output through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent data. Two new entries are registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly under SQLite.
The new operation is proposed as menu number **73** -- the next available slot
at the top of the Insights cluster (73-79), adjacent to the existing site
devices cluster (60-72) where this count belongs operationally.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and the
optional `MIST_SITE_ID` default.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
Local fallback is SQLite at `data/mist_data.db`; CSV files land in `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend when
configured.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known site from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- proposed menu number 73 sits inside the default
test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
`ghcr.io/jmorrison-juniper/misthelper:latest` for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines)
with optional Gunicorn web UI on port 8055. This feature is CLI-only.
**Performance Goals**: Single GET request completes in <=5 seconds. The
endpoint returns a small aggregation payload (one summary object + a results
array bounded by the `limit` query parameter, default 100). Adaptive delay
metrics in `delay_metrics.json` and `tuning_data.json` continue to govern
back-off; no special tuning required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); 5-Item Rule applies to the new method
(<=25 lines, <=5 parameters, <=5 nesting blocks).
**Scale/Scope**: One new public menu method (~25 lines) on the existing
`DeviceConfigHistoryExportUtils` class (or, if that class does not yet exist
in `MistHelper.py`, on the `SiteDevicesExportUtils` class that owns adjacent
operations 60-72). Two new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. Two
new CSV/SQLite tables (`site_device_config_history_count_summary` and
`site_device_config_history_count_results`). One menu registration entry. One
README operation-count bump. One CHANGELOG line. No new dependencies, no new
modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_site_device_config_history_count()` stays under 25 lines, takes <=5
  parameters (`self`, `site_id`, `distinct`, `time_window`, `limit`), and
  contains <=5 logical blocks (prompt -> API call -> flatten summary ->
  flatten results -> DataExporter call). Hierarchy is unchanged: one new
  method on an existing class. Two flatten helpers are added as private
  methods on the same class if they would exceed 5 lines inline. No new
  packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on an existing
  class that owns adjacent site-device operations (the same class that holds
  the related `listSiteDevices` / `searchSiteDeviceConfigHistory` exports).
  No standalone wrapper function is introduced. The menu dispatch references
  the class method directly. Variable names use full words
  (`distinct_field`, `count_summary_row`, `count_result_row`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (e.g.
  `"site_device_config_history_count:site_id"`,
  `"site_device_config_history_count:distinct"`) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET) and returns aggregated counts only -- no destructive
  confirmation gate is required. `site_id` is validated against the Mist
  UUID shape via the existing `is_valid_uuid()` helper before the API call;
  on validation failure the method logs a `WARNING` and returns early. The
  API token comes from `.env` via the existing `mistapi.APISession` and is
  never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` ->
  `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 73 countSiteDeviceConfigHistory` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style
  formatting. `INFO` is emitted before the API call ("Counting device config
  history entries for site %s distinct=%s"); `DEBUG` after the call with
  summary counts ("Count results: total=%d returned=%d"); `WARNING` on 404
  or empty payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the two new
  PK strategy dictionary entries, and the menu registration line will carry
  an inline comment explaining *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing site-devices menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with result counts, `logging.info(...)` before
  each flatten step, `logging.debug(...)` after each flatten step with row
  counts, `logging.info(...)` before each DataExporter write,
  `logging.debug(...)` after each write. The DataExporter call already emits
  its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/546-mist-count-site-device-config-history/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── count_site_device_config_history.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the site-devices export class + two
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entries + menu 73
                         # registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table
                         # for op 73
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing the
                         # menu 73 addition
data/                    # Runtime output target (existing dir; no schema
                         # migration needed beyond the two new SQLite tables
                         # created on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing site-devices export class (the class that
already owns operations 60-72). The menu number proposal is **73**, chosen
because the cluster boundaries documented in `.github/copilot-instructions.md`
are 60-72 Site Devices, 73-79 Insights, 80-91 Stats, 92-96 Viewers. A
config-history *count* is operationally an insight (aggregated analytics over
device history), so position 73 -- the top of the Insights cluster, adjacent
to the site-devices cluster -- is the most discoverable slot for a NOC
engineer. The number is provisional: at `/speckit.tasks` time, `MistHelper.py`
is grep'd for the latest allocated menu integer and 73 is shifted forward if
a conflict exists.

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
  The two `ENDPOINT_PRIMARY_KEY_STRATEGIES` additions are single inserts in
  the existing dict literal, no structural change.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing
  site-devices export class. No wrappers introduced. Flatten helpers are
  private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path for every user value. UUID validation happens
  before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the two new
  PK strategy entries and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten summary, flatten results, summary write, results write).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
