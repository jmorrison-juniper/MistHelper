# Implementation Plan: GetMspInventoryByMac Menu Item

**Branch**: `583-mist-get-msp-inventory-by-mac` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/583-mist-get-msp-inventory-by-mac/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}/inventory/{device_mac}` (operationId `getMspInventoryByMac`)
to look up a single device record across every organization owned by a Managed Service
Provider (MSP) by its hardware MAC address. The menu item prompts the user for an
`msp_id` and a `device_mac` via `safe_input()`, normalizes the MAC to the
colon-separated lowercase form the API expects, invokes the `mistapi` SDK exactly once,
and persists the single-object response through
`DataExporter.write_with_format_selection()` so the CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated lookups upsert cleanly on the natural
`(msp_id, mac)` composite key. The new operation is proposed as menu number **117a**
implementation-wise routed to the next free integer in the MSP cluster
(currently slot **96**, sitting next to the existing `MSPInventoryExporter` at menu
117 and the safe-export block ending at 95). The final integer is reconciled at
task-generation time so it does not collide with an in-flight feature branch.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using a known `MSP_ID` and `MSP_TEST_DEVICE_MAC` from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The destructive / heavy skip list
(14, 18, 63-65, 90-100) does NOT contain the new menu number, so it sits inside the
default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint is
non-paginated -- response is a single JSON object describing one device. Adaptive delay
metrics in `delay_metrics.json` and `tuning_data.json` continue to govern back-off; this
endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`);
MAC normalization to colon-separated lowercase before the SDK call so a user-entered
`AA-BB-CC-DD-EE-FF` or `aabbccddeeff` still resolves.
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`MSPInventoryExporter` class (which already owns menu 117 -- MSP-level inventory export),
one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV/SQLite table
(`msp_inventory_by_mac`), one menu registration entry, one README operation-count bump,
one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `lookup_msp_inventory_by_mac()` stays under
  25 lines, takes <=3 parameters (`self`, `msp_id`, `device_mac`), and contains <=5
  logical blocks (prompt -> validate / normalize MAC -> API call -> single-row flatten ->
  DataExporter call). Hierarchy is unchanged: one new method on an existing class. No
  new packages, modules, or top-level constants are introduced. The MAC normalization
  helper, if extracted, lands as a small private method on the same class and remains
  under 10 lines.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `MSPInventoryExporter` class (the same class that owns the related menu 117 MSP
  inventory export). No standalone wrapper function is introduced. The menu dispatch in
  the main loop references the class method directly. Variable names use full words
  (`mac_normalized`, `inventory_row`, `output_filename`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- Both prompts are collected through `safe_input()` with explicit
  `context=` strings (`"msp_inventory_by_mac:msp_id"`,
  `"msp_inventory_by_mac:device_mac"`) so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. `msp_id` is validated against the Mist
  UUID shape and `device_mac` is validated against a 12-hex-digit regex (after stripping
  separators) before the API call; on validation failure the method logs a `WARNING`
  and returns early. API token comes from `.env` via the existing `mistapi.APISession`
  and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 getMspInventoryByMac` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Looking up MSP %s inventory for MAC %s"); `DEBUG` after
  the call with a single-row summary ("Inventory hit: org_id=%s site_id=%s model=%s
  serial=%s"); `WARNING` on 404 / empty payload ("MAC %s not found in MSP %s
  inventory"); `ERROR` via `logging.exception` on unexpected exception. No secrets,
  tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line
  will carry an inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing MSP
  inventory cluster around menu 117) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with the matched
  device summary, `logging.info(...)` before flatten / write, `logging.debug(...)`
  after write with the resolved output path. The DataExporter call already emits its
  own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/583-mist-get-msp-inventory-by-mac/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_msp_inventory_by_mac.md    # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on MSPInventoryExporter class + new
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu registration.
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for the
                         # new operation number
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing the addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
documentation/api/msps/GET_msps_msp_id_inventory_device_mac.md  # Already exists --
                         # source-of-truth contract referenced from contracts/
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `MSPInventoryExporter` class in `MistHelper.py` (the same class
that owns menu 117 MSP-level inventory export). The menu number proposal is **96** --
the next free slot directly above the safe-org-exports cluster (51-95) and well inside
the default test sweep (the resource-intensive block at 97-101 is unaffected). The full
menu list is re-verified at task-generation time; if 96 collides with an in-flight
feature branch, the next free integer in the same cluster is used. The MSP grouping
remains conceptually intact because dispatch reads the method off
`MSPInventoryExporter`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `MSPInventoryExporter`. No
  wrappers introduced. The MAC normalization helper, if extracted, is added as a private
  method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID + MAC validation happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token. The MAC is logged because it is
  a hardware identifier the user just typed; it is not a secret.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and the
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, normalize, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
