# Implementation Plan: countSiteSkyatpEvents Menu Item

**Branch**: `559-mist-count-site-skyatp-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/559-mist-count-site-skyatp-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/skyatp/events/count` (operationId `countSiteSkyatpEvents`)
to return aggregated counts of Sky ATP (Advanced Threat Prevention) events at a single
site, grouped by a caller-chosen `distinct` attribute (e.g. `type`, `threat_level`,
`mac`, `device_mac`, `ip`). The new method lives on the existing `SiteAnomalyExporter`
class -- the same class that owns adjacent site-level threat / anomaly exporters --
prompts for `site_id` and the optional `distinct` / time-window parameters via
`safe_input()`, calls `mistapi.api.v1.sites.skyatp.events.count.countSiteSkyatpEvents()`
exactly once, flattens the `results[]` bucket array into one row per bucket (each row
carrying the parent query envelope: `distinct`, `start`, `end`, `limit`, `total`), and
persists the output through `DataExporter.write_with_format_selection()` so the CSV,
SQLite, and ArangoDB+Redis backends all receive consistent data. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (alongside the existing
`searchSiteSkyatpEvents` entry) so SQLite upserts cleanly on repeated runs. The new
operation is proposed as menu number **195** -- the next free integer above the current
194-operation catalogue, sitting in the safe-read site-security cluster. The final
number is re-verified at task-generation time and bumped if a sibling feature branch
lands first.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`. No new dependencies introduced.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend. New table on first run:
`site_skyatp_events_count`.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known `MIST_SITE_ID` from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy/destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- menu 195 sits outside it. If 195 lands inside
a future destructive cluster, the test runner skip list is updated in the same PR.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a `1d` default
window. The endpoint is bounded by `limit` (default 100, capped server-side) so the
response is small; no client-side pagination loop is required. Adaptive delay metrics
in `delay_metrics.json` and `tuning_data.json` continue to govern back-off.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; API token never
logged; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); no Unicode/emoji in code, comments, log lines, or commit messages.
**Scale/Scope**: One new public method (~22 lines) on the existing `SiteAnomalyExporter`
class; one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`; one new CSV/SQLite table
(`site_skyatp_events_count`); one menu registration entry; one README operation-count
bump (194 -> 195) plus new row in the menu table; one CHANGELOG line. No new modules,
no new top-level constants, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_site_skyatp_events_count()` stays
  under 25 lines, takes <=4 parameters (`self`, `site_id`, `distinct`, `time_window`),
  and contains <=5 logical blocks (validate inputs -> build kwargs -> API call ->
  flatten bucket rows -> DataExporter call). Hierarchy is unchanged: one new method on
  an existing class. No new packages, modules, or top-level constants. If the flatten
  block exceeds 5 lines during implementation, it is extracted to a private helper
  `_flatten_skyatp_count_buckets()` on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behaviour is added as a method on the existing
  `SiteAnomalyExporter` class. No standalone wrapper function is introduced. The menu
  dispatcher in the main loop references the class method directly. Variable names use
  full words (`bucket_row`, `event_count`, `threat_level`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"site_skyatp_count:site_id"`, `"site_skyatp_count:distinct"`,
  `"site_skyatp_count:window"`) so SSH / container EOF exits cleanly with code 0 and
  no traceback. The endpoint is strictly read-only (HTTP GET), so no typed destructive-
  confirmation gate is required. `site_id` is validated against the Mist UUID shape
  via `ValidationUtils` before the API call; on validation failure the method logs a
  warning and returns early. The API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 195 countSiteSkyatpEvents`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Fetching Sky ATP event counts for site %s
  distinct=%s window=%s"); `DEBUG` after the call with the bucket count
  ("Received %d count buckets total=%d"); `WARNING` on 404 / empty `results`; `ERROR`
  on unexpected exception via `logging.exception`. No secrets, tokens, or full request
  URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line will carry
  an inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the constitution.
  Any uncommented adjacent lines in the touched block (the existing site-anomaly /
  site-security exporter cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with `len(results)` and `total`, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten with row count, `logging.info(...)` before
  DataExporter call, `logging.debug(...)` after with filename. The DataExporter call
  itself emits per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/559-mist-count-site-skyatp-events/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── count_site_skyatp_events.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SiteAnomalyExporter class + PK strategy + menu 195
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump (194 -> 195) + new row in the menu table
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 195 addition
data/                    # Runtime output target (existing dir). New SQLite table
                         # `site_skyatp_events_count` is auto-created on first run by
                         # DataExporter using the new ENDPOINT_PRIMARY_KEY_STRATEGIES entry.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `SiteAnomalyExporter` class in `MistHelper.py` -- the
same class that owns adjacent site-level threat and anomaly exporters. The menu number
proposal is **195**, chosen because the current catalogue ends at 194 (per
`.github/copilot-instructions.md`) and Sky ATP belongs to the safe-read site-security
cluster, not the destructive 154-194 block. The full menu list is re-verified at task-
generation time; if 195 collides with another in-flight feature branch, the next free
integer is used and `README.md` is updated accordingly.

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry is a single insert against an
  existing structure, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `SiteAnomalyExporter`. No
  wrappers introduced. The optional flatten helper, if added, is a private method on
  the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call.
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
