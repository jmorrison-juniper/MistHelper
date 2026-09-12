# Implementation Plan: GetMspAdmin Menu Item

**Branch**: `581-mist-get-msp-admin` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/581-mist-get-msp-admin/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}/admins/{admin_id}` (operationId `getMspAdmin`) to fetch the
full profile, contact info, and privilege list of a single MSP administrator. The new
menu method prompts the user for `msp_id` and `admin_id` via `safe_input()`, calls the
`mistapi` SDK, splits the response into a flat admin-summary row plus zero-or-more
per-privilege rows, and persists both via `DataExporter.write_with_format_selection()`
so CSV, SQLite, and ArangoDB+Redis backends receive consistent output. Two new entries
are registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean upserts on repeated polls.
The new operation is proposed as menu number **57** -- the next available slot inside
the Safe Org Exports / MSP cluster (1-59 range), well below the resource-intensive and
destructive blocks.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (loads
`MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; the polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using the `MIST_MSP_ID` / `MIST_ADMIN_ID` values from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- proposed menu 57 sits inside the default sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds (the endpoint is
non-paginated and returns one JSON object). Adaptive delay metrics in `delay_metrics.json`
and `tuning_data.json` continue to govern back-off; this endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); class-based hierarchy (no wrappers).
**Scale/Scope**: One new public menu method (~22 lines) on a new `MspAdminExportUtils`
class (no existing MSP admin class to extend -- the constitution forbids wrapper
functions, and the closest existing MSP code lives in unrelated MSP org-membership
exports). Two new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`; two new SQLite tables
(`msp_admins` and `msp_admin_privileges`); one menu registration line; one README
operation-count bump; one CHANGELOG line. No new dependencies, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_msp_admin()` stays under 25 lines,
  takes <=3 parameters (`self`, `msp_id`, `admin_id`), and contains <=5 logical blocks
  (prompt for msp_id -> prompt for admin_id -> API call -> flatten summary + privileges
  -> DataExporter writes). Hierarchy: one new class `MspAdminExportUtils` with one
  public method and two private flatten helpers (`_flatten_admin_summary`,
  `_flatten_admin_privileges`), each well below the 5-children-per-level cap. No new
  packages or top-level constants are introduced beyond two dict entries in the existing
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` literal.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `MspAdminExportUtils` class, modeled after the existing `*ExportUtils` classes
  (e.g. `LicenseExportUtils`, `SiteExportUtils`). A new class is justified because no
  existing class owns MSP-admin endpoints -- adding the method to an unrelated MSP class
  would violate single responsibility. No standalone wrapper functions are introduced.
  Variable names use full words (`admin_record`, `privilege_row`, `scope_target`) --
  no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input flows through `safe_input()` with explicit
  `context=` strings (`"msp_admin:msp_id"`, `"msp_admin:admin_id"`) so SSH and container
  EOF exits cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate (e.g. `Type 'UPGRADE'`) is
  required. Both UUIDs are validated via the existing `is_valid_uuid()` helper before
  the API call; on validation failure the method logs a `WARNING` and returns early.
  API token loads from `.env` via `mistapi.APISession` and is never logged. The
  endpoint exposes admin contact info (email, phone) -- the implementation logs only
  `admin_id`, never raw PII fields, at any log level.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 57 getMspAdmin` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the SDK call ("Fetching MSP admin %s for MSP %s"); `DEBUG` after
  the call with non-PII counts ("Admin record: role=%s privilege_count=%d via_sso=%s");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full
  traceback via `logging.exception`. PII fields (`email`, `phone`, `phone2`,
  `first_name`, `last_name`) are persisted to backends but never written to log
  output. The API token is never logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, both helper methods,
  the two new PK strategy dictionary entries, and the menu registration line will
  carry an inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  Safe Org Exports menu cluster around the proposed insertion point) get comments
  added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before each prompt, `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a non-PII summary, `logging.info(...)` before each
  flatten, `logging.debug(...)` after each flatten with the row count,
  `logging.info(...)` before each DataExporter write. The DataExporter call already
  emits its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. The Complexity Tracking table is
intentionally empty at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/581-mist-get-msp-admin/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registrations
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_msp_admin.md # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New MspAdminExportUtils class with one public menu method
                         # (export_msp_admin) and two private flatten helpers, plus two
                         # new entries in ENDPOINT_PRIMARY_KEY_STRATEGIES and one menu
                         # 57 registration line. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 57
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 57
data/                    # Runtime output target (existing dir). DataExporter creates
                         # the two new SQLite tables on first write via CREATE TABLE
                         # IF NOT EXISTS; no schema migration required beyond the two
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entries.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a public
method on a new `MspAdminExportUtils` class in `MistHelper.py`. A new class -- not a
new method on an existing class -- is justified because no existing class owns
MSP-admin read operations; co-locating MSP admin logic in a single class follows the
established `*ExportUtils` pattern (e.g. `LicenseExportUtils`, `SiteExportUtils`) and
keeps future MSP-admin endpoints (`listMspAdmins`, `updateMspAdmin`, etc.) clustered
in one named object rather than scattered across unrelated MSP code. The menu number
proposal is **57**, chosen because operations 1-59 are the Safe Org Exports cluster
and 57 is the next available integer in the MSP / org-admin sub-band, far from the
resource-intensive (97-101, 153), WebSocket (102-123), interactive (124-152), and
destructive (154-194) clusters. The full menu list is re-verified at task generation
time; if 57 collides with an in-flight feature branch, the next free integer in the
same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/get_msp_admin.md`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. Each of the
  two flatten helpers is a single comprehension under 10 lines. The two new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries are simple dict inserts (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All new work lives on the new
  `MspAdminExportUtils` class. No wrappers introduced. Flatten helpers are private
  methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only with no destructive side effect. `safe_input()` is the documented prompt
  path. Both UUIDs are validated before the SDK call. PII handling is documented in
  the contract (persist to data backends, never to logs).
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting, never include the API token, and never echo PII
  fields like `email`, `phone`, or names at any log level.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the two PK strategy entries
  and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (each prompt, the API call,
  each flatten, each export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
