# Implementation Plan: countSiteBgpStats Menu Item

**Branch**: `544-mist-count-site-bgp-stats` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/544-mist-count-site-bgp-stats/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/stats/bgp_peers/count` (operationId `countSiteBgpStats`) to
retrieve the count of BGP peer statistics at a site, grouped by a caller-supplied distinct
attribute (e.g. `state`, `neighbor_as`, `vrf_name`). The menu item prompts the user via
`safe_input()` for `site_id`, an optional BGP `state` filter, an optional `distinct`
grouping field, and an optional row `limit`. It invokes the `mistapi` SDK, flattens the
`results` array into one row per distinct bucket, augments each row with site context and
a poll timestamp, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so SQLite upserts on repeated runs replace prior counts
rather than accumulating duplicates. The new operation is proposed as menu number **91**
-- the next available slot in the 80-91 Site Stats cluster, sitting adjacent to other
BGP / gateway stats menu items.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST`, `MIST_API_TOKEN`, optional `MIST_ORG_ID`, optional
`MIST_SITE_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using a known site from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. The
default test sweep already covers the 80-91 range; the heavy/destructive skip list
(14, 18, 63-65, 90-100) does not exclude 91.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical BGP peer
counts (the endpoint is a count aggregation -- payload is small, bounded by `limit`,
default 100 rows). Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json`
continue to govern back-off; this endpoint is light enough that no special tuning is
required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`).
Site UUID validated client-side before the SDK call.
**Scale/Scope**: One new public menu method (~25 lines) on the existing
`GatewayStatsExportUtils` class (the same class that owns adjacent BGP / gateway stats
exports). One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new CSV/SQLite table
(`site_bgp_stats_count`). One menu registration entry, one README operation-count bump,
one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `count_site_bgp_stats()` stays under 25 lines,
  takes <=5 parameters (`self`, `site_id`, `state`, `distinct`, `limit`), and contains
  <=5 logical blocks (prompt -> validate -> API call -> flatten results -> DataExporter
  call). Hierarchy unchanged: one new method on an existing class. No new packages,
  modules, or top-level constants are introduced. The flattening step is a single
  comprehension; if it grows past 5 lines during implementation, it is extracted to a
  private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `GatewayStatsExportUtils` class (the class that owns the related `searchSiteBgpStats`
  and gateway-metrics exports). No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names use
  full words (`distinct_field`, `count_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"count_site_bgp_stats:site_id"`,
  `"count_site_bgp_stats:state"`, `"count_site_bgp_stats:distinct"`,
  `"count_site_bgp_stats:limit"`) so SSH / container EOF exits cleanly with code 0 and
  no traceback. The endpoint is strictly read-only (HTTP GET), so no typed destructive-
  confirmation gate is required. `site_id` is validated against the Mist UUID shape
  before the API call; on validation failure the method logs a warning and returns
  early. `limit` is coerced to int and clamped to [1, 1000] before being sent. API
  token comes from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 91 countSiteBgpStats` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Counting BGP stats for site %s distinct=%s"); `DEBUG`
  after the call with bucket counts ("Count response: total=%d buckets=%d");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full traceback
  via `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing BGP stats menu cluster) get comments added
  in the same PR.

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
specs/544-mist-count-site-bgp-stats/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_bgp_stats.md           # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on GatewayStatsExportUtils class + PK strategy +
                         # menu 91 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 91
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 91
                         # addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `GatewayStatsExportUtils` class in `MistHelper.py` -- the same
class that owns adjacent BGP / OSPF / gateway-metric site stats exports. If grep at
implementation time reveals the BGP count operation has no obvious owning class, the
fallback is to add it to the broader `SiteStatsExportUtils` class. The menu number
proposal is **91**, chosen because operations 80-91 are the Site Stats cluster per the
copilot-instructions menu table and 91 is the next available slot below the Viewers
range that begins at 92. The full menu list will be re-verified at task generation time;
if 91 collides with an in-flight feature branch, the next free integer in the same
cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method skeleton in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `GatewayStatsExportUtils`.
  No wrappers introduced. The single flattening helper, if needed, is added as a
  private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call; `limit` is clamped before being
  sent.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompts, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
