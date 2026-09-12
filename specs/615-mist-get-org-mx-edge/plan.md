# Implementation Plan: GetOrgMxEdge Menu Item

**Branch**: `615-mist-get-org-mx-edge` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/615-mist-get-org-mx-edge/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/mxedges/{mxedge_id}` (operationId `getOrgMxEdge`) to retrieve
the full configuration record for a single Mist Edge (MxEdge) appliance within an
organization. The menu prompts the user for the target `org_id` and `mxedge_id` via
`safe_input()`, calls `mistapi.api.v1.orgs.mxedges.getOrgMxEdge()`, flattens the deeply
nested response object into one row, and persists output through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent data. A `natural_pk` entry on `id` is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly into SQLite without
producing duplicate primary keys. The new operation is proposed as menu number **235**,
the next available slot in the safe-org-export / MxEdge cluster, sitting adjacent to the
existing `listOrgMxEdges` export (op `OrgConfigExporter.mx_edges`) and below the
resource-intensive band that starts at 97.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to the Mist Cloud REST surface); `requests` (transport, transitive);
`python-dotenv` for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend when configured.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org and a known MxEdge ID supplied through `.env` (`MIST_MXEDGE_ID`
or the existing fixture-resolution path). Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected:
menu 235 is read-only and sits well outside that range.
**Target Platform**: Windows 11 + `.venv` for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both
environments execute the same code with no platform-specific branches.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request returns one JSON object and completes in
<=5 seconds for healthy MxEdge appliances. The endpoint is not paginated, so the call
is constant-time with respect to org size. Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; no special
tuning is required.
**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()` for every
prompt; no secrets or full request URLs in logs; all output under `data/`;
Windows-safe path joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public static method (~22 lines) on the existing
`OrgConfigExporter` class -- the same class that owns the related
`OrgConfigExporter.mx_edges()` listing export. One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (`getOrgMxEdge` -> `natural_pk` on `id`). One new
CSV/SQLite table `org_mxedge_detail`. One menu registration entry. One README operation
table row. One CHANGELOG line. No new dependencies, modules, packages, or directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `get_org_mxedge_detail()` stays under 25 lines,
  takes <=3 parameters (`self` or `cls`-bound static, `org_id`, `mxedge_id`), and
  contains <=5 logical blocks (validate input -> log INFO -> SDK call -> flatten ->
  DataExporter call). Hierarchy is unchanged: one new method on an existing class. No
  new packages, modules, or top-level constants are added. The flattening step is a
  single `flatten_dict()` call against the existing helper -- no new nested loops.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgConfigExporter` class (line ~11982 in `MistHelper.py`), the same class that owns
  `mx_edges()` (line ~12007). No standalone wrapper function is introduced. The menu
  dispatch references the class method directly. Variable names use full words
  (`mxedge_record`, `flattened_row`, `output_filename`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_mxedge_detail:org_id"`, `"org_mxedge_detail:mxedge_id"`) so
  SSH / container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET); no typed destructive-confirmation gate is required.
  Both `org_id` and `mxedge_id` are validated against the Mist UUID regex before the
  SDK call; on validation failure the method logs a warning and returns early without
  contacting the API. API token comes from `.env` via the existing `mistapi.APISession`
  and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- The standard pipeline applies without modification:
  `python -m py_compile MistHelper.py` -> `python -m ruff check MistHelper.py` ->
  `python -m black --check MistHelper.py` -> commit with `version YY.MM.DD.HH.MM - add
  menu 235 getOrgMxEdge` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs validation + multi-arch build ->
  `gh run watch <run-id>` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> `podman stop misthelper ; podman rm
  misthelper` -> `podman run -d ...` -> `podman ps` verification. No deviation.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` / `%d` style formatting,
  never f-strings, so log shipping stays cheap. `INFO` is emitted before the API call
  ("Fetching MxEdge detail for org %s mxedge %s"); `DEBUG` after with a one-line
  result summary ("MxEdge detail: id=%s model=%s mxcluster_id=%s tunterm_registered=%s");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception via
  `logging.exception(...)` so the full traceback lands in the per-host log without
  leaking the API token. The MxEdge `magic` field and any password-like fields
  (`mist_password`, `root_password`) are explicitly redacted before the DEBUG line and
  before the flatten step.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line of the new method, the new PK strategy
  dictionary entry, and the menu registration line carries an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented
  adjacent lines in the touched block (the existing MxEdge export cluster around
  `OrgConfigExporter.mx_edges()`) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before each prompt, after each prompt, before the SDK call, after
  the SDK call with a summary count of populated top-level fields, before flatten,
  after flatten with row width, before write, after write. The DataExporter call emits
  its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/615-mist-get-org-mx-edge/
|-- plan.md                            # This file
|-- research.md                        # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md                      # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md                      # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_mx_edge.md             # Phase 1 - HTTP + SDK contract
`-- tasks.md                           # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method get_org_mxedge_detail() on OrgConfigExporter class
                         # (line ~12007 neighborhood, adjacent to mx_edges()), one new
                         # entry in ENDPOINT_PRIMARY_KEY_STRATEGIES for getOrgMxEdge,
                         # one new menu dispatch entry at op 235. No new modules.
README.md                # Operation count bump + new row in the menu table for op 235
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 235
data/                    # Runtime output target. Existing dir. No schema migration
                         # beyond the new SQLite table `org_mxedge_detail` created on
                         # first run by DataExporter.
documentation/api/orgs/  # Reference docs already present:
  GET_orgs_org_id_mxedges_mxedge_id.md
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public static method on the existing `OrgConfigExporter` class in `MistHelper.py` (the
same class that owns the other MxEdge listing exports). The proposed menu number is
**235**, chosen because the in-flight specs in this batch are landing in the
220-250 range for safe org reads (e.g. spec 535 proposes 230). 235 sits below the
resource-intensive cluster (97-101) when normalized and reserves a clean slot adjacent
to the existing `OrgConfigExporter.mx_edges()` listing export. If 235 collides with a
sibling in-flight branch at task-generation time, the next free integer in the same
cluster is used and the README/CHANGELOG numbers are updated in the same PR.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/get_org_mx_edge.md`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary insert is a single block; the flatten
  step is one `flatten_dict()` call against the existing helper.
- **Principle II (Class-Based)**: PASS -- All new code lives on `OrgConfigExporter`.
  No wrappers introduced. Helper functions, if needed, become private methods on the
  same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call. Password-like fields are redacted
  before logging and flatten.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token or password-like fields.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 `quickstart.md` shows the
  expected comment density on every executable line, including the PK strategy entry
  and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 `quickstart.md` enumerates the
  before/after log pairs for every meaningful action (prompts, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
