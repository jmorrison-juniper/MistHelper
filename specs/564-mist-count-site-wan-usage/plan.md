# Implementation Plan: countSiteWanUsage Menu Item

**Branch**: `564-mist-count-site-wan-usage` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/564-mist-count-site-wan-usage/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/wan_usages/count` (operationId `countSiteWanUsage`) to
return the distinct-value count of WAN usage records observed at a site over a chosen
time window. The menu prompts the user via `safe_input()` for a `site_id`, the field to
group by (`distinct`), and a duration string; invokes the `mistapi` SDK; flattens the
count envelope (`distinct`, `start`, `end`, `limit`, `total`) plus the `results[]` array
into row dicts; and persists results through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly into SQLite without
duplicates. The operation is proposed as menu number **91** -- the next available slot
inside the interactive-safe Stats cluster (80-91), adjacent to the existing site-level
count and stat operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the only
permitted interface to the Mist Cloud); `requests` (transport, transitive);
`python-dotenv` for `.env` bootstrap of `MIST_HOST`, `MIST_API_TOKEN`, and the optional
`MIST_SITE_ID` default.
**Storage**: Multi-backend through `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land under `data/`; the
polyglot ArangoDB + Redis backend handles graph + cache writes.
**Testing**: `python MistHelper.py --test` exercises the new menu item against the
default site loaded from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, and `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) leaves menu
91 inside the standard automated sweep.
**Target Platform**: Windows 11 + venv for local development; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and SSH-on-2200. Both
targets must run without code change.
**Project Type**: CLI tool. A single-file Python monolith (`MistHelper.py`, ~28K lines)
with an optional Gunicorn web UI on 8055. This feature lives entirely inside the CLI.
**Performance Goals**: A single GET request completes in <=5 seconds for the default
1-day duration window. The endpoint supports server-side `limit` paging (default 100)
but is not stream-paginated like search endpoints; one call returns the full count
envelope. Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json`
continue to govern back-off without endpoint-specific tuning.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; the API token is
loaded from `.env` and never logged; all output land under `data/`; Windows-safe path
joining (`os.path.join` / `pathlib.Path`). The 5-Item Rule limits the new method to
<=25 lines, <=5 parameters, and <=5 logical blocks.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SiteStatsExportUtils` class (the same class hosting other site-scoped count and stat
exports), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
(`site_wan_usage_counts`), one menu registration entry, one README operation-count
bump, and one CHANGELOG line. No new dependencies, modules, or directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_site_wan_usage_counts()` stays under
  25 lines, takes <=4 parameters (`self`, `site_id`, `distinct_field`, `duration`),
  and contains <=5 logical blocks (prompt -> validate -> API call -> flatten ->
  DataExporter call). Hierarchy is unchanged: a single new method on an existing class.
  No new packages, modules, or top-level constants are introduced. The flatten helper
  is inlined as a single comprehension; if it grows past 5 lines during implementation,
  it is extracted to a private method on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `SiteStatsExportUtils` class (the class that owns the other site-scoped count and
  stat exports). No standalone wrapper function is introduced. The menu dispatch in the
  main loop references the class method directly. Variable names use full words
  (`distinct_field`, `result_rows`) -- no single-letter iterators are introduced.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"site_wan_usage_count:site_id"`,
  `"site_wan_usage_count:distinct"`, `"site_wan_usage_count:duration"`) so SSH and
  container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. The
  `site_id` is validated against the Mist UUID shape via `is_valid_uuid()` before the
  API call; on validation failure the method logs a warning and returns early. The API
  token is loaded from `.env` via `mistapi.APISession` and is never written to logs.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black
  --check` -> commit with `version YY.MM.DD.HH.MM - add menu 91 countSiteWanUsage` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove
  / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call (`"Fetching WAN usage count for site %s distinct=%s
  duration=%s"`); `DEBUG` after the call with summary counts (`"WAN usage count:
  total=%d results=%d"`); `WARNING` on 404 or empty payload; `ERROR` on unexpected
  exception with full traceback via `logging.exception`. No secrets, tokens, or full
  request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line carries an
  inline comment that explains *why* the line exists, not merely what it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched block (the existing site-stats menu
  cluster) receive comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with a row-count summary, `logging.info(...)` before flatten, `logging.debug(...)`
  after flatten, `logging.info(...)` before write, and `logging.debug(...)` after
  write. The DataExporter call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/564-mist-count-site-wan-usage/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_wan_usage.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SiteStatsExportUtils + PK strategy + menu 91
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 91
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 91 addition
data/                    # Runtime output target (existing dir). No schema migration is
                         # needed beyond the new SQLite table created on first write by
                         # DataExporter.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `SiteStatsExportUtils` class in `MistHelper.py` (the
same class that owns adjacent site count and stat exports). The menu number proposal
is **91**, chosen because operations 80-91 are the interactive-safe Stats sub-cluster
and 91 is the next available integer below the resource-intensive block at 97-101.
The final number is re-verified at task generation time; if 91 collides with an
in-flight feature branch, the next free integer inside the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions are required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` insert is a single dict entry (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `SiteStatsExportUtils`.
  No wrapper functions introduced. Any flattening helper, if needed, is added as a
  private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or request URL.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy entry
  and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
