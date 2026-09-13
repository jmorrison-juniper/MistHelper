# Implementation Plan: countSiteAlarms Menu Item

**Branch**: `541-mist-count-site-alarms` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/541-mist-count-site-alarms/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/alarms/count` (operationId `countSiteAlarms`) to retrieve
distinct-attribute counts of alarms scoped to a single site. The menu item prompts the
user for `site_id` and an optional `distinct` grouping field via `safe_input()`, allows
optional time-range, severity, type, group, and acked filters (all defaulted), invokes
the `mistapi.api.v1.sites.alarms.count.countSiteAlarms()` SDK call, flattens the response
into a summary row (`distinct`, `start`, `end`, `limit`, `total`) plus one row per item
in the `results` array, and persists every row through
`DataExporter.write_with_format_selection()` so the CSV, SQLite, and ArangoDB+Redis
backends all stay in sync. A new entry is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
so repeated runs upsert cleanly into SQLite. The new operation is proposed as menu number
**97** -- the next available slot in the safe-site stats cluster (80-91 -> 92-96 viewers
-> 97 next free); final number is reverified at `/speckit.tasks` time against any
in-flight feature branches.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the only
permitted interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv`
for loading `MIST_HOST` and `MIST_API_TOKEN` from `.env`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land under `data/`; the polyglot
ArangoDB + Redis containers handle graph + cache when configured.
**Testing**: `python MistHelper.py --test` exercises the new menu item in non-interactive
mode using a known site_id from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The skip list (14, 18, 63-65, 90-100) is unaffected because the proposed
menu number 97 sits just above the destructive 90-100 range; if 97 is reassigned to a
different cluster at task time, the test sweep skip list is reviewed in the same edit.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET completes in <=5 seconds for the default 1d window;
the endpoint is not deeply paginated (returns count buckets, not raw alarm records), so
no special back-off is required. Existing `delay_metrics.json` and `tuning_data.json`
adaptive controls continue to apply unchanged.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; API token never
logged; all output stays under `data/`; Windows-safe path joining via `os.path.join` /
`pathlib.Path`. The endpoint is strictly GET, so no destructive-confirmation gate is
required.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SiteAlarmsManager`-style class (the AlarmsExportUtils cluster that owns
`searchOrgAlarms` at menu 56). One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. Two
new tables in SQLite (`site_alarms_count_summary`, `site_alarms_count_buckets`). One
menu registration entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_site_alarms_count()` stays under 25
  lines, takes <=4 parameters (`self`, `site_id`, `distinct`, `time_filters`), and uses
  <=5 logical blocks (prompt -> filter assembly -> SDK call -> flatten -> DataExporter).
  No new packages or modules; one new method on an existing class. The flatten step is
  one comprehension; if it grows past 5 lines during implementation it is extracted to a
  private helper on the same class. The PK strategy registration is a single dict insert
  -- no new top-level constant tier.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The behavior is added as a method on the existing alarms-export
  class that already owns menu 56 (`searchOrgAlarms`). No standalone wrapper function is
  introduced. The menu dispatch references the class method directly. Variable names use
  full words (`alarm_count_row`, `bucket_record`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"site_alarms_count:site_id"`, `"site_alarms_count:distinct"`,
  `"site_alarms_count:duration"`) so SSH or container EOF exits 0 cleanly with no
  traceback. The endpoint is read-only HTTP GET, so no typed destructive-confirmation
  gate is required. `site_id` is validated against the Mist UUID shape before the SDK
  call; on validation failure the method logs a warning and returns early. API token is
  loaded from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 97 countSiteAlarms` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / rm / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- Log calls use ASCII text and `%s`-style formatting. `INFO` is
  emitted before the API call ("Fetching alarm counts for site %s distinct=%s"); `DEBUG`
  after the call with the bucket count ("Alarm count buckets=%d total=%d"); `WARNING`
  on 404 or empty payload; `ERROR` with `logging.exception` on unexpected exception.
  No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line carries an
  inline comment explaining *why*, not just *what*. Blank lines, closing parentheses,
  and decorators are exempt per the constitution. Any uncommented adjacent lines in the
  touched alarms-export block get inline comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with result counts,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten with row
  counts, `logging.info(...)` before write, and the existing `DataExporter` emits its
  own per-backend log lines (not duplicated by this method).

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/541-mist-count-site-alarms/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_alarms.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the alarms-export class + PK strategy +
                         # menu 97 registration. No new modules; same monolith.
README.md                # Operation count bump + new row in the menu table for op 97
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry for menu 97 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # beyond the two new SQLite tables created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing alarms-export class in `MistHelper.py` (the class that owns the
`searchOrgAlarms` menu 56 path). If that class is currently named
`AlarmsExportUtils` it is reused; if a clearly named class does not yet exist for the
alarms cluster, a `SiteAlarmsManager` class is introduced at the same indent level as
the other `*Manager` classes (`WebSocketManager`, `PacketCaptureManager`, etc.) and the
existing `searchOrgAlarms` method is left in place under its current owner (no
cross-class moves in this PR). The menu number proposal is **97**, the next free slot
above the destructive 90-100 cluster. The final number is reverified at
`/speckit.tasks` time against in-flight 5xx feature branches; if 97 collides with an
already-merged operation, the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert, so no level-5
  hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on a single existing or
  newly-introduced manager class. No wrappers introduced. Helpers, if needed, are
  added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The quickstart shows the expected comment
  density on every executable line, including the PK strategy entry and the menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- The quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
