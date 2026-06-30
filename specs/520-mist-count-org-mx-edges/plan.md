# Implementation Plan: countOrgMxEdges Menu Item

**Branch**: `520-mist-count-org-mx-edges` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/520-mist-count-org-mx-edges/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/mxedges/count` (operationId `countOrgMxEdges`) to
return grouped counts of Mist Edge appliances for an organization, optionally
filtered by site, cluster, model, distro, tunterm version, or time window. The
menu item prompts the user for an `org_id` and a `distinct` field name via
`safe_input()`, invokes the `mistapi` SDK, flattens the response (a single
summary object plus a `results` array of `{distinct_value, count}` rows) into
two logical row sets, and persists them through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. Two entries are registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so SQLite upserts cleanly on repeated polls.
The new operation is proposed as menu number **96** -- the next available slot
adjacent to the existing Mist Edge org-stats/inventory operations and just
below the resource-intensive cluster boundary.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode against the org from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy/destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- the proposed number 96 sits at the
boundary and is included in the default `--test` sweep unless the existing
range definition needs adjustment; if 96 falls inside the resource-intensive
block at task time, the number is shifted to the first free safe-range slot.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
counts. The endpoint supports pagination via `limit`/`page` but most distinct
groupings (model, distro, cluster) produce tens of rows, not thousands; the
default `limit=100` is sufficient and matches the upstream default.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining via
`os.path.join` / `pathlib.Path`. Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; this
endpoint is light enough that no per-endpoint tuning override is required.
**Scale/Scope**: One new public menu method (~25 lines) on the existing
`MxEdgeExportUtils` class (the same class that owns `listOrgMxEdges`,
`searchOrgMxEdges`, and related Mist Edge operations -- a new class is not
justified for a single new method per Constitution Principle II), two new
entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new CSV/SQLite tables
(`org_mxedge_count_summary` and `org_mxedge_count_results`), one menu
registration entry, one README operation-count bump, one CHANGELOG line. No
new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_mxedge_count()` stays
  under 25 lines, takes <=4 parameters (`self`, `org_id`, `distinct`,
  `extra_filters`), and contains <=5 logical blocks (prompt -> validate ->
  API call -> flatten summary + results -> DataExporter call x2). Hierarchy
  unchanged: one new method on one existing class, no new packages, modules,
  or top-level constants. Two output flatteners are inlined as comprehension
  blocks; if either exceeds 5 lines during implementation, it is extracted
  to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `MxEdgeExportUtils` class (the same class that owns the other Mist Edge
  org-level exports such as `listOrgMxEdges` and `searchOrgMxEdges`). No
  standalone wrapper function is introduced; the menu dispatch in the main
  loop references the class method directly. Variable names use full words
  (`distinct_field`, `count_row`, `result_entry`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_mxedge_count:org_id"`,
  `"org_mxedge_count:distinct"`) so SSH and container EOF exits cleanly with
  code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so
  no typed destructive-confirmation gate is required. The supplied `org_id` is
  validated against the Mist UUID shape via the existing `is_valid_uuid()`
  helper before the API call; on validation failure the method logs a
  `WARNING` and returns early. The `distinct` field is validated against a
  small allow-list (`mxedge_id`, `site_id`, `mxcluster_id`, `model`, `distro`,
  `tunterm_version`) derived from the OpenAPI query parameter list to avoid
  passing arbitrary user strings into the API. API token comes from `.env`
  via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` -> `python -m black --check MistHelper.py`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 countOrgMxEdges`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs
  -> `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Counting Mist Edges for org %s by
  distinct=%s"); `DEBUG` after the call with summary counts ("Count returned:
  total=%d distinct=%s rows=%d"); `WARNING` on 404 or empty `results`;
  `ERROR` on unexpected exception with full traceback via `logging.exception`.
  No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the two new
  PK strategy dictionary entries, and the menu registration line will carry
  an inline comment explaining *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing Mist Edge export menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each prompt, the prompt itself,
  `logging.info(...)` before the SDK call, the call,
  `logging.debug(...)` after with summary + row counts,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before each write, `logging.debug(...)` after each
  write. The DataExporter call already emits its own per-backend log lines;
  the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. The Complexity Tracking table
remains empty.

## Project Structure

### Documentation (this feature)

```text
specs/520-mist-count-org-mx-edges/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_mx_edges.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on MxEdgeExportUtils class + two PK strategy
                         # entries + menu 96 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the two new SQLite tables created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `MxEdgeExportUtils` class in `MistHelper.py`
(the same class that owns the other org-mxedges exports). The menu number
proposal is **96**, chosen because it is the next contiguous integer adjacent
to the existing Mist Edge org-export cluster and remains below the destructive
block (154-194). The full menu list will be re-verified at task generation
time; if 96 collides with an in-flight feature branch or sits inside a
resource-intensive sub-range, the next free integer in the same safe cluster
is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The skeleton in `quickstart.md`
  confirms <=25 lines, <=4 parameters, <=5 logical blocks. The two
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` inserts share the existing dict (no new
  level-5 hierarchy).
- **Principle II (Class-Based)**: PASS -- All work lives on
  `MxEdgeExportUtils`. No wrappers introduced. Flatteners, if extracted,
  become private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID and distinct-field validation occur
  before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design
  are ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows
  the expected comment density on every executable line, including the
  two PK strategy entries and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action
  (prompt, validate, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
