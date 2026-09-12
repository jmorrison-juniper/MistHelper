# Implementation Plan: getOrgOtherDeviceStats Menu Item

**Branch**: `630-mist-get-org-other-device-stats` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/630-mist-get-org-other-device-stats/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/stats/otherdevices/{device_mac}` (operationId
`getOrgOtherDeviceStats`) to retrieve current-state statistics for a single non-Juniper
("other") device discovered on the network -- typically a Cradlepoint LTE gateway or
similar third-party appliance. The menu item prompts the user for an `org_id` and a
`device_mac` via `safe_input()`, invokes the `mistapi` SDK, flattens the nested response
(top-level stats plus per-connected-device, per-interface, and per-vendor-specific-port
sub-objects) into four related row streams, and persists them through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. Four new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
guarantee clean SQLite upserts on repeated polls. The new operation is proposed as menu
number **630**, matching the feature branch numeric prefix and keeping the operation
number stable across spec, branch, and CHANGELOG.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution Technology & Compatibility
Constraints and the existing venv baseline).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to the Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (`.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, optional
`MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. Local
fallback is SQLite at `data/mist_data.db`; CSV output lands directly under `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item non-interactively
using values from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. The
default `--test` skip list (14, 18, 63-65, 90-100) does not include 630, so the new
item joins the standard sweep.
**Target Platform**: Windows 11 + venv for local development; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and SSH-on-2200; both
must work without source change. Path joins use `os.path.join` / `pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: A single GET returns one JSON object per device MAC and
completes in <=5 seconds on a healthy WAN. The endpoint is not paginated. Adaptive
delay state in `delay_metrics.json` / `tuning_data.json` continues to govern back-off;
no endpoint-specific tuning is required.
**Constraints**: ASCII-only logging (no Unicode/emoji); `safe_input()` for every user
prompt; API token never appears in any log line; all output under `data/`; Windows-safe
path construction throughout.
**Scale/Scope**: One new public menu method (~22 lines) on a new
`OtherDeviceStatsExportUtils` class (there is no existing "other device" class -- see
Structure Decision below), four new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries, four
new SQLite tables (summary, connected devices, interfaces, vendor-specific interfaces),
one menu registration entry, one README menu-table row and operation-count bump, one
CHANGELOG line. No new third-party dependencies, no new packages, no new directories
outside the spec dir itself.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_other_device_stats()` stays under
  25 lines, takes <=3 parameters (`self`, `org_id`, `device_mac`), and contains <=5
  logical blocks (prompt org -> prompt MAC -> API call -> flatten four streams ->
  DataExporter calls). Any flattener that grows past 5 lines during implementation is
  extracted to a private helper on the same class. The new class
  `OtherDeviceStatsExportUtils` sits at hierarchy level 4 (class), its methods at
  level 5 (methods) -- unchanged depth. No new packages, no new modules.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `OtherDeviceStatsExportUtils` class. A new class (rather than reusing an existing
  one) is justified because the "other devices" area currently has no exports in
  MistHelper -- adding a bespoke class keeps the domain boundary clean and matches the
  pattern used by `SFPTransceiverDataProcessor` and `FirmwareManager`. No standalone
  wrapper function is introduced; the menu dispatch calls the class method directly.
  Variable names use full words (`connected_device_row`, `interface_rows`,
  `vendor_port_rows`) -- no single-letter iterators outside comprehensions.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_other_device_stats:org_id"`,
  `"org_other_device_stats:device_mac"`) so SSH / container EOF exits cleanly with
  code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. `org_id` is validated against the Mist
  UUID shape and `device_mac` is normalized (lowercase, colons/dashes stripped) and
  validated against the 12-hex-char shape before the API call; on validation failure
  the method logs a `WARNING` and returns early. The API token comes from `.env` via
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 630 getOrgOtherDeviceStats` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove
  / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`/`%d` lazy formatting.
  `INFO` is emitted before the API call ("Fetching other-device stats for org %s
  device %s"); `DEBUG` after the call with summary counts ("Other-device stats:
  status=%s vendor=%s interfaces=%d connected=%d"); `WARNING` on 404 / empty payload;
  `ERROR` on unexpected exception with full traceback via `logging.exception`. No
  secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new class, the new PK strategy
  entries, and the menu registration line will carry an inline comment that explains
  *why* the line exists, not merely what it does. Blank lines, closing parentheses,
  and decorators are exempt per the constitution. Any uncommented adjacent lines in
  the touched block (the menu dispatch table and the `ENDPOINT_PRIMARY_KEY_STRATEGIES`
  dictionary literal) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before each SDK call and each significant transform, followed by
  `logging.debug(...)` with a result summary or row count. The pattern is applied to
  prompting, API invocation, each of the four flatten steps, and each of the four
  DataExporter writes. DataExporter itself already emits per-backend log lines; the
  new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/630-mist-get-org-other-device-stats/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_other_device_stats.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New OtherDeviceStatsExportUtils class + 4 PK strategy
                         # entries + menu 630 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 630
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 630
data/                    # Runtime output target (existing dir). New SQLite tables are
                         # created on first run by DataExporter via CREATE TABLE IF
                         # NOT EXISTS -- no manual schema migration required.
```

**Structure Decision**: Single-file monolith. The new menu item is implemented as a
public method on a new `OtherDeviceStatsExportUtils` class in `MistHelper.py`. A new
class is justified rather than folding the method into an existing exporter because
"other devices" (third-party, non-Juniper devices discovered on the network) is a
distinct domain from the existing `SFPTransceiverDataProcessor`, `FirmwareManager`,
and generic device exporters -- and because at least one adjacent "other devices"
endpoint (`GET /orgs/{org_id}/otherdevices`) is likely to grow into its own menu item
in a follow-up spec, at which point the new class already owns the domain. The menu
number proposal is **630**, chosen to match the feature branch numeric prefix so that
spec / branch / commit / CHANGELOG all reference the same integer -- consistent with
recent large-batch API cataloging specs (500+ series). The full menu list is
re-verified at task-generation time; if 630 collides with an in-flight feature
branch, the next free integer in the same 6xx cluster is used.

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
  `quickstart.md` confirms <=25 lines, <=3 parameters, and <=5 logical blocks. Each
  flatten helper is a single comprehension or short loop and stays <=25 lines. The
  four `ENDPOINT_PRIMARY_KEY_STRATEGIES` inserts share the same dict literal, so no
  level-5 hierarchy explosion occurs.
- **Principle II (Class-Based)**: PASS -- All work lives on the new
  `OtherDeviceStatsExportUtils` class. Flatteners are private methods on that same
  class. No standalone wrapper functions are introduced.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET-only with no destructive side effect. `safe_input()` is the
  documented prompt path. `org_id` UUID validation and `device_mac` shape validation
  happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with lazy `%s`/`%d` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the four PK strategy entries
  and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (each prompt, the API call, each
  of the four flatten steps, each of the four export writes).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
