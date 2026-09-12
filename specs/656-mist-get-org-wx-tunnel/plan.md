# Implementation Plan: GetOrgWxTunnel Menu Item

**Branch**: `656-mist-get-org-wx-tunnel` | **Date**: 2026-07-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/656-mist-get-org-wx-tunnel/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/wxtunnels/{wxtunnel_id}` (operationId `getOrgWxTunnel`) to
retrieve full configuration details for a single WxLAN tunnel. The menu item prompts the
user for both an `org_id` and a `wxtunnel_id` via `safe_input()`, invokes the mistapi
SDK at `mistapi.api.v1.orgs.wxtunnels.getOrgWxTunnel()`, flattens the returned JSON
(including the nested `dmvpn`, `ipsec`, and `sessions` sub-objects) into a parent row
plus zero or more session rows, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **59** -- the last available slot in the Safe Org
Exports / Templates block (37-59) directly adjacent to related org-configuration
retrieval operations, before the Interactive Safe range at 60+.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using known org and wxtunnel IDs from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65,
90-100) is unaffected -- new item 59 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint returns
a single JSON object (one WxTunnel) with no pagination. Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; this endpoint
is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets (API
token, IPsec pre-shared key) in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`). The `ipsec.psk` field in the response is treated as a
secret and MUST be redacted before any log emission.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`TemplateExportUtils` class (the class that owns org-template retrieval operations such
as WLAN templates, network templates, and RF templates -- WxTunnels are a template-class
org resource). One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` covering two logical
tables (`org_wxtunnels` + `org_wxtunnel_sessions`). One menu registration entry, one
README operation-count bump, one CHANGELOG line. No new dependencies, no new modules,
no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_wx_tunnel()` stays under 25 lines,
  takes <=3 parameters (`self`, `org_id`, `wxtunnel_id`), and contains <=5 logical
  blocks (prompt org -> prompt tunnel -> API call -> flatten parent + sessions ->
  DataExporter calls). Hierarchy is unchanged: one new method on an existing class. Two
  small private helpers (`_flatten_wxtunnel_row`, `_flatten_wxtunnel_sessions`) may be
  added, each staying under 25 lines and 5 blocks.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `TemplateExportUtils` class (the same class that owns adjacent org template retrieval
  exports for WLAN templates, network templates, and RF templates). No standalone
  wrapper function is introduced. The menu dispatch in the main loop references the
  class method directly. Variable names use full words (`wxtunnel_row`,
  `session_rows`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_wx_tunnel:org_id"`, `"org_wx_tunnel:wxtunnel_id"`) so SSH
  and container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is required.
  Both UUIDs are validated against the Mist UUID shape via `is_valid_uuid()` before the
  API call; on validation failure the method logs a warning and returns early. API
  token comes from `.env` via the existing `mistapi.APISession` and is never logged.
  The response `ipsec.psk` field is redacted to the string `"<redacted>"` before any
  log emission and before write to CSV / SQLite.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 59 getOrgWxTunnel` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching WxTunnel %s for org %s"); `DEBUG` after the
  call with a redacted summary ("WxTunnel name=%s use_udp=%s sessions=%d dmvpn=%s
  ipsec_enabled=%s psk=<redacted>"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets, tokens,
  full request URLs, or IPsec pre-shared keys are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the two private
  flatteners, the new PK strategy dictionary entry, and the menu registration line will
  carry an inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched block (the existing template-export menu
  cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before each `safe_input()` prompt, `logging.info(...)` before the SDK call, the call
  itself, `logging.debug(...)` after with a redacted result summary,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten with counts,
  `logging.info(...)` before each DataExporter write, `logging.debug(...)` after each
  write. The DataExporter call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/656-mist-get-org-wx-tunnel/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_wx_tunnel.md    # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on TemplateExportUtils class + PK strategy entries
                         # + menu 59 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 59
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 59 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables auto-created on first
                         # write by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `TemplateExportUtils` class in `MistHelper.py`. The menu number
proposal is **59**, chosen because operations 37-59 form the Safe Org Exports /
Templates cluster and 59 is the last available slot in that cluster before the
Interactive Safe block at 60. The number is provisional -- at `/speckit.tasks` time,
MistHelper.py is grep'd for the latest allocated menu integer and 59 is shifted forward
if a conflict exists with an in-flight feature branch.

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
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The two
  private flatteners are each single-purpose and small. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary receives two inserts (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `TemplateExportUtils`. No
  wrappers introduced. Flattening helpers are private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. Both UUIDs are validated before the SDK call. `ipsec.psk` redaction is
  documented in `data-model.md`.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token or the IPsec PSK.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entries and
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt org, prompt tunnel, API
  call, flatten parent, flatten sessions, export parent, export sessions).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
