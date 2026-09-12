# Implementation Plan: GetOrgMxEdgeUpgrade Menu Item

**Branch**: `617-mist-get-org-mx-edge-upgrade` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/617-mist-get-org-mx-edge-upgrade/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/mxedges/upgrade/{upgrade_id}` (operationId
`getOrgMxEdgeUpgrade`) to retrieve the status, target firmware version, and
per-Mist-Edge progress of a single Mist Edge upgrade job inside an organization.
The menu item prompts the user for the `org_id` and the `upgrade_id` via
`safe_input()`, invokes `mistapi.api.v1.orgs.mxedges.getOrgMxEdgeUpgrade()`,
flattens the upgrade job object into one summary row plus zero or more
per-Mist-Edge progress rows, and persists results through
`DataExporter.write_with_format_selection()` so the CSV, SQLite, and
ArangoDB+Redis backends all behave consistently. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly on the
natural key `(org_id, upgrade_id)`. The new operation is proposed as menu
number **96** -- the next available viewer slot in the interactive-safe cluster
(60-96), sitting adjacent to the existing Mist Edge stats / viewer operations
and just below the resource-intensive block at 97-101.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (HTTP transport, transitive);
`python-dotenv` (loads `MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV outputs land in
`data/`; the polyglot ArangoDB + Redis backend handles graph + cache when
configured.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive sweep mode using a known `org_id` and `upgrade_id` resolved
from `.env` defaults; per-test prompts are bypassed by the existing
`--menu <num>` shortcut. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) does
**not** exclude operation 96; it sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local development; Podman Linux
container (`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and
SSH-on-2200 access. Both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines)
with an optional Gunicorn web UI on port 8055. This feature lives entirely in
the CLI.
**Performance Goals**: A single GET request completes in <=5 seconds for a
typical Mist Edge upgrade job (the endpoint is non-paginated and returns one
JSON object). The adaptive delay system (`delay_metrics.json` +
`tuning_data.json`) continues to govern back-off; this endpoint is light enough
that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`MxEdgeExportUtils` class (or `MxEdgeManager` if that is the canonical owner
in the current MistHelper.py revision), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new CSV/SQLite tables
(`org_mx_edge_upgrade_summary` and `org_mx_edge_upgrade_progress`), one menu
registration entry, one README operation-count bump, one CHANGELOG line. No
new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_mx_edge_upgrade()` stays
  under 25 lines, takes <=3 parameters (`self`, `org_id`, `upgrade_id`), and
  contains <=5 logical blocks (prompt -> API call -> flatten summary ->
  flatten per-edge progress -> DataExporter call). Hierarchy is unchanged: one
  new method on an existing class. No new packages, modules, or top-level
  constants are introduced. The progress-row flattener is a single dict
  comprehension; if it grows past 5 lines during implementation it is
  extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `MxEdgeExportUtils` class (the class that owns related Mist Edge exports
  such as `listOrgMxEdges` and `getOrgMxEdge`). No standalone wrapper function
  is introduced. The menu dispatch in the main loop references the class
  method directly. Variable names use full words (`upgrade_summary_row`,
  `per_mxedge_progress`) -- no single-letter iterators in user-facing logic.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected via `safe_input()` with
  explicit `context=` strings (`"org_mx_edge_upgrade:org_id"`,
  `"org_mx_edge_upgrade:upgrade_id"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP
  GET), so no typed destructive-confirmation gate is required. Both
  identifiers are validated against the Mist UUID shape before the SDK call;
  on validation failure the method logs a warning and returns early. The API
  token is loaded from `.env` via the existing `mistapi.APISession` and is
  never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 96
  getOrgMxEdgeUpgrade` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` -> `podman
  pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching Mist Edge upgrade %s for
  org %s"); `DEBUG` after the call with summary counts ("Upgrade status=%s
  target_version=%s mxedge_count=%d"); `WARNING` on 404 / empty payload;
  `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment explaining *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing Mist Edge export cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a result summary, `logging.info(...)`
  before flatten, `logging.debug(...)` after flatten, `logging.info(...)`
  before write, `logging.debug(...)` after write. The DataExporter call
  already emits its own per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/617-mist-get-org-mx-edge-upgrade/
|-- plan.md              # This file
|-- research.md          # Phase 0 -- SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 -- response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 -- local run + .env + quality gates
|-- contracts/
|   `-- get_org_mx_edge_upgrade.md   # Phase 1 -- HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on MxEdgeExportUtils class + PK strategy
                         # + menu 96 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table
                         # for operation 96.
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing the
                         # menu 96 addition.
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the new SQLite tables
                         # created on first run by DataExporter).
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `MxEdgeExportUtils` class in
`MistHelper.py` (the same class that owns the other Mist Edge exports such
as `listOrgMxEdges`, `getOrgMxEdge`, and `getOrgMxEdgesUpgrades`). If the
current MistHelper.py revision uses a slightly different canonical class name
for Mist Edge operations (for example `MxEdgeManager`), the method is added
to whichever class already owns the related read-only Mist Edge endpoints --
no new class is introduced. The menu number proposal is **96**, chosen
because it is the next free slot in the viewers cluster (92-96) of the
Interactive Safe range (60-96), immediately below the resource-intensive
block at 97-101 and inside the default `--test` sweep range. The full menu
list will be re-verified at task generation time; if 96 collides with an
in-flight feature branch, the next free integer in the same cluster is
selected.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions are required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary receives a single insert
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `MxEdgeExportUtils`. No wrappers introduced. Flattening helpers, if
  needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms
  the endpoint is GET only, with no destructive side effect. `safe_input()`
  is the documented prompt path. UUID validation happens before the SDK
  call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows
  the expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action
  (prompt, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
