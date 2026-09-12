# Implementation Plan: GetOrgAosRegisterCmd Menu Item

**Branch**: `595-mist-get-org-aos-register-cmd` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/595-mist-get-org-aos-register-cmd/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/aos/register_cmd` (operationId `getOrgAosRegisterCmd`)
to retrieve TPM-based brownfield registration CLI commands for AOS (Aruba OS) devices.
The menu item prompts the user for an `org_id` via `safe_input()`, invokes the
`mistapi` SDK once per call, captures the returned `cli_commands` string into a single
flattened row that also records the requesting org and the poll timestamp, and persists
the result through `DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated polls do not duplicate historical
registration commands. The new operation is proposed as menu number **58** -- the next
available slot in the Safe Org Exports / Misc cluster, sitting alongside the related
SSR and 128T register-command exports.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (loads
`MIST_HOST`, `MIST_API_TOKEN`, and optional `MIST_ORG_ID` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the new menu item in non-interactive
mode against the default org from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected --
the proposed menu 58 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both must
work without code change. Paths use `os.path.join` / `pathlib.Path` only.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET completes in <=5 seconds for typical responses (the
endpoint returns a single small JSON object with one string field, is non-paginated, and
has no nested arrays). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; the returned
`cli_commands` string contains a time-sensitive registration token -- it is written to
`data/` but never logged at any level (Constitution III + Spec gotcha); all output under
`data/`; Windows-safe path joining.
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`DeviceExportUtils` class (the same class that owns adjacent device-onboarding exports),
one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
(`org_aos_register_cmd`), one menu registration entry, one README operation-count bump,
one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_aos_register_cmd()` stays under
  25 lines, takes <=2 parameters (`self`, `org_id`), and contains <=4 logical blocks
  (prompt -> validate -> API call -> DataExporter call). Hierarchy is unchanged: one new
  method on an existing class. No new packages, modules, or top-level constants are
  introduced. The single flattening step is one assignment with one comprehension; if it
  grows past 5 lines during implementation, it is extracted to a private helper
  `_flatten_aos_register_cmd()` on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `DeviceExportUtils` class (the same class that owns adjacent org-device exports such
  as inventory listings and device registration helpers). No standalone wrapper function
  is introduced. The menu dispatch in the main loop references the class method
  directly. Variable names use full words (`register_command_body`,
  `aos_register_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with an
  explicit `context="org_aos_register_cmd:org_id"` so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no
  typed destructive-confirmation gate is required. Org ID is validated against the Mist
  UUID shape before the API call; on validation failure the method logs a `WARNING` and
  returns early. The returned `cli_commands` string contains a time-sensitive
  registration token: it is persisted to `data/` (which is `.gitignore`'d) but is
  **never logged at any level** -- only the org ID, response length, and HTTP status are
  logged. API token comes from `.env` via the existing `mistapi.APISession` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 58 getOrgAosRegisterCmd` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching AOS register command for org %s"); `DEBUG`
  after the call with the response length only ("AOS register command returned: length=%d
  chars"); `WARNING` on 404 / empty payload; `ERROR` on unexpected exception via
  `logging.exception`. The registration command string itself, the API token, and any
  fragment of `cli_commands` are never logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment
  explaining *why* the line exists. Blank lines, closing parentheses, and decorators
  are exempt per the constitution. Any uncommented adjacent lines in the touched block
  (the existing device-export menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the prompt, `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after the call with the response length (not content),
  `logging.info(...)` before write, `logging.debug(...)` after write. The DataExporter
  call already emits its own per-backend log lines; the new method does not duplicate
  them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/595-mist-get-org-aos-register-cmd/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_aos_register_cmd.md     # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on DeviceExportUtils class + PK strategy +
                         # menu 58 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `DeviceExportUtils` class in `MistHelper.py` (the same class that
owns adjacent org-device onboarding and inventory exports). The menu number proposal is
**58**, chosen because operations 1-59 are the Safe Org Exports cluster, with 56-59
being the Misc sub-range that holds onboarding-helper exports; placing this AOS
registration helper adjacent to its SSR / 128T cousins keeps related onboarding tooling
co-located in the menu. The full menu list is re-verified at `/speckit.tasks` time; if
58 collides with an in-flight feature branch, the next free integer in the same cluster
is used.

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
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=4 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary receives a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `DeviceExportUtils`. No
  wrappers introduced. Any future flatten helper is added as a private method on the
  same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call. The time-sensitive
  `cli_commands` string is persisted but never logged.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token or the registration command
  string. Only org ID and string length are logged.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
