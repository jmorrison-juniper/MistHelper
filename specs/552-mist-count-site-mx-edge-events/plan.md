# Implementation Plan: countSiteMxEdgeEvents Menu Item

**Branch**: `552-mist-count-site-mx-edge-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/552-mist-count-site-mx-edge-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/mxedges/events/count` (operationId `countSiteMxEdgeEvents`)
to retrieve a count of Mist Edge events at a site, grouped by a caller-supplied
`distinct` attribute (for example `type`, `service`, `mxedge_id`, or `mxcluster_id`).
The menu item prompts the user for `site_id` plus optional grouping / filter parameters
through `safe_input()`, calls the `mistapi` SDK, flattens the wrapper response into a
single envelope row plus one row per `results[*]` bucket, and persists the result through
`DataExporter.write_with_format_selection()` so the CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly into SQLite. The new
operation is proposed as menu number **96** -- the next available slot in the Safe Org
Exports / SLE / Mist Edge cluster (51-95 are taken; 97-101 are the resource-intensive
block), sitting adjacent to the existing Mist Edge inventory and event search menu items.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive via mistapi);
`python-dotenv` (loads `MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback. CSV files land in `data/`. The polyglot
ArangoDB + Redis containers handle the graph + cache backend. Two SQLite tables are
created on first run: `site_mxedge_events_count_summary` (envelope) and
`site_mxedge_events_count_buckets` (per-bucket counts).
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode against a known site from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65,
90-100) excludes menu 96 -- the new item lives inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET completes in <=5 seconds for typical sites (the count
endpoint returns a small JSON envelope -- no large payloads). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; this endpoint
is light enough that no special tuning is required. With `--fast`, the retry cap is
respected and concurrency may be raised.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); 5-Item Rule compliance for the new method (<=25 lines, <=5 params,
<=5 logical blocks).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`MxEdgeExportUtils` class (the same class that owns the related `listSiteMxEdges` and
`searchSiteMxEdgeEvents` exports). One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
Two new SQLite tables (summary + buckets). One menu registration entry. One README
operation-count bump. One CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_site_mxedge_events_count()` stays under 25 lines, takes <=5 parameters
  (`self`, `site_id`, `distinct`, `filters`, `duration`), and contains <=5 logical
  blocks (prompt -> SDK call -> flatten envelope -> flatten buckets -> DataExporter
  call). The `filters` parameter is a small dict bundling the optional
  `mxedge_id` / `mxcluster_id` / `type` / `service` / `start` / `end` / `limit`
  values -- keeping the signature under the 5-parameter limit. The hierarchy is
  unchanged: one new method on an existing class. If either flatten step grows past
  five lines during implementation, it is extracted to a private helper on the same
  class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a public method on the existing
  `MxEdgeExportUtils` class (the same class that owns the adjacent Mist Edge inventory
  and event-search exports). No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names use
  full words (`distinct_attribute`, `bucket_row`, `envelope_row`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"site_mxedge_events_count:site_id"`,
  `"site_mxedge_events_count:distinct"`, etc.) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no
  typed destructive-confirmation gate is required. The `site_id` value is validated
  against the Mist UUID shape before the SDK call; on validation failure the method
  logs a warning and returns early. The API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 96 countSiteMxEdgeEvents` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification. README.md and
  CHANGELOG.md are committed in the same change set.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the SDK call ("Counting Mist Edge events for site %s by
  distinct=%s"); `DEBUG` after the call with summary counts ("Received envelope:
  total=%d buckets=%d limit=%d"); `WARNING` on 404 / empty `results`; `ERROR` on
  unexpected exception via `logging.exception`. No secrets, tokens, or full request
  URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entries, and the menu registration
  line will carry an inline comment that explains *why* the line exists, not merely
  what it does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  Mist Edge menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result count; `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten; `logging.info(...)` before export,
  `logging.debug(...)` after export. The `DataExporter` already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/552-mist-count-site-mx-edge-events/
| - plan.md              # This file
| - research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
| - data-model.md        # Phase 1 - response entities + DDL + PK registration
| - quickstart.md        # Phase 1 - local run + .env + quality gates
| - contracts/
|     | - count_site_mx_edge_events.md   # Phase 1 - HTTP + SDK contract
| - tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on MxEdgeExportUtils class + two PK strategy
                         # entries + menu 96 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96
data/                    # Runtime output target (existing dir). DataExporter creates
                         # the two new SQLite tables on first run; no manual schema
                         # migration is needed beyond the new ENDPOINT_PRIMARY_KEY_
                         # STRATEGIES entries.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `MxEdgeExportUtils` class in `MistHelper.py` (the same
class that owns the other Mist Edge exports). The menu number proposal is **96**,
chosen because operations 51-95 are the Safe Org Exports / Org-License / SLE / Mist
Edge cluster and 96 is the next available integer below the resource-intensive block
at 97-101. The full menu list will be re-verified at task generation time; if 96
collides with an in-flight feature branch, the next free integer in the same cluster
is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks. The two
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` inserts use the existing dictionary structure, so
  no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `MxEdgeExportUtils`. No
  wrappers introduced. Flattening helpers, if needed, are added as private methods on
  the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or full URL.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including both PK strategy entries and
  the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, SDK call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
