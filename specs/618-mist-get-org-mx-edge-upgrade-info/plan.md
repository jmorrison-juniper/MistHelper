# Implementation Plan: GetOrgMxEdgeUpgradeInfo Menu Item

**Branch**: `618-mist-get-org-mx-edge-upgrade-info` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/618-mist-get-org-mx-edge-upgrade-info/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/mxedges/versions` (operationId `getOrgMxEdgeUpgradeInfo`)
to retrieve the list of available Mist Edge firmware packages and versions for a given
organization. The menu method prompts the user for an `org_id` (defaulting to
`MIST_ORG_ID` from `.env`) and two optional filters -- `channel` (`stable` / `beta` /
`alpha`) and `distro` (e.g. `bullseye`, `buster`) -- via `safe_input()`. It calls the
`mistapi` SDK once, flattens the returned JSON array (`{default, distro, package,
version}`) into rows, and persists results through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so SQLite upserts on repeated runs do not
accumulate duplicates. The new operation is proposed as menu number **59** -- the next
free slot in the Safe Org Exports "Misc" cluster (56-59) directly adjacent to existing
Mist Edge inventory and stats operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode against the org configured in `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 59 sits inside the standard test sweep
range (heavy/destructive skip list 14, 18, 63-65, 90-100 does not affect it).
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both
must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint is
non-paginated and returns a small JSON array (tens of rows in practice), so no
special back-off tuning is required beyond the standard adaptive-delay system in
`delay_metrics.json` and `tuning_data.json`.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; API token never
logged; all output under `data/`; Windows-safe path joining via `os.path.join` or
`pathlib.Path`; `--fast` flag respected (no special handling needed -- single call,
no retries beyond the default).
**Scale/Scope**: One new public menu method (~20 lines) added to the existing
`FirmwareManager` class (the same class that owns other Mist Edge firmware
operations), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite
table (`org_mxedge_upgrade_info`), one menu registration line, one README operation
count bump, one CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_mxedge_upgrade_info()` stays under 25 lines, takes <=4 parameters
  (`self`, `org_id`, `channel`, `distro`), and contains <=5 logical blocks (prompt
  org -> prompt filters -> API call -> flatten -> DataExporter write). No new
  packages, modules, or top-level constants are introduced. If the flatten step
  grows past 5 lines during implementation, it is extracted to a private helper
  `_flatten_mxedge_upgrade_rows()` on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `FirmwareManager` class (which already owns Mist Edge and AP firmware tooling).
  No standalone wrapper function is introduced. The menu dispatch table in the
  main loop references the class method directly. Variable names use full words
  (`upgrade_row`, `channel_choice`, `distro_filter`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_mxedge_upgrade_info:org_id"`,
  `"org_mxedge_upgrade_info:channel"`, `"org_mxedge_upgrade_info:distro"`) so
  SSH / container EOF exits cleanly with code 0 and no traceback. The endpoint
  is HTTP GET only, so no typed destructive-confirmation gate is required.
  `org_id` is validated against the Mist UUID shape via `is_valid_uuid()` before
  the API call; on validation failure the method logs a `WARNING` and returns
  early. The API token is loaded from `.env` by `mistapi.APISession` and is
  never logged. Channel and distro values are passed through unmodified -- Mist
  rejects unknown values with HTTP 400, which is handled in the contract.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 59
  getOrgMxEdgeUpgradeInfo` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch <run-id>` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification. No deviations.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching Mist Edge upgrade info for
  org %s"); `DEBUG` after with the row count ("Received %d firmware
  packages"); `WARNING` on 404 / empty payload; `ERROR` on 401/403 with a
  remediation hint; full traceback via `logging.exception` only on unexpected
  exceptions. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dict entry, and the menu registration line will carry an inline
  comment explaining *why* the line exists, not merely *what* it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution.
  Any uncommented adjacent lines in the touched `FirmwareManager` block get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each `safe_input()` prompt, `logging.info(...)`
  before the SDK call, `logging.debug(...)` after the call with the row count,
  `logging.info(...)` before the flatten step, `logging.debug(...)` after the
  flatten with the resulting row count, `logging.info(...)` before the
  `DataExporter` write. The `DataExporter` itself emits per-backend log lines;
  the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/618-mist-get-org-mx-edge-upgrade-info/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates + skeleton
|-- contracts/
|   `-- get_org_mx_edge_upgrade_info.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on FirmwareManager class + PK strategy +
                         # menu 59 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 59
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 59 addition
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the new SQLite table created
                         # on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `FirmwareManager` class in `MistHelper.py`. This
class already owns the firmware/upgrade-related tooling for Mist Edges and APs,
and the new endpoint -- returning available Mist Edge firmware packages and
versions -- belongs naturally with that responsibility. The menu number proposal
is **59**, chosen because operations 56-59 are the Misc sub-cluster inside the
Safe Org Exports range (1-59), and 59 is the next free integer below the
Interactive Safe block starting at 60. The full menu list will be re-verified at
task generation time; if 59 collides with an in-flight feature branch, the next
free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All new work lives on the existing
  `FirmwareManager` class. No wrappers introduced. Flattening helper, if
  needed, is added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline
  documented in the constitution and `.github/copilot-instructions.md`.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompts, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
