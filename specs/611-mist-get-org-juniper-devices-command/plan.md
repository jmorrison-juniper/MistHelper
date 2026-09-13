# Implementation Plan: getOrgJuniperDevicesCommand Menu Item

**Branch**: `611-mist-get-org-juniper-devices-command` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/611-mist-get-org-juniper-devices-command/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/ocdevices/outbound_ssh_cmd` (operationId
`getOrgJuniperDevicesCommand`) to retrieve the per-org outbound SSH + NETCONF
bootstrap command string that Juniper OC (OpenConfig) devices use to phone home
to Mist. The menu item prompts the user for an `org_id` (defaulted from `.env`)
via `safe_input()`, optionally prompts for a `site_id` (used by Mist for proxy
checking and automatic site assignment), invokes the `mistapi` SDK once,
augments the single-field `{cmd: "..."}` response with the supplied org/site
identifiers plus a retrieval timestamp, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs.
The new operation is proposed as menu number **58**, the next available slot in
the Misc Safe Org Exports cluster (56-59).

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers serve as the graph + cache
backend when configured. New SQLite table:
`org_juniper_devices_outbound_ssh_cmd`.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- new item 58 sits inside the default test
sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=2 seconds for a
typical org (the endpoint is non-paginated and the response is a single JSON
object with one string field). Adaptive delay metrics in `delay_metrics.json`
and `tuning_data.json` continue to govern back-off; this endpoint is light
enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs (the returned `cmd` string itself contains a per-org OC
bootstrap snippet -- it is operationally sensitive but not a long-term
credential, so it is written to `data/` like any other API response, never to
the application log); all output under `data/`; Windows-safe path joining via
`os.path.join` or `pathlib.Path`.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgDevicesExportUtils` class (or the most adjacent existing org-devices
exporter class -- verified at task generation), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV/SQLite table
(`org_juniper_devices_outbound_ssh_cmd`), one menu registration entry, one
README operation-count bump, one CHANGELOG line. No new dependencies, no new
modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_juniper_devices_outbound_ssh_cmd()` stays under 25 lines, takes
  <=3 parameters (`self`, `org_id`, `site_id`), and contains <=5 logical
  blocks (prompt -> SDK call -> flatten one row -> DataExporter call ->
  return). Hierarchy is unchanged: one new method on an existing class. No
  new packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgDevicesExportUtils` class (the same class that owns the other
  org-devices read-only exporters). No standalone wrapper function is
  introduced. The menu dispatch in the main loop references the class method
  directly. Variable names use full words (`outbound_ssh_cmd`,
  `juniper_command_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings
  (`"org_juniper_devices_outbound_ssh_cmd:org_id"`,
  `"org_juniper_devices_outbound_ssh_cmd:site_id"`) so SSH / container EOF
  exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is
  required. The supplied `org_id` (and `site_id` if provided) is validated
  against the Mist UUID shape before the API call; on validation failure the
  method logs a warning and returns early. The API token comes from `.env`
  via the existing `mistapi.APISession` and is never logged. The returned
  `cmd` value contains an OC bootstrap snippet -- it is written to `data/`
  output but never to the application log.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification:
  `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check` ->
  commit with
  `version YY.MM.DD.HH.MM - add menu 58 getOrgJuniperDevicesCommand` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style
  formatting. `INFO` is emitted before the API call ("Fetching outbound SSH
  command for org %s (site=%s)"); `DEBUG` after the call with a length-only
  summary ("Received cmd payload: length=%d"); `WARNING` on 404 / missing
  `cmd` field; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or the cmd string body are
  logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line carries an inline
  comment that explains *why* the line exists, not merely what it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution.
  Any uncommented adjacent lines in the touched block (the existing
  org-devices export cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a length-only result summary, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten, `logging.info(...)` before write,
  `logging.debug(...)` after write. The DataExporter call already emits its
  own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/611-mist-get-org-juniper-devices-command/
|-- plan.md              # This file
|-- spec.md              # Pre-existing feature spec (not modified)
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_juniper_devices_command.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgDevicesExportUtils class + PK strategy
                         # + menu 58 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir; new SQLite table
                         # org_juniper_devices_outbound_ssh_cmd auto-created on first
                         # run by DataExporter)
documentation/api/orgs/GET_orgs_org_id_ocdevices_outbound_ssh_cmd.md
                         # Enriched per-endpoint doc (already exists; the
                         # authoritative input for this plan)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `OrgDevicesExportUtils` class in
`MistHelper.py` (the same class that owns other org-devices exports). If task
generation reveals no such class, the implementer hosts the method on the most
adjacent existing exporter class (e.g., `OrgInventoryExportUtils`) -- adding a
new class is explicitly avoided to preserve the Class-Based Architecture
principle's "no new top-level structures without justification" rule. The menu
number proposal is **58**, chosen because operations 56-59 are the Misc safe
org exports slot and 58 is the next available integer adjacent to the existing
device/inventory exporters. The full menu list will be re-verified at task
generation time; if 58 collides with an in-flight feature branch, the next
free integer in the same cluster (59) is used.

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
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `OrgDevicesExportUtils`. No wrappers introduced. The single-row flatten is
  inline; if it ever exceeds 5 lines it becomes a private method on the same
  class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms
  the endpoint is GET only, with no destructive side effect. `safe_input()`
  is the documented prompt path. UUID validation happens before the SDK
  call. The returned `cmd` is treated as data (written to `data/` files
  only) and never logged.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting, never include the API token, and never
  include the `cmd` body itself (only its length).
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows
  the expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action (prompt,
  API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
