# Implementation Plan: getOrgEvpnTopology Menu Item

**Branch**: `606-mist-get-org-evpn-topology` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/606-mist-get-org-evpn-topology/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/evpn_topologies/{evpn_topology_id}` (operationId
`getOrgEvpnTopology`) to retrieve the full configuration of a single EVPN VxLAN /
MP-BGP topology -- including overlay/underlay BGP parameters, per-switch role
assignments, pod mapping, and switch-level network/dhcpd overrides. The menu item
prompts the user for `org_id` (default loaded from `.env` `MIST_ORG_ID`) and the
target `evpn_topology_id` via `safe_input()`, invokes the
`mistapi.api.v1.orgs.evpn_topologies.getOrgEvpnTopology()` SDK call exactly once,
flattens the nested response into a primary header row plus zero-or-more per-switch
detail rows, and persists everything through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends remain consistent. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (natural primary key on `id`) so repeated runs
upsert cleanly without duplicate rows. The new operation is proposed as menu
number **195** -- the next available integer after the current ceiling of menu 194
(`DeviceConfigTemplateClonerManager.clone`). Placement keeps the read-only EVPN
fetch above the destructive block while remaining adjacent to the existing
`listOrgEvpnTopologies` machinery already registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to the Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and the
optional `MIST_ORG_ID` default).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; the
polyglot ArangoDB + Redis containers (spec 188) handle the graph + cache backend.
Two physical outputs are produced per run: `OrgEvpnTopology.csv` (header row) and
`OrgEvpnTopologySwitches.csv` (one row per `switches[]` entry).
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using `MIST_ORG_ID` and `MIST_EVPN_TOPOLOGY_ID` (or the
first ID discovered via the existing `listOrgEvpnTopologies` cache) from `.env`.
Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`.
Menu 195 sits outside the heavy/destructive skip list (14, 18, 63-65, 90-100) so it
is included in the default test sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both
must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a typical
EVPN topology (the endpoint is non-paginated and returns one JSON object that
embeds the full switch list). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that
no endpoint-specific tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets
(API token, full URL with token) in logs; all output under `data/`; Windows-safe
path joining via `os.path.join` / `pathlib.Path`; UUID shape validated before the
SDK call to fail fast on operator typos.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgConfigExporter` class, one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`,
two new CSV/SQLite tables (`org_evpn_topology` header and
`org_evpn_topology_switches` detail), one menu registration entry in the dispatch
dict, one README operation-count bump and menu-table row, one CHANGELOG line. No
new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_evpn_topology_detail()` stays under 25 lines, takes <=3 parameters
  (`self`, `org_id`, `evpn_topology_id`), and contains <=5 logical blocks
  (prompt -> validate -> API call -> flatten header + switches -> two DataExporter
  calls). Hierarchy is unchanged: one new method on an existing class. No new
  packages, modules, or top-level constants are introduced. The per-switch
  flattener is a single comprehension; if it grows past five lines during
  implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a static method on the existing
  `OrgConfigExporter` class (the same class that already owns `psks`, `webhooks`,
  `wlans`, and `mx_edges` org-config exports). No standalone wrapper function is
  introduced. The menu dispatch dict in `MistHelper.py` (line ~21947) references
  the class method directly via `OrgConfigExporter.evpn_topology_detail`.
  Variable names use full words (`evpn_topology`, `switch_row`, `pod_number`) --
  no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_evpn_topology:org_id"`,
  `"org_evpn_topology:evpn_topology_id"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate (e.g. `Type 'UPGRADE' to proceed`)
  is required. Both `org_id` and `evpn_topology_id` are validated against the
  Mist UUID shape before the SDK call; on validation failure the method logs a
  warning and returns early without hitting the API. The API token comes from
  `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 195
  getOrgEvpnTopology` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs validation + multi-arch build ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching EVPN topology %s for org %s");
  `DEBUG` after the call with summary counts ("EVPN topology %s: switches=%d
  pods=%d"); `WARNING` on 404 / empty payload ("EVPN topology %s not found in
  org %s"); `ERROR` on unexpected exception via `logging.exception` (which
  captures the traceback without the API token). No secrets, tokens, or full
  request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration
  line will carry an inline comment that explains *why* the line exists, not
  merely what it does. Blank lines, closing parentheses, and decorators are
  exempt per the constitution. Any uncommented adjacent lines in the touched
  block (the existing `OrgConfigExporter` methods) get comments added in the
  same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with switch + pod counts, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten, `logging.info(...)` before each
  `DataExporter.write_with_format_selection()`, `logging.debug(...)` after.
  The DataExporter call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/606-mist-get-org-evpn-topology/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_evpn_topology.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New evpn_topology_detail() static method on
                         # OrgConfigExporter (~line 12047) + new
                         # getOrgEvpnTopology entry in
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES (~line 3944, beside the
                         # existing listOrgEvpnTopologies entry) + menu 195
                         # registration in the dispatch dict (~line 21947).
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 195
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 195
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the two new SQLite tables
                         # created on first run by DataExporter)
documentation/api/orgs/  # Enriched endpoint reference, already present:
                         # GET_orgs_org_id_evpn_topologies_evpn_topology_id.md
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public static method on the existing `OrgConfigExporter` class in
`MistHelper.py` (the same class that owns the other org-config exports such as
`psks`, `webhooks`, `wlans`, and `mx_edges`). The menu number proposal is **195**,
chosen because the current dispatch dict (line ~21947) tops out at 194 and the
read-only EVPN fetch belongs above the destructive block (154-194). The full
menu list will be re-verified at task generation time; if 195 collides with an
in-flight feature branch, the next free integer above 194 is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/get_org_evpn_topology.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert beside the
  existing `listOrgEvpnTopologies` entry, so no level-5 hierarchy explosion. The
  per-switch flattener stays inline as a single comprehension.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgConfigExporter`.
  No wrappers introduced. The optional flattening helper, if added, is a private
  static method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path for both `org_id` and `evpn_topology_id`. UUID
  validation happens before the SDK call. 404 / 401 / 403 / 429 errors are
  caught and logged as warnings rather than tracebacks.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
  Container build + GHCR push + Quadlet restart proceed unchanged.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or full URL.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API
  call, flatten, two exports).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
