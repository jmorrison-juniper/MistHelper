# Implementation Plan: countMspAuditLogs Menu Item

**Branch**: `504-mist-count-msp-audit-logs` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/504-mist-count-msp-audit-logs/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}/logs/count` (operationId `countMspAuditLogs`) to return a
distinct-value count breakdown of MSP-scoped audit log entries. The new menu item prompts
the user for an `msp_id` (defaulting to the currently selected MSP from `selected_msp`
when present) via `safe_input()`, then prompts for the optional `distinct` field
(`admin_name`, `message`, `org_id`, `admin_id`, or empty for the API default) and
optional `limit` (default 100). The call is dispatched through the `mistapi` SDK
(`mistapi.api.v1.msps.logs.countMspAuditLogs`), the response is flattened into one
summary row plus N per-distinct-value rows, and the result is persisted through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **146** -- the next available slot in the
Interactive / Management cluster immediately adjacent to menu 144 (MSP-Wide Device
Inventory Export), which is the closest existing MSP-scoped read operation.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv`
(loads `MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend. Two new SQLite tables
are created on first run: `msp_audit_logs_count_summary` (one row per invocation
context) and `msp_audit_logs_count_results` (one row per distinct value returned).
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using an MSP id resolved from `selected_msp` or a `MIST_MSP_ID` `.env` override.
Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. Heavy /
destructive skip list (14, 18, 63-65, 90-100) is unaffected -- the new menu 146 sits
inside the Interactive cluster and inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both
must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical MSP
audit log volumes (the endpoint is a count aggregate, not a full log dump, and is
bounded by `limit` <= 100 by default). Adaptive delay metrics in `delay_metrics.json`
and `tuning_data.json` continue to govern back-off; this endpoint is light enough
that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); MSP-scoped endpoints must guard against absent MSP privileges
(reuse the `msp_privileges` / `selected_msp` global pattern documented around
`MistHelper.py` line 2188).
**Scale/Scope**: One new public menu method (~22 lines) on a new thin
`MSPAuditLogExporter` class placed immediately after `MSPInventoryExporter`
(`MistHelper.py` line 19380) to keep all MSP-scoped read-only exporters together. One
new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`; two new SQLite tables (summary +
results); one menu registration line; one README operation-count bump; one CHANGELOG
line. No new dependencies, no new modules, no new directories. A separate class is
chosen instead of bolting onto `MSPInventoryExporter` because the inventory exporter
fans out across all MSPs and all orgs and owns its own multi-MSP loop, whereas this
new menu is single-MSP and single-request -- coupling the two would violate the
Single-Responsibility shape implied by the Five-Item Rule.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_msp_audit_logs_count()` stays under
  25 lines, takes <=3 parameters (`self`, `msp_id`, `distinct`), and contains <=5
  logical blocks (prompt -> resolve msp_id -> API call -> flatten -> DataExporter
  call). Hierarchy is unchanged: one new method on one new small class. No new
  packages, modules, or top-level constants are introduced. The flattening step is a
  single list comprehension over `response["results"]`; if it grows past 5 lines
  during implementation it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new class
  `MSPAuditLogExporter` placed in the MSP-export region of `MistHelper.py` (just
  below `MSPInventoryExporter`). No standalone wrapper function is introduced. The
  menu dispatch in the main loop instantiates the class and calls the public method
  directly. Variable names use full words (`distinct_field`, `count_row`,
  `summary_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"msp_audit_logs_count:msp_id"`,
  `"msp_audit_logs_count:distinct"`, `"msp_audit_logs_count:limit"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. The
  resolved `msp_id` is validated against the Mist UUID shape before the API call;
  on validation failure the method logs a warning and returns early. The API token
  comes from `.env` via the existing `mistapi.APISession` and is never logged. Lack
  of MSP privileges is detected up front via the `msp_privileges` global and
  surfaces as a logged warning, not a traceback.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 146 countMspAuditLogs` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call (`"Menu #146: counting MSP audit logs for
  msp %s distinct=%s"`); `DEBUG` after the call with summary counts
  (`"countMspAuditLogs returned total=%d limit=%d results=%d"`); `WARNING` on 404 /
  empty payload or absent MSP privileges; `ERROR` on unexpected exception with full
  traceback via `logging.exception`. No secrets, tokens, MSP IDs are truncated to
  the first 8 hex chars in user-visible log lines (full UUIDs allowed at DEBUG
  level only).

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `MSPAuditLogExporter` class, the new PK strategy dictionary entry, and the menu
  registration line will carry an inline comment that explains *why* the line
  exists, not merely what it does. Blank lines, closing parentheses, and decorators
  are exempt per the Constitution. Any uncommented adjacent lines inside the
  touched menu-dispatch block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result count, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten with the per-distinct row count,
  `logging.info(...)` before write, `logging.debug(...)` after write. The
  DataExporter call already emits its own per-backend log lines; the new method
  does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/504-mist-count-msp-audit-logs/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── count_msp_audit_logs.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New MSPAuditLogExporter class (~30 lines) inserted just
                         # after MSPInventoryExporter (line ~19380). New entry in the
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES dict. New menu 146
                         # registration in the main menu dispatch table. No new
                         # modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 146
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 146
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the two new SQLite tables auto-created on
                         # first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a method
on a new small `MSPAuditLogExporter` class in `MistHelper.py`, placed in the MSP-export
region right after the existing `MSPInventoryExporter` (around line 19380). A separate
class -- not a new method on `MSPInventoryExporter` -- is chosen because the inventory
exporter owns a multi-MSP / multi-org fan-out loop, while this new feature is a
single-MSP / single-request aggregate; bundling them would push `MSPInventoryExporter`
past the Five-Item Rule's structural complexity ceiling. The menu number proposal is
**146**, chosen because (a) menu 144 is the existing MSP-Wide Device Inventory Export
and (b) menus 146-148, 150, and 151-153 are currently free in the source (verified by
`Select-String -Pattern 'Menu #14[6-8]|Menu #15[0-3]'` returning zero hits). The full
menu list will be re-verified at task generation time; if 146 collides with an
in-flight feature branch, the next free integer in the same Interactive cluster
(147, 148, 150) is used.

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

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=3 parameters, <=5 logical blocks. The PK strategy entry is
  a single dict insert (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `MSPAuditLogExporter`.
  No wrappers introduced. Flattening helpers, if needed, are added as private
  methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID validation happens before the SDK call. MSP-privilege guard
  precedes the API call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
