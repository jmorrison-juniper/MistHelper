# Implementation Plan: countOrgSwOrGwPorts Menu Item

**Branch**: `529-mist-count-org-sw-or-gw-ports` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/529-mist-count-org-sw-or-gw-ports/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/stats/ports/count` (operationId `countOrgSwOrGwPorts`) to
return aggregated counts of switch and gateway ports at the organization level grouped
by a distinct attribute (port_id, mac, neighbor_system_name, speed, stp_state, etc.).
The menu item prompts the user for `org_id` via `safe_input()` (defaulting to the
`MIST_ORG_ID` value loaded from `.env` when present), prompts for the `distinct` group
field, optionally collects a small subset of high-value filter parameters (`site_id`,
`up`, `duration`), invokes the `mistapi` SDK function
`mistapi.api.v1.orgs.stats_ports.countOrgSwOrGwPorts()`, flattens the envelope (top-level
`distinct`, `start`, `end`, `limit`, `total`) plus the `results[]` array into rows, and
persists the result via `DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. A new entry is added to
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts. The new operation is
proposed as menu number **89**, the next available slot in the Stats cluster (80-91)
that already groups the org/site stats endpoints.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST`, `MIST_API_TOKEN`, and optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. Heavy/destructive skip list (14, 18, 63-65, 90-100) is unaffected --
menu 89 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical orgs.
The endpoint is server-side aggregation (count by distinct), so payloads are small (one
row per distinct value, bounded by `limit`, default 100). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; this endpoint
is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); the 30+ optional query parameters are intentionally NOT all exposed --
only the high-value subset (`distinct`, `site_id`, `up`, `duration`, `limit`) is
prompted, with the rest available via a future `--filters` JSON pass-through if needed.
**Scale/Scope**: One new public menu method (~24 lines) on the existing
`OrgStatsExportUtils` class (the same class that already owns the org_stats_* menu
exports), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
(`org_stats_ports_count`), one menu registration entry, one README operation-count
bump, one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_sw_or_gw_ports_count()` stays
  under 25 lines, takes <=4 parameters (`self`, `org_id`, `distinct_field`,
  `extra_filters`), and contains <=5 logical blocks (prompt -> validate -> API call ->
  flatten -> DataExporter call). Hierarchy is unchanged: one new method on an existing
  class. No new packages, modules, or top-level constants are introduced. The flatten
  step is a single list-comprehension block; if it grows past 5 lines during
  implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgStatsExportUtils` class (the same class that owns the adjacent org_stats_* menu
  items including the related `searchOrgSwOrGwPorts` exporter when present). No
  standalone wrapper function is introduced. The menu dispatch in the main loop
  references the class method directly. Variable names use full words
  (`distinct_field`, `count_row`, `result_payload`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_ports_count:org_id"`, `"org_ports_count:distinct"`,
  `"org_ports_count:site_id"`, `"org_ports_count:duration"`) so SSH / container EOF
  exits cleanly with code 0 and no traceback. The endpoint is strictly read-only (HTTP
  GET), so no typed destructive-confirmation gate is required. Org ID is validated
  against the Mist UUID shape before the API call; the `distinct` value is checked
  against a closed allow-list derived from the OpenAPI parameter set; on validation
  failure the method logs a warning and returns early. API token comes from `.env` via
  the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit with `version
  YY.MM.DD.HH.MM - add menu 89 countOrgSwOrGwPorts` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run container ->
  `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style formatting. `INFO` is
  emitted before the API call ("Counting org ports for org %s by distinct=%s");
  `DEBUG` after the call with summary counts ("Count response: total=%d results=%d
  start=%s end=%s"); `WARNING` on 404 / empty results; `ERROR` on unexpected exception
  with full traceback via `logging.exception`. No secrets, tokens, or full request URLs
  are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched block (the existing org-stats menu cluster)
  get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a result count,
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
specs/529-mist-count-org-sw-or-gw-ports/
+-- plan.md              # This file
+-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
+-- data-model.md        # Phase 1 - response entities + DDL + PK registration
+-- quickstart.md        # Phase 1 - local run + .env + quality gates
+-- contracts/
|   +-- count_org_sw_or_gw_ports.md   # Phase 1 - HTTP + SDK contract
+-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgStatsExportUtils class + PK strategy entry
                         # + menu 89 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 89
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 89
                         # addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `OrgStatsExportUtils` class in `MistHelper.py` (the same
class that owns the adjacent org-stats exports). The menu number proposal is **89**,
chosen because operations 80-91 are the Stats cluster and 89 is a free slot below the
final slot 91; the count-by-distinct semantics fit naturally beside the existing
org_stats menu items. The full menu list will be re-verified at task-generation time;
if 89 collides with an in-flight feature branch, the next free integer in the same
cluster (90 is reserved as the start of the destructive range, so the picker walks
*down* from 89 to the next free slot, never up).

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgStatsExportUtils`. No
  wrappers introduced. Flattening helper, if needed, is added as a private method on
  the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation and `distinct` allow-list validation happen before the SDK
  call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
