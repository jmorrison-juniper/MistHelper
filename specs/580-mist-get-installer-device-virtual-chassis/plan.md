# Implementation Plan: GetInstallerDeviceVirtualChassis Menu Item

**Branch**: `580-mist-get-installer-device-virtual-chassis` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/580-mist-get-installer-device-virtual-chassis/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/installer/orgs/{org_id}/devices/{fpc0_mac}/vc` (operationId
`getInstallerDeviceVirtualChassis`) to retrieve the combined Virtual Chassis (VC)
topology and per-member runtime stats for a switch stack, as seen through the
**Installer** scope (a narrower-permission role than the admin VC endpoint already
surfaced at menu 92-94). The new menu item prompts the user for `org_id` (default from
`.env`) and `fpc0_mac` (the FPC0 / master switch MAC) via `safe_input()`, invokes the
`mistapi` SDK, flattens the response into one summary row plus N per-member rows, and
persists results through `DataExporter.write_with_format_selection()` so CSV, SQLite,
and ArangoDB+Redis backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **96** -- the next available slot in the
Interactive Safe cluster, immediately adjacent to the existing admin-scope VC viewers
at menu 92-94.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using a known org and a known FPC0 MAC from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65,
90-100) is unaffected -- new item 96 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical switch
stacks (endpoint is non-paginated; response is one JSON object with a small `members`
array, typically 1-10 entries). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; the endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`);
FPC0 MAC must be normalized (lowercase, no separators) before the SDK call to match the
Mist API canonical form.
**Scale/Scope**: One new public menu method (~22 lines) on a new
`VirtualChassisInstallerExportUtils` class (justified below -- no existing class owns
installer-scope VC reads; the admin-scope VC viewers at menu 92-94 live on a different
class with `admin` permission semantics), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new CSV/SQLite tables
(`installer_device_vc_summary` and `installer_device_vc_members`), one menu registration
entry, one README operation-count bump, one CHANGELOG line. No new external dependencies,
no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_installer_device_virtual_chassis()`
  stays under 25 lines, takes <=3 parameters (`self`, `org_id`, `fpc0_mac`), and contains
  <=5 logical blocks (prompt -> normalize/validate -> API call -> flatten summary +
  members -> DataExporter call). Hierarchy is unchanged: one new class with one new
  method. No new packages, modules, or top-level constants beyond the one
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry. Two output flatteners are inlined as single
  comprehension blocks; if either grows past 5 lines during implementation, it is
  extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `VirtualChassisInstallerExportUtils` class. A new class is justified because no
  existing class owns Installer-scope VC reads -- the admin-scope VC viewers at menu
  92-94 live on a different utilities class with admin permission semantics and a
  different SDK module path. No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names use
  full words (`member_row`, `vc_summary_row`, `fpc0_mac_normalized`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"installer_vc:org_id"`, `"installer_vc:fpc0_mac"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. Both
  `org_id` (UUID shape) and `fpc0_mac` (12 hex chars after normalization) are validated
  before the API call; on validation failure the method logs a warning and returns
  early. API token comes from `.env` via the existing `mistapi.APISession` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 getInstallerDeviceVirtualChassis`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching installer VC status for org %s fpc0 %s");
  `DEBUG` after the call with summary counts ("VC response: id=%s model=%s members=%d");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full traceback
  via `logging.exception`. No secrets, tokens, or full request URLs are logged. The
  `fpc0_mac` is logged because it is a hardware identifier, not a credential.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the menu dispatch table region around op 96) get comments
  added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a result count
  (member array length), `logging.info(...)` before flatten, `logging.debug(...)` after
  flatten with row counts, `logging.info(...)` before write, `logging.debug(...)` after
  write. The DataExporter call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/580-mist-get-installer-device-virtual-chassis/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_installer_device_virtual_chassis.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New VirtualChassisInstallerExportUtils class + new method +
                         # PK strategy entry + menu 96 registration. No new modules;
                         # same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the two new SQLite tables created on first run by
                         # DataExporter)
documentation/api/installer/GET_installer_orgs_org_id_devices_fpc0_mac_vc.md
                         # Authoritative enriched endpoint reference (already present)
```

**Structure Decision**: Single-file monolith. The new menu item is added as the sole
public method on a new `VirtualChassisInstallerExportUtils` class in `MistHelper.py`.
The new class is justified because the admin-scope VC viewers at menu 92-94 live on a
different utilities class that uses the admin SDK module (`mistapi.api.v1.sites...`) and
admin permission semantics; bundling installer-scope VC reads onto that class would
muddy its responsibility boundary. The menu number proposal is **96**, chosen because
it is the next available slot in the Interactive Safe cluster (60-96), sitting
immediately adjacent to the existing admin VC viewers at 92-94 so a NOC engineer
debugging VC issues finds both the installer-scope and admin-scope reads in the same
visual neighborhood. The full menu list will be re-verified at task generation time; if
96 collides with an in-flight feature branch, the next free integer in the same cluster
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
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `VirtualChassisInstallerExportUtils`. No wrappers introduced. Flattening helpers, if
  needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID and MAC validation happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validation, API call,
  flatten summary, flatten members, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
