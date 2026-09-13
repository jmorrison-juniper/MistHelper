# Implementation Plan: GetOrgOtherDevice Menu Item

**Branch**: `629-mist-get-org-other-device` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/629-mist-get-org-other-device/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/otherdevices/{device_mac}` (operationId `getOrgOtherDevice`)
to retrieve the full record for a single non-Juniper (third-party) device tracked by an
organization. The menu item prompts the user for `org_id` (resolved from `.env`
`MIST_ORG_ID` if present) and `device_mac` via `safe_input()`, validates both, invokes
the `mistapi.api.v1.orgs.otherdevices.getOrgOtherDevice()` SDK call exactly once, wraps
the single-object JSON response in a one-row list, and persists via
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new `natural_pk` entry keyed on `id` is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly. Proposed menu number
is **96** (next free slot in the Interactive Safe / Viewers cluster 92-96); if 96 is
claimed by a merged in-flight spec at task time, the next free integer in the same
cluster is used.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST`, `MIST_API_TOKEN`, and optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend. New SQLite table
`org_other_device` created on first run by the exporter using the DDL derived from the
registered PK strategy.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using `MIST_ORG_ID` and a known `MIST_TEST_OTHER_DEVICE_MAC` (or first MAC returned
by `listOrgOtherDevices` if the test hook is absent). Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- item 96 sits inside the default test sweep
range and is strictly read-only.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single non-paginated GET returns a single JSON object; end-to-end
completion in <=2 seconds under normal conditions. Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off with no
endpoint-specific tuning required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; API token never
logged; all output under `data/`; Windows-safe path joining via `os.path.join` /
`pathlib.Path`; UUID validation for `org_id` and MAC-address canonicalization (lowercase,
no separators) for `device_mac` before the SDK call.
**Scale/Scope**: One new public menu method (`~18-22` lines) on the existing
`OrgExportUtils` class (the same class that already owns generic org export helpers
and the sibling `listOrgOtherDevices` output), one new `ENDPOINT_PRIMARY_KEY_STRATEGIES`
entry, one new SQLite table `org_other_device`, one menu registration line, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `export_org_other_device()` stays under 25 lines,
  takes <=3 parameters (`self`, `org_id`, `device_mac`), and contains <=5 logical
  blocks (prompt -> validate -> API call -> wrap-single-object -> DataExporter call).
  Hierarchy is unchanged: one new method on one existing class. No new packages,
  modules, or top-level constants are introduced. MAC canonicalization is delegated to
  the existing `ValidationUtils` helper.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgExportUtils` class in `MistHelper.py` (line ~12165). No standalone wrapper
  function is introduced. Menu dispatch references the class method directly. Variable
  names use full words (`other_device_row`, `device_mac_normalized`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_other_device:org_id"`, `"org_other_device:device_mac"`) so
  SSH / container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is required.
  `org_id` is validated against the Mist UUID shape by `ValidationUtils`; MAC address
  is normalized (lowercase, colons/hyphens stripped, length 12) before the SDK call.
  On validation failure the method logs a warning and returns early. API token comes
  from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 getOrgOtherDevice` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call (`"Fetching other device %s for org %s"`); `DEBUG` after
  the call with the returned `id`, `vendor`, `model`, and `state`; `WARNING` on 404
  ("Other device not found: %s"); `ERROR` on unexpected exception via
  `logging.exception`. No secrets, tokens, MAC addresses of unrelated devices, or full
  request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line will carry
  an inline comment explaining *why* the line exists, not merely what it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution.
  Uncommented adjacent lines within the touched cluster get comments added in the same
  PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with the resolved device summary, `logging.info(...)` before write, and
  `logging.debug(...)` after write. The DataExporter call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. The Complexity Tracking table below is
intentionally empty.

## Project Structure

### Documentation (this feature)

```text
specs/629-mist-get-org-other-device/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_other_device.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgExportUtils (~line 12165) + PK strategy
                         # entry near line 4012 (adjacent to listOrgOtherDevices) +
                         # menu 96 registration. No new modules; same monolith.
README.md                # Operation count bump + new row in menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96
data/                    # Runtime output target (existing dir). DataExporter creates
                         # data/org_other_device.csv and the org_other_device SQLite
                         # table on first run.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a public
method on the existing `OrgExportUtils` class in `MistHelper.py` (chosen because the
sibling operationId `listOrgOtherDevices` already lives in the org-export cluster and
carries the exact same PK shape). No new class is justified: this endpoint is a single
GET returning one object of a type already understood by the codebase. The proposed
menu number is **96** -- the next available slot in the Interactive Safe / Viewers
cluster (92-96), which is the correct category because the menu item is interactive
(prompts for a specific `device_mac`) and read-only. If 96 is claimed by a merged
in-flight branch at task-generation time, the next free integer in the same 92-96
cluster is used; if the cluster is full, the item is promoted to the tail of the safe
range at 91 or displaced to the end of the interactive-safe block at 97-adjacent.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=22 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` addition is a single dictionary insert.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgExportUtils`. No
  wrappers introduced. If a MAC-normalization helper is extracted for reuse, it
  becomes a private static method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID and MAC validation happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or unrelated PII.
- **Principle VI (Inline Comments)**: PASS -- The quickstart shows expected comment
  density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- The quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
