# Implementation Plan: GetOrgMxEdgeCluster Menu Item

**Branch**: `616-mist-get-org-mx-edge-cluster` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/616-mist-get-org-mx-edge-cluster/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/mxclusters/{mxcluster_id}` (operationId
`getOrgMxEdgeCluster`) to retrieve the full configuration of a single Mist Edge
cluster (RadSec servers, NAC settings, tunterm hosts, DHCP relay, proxy, etc.).
The menu item prompts the user for an `org_id` (from `.env` or override) and a
`mxcluster_id` via `safe_input()`, invokes the `mistapi` SDK, flattens the
nested configuration object into a single row (with selected nested arrays
exported as JSON-encoded columns), and persists the result through
`DataExporter.write_with_format_selection()` so the CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on `getOrgMxEdgeCluster`
for clean SQLite upserts on repeated runs. The new operation is proposed as
menu number **96** -- a free slot inside the Interactive Safe Org Exports
cluster (60-96), positioned adjacent to existing MxEdge-related operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV file
`data/OrgMxEdgeCluster.csv` lands in `data/`; polyglot ArangoDB + Redis
containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using `MIST_ORG_ID` and a sentinel `MIST_TEST_MXCLUSTER_ID`
from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`.
The default test sweep range covers menu 96; existing skip list (14, 18,
63-65, 90-100 destructive cluster) is not affected by this menu number.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200.
Both runtimes must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a
well-formed cluster (the endpoint is non-paginated and returns a single JSON
object describing one MxCluster). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs (RADIUS shared secrets and root passwords in the response are
redacted before debug logging); all output under `data/`; Windows-safe path
joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public method (~22 lines) added to the existing
`OrgExportUtils` class (the same class that owns `mx_edges` and other org-level
exports), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new
CSV/SQLite table (`org_mx_edge_cluster`), one menu registration entry, one
README operation-count bump, one CHANGELOG line. No new dependencies, no new
modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_mx_edge_cluster()` stays under 25 lines, takes <=3 parameters
  (`self`, `org_id`, `mxcluster_id`), and contains <=5 logical blocks (prompt
  -> UUID validate -> API call -> flatten -> DataExporter call). The flatten
  step uses one private helper `_flatten_mxcluster_row()` to keep the public
  method short. Hierarchy is unchanged: one new public method + one new
  private helper on an existing class. No new packages, modules, or top-level
  constants are introduced beyond the single PK-strategy dict entry.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgExportUtils` class (which already owns `mx_edges`, `webhooks`, `wlans`,
  `msp`, and other org-scope exports). No standalone wrapper function is
  introduced. The menu dispatch in the main loop references the class method
  directly. Variable names use full words (`cluster_record`, `radsec_servers`,
  `tunterm_host_list`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_mx_edge_cluster:org_id"`,
  `"org_mx_edge_cluster:mxcluster_id"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP
  GET), so no typed destructive-confirmation gate is required. Both UUIDs are
  validated against the Mist UUID shape before the API call; on validation
  failure the method logs a warning and returns early. API token comes from
  `.env` via the existing `mistapi.APISession` and is never logged. RADIUS
  shared secrets, `mist_password`, and `root_password` fields in the response
  are redacted to `***` before any DEBUG log emission.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` -> `python -m black --check
  MistHelper.py` -> commit with `version YY.MM.DD.HH.MM - add menu 96
  getOrgMxEdgeCluster` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs ->
  `gh run watch <run-id>` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style formatting.
  `INFO` is emitted before the API call ("Fetching MxEdge cluster %s for org
  %s"); `DEBUG` after the call with a redacted summary
  ("MxCluster fetched: id=%s name=%s radsec_auth_servers=%d
  tunterm_hosts=%d"); `WARNING` on 404 / empty payload;
  `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, RADIUS shared secrets, or full
  request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, the private flatten helper, and the menu
  registration line will carry an inline comment that explains *why* the line
  exists, not merely what it does. Blank lines, closing parentheses, and
  decorators are exempt per the constitution. Any uncommented adjacent lines
  in the touched block (the existing `OrgExportUtils.mx_edges` neighborhood)
  get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a result summary, `logging.info(...)`
  before flatten, `logging.debug(...)` after flatten with column count,
  `logging.info(...)` before write, `logging.debug(...)` after write with
  backend name. The DataExporter call already emits its own per-backend log
  lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/616-mist-get-org-mx-edge-cluster/
| spec.md              # Feature specification (already exists)
| plan.md              # This file
| research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
| data-model.md        # Phase 1 - response entities + DDL + PK registration
| quickstart.md        # Phase 1 - local run + .env + quality gates
| contracts/
|   `- get_org_mx_edge_cluster.md   # Phase 1 - HTTP + SDK contract
`- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New public method export_org_mx_edge_cluster() and
                         # private helper _flatten_mxcluster_row() added to the
                         # existing OrgExportUtils class. New entry in
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES dict (keyed on
                         # "getOrgMxEdgeCluster"). New row in the menu dispatch
                         # table for op 96. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table
                         # for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu
                         # 96 addition
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the new SQLite table
                         # org_mx_edge_cluster created on first run by
                         # DataExporter)
documentation/api/orgs/  # Already contains
                         # GET_orgs_org_id_mxclusters_mxcluster_id.md;
                         # no doc generation required.
```

**Structure Decision**: Single-file monolith. The new menu item is added as
a public method on the existing `OrgExportUtils` class in `MistHelper.py`
(the same class that owns `mx_edges` and other org-scope exports). Extending
`OrgExportUtils` rather than creating a new `MxClusterExportUtils` class is
correct because the response is a single org-scoped object and the work
(prompt -> call -> flatten -> export) matches the established export
pattern. The menu number proposal is **96**, chosen because operations
60-96 are the Interactive Safe Org Exports cluster and 96 is the next
available slot before the resource-intensive block at 97-101. The full
menu list will be re-verified at task generation time; if 96 collides with
an in-flight feature branch, the next free integer in the same cluster is
used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
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
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert
  (existing structure), so no level-5 hierarchy explosion. The
  `_flatten_mxcluster_row()` helper is itself <=25 lines because nested
  arrays are JSON-encoded rather than expanded.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `OrgExportUtils`. No wrappers introduced. The flatten helper is a private
  method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. Both UUIDs are validated before the SDK call.
  Secret fields are redacted before DEBUG logging.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or any
  RADIUS shared secret.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry, the flatten helper, and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
