# Implementation Plan: GetMspOrg Menu Item

**Branch**: `584-mist-get-msp-org` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/584-mist-get-msp-org/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}/orgs/{org_id}` (operationId `getMspOrg`) to retrieve the
configuration and metadata of a single organization managed by a Managed Service
Provider (MSP). The menu item prompts the user for an `msp_id` and `org_id` via
`safe_input()` (defaulting from `.env` where available), invokes the `mistapi` SDK
once, flattens the single returned JSON object into one row, and persists it via
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the org UUID for clean SQLite upserts on
repeated runs. The new operation is proposed as menu number **94** -- the next
available slot in the Safe Org Exports cluster adjacent to other MSP- and org-level
config reads. Final number reconciled at `/speckit.tasks` time if a collision exists.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints section).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, optional `MIST_MSP_ID`, and
optional `MIST_ORG_ID` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback. CSV files land in `data/`. Polyglot
ArangoDB + Redis containers handle the graph + cache backend when configured.
**Testing**: `python MistHelper.py --test` exercises the menu item non-
interactively against the MSP/org pair configured in `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- new item 94 sits inside the standard test sweep.
**Target Platform**: Windows 11 + venv for local development; Podman Linux
container (`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and
SSH-on-port-2200; both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
MSP-managed orgs (the endpoint is non-paginated and the response is a single small
JSON object). Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json`
continue to govern back-off; this endpoint is light enough that no special tuning
is required.
**Constraints**: ASCII-only logging; `safe_input()` for every user prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); 5-Item Rule on the new method (<=25 lines, <=5
params, <=5 nested blocks).
**Scale/Scope**: One new public menu method (~22 lines) on a new or existing
`MspExportUtils` class, one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one
new SQLite table (`msp_org`), one menu registration entry, one README operation-
count bump, one CHANGELOG line. No new third-party dependencies, no new modules
or directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_msp_org_details()` stays under
  25 lines, takes <=3 parameters (`self`, `msp_id`, `org_id`), and contains <=5
  logical blocks (prompt msp_id -> prompt org_id -> validate -> API call ->
  flatten + DataExporter call). Hierarchy is unchanged: one new method on a
  single class (extending `OrgExportUtils` or, if MSP-specific helpers grow, a
  sibling `MspExportUtils` class -- decision finalized in Phase 1 once existing
  MSP-related methods are surveyed). No new packages, modules, or top-level
  constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a semantically
  named class (`MspExportUtils` if created, else co-located on the existing
  `OrgExportUtils` if it already hosts MSP-org reads). No standalone wrapper
  function is introduced. The menu dispatch in the main loop references the
  class method directly. Variable names use full words (`msp_org_row`,
  `apisession`) -- no single-letter iterators in user-facing code.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"msp_org:msp_id"`, `"msp_org:org_id"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is
  required. Both UUIDs are validated against the existing `is_valid_uuid()`
  helper before the API call; on validation failure the method logs a `WARNING`
  and returns early. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 94 getMspOrg` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching MSP-managed org details for
  msp %s org %s"); `DEBUG` after the call with summary fields ("MSP org: name=%s
  msp_name=%s session_expiry=%s"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with traceback via `logging.exception`. No secrets,
  tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an inline
  comment that explains *why* the line exists, not merely *what* it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution.
  Any uncommented adjacent lines in the touched block (the existing MSP / org-
  config menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each `safe_input()` prompt, `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a
  result summary, `logging.info(...)` before flatten + write, `logging.debug(...)`
  after with row count. The `DataExporter` call already emits its own per-
  backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/584-mist-get-msp-org/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_msp_org.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on MspExportUtils (or OrgExportUtils) class +
                         # PK strategy entry + menu 94 registration. No new modules;
                         # same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 94
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 94
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run
                         # by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on a semantically named class. Implementation will first grep
`MistHelper.py` for the existing MSP method footprint: if a `MspExportUtils`
class already exists, the new method is added there; otherwise the new method is
co-located on `OrgExportUtils` and an `MspExportUtils` class is introduced only
when a second MSP-related method lands (per Constitution Principle II's no-
premature-abstraction rule). The menu number proposal is **94**, chosen because
operations 51-93 are the Safe Org Exports / SLE cluster and 95 is already
proposed by feature 500; 94 is the next free integer below the resource-
intensive block at 96-101 and well away from the destructive block at 154-194.
The full menu list will be re-verified at task generation time and the number
shifted forward if a conflict exists.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/get_msp_org.md`), the seven principles are re-
evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary receives a single new entry, no
  level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on a single semantic
  class (`MspExportUtils` or `OrgExportUtils`). No wrappers introduced. If a
  helper for flattening grows past five lines, it is added as a private method
  on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. Both UUIDs are validated before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
