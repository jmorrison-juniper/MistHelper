# Implementation Plan: GetOrgMxTunnel Menu Item

**Branch**: `620-mist-get-org-mx-tunnel` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/620-mist-get-org-mx-tunnel/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/mxtunnels/{mxtunnel_id}` (operationId `getOrgMxTunnel`) to
retrieve the full configuration of a single Mist tunnel (mxtunnel) belonging to an
organization. The menu method prompts the user for `org_id` and `mxtunnel_id` via
`safe_input()`, calls the `mistapi` SDK once, flattens the nested mxtunnel object into a
parent summary row plus child rows for the embedded `ipsec.extra_routes` array, and
persists the result through `DataExporter.write_with_format_selection()` so CSV, SQLite,
and ArangoDB+Redis backends all receive consistent output. Two entries are registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (one summary table keyed on the natural mxtunnel `id`
UUID, one child table for IPSec extra routes). The new operation is proposed as menu
number **96** -- the next available slot adjacent to the existing
`listOrgMxTunnels`/`getOrgMxClusters` cluster inside the Safe Org Exports range.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology and Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to the Mist Cloud); `requests` (transport, transitive); `python-dotenv`
(for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; the polyglot
ArangoDB + Redis containers handle the graph + cache backend. No schema migration is
required beyond adding the two new tables on first write.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known `MIST_ORG_ID` and `MIST_MXTUNNEL_ID` from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The standard heavy/destructive skip list
(14, 18, 63-65, 90-100) excludes operation 96, so this item is part of the default sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-port-2200; both
must work without code change. File paths use `os.path.join`/`pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` at roughly 28K lines),
optionally fronted by a Gunicorn web UI on port 8055. This feature lives entirely in the
CLI -- no UI work required.
**Performance Goals**: Single GET request completes in <=5 seconds; the endpoint is
non-paginated and returns one JSON object whose worst-case size is dominated by the
`ipsec.extra_routes`, `vlan_ids`, `mxcluster_ids`, and `anchor_mxtunnel_ids` arrays
(typically <100 entries combined). Adaptive delay (`delay_metrics.json`,
`tuning_data.json`) governs back-off but no endpoint-specific tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; API token never
logged; all output under `data/`; Windows-safe path joining; 5-Item Rule applies to every
new function (<=25 lines, <=5 parameters, <=5 nesting blocks).
**Scale/Scope**: One new public menu method (~22 lines) on a new
`MxTunnelExportUtils` class (no existing class is the obvious owner -- see Structure
Decision below), two new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new SQLite
tables (`org_mxtunnels` and `org_mxtunnel_ipsec_extra_routes`), one menu registration
entry, one README operation-count bump, one CHANGELOG line. No new third-party
dependencies, no new top-level modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_mxtunnel()` stays under 25 lines,
  takes <=3 parameters (`self`, `org_id`, `mxtunnel_id`), and contains <=5 logical
  blocks (two prompts -> validate -> API call -> flatten -> two exports). The flatten
  logic for the embedded `ipsec.extra_routes` array is delegated to a private helper
  method `_flatten_mxtunnel_extra_routes()` on the same class to keep the public method
  short. No new packages, modules, or top-level constants are introduced beyond the two
  PK strategy entries (dictionary entries, not new top-level names).

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- A new `MxTunnelExportUtils` class is introduced because no existing
  class owns the `mxtunnels` API surface (the existing list-mxtunnels operation, when it
  ships, will be added to the same class). The constitution allows new classes when a new
  domain enters the codebase; it forbids standalone wrapper functions. The menu dispatch
  references the class method directly. Variable names use full words
  (`mxtunnel_record`, `extra_route_row`); no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- Both inputs are collected through `safe_input()` with explicit
  `context=` strings (`"org_mxtunnel:org_id"` and `"org_mxtunnel:mxtunnel_id"`) so
  SSH / container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is required.
  Both UUIDs are validated against the Mist UUID shape via the existing
  `is_valid_uuid()` helper before the API call; on validation failure the method logs a
  warning and returns early. The API token comes from `.env` via `mistapi.APISession`
  and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 getOrgMxTunnel`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability and Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching mxtunnel %s for org %s"); `DEBUG` after the call
  with summary counts ("Mxtunnel: name=%s protocol=%s mxclusters=%d vlan_ids=%d");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full traceback
  via `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new helper, the two
  PK strategy dictionary entries, and the menu registration line carries an inline
  comment that explains *why* the line exists, not merely what it does. Blank lines,
  closing parentheses, and decorators are exempt per the constitution. Any uncommented
  adjacent lines in the touched menu-registration block get comments added in the same
  PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a result summary,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten, `logging.info(...)`
  before each write, and `logging.debug(...)` after the second write. The DataExporter
  call already emits its own per-backend log lines; the new method does not duplicate
  them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/620-mist-get-org-mx-tunnel/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates + skeleton
|-- contracts/
|   `-- get_org_mx_tunnel.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New MxTunnelExportUtils class + export_org_mxtunnel() method
                         # + two ENDPOINT_PRIMARY_KEY_STRATEGIES entries + menu 96
                         # registration. No new modules; single-file monolith preserved.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir). Two new SQLite tables
                         # (org_mxtunnels, org_mxtunnel_ipsec_extra_routes) are created
                         # on first run by DataExporter; CSV files land here too.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on a new `MxTunnelExportUtils` class in `MistHelper.py` (the constitution allows
adding classes when a new API surface area lands; the existing
`SiteDeviceUtils`/`OrgInventoryUtils`/`LicenseExportUtils` cluster does not own
mxtunnels). The menu number proposal is **96**, chosen because the safe-org-exports
range runs through 95 and 96 is the next contiguous integer that has not been claimed by
the existing resource-intensive cluster at 97-101. The menu list is re-verified at
`/speckit.tasks` time by grepping `MistHelper.py` for the latest allocated menu integer;
if 96 collides with an in-flight feature branch, the next free integer in the same safe
cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/get_org_mx_tunnel.md`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method skeleton in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks for the public
  method, and the helper `_flatten_mxtunnel_extra_routes()` is a single comprehension
  block. The `ENDPOINT_PRIMARY_KEY_STRATEGIES` insertions are two dictionary entries, so
  no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `MxTunnelExportUtils`. No
  wrappers introduced. The flatten helper is a private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path for both `org_id` and `mxtunnel_id`. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- All log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart skeleton shows the
  expected comment density on every executable line, including both PK strategy entries
  and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompts, API call, flatten, two
  exports).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
