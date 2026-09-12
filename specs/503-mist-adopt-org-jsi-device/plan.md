# Implementation Plan: adoptOrgJsiDevice Menu Item

**Branch**: `503-mist-adopt-org-jsi-device` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/503-mist-adopt-org-jsi-device/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/jsi/devices/outbound_ssh_cmd` (operationId
`adoptOrgJsiDevice`) to retrieve the outbound-SSH adoption command string used when
onboarding Juniper Secure Infrastructure (JSI) devices to an organization. The menu
method prompts for an `org_id` via `safe_input()` (with `MIST_ORG_ID` from `.env` as
the default), invokes the `mistapi` SDK once, captures the returned `cmd` string,
flattens the single-key payload into one MistHelper-owned row (`org_id`, `cmd`,
`polled_at_utc`), and persists through `DataExporter.write_with_format_selection()` so
CSV, SQLite, and ArangoDB+Redis backends all receive consistent output. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed by `org_id` for clean upserts on
re-poll. The new operation is proposed as menu number **96** -- the next contiguous
integer in the Safe Org Exports cluster directly after the spec 500 license/claim
addition at 95, and well below the destructive block at 154-194.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST`, `MIST_API_TOKEN`, and optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB +
Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using the org from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. The
heavy/destructive skip list (14, 18, 63-65, 90-100) is unaffected -- new item 96 sits
inside the resource-intensive band (97-101 + 153) edge but the call itself is a single
small GET so it executes as part of the default sweep without special handling.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=2 seconds (response body is a
single `cmd` string -- tens to hundreds of bytes). No pagination. Adaptive delay metrics
in `delay_metrics.json` and `tuning_data.json` continue to govern back-off; this endpoint
is light enough that no endpoint-specific tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; the returned `cmd`
string may contain sensitive bootstrap material so it is written to `data/` like any
other Mist payload but is never echoed to stdout and is never included in log messages
above `DEBUG`; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~15 lines) on a new (or reused)
`JsiExportUtils` class -- see Structure Decision below; one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`; one new SQLite table (`org_jsi_outbound_ssh_cmd`);
one menu registration entry; one README operation-count bump; one CHANGELOG line. No
new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_jsi_outbound_ssh_cmd()` stays
  under 25 lines, takes <=2 parameters (`self`, `org_id`), and contains <=4 logical
  blocks (prompt -> validate -> API call -> flatten + DataExporter call). Hierarchy is
  unchanged: one new method on an existing or new class within the existing
  `MistHelper.py` monolith. No new packages, modules, or top-level constants beyond the
  single `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict insert.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a JSI-export class
  (either reusing `OrgConfigExportUtils` if it already owns adjacent JSI calls or
  introducing a new `JsiExportUtils` class -- the choice is finalized in
  `research.md` Task 4 once the source tree is inspected). No standalone wrapper
  function is introduced. The menu dispatch references the class method directly.
  Variable names use full words (`outbound_ssh_cmd_row`, `cmd_string`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input flows through `safe_input()` with an explicit
  `context="org_jsi_outbound_ssh_cmd:org_id"` tag so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no
  typed destructive-confirmation gate is required. `org_id` is validated against the
  Mist UUID shape (`is_valid_uuid()`) before the API call; on validation failure the
  method logs a `WARNING` and returns early. The API token comes from `.env` via
  `mistapi.APISession` and is never logged. The `cmd` string returned by the API may
  contain bootstrap material; it is persisted to `data/` like other payloads but is
  never written to stdout and is never logged at `INFO` or above.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 adoptOrgJsiDevice` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification. See `quickstart.md` for the full command list.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching JSI outbound SSH cmd for org %s"); `DEBUG`
  after the call with the length of the returned command string only ("Received cmd
  length=%d") -- the command itself is never echoed to a log; `WARNING` on 404 or
  empty payload; `ERROR` on unexpected exception with traceback via
  `logging.exception`. No secrets, tokens, request URLs, or `cmd` content are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict entry, and the menu registration line carries
  an inline comment that explains *why* the line exists, not merely what it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution. Any
  adjacent uncommented lines in the touched block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a length count,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write. The DataExporter call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/503-mist-adopt-org-jsi-device/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- adopt_org_jsi_device.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the JSI export class + PK strategy entry +
                         # menu 96 registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir); new SQLite table
                         # org_jsi_outbound_ssh_cmd is created on first write by DataExporter
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on a JSI-focused class in `MistHelper.py`. If `MistHelper.py` already
hosts a JSI export class (e.g., `JsiExportUtils` or `OrgJsiExportUtils`), the method
attaches there. If no such class exists, a new `JsiExportUtils` class is introduced and
documented in Research Task 4 -- this remains within Constitution Principle II (a new
class is preferred over a standalone wrapper function). The menu number proposal is
**96**, chosen because operations 51-95 are the Safe Org Exports / Org-License / SLE
cluster (with spec 500 taking 95) and 96 is the next contiguous integer below the
resource-intensive block at 97-101. The full menu list is re-verified at task
generation time; if 96 collides with another in-flight feature branch, the next free
integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/adopt_org_jsi_device.md`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=4 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary gets a single insert, no structural
  change to existing levels.
- **Principle II (Class-Based)**: PASS -- All work lives on a single JSI-focused
  class. No wrappers introduced. The flatten step is inline (3 lines) so no helper
  method is required; if extended later it becomes a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call. The `cmd` payload is treated as
  sensitive and excluded from non-DEBUG logs.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting, never include the API token, and never include the `cmd`
  string content (only its length).
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
