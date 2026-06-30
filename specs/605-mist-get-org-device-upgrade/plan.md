# Implementation Plan: GetOrgDeviceUpgrade Menu Item

**Branch**: `605-mist-get-org-device-upgrade` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/605-mist-get-org-device-upgrade/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}` (operationId
`getOrgDeviceUpgrade`) to retrieve the full status of a single multi-device
firmware upgrade job, including per-site progress and per-device MAC lists
grouped by phase (`downloaded`, `downloading`, `failed`, `rebooted`,
`upgraded`, etc.). The menu item prompts the user for `org_id` (default from
`.env`) and the `upgrade_id` (no default -- the user must supply the UUID
returned by `listOrgDeviceUpgrades`), invokes the `mistapi` SDK exactly once,
flattens the single response object into one summary row plus N per-site
detail rows, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. Two new entries are
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (one per table) for clean
SQLite upserts on repeated polling. The new operation is proposed as menu
number **96** -- the next available slot in the safe viewer / read-only
firmware-status cluster (92-96), sitting adjacent to the existing firmware
status checker (`FirmwareUpgradeStatusChecker` at MistHelper.py line 18421)
and well clear of the destructive firmware-write block at 154-160.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK --
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/` (one summary CSV plus one per-site detail CSV per invocation);
polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org and a recently completed upgrade UUID
from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`.
Heavy / destructive skip list (14, 18, 63-65, 90-100) is partially adjacent:
proposed menu 96 sits just inside the skipped range, so the test harness
override flag (`--menu 96`) is required to run it under `--test`.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH on port
2200; both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds; the
endpoint is non-paginated and returns one JSON object regardless of fleet
size (the per-device MACs are inlined arrays). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; the
endpoint doc explicitly warns "poll periodically rather than continuously"
so no auto-loop is added at this stage.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); `upgrade_id` validated against the Mist
UUID shape before the SDK call.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`FirmwareUpgradeStatusChecker` class, two new entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (`getOrgDeviceUpgrade` summary +
`getOrgDeviceUpgrade_site_details` detail), two new CSV/SQLite tables
(`org_device_upgrade` and `org_device_upgrade_site_details`), one menu
registration entry, one README operation-count bump, one CHANGELOG line.
No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_device_upgrade_detail()` stays under 25 lines, takes <=3
  parameters (`self`, `org_id`, `upgrade_id`), and contains <=5 logical
  blocks (prompt -> UUID validate -> SDK call -> flatten summary + per-site
  detail -> DataExporter write). Hierarchy is unchanged: one new method on
  an existing class. No new packages, modules, or top-level constants are
  introduced. The per-site flatten is a single list comprehension; if it
  grows past 5 lines during implementation, it is extracted to a private
  helper `_flatten_upgrade_site_row()` on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `FirmwareUpgradeStatusChecker` class (MistHelper.py line 18421), which
  already owns the firmware-upgrade status read paths. No standalone wrapper
  function is introduced. The menu dispatch in the main loop references the
  class method directly. Variable names use full words (`upgrade_record`,
  `site_upgrade_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()`
  with explicit `context=` strings (`"org_device_upgrade:org_id"`,
  `"org_device_upgrade:upgrade_id"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP
  GET), so no typed destructive-confirmation gate is required. Both `org_id`
  and `upgrade_id` are validated against the Mist UUID shape before the API
  call; on validation failure the method logs a warning and returns early.
  API token comes from `.env` via the existing `mistapi.APISession` and is
  never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 96
  getOrgDeviceUpgrade` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style
  formatting. `INFO` is emitted before the API call ("Fetching device
  upgrade detail for org %s upgrade %s"); `DEBUG` after the call with
  summary counts ("Upgrade detail: strategy=%s target=%s sites=%d total=%d");
  `WARNING` on 404 / empty payload ("Upgrade %s not found or empty");
  `ERROR` on unexpected exception via `logging.exception`. No secrets,
  tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the two new
  PK strategy dictionary entries, and the menu registration line will carry
  an inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing `FirmwareUpgradeStatusChecker` cluster) get comments added in the
  same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a result count, `logging.info(...)`
  before flatten, `logging.debug(...)` after flatten, `logging.info(...)`
  before write, `logging.debug(...)` after write. The DataExporter call
  already emits its own per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/605-mist-get-org-device-upgrade/
|-- plan.md              # This file
|-- spec.md              # Feature specification (already authored)
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_device_upgrade.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on FirmwareUpgradeStatusChecker class
                         # (line 18421) + two PK strategy entries near
                         # listOrgDeviceUpgrades (line 3983) + menu 96
                         # registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table
                         # for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing
                         # menu 96 addition
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the two new SQLite
                         # tables created on first run by DataExporter)
documentation/api/utilities/GET_orgs_org_id_devices_upgrade_upgrade_id.md
                         # Enriched endpoint reference (already on disk;
                         # consulted by Phase 0 research, not modified)
```

**Structure Decision**: Single-file monolith. The new menu item is added as
a new public method on the existing `FirmwareUpgradeStatusChecker` class in
`MistHelper.py` (the same class that owns the firmware-upgrade status read
paths, sibling to `FirmwareManager`). The menu number proposal is **96**,
chosen because operations 92-96 are the safe Viewers cluster (per
`.github/copilot-instructions.md` Menu Categories table) and 96 is the next
available integer that does not collide with reference spec 500's proposed
**95**. The full menu list will be re-verified at task generation time; if
96 collides with another in-flight feature branch (e.g. a sibling 6xx
spec), the next free integer in the same Viewers cluster (then the
80-91 Stats cluster) is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks.
  Each `ENDPOINT_PRIMARY_KEY_STRATEGIES` insert is a single dictionary
  entry (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `FirmwareUpgradeStatusChecker`. No wrappers introduced. The optional
  flatten helper, if needed, is a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design
  are ASCII-only with `%s` formatting and never include the API token or
  full request URL.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including each PK
  strategy entry and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, UUID
  validation, SDK call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
