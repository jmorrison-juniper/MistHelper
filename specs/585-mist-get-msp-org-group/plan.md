# Implementation Plan: GetMspOrgGroup Menu Item

**Branch**: `585-mist-get-msp-org-group` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/585-mist-get-msp-org-group/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}/orggroups/{orggroup_id}` (operationId `getMspOrgGroup`) to
retrieve the details of a single MSP-managed Organization Group, including its display
name, parent MSP, and the list of member organization UUIDs (`org_ids`). The menu item
prompts the user for `msp_id` and `orggroup_id` via `safe_input()`, invokes the
`mistapi.api.v1.msps.org_groups.getMspOrgGroup()` SDK function once, flattens the single
returned JSON object into one summary row plus zero-or-more member-org join rows, and
persists the result through `DataExporter.write_with_format_selection()` so CSV, SQLite,
and ArangoDB+Redis backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed by `getMspOrgGroup` for clean SQLite upserts on
repeated runs. The new operation is proposed as menu number **96** -- the next available
slot in the Interactive Safe cluster (60-96), sitting adjacent to other single-record
viewer operations and well clear of the resource-intensive block at 97-101.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Principle: Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transport, transitive via mistapi);
`python-dotenv` (loads `MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. Local
fallback is SQLite at `data/mist_data.db`; CSVs land in `data/`; the polyglot ArangoDB +
Redis containers handle graph + cache. Two SQLite tables are created on first run:
`msp_org_groups` (one row per org-group) and `msp_org_group_members` (one row per
`(orggroup_id, org_id)` membership edge).
**Testing**: `python MistHelper.py --test` exercises the menu item non-interactively
using known MSP / orggroup IDs from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected
because the proposed number 96 is at the upper boundary of the Interactive Safe range
but is read-only and lightweight; if scheduling later requires placing it inside the
skipped band, the test harness flag is updated in the same PR.
**Target Platform**: Windows 11 + venv for local development; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and the SSH-on-2200
session model. Both targets must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=2 seconds for a typical org
group (the endpoint is non-paginated and the response is a single small JSON object,
typically under 1 KB). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that no
endpoint-specific tuning entry is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output written under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); the API token is never echoed or logged.
**Scale/Scope**: One new public menu method (~22 lines) on a newly introduced
`MspOrgGroupExportUtils` class (no existing class owns MSP-org-group endpoints today),
one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new CSV/SQLite tables, one menu
registration entry, one README operation-count bump, one CHANGELOG line. No new
third-party dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_msp_org_group()` stays under 25 lines,
  takes <=3 parameters (`self`, `msp_id`, `orggroup_id`), and has <=5 logical blocks
  (prompt -> validate -> SDK call -> flatten (summary + members) -> DataExporter call).
  The new `MspOrgGroupExportUtils` class introduces one class at the existing module
  level -- the second hierarchy level remains under 5 sibling classes per feature
  cluster. If member-row flattening grows past 5 lines, it is extracted to a private
  helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- A new class `MspOrgGroupExportUtils` is introduced because no
  existing class owns MSP-org-group read endpoints today; this is a genuine new
  structural unit, not a wrapper. Adding a free function `get_msp_org_group()` would
  violate the no-wrappers rule. The menu dispatch in the main loop references the class
  method directly. Variable names are full words (`org_group_row`, `member_org_ids`) --
  no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- Both user inputs are collected through `safe_input()` with
  explicit `context=` strings (`"msp_org_group:msp_id"`,
  `"msp_org_group:orggroup_id"`) so an SSH or container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Both inputs are validated against the
  Mist UUID shape before the SDK call; on validation failure the method logs a warning
  and returns early. API token comes from `.env` via the existing `mistapi.APISession`
  and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit with `version
  YY.MM.DD.HH.MM - add menu 96 getMspOrgGroup` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch <id>` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run container ->
  `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the SDK call (`"Fetching MSP org group msp=%s orggroup=%s"`); `DEBUG`
  after the call with field summary (`"Org group received: name=%s member_orgs=%d"`);
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full traceback
  via `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched menu-dispatch block receive comments in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before prompting, `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with response field counts, `logging.info(...)` before the
  flatten step, `logging.debug(...)` after flatten with row counts, `logging.info(...)`
  before write, `logging.debug(...)` after write. The DataExporter call already emits its
  own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/585-mist-get-msp-org-group/
|-- plan.md              # This file
|-- spec.md              # Feature spec (already authored, NOT modified here)
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_msp_org_group.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New class MspOrgGroupExportUtils with method
                         # export_msp_org_group() + ENDPOINT_PRIMARY_KEY_STRATEGIES
                         # entry + menu 96 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the two new SQLite tables created on first
                         # run by DataExporter)
.env                     # Adds MSP_ID and MSP_ORG_GROUP_ID for non-interactive --test
                         # runs; existing MIST_HOST and MIST_API_TOKEN are reused
```

**Structure Decision**: Single-file monolith. The new menu item is added as a method on
a new `MspOrgGroupExportUtils` class in `MistHelper.py` (no existing class owns MSP /
orggroup read endpoints; creating one is the class-based architectural choice rather
than appending to an unrelated class). The menu number proposal is **96**, chosen
because operations 60-96 are the Interactive Safe cluster, this endpoint requires
interactive input for two UUIDs, and 96 is the next available slot below the
resource-intensive block at 97-101. The full menu list is re-verified at
`/speckit.tasks` time; if 96 collides with an in-flight feature branch, the next free
integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/get_msp_org_group.md`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry is a single dict insert (existing structure),
  so no level-5 hierarchy explosion. The two-table schema in `data-model.md` keeps
  member-edge data normalized rather than packing it into a single denormalized row,
  preserving the 5-Item Rule at the data layer too.
- **Principle II (Class-Based)**: PASS -- All work lives on the new
  `MspOrgGroupExportUtils` class. No free functions. Flattening helpers, if any, are
  added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path; both UUIDs are validated before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard deployment
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 `quickstart.md` shows the
  expected comment density on every executable line, including the PK strategy entry and
  the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 `quickstart.md` enumerates the
  before/after log pairs for every meaningful action (prompt, validate, SDK call,
  flatten summary, flatten members, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
