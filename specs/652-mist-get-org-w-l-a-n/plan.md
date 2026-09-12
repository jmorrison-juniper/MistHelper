# Implementation Plan: getOrgWLAN Menu Item

**Branch**: `652-mist-get-org-w-l-a-n` | **Date**: 2026-07-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/652-mist-get-org-w-l-a-n/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/wlans/{wlan_id}` (operationId `getOrgWLAN`) to fetch the full
configuration document for a single org-scoped WLAN (SSID) by its UUID. The menu method
prompts the user via `safe_input()` for `org_id` (defaulting to `MIST_ORG_ID` from `.env`)
and `wlan_id`, calls `mistapi.api.v1.orgs.wlans.getOrgWLAN()` exactly once, flattens the
deeply nested response object into a single tabular row (nested arrays such as
`acct_servers`, `auth_servers`, and `coa_servers` are re-serialized to JSON strings for
CSV/SQLite compatibility, matching the pattern used by the adjacent
`listOrgWlans` exporter), and persists results through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed by the WLAN's stable UUID for clean upserts. The
new operation is proposed as menu number **96**, the next available slot in the
Interactive Safe / Viewers cluster (92-96) alongside the existing WLAN-list viewers at
menu 48, 102, and 122.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (`.env`
loading of `MIST_HOST`, `MIST_API_TOKEN`, and optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org and one WLAN UUID discovered by the adjacent `listOrgWlans`
menu item. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. The
heavy / destructive skip list (14, 18, 63-65, 90-100) does not include 96, so this
new item is exercised by the default test sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and SSH-on-2200; both
must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with the
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET completes in <=5 seconds. The endpoint returns a
single JSON object (not paginated), so no fan-out required. Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; no
endpoint-specific tuning is required.
**Constraints**: ASCII-only logging (no Unicode/emoji); `safe_input()` for every
prompt; API token loaded from `.env` and never logged; all output routed under
`data/`; Windows-safe path joining via `os.path.join()` / `pathlib.Path()`.
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`WlanExportUtils` class (same class that owns the org-list and site-list WLAN
exporters), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite
table `org_wlan_detail`, one menu registration entry, one README operation-count
bump, one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_wlan_detail()` stays under 25
  lines, takes <=3 parameters (`self`, `org_id`, `wlan_id`), and contains <=5 logical
  blocks (prompt org_id -> prompt wlan_id -> validate UUIDs -> SDK call -> flatten and
  export). Hierarchy is unchanged: one new method on an existing class. No new
  packages, modules, or top-level constants are introduced. The flattening helper
  `_flatten_wlan_row()` is added as a private method on the same class and stays
  under 25 lines by re-using the existing `flatten_dict()` utility already used by
  `listOrgWlans`.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `WlanExportUtils` class (the same class that owns the multi-WLAN list export
  invoked by menu 48). No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names
  use full words (`wlan_row`, `nested_auth_servers`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every user prompt is collected through `safe_input()` with
  explicit `context=` strings (`"org_wlan_detail:org_id"`,
  `"org_wlan_detail:wlan_id"`) so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Both `org_id` and `wlan_id` are
  validated against the Mist UUID shape via the existing `is_valid_uuid()` helper
  before any API call; on validation failure the method logs a warning and returns
  early. The API token comes from `.env` via `mistapi.APISession` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 96 getOrgWLAN`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style formatting.
  `INFO` is emitted before the API call ("Fetching WLAN detail for org %s wlan %s");
  `DEBUG` after the call with summary fields ("WLAN detail: ssid=%s enabled=%s
  auth_type=%s"); `WARNING` on 404 or empty payload; `ERROR` on unexpected
  exception with full traceback via `logging.exception`. No secrets, tokens, or
  full request URLs are logged. The `psk` and RADIUS `secret` fields present in
  the response are redacted before any DEBUG dump.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment
  that explains *why* the line exists, not merely what it does. Blank lines,
  closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched block (existing WLAN-export cluster)
  get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each prompt, `logging.info(...)` before the SDK call,
  the call itself, `logging.debug(...)` after with a summary of key fields,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten with row
  count, `logging.info(...)` before write. The `DataExporter` call already emits
  its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/652-mist-get-org-w-l-a-n/
|-- spec.md              # Feature specification (already exists, not modified)
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_w_l_a_n.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on WlanExportUtils class + PK strategy entry +
                         # menu 96 registration. No new modules; same single-file
                         # monolith. Existing flatten_dict() and DataExporter reused.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by
                         # DataExporter via ENDPOINT_PRIMARY_KEY_STRATEGIES)
documentation/api/orgs/GET_orgs_org_id_wlans_wlan_id.md
                         # Read-only source of truth for parameters and response schema
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `WlanExportUtils` class in `MistHelper.py` (the same
class that owns `listOrgWlans` and site-scoped WLAN exports). The menu number
proposal is **96**, chosen because operations 60-96 form the Interactive Safe /
Viewers cluster and 96 is the next available slot below the Resource Intensive
block that starts at 97. This placement puts a single-WLAN viewer next to related
WLAN operations without crossing into destructive territory. The final integer
is re-verified at `/speckit.tasks` time; if 96 collides with an in-flight feature
branch, the next free integer inside the 60-96 cluster is used.

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
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` addition is a single dict entry (existing
  structure), so no level-5 hierarchy explosion. The private `_flatten_wlan_row()`
  helper re-uses `flatten_dict()` and adds no new nesting.
- **Principle II (Class-Based)**: PASS -- All work lives on `WlanExportUtils`. No
  wrappers introduced. The flatten helper is a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. Both UUIDs are validated before the SDK call. RADIUS secrets and
  PSK fields are redacted from DEBUG logs by the flatten helper.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token, PSK, or
  RADIUS shared secret.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (each prompt, validation,
  API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
