# Implementation Plan: countOrgSiteMxEdgeEvents Menu Item

**Branch**: `527-mist-count-org-site-mx-edge-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/527-mist-count-org-site-mx-edge-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/mxedges/events/count` (operationId `countOrgSiteMxEdgeEvents`)
to retrieve grouped counts of Mist Edge events for an organization, bucketed by a caller-
specified `distinct` attribute (event type, service, mxedge_id, mxcluster_id, etc.) over a
bounded time range. The new menu method prompts the user for `org_id` plus optional
`distinct`, `mxedge_id`, `mxcluster_id`, `type`, `service`, time-range, and `limit`
filters using `safe_input()`, invokes the `mistapi` SDK, flattens the response envelope
(`distinct`, `start`, `end`, `limit`, `total`) plus the dynamic `results[]` array into
one summary row and N detail rows, and persists everything through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive identical output. A new entry is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
for clean upserts on repeated runs. The new operation is proposed as menu number **58** --
the next available slot in the Safe Org Exports cluster (1-59), placed adjacent to the
existing Events (20-26) family so NOC engineers find it by category.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK, the sole permitted
interface to Mist Cloud); `requests` (transitive transport); `python-dotenv` (loads
`MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB +
Redis containers handle the graph + cache backend when configured.
**Testing**: `python MistHelper.py --test` exercises the menu item non-interactively using
a known org from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. The new
item 58 sits inside the default test sweep range (skip list 14, 18, 63-65, 90-100 is
unaffected).
**Target Platform**: Windows 11 + venv for local development; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical 1-day count
windows; longer windows respect Mist API rate limits and the adaptive delay system
(`delay_metrics.json` + `tuning_data.json`). The endpoint returns a small aggregate (one
results array bounded by the `limit` parameter, default 100), so no pagination loop is
required for typical usage.
**Constraints**: ASCII-only logging; `safe_input()` wraps every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining via `os.path.join` / `pathlib.Path`.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`MistEdgeExportUtils` class (the class that owns adjacent mxedge operations), one new
entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new SQLite tables
(`org_mxedge_events_count_summary` and `org_mxedge_events_count_results`), one menu
registration entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_mxedge_events_count()` stays under
  25 lines, takes <=5 parameters (`self`, `org_id`, `distinct`, `filters_dict`,
  `time_range_tuple`) where `filters_dict` packs the optional `mxedge_id` / `mxcluster_id`
  / `type` / `service` / `limit` values to stay inside the parameter cap, and contains
  <=5 logical blocks (collect prompts -> validate -> API call -> flatten summary +
  results -> DataExporter write). Hierarchy is unchanged: one new method on an existing
  class. If the flatten step grows past 5 lines during implementation it is extracted to
  a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `MistEdgeExportUtils` class (the same class that owns the related `listOrgMistEdges`
  and `searchOrgMistEdgeEvents` exports). No standalone wrapper function is introduced;
  the menu dispatch in the main loop references the class method directly. Variable
  names use full words (`distinct_attribute`, `results_row`, `summary_row`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_mxedge_events_count:org_id"`,
  `"org_mxedge_events_count:distinct"`, `"org_mxedge_events_count:duration"`, etc.) so
  SSH / container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is required.
  `org_id` is validated against the Mist UUID shape before the API call; on validation
  failure the method logs a warning and returns early. The API token comes from `.env`
  via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 58 countOrgSiteMxEdgeEvents` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Counting org mxedge events for org %s distinct=%s
  duration=%s"); `DEBUG` after the call with summary counts ("MxEdge events count:
  distinct=%s total=%d results=%d window=[%s..%s]"); `WARNING` on 404 or empty
  payload; `ERROR` on unexpected exception via `logging.exception`. No tokens, full
  URLs, or auth headers are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line
  carries an inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  mxedge-export cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with a result count, `logging.info(...)` before flatten, `logging.debug(...)` after
  flatten with row counts, `logging.info(...)` before write, `logging.debug(...)` after
  write. The DataExporter call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/527-mist-count-org-site-mx-edge-events/
+-- plan.md              # This file
+-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
+-- data-model.md        # Phase 1 - response entities + DDL + PK registration
+-- quickstart.md        # Phase 1 - local run + .env + quality gates
+-- contracts/
|   +-- count_org_site_mx_edge_events.md   # Phase 1 - HTTP + SDK contract
+-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on MistEdgeExportUtils class + new
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 58 registration.
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58.
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing the addition.
data/                    # Runtime output target (existing dir). DataExporter creates the
                         # two new SQLite tables on first run; no schema migration script
                         # is required beyond the new PK strategy entry.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `MistEdgeExportUtils` class in `MistHelper.py` (the same class
that already owns the other Mist-Edge-scoped operations). If `MistEdgeExportUtils` does
not yet exist as a distinct class (the monolith has historically grouped mxedge
operations alongside org exports under a broader `OrgExportUtils` class), the new method
is added to whichever existing class currently owns
`searchOrgMistEdgeEvents` / `listOrgMistEdges`; no new class is created solely for this
single method. The menu number proposal is **58**, chosen because operations 1-59 are
the Safe Org Exports cluster and 58 is the next available slot adjacent to the Events
(20-26) family. The full menu list is re-verified at task generation time; if 58
collides with an in-flight feature branch, the next free integer in the same cluster
is used.

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
  `quickstart.md` confirms <=25 lines, <=5 parameters (with optional filters packed in a
  single dict), <=5 logical blocks. `ENDPOINT_PRIMARY_KEY_STRATEGIES` receives one
  insert into an existing structure -- no hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing
  `MistEdgeExportUtils` (or equivalent existing mxedge-scoped class). No wrappers
  introduced. Flatten helpers, if needed, are private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, no destructive side effect. `safe_input()` is the documented prompt path.
  UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token or full request URL.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and the
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
