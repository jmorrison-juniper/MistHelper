# Implementation Plan: GetOrgDeviceProfile Menu Item

**Branch**: `604-mist-get-org-device-profile` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/604-mist-get-org-device-profile/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/deviceprofiles/{deviceprofile_id}` (operationId
`getOrgDeviceProfile`) to retrieve the full configuration of a single org-level
device profile (AP, switch, or gateway profile) by its UUID. The new menu method
prompts the user for `org_id` (defaulting to `MIST_ORG_ID` from `.env`) and
`deviceprofile_id` via `safe_input()`, invokes the `mistapi` SDK call
`mistapi.api.v1.orgs.deviceprofiles.getOrgDeviceProfile()`, normalizes the
single-object JSON response into one flat row, registers a `natural_pk` entry
keyed on `id` in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, and persists the result
through `DataExporter.write_with_format_selection()` so the CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. The new operation is
proposed as menu number **96** -- the next available slot in the `92-96` Viewers
cluster, sitting alongside the existing single-record viewer operations and just
below the resource-intensive block at 97-101.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints; project README requires Python 3.13 or newer).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `.env` for `MIST_HOST`, `MIST_API_TOKEN`,
`MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; the polyglot ArangoDB + Redis container stack handles the graph + cache
backend. New SQLite table `org_device_profile` is created on first run.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org / deviceprofile pair from `.env`. Local
quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`.
The heavy / destructive skip list (14, 18, 63-65, 90-100) does not affect this
slot; menu 96 is a safe interactive viewer.
**Target Platform**: Windows 11 + venv for local development; Podman Linux
container (`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH
on port 2200; both must run identical code without modification.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on port 8055. This feature lives entirely in the
CLI; no web UI surface is added.
**Performance Goals**: Single non-paginated GET completes in <=5 seconds for a
typical device profile (response is one JSON object, not a list). Adaptive
delay metrics in `delay_metrics.json` and `tuning_data.json` continue to govern
back-off; no special tuning required for this lightweight call.
**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()` for
every prompt; API token never logged; all output under `data/`; Windows-safe
path joining via `os.path.join` / `pathlib.Path`.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
template / profile export class (`OrgTemplateExportUtils` or the closest
existing org-config export class -- the precise class is selected at task
generation by reading `MistHelper.py` for the owner of `listOrgDeviceProfiles`),
one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
(`org_device_profile`), one menu registration entry, one README operation-count
bump, one CHANGELOG entry. No new dependencies, modules, or directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `export_org_device_profile()` stays under
  25 lines, takes <=3 parameters (`self`, `org_id`, `deviceprofile_id`), and
  contains <=5 logical blocks (prompt -> validate UUIDs -> API call -> flatten
  to one row -> DataExporter call). Hierarchy unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants. If
  nested-config flattening exceeds 5 lines it is extracted into a private
  helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  org-templates / device-profile export class (the same class that owns the
  related `listOrgDeviceProfiles` export -- exact class name confirmed at task
  generation by grepping `MistHelper.py`). No standalone wrapper function is
  introduced. Menu dispatch references the class method directly. Variable
  names use full words (`device_profile_row`, `profile_payload`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All prompts use `safe_input()` with explicit `context=`
  strings (`"org_device_profile:org_id"`,
  `"org_device_profile:deviceprofile_id"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only HTTP GET, so
  no typed destructive-confirmation gate is required. Both UUIDs are validated
  against the Mist UUID shape before the API call; on validation failure the
  method logs a warning and returns early. API token comes from `.env` via the
  existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- The standard pipeline applies without modification:
  `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check` ->
  commit with `version YY.MM.DD.HH.MM - add menu 96 getOrgDeviceProfile` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching device profile %s for org %s");
  `DEBUG` after with response field summary ("Profile fetched: type=%s name=%s");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full
  traceback via `logging.exception`. No secrets, tokens, full request URLs, or
  Authorization headers are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration
  line carries an inline comment explaining *why* the line exists, not merely
  what it does. Blank lines, closing parentheses, and decorators are exempt per
  the constitution. Any adjacent uncommented lines in the touched block (the
  existing org-templates / device-profiles export cluster) receive comments in
  the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after
  pattern: `logging.info(...)` before each meaningful step (prompt, validate,
  API call, flatten, export), `logging.debug(...)` after with a concise result
  summary. The `DataExporter` already emits per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/604-mist-get-org-device-profile/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu slot, prompts
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_device_profile.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method export_org_device_profile() on the existing
                         # org-templates / device-profile export class
                         # (owner of listOrgDeviceProfiles), one new entry in
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES, one new menu 96
                         # registration line. No new modules; same monolith.
README.md                # Operation count bump + new row in the menu table for
                         # operation 96 (Viewers cluster, 92-96).
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing the
                         # menu 96 addition.
data/                    # Runtime output target (existing). DataExporter creates
                         # the new SQLite table org_device_profile and the CSV
                         # file org_device_profile.csv on first run.
documentation/api/orgs/GET_orgs_org_id_deviceprofiles_deviceprofile_id.md
                         # Enriched endpoint reference (already exists -- used
                         # as the authoritative source for the contract file).
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing org-templates / device-profile export class in
`MistHelper.py` (the same class that owns `listOrgDeviceProfiles`, currently
exposed at menu 35). The menu number proposal is **96**, chosen because the
`92-96` block is the Viewers cluster for single-record interactive lookups,
which exactly matches the read-one-by-UUID semantics of this endpoint, and 96
is the next free integer below the resource-intensive block at 97-101. If 96
collides with an in-flight feature branch at task time, the next free integer
in the same Viewers cluster is used (94 -> 93 -> 92 as fallbacks).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing
  org-templates / device-profile export class. No wrappers. Optional flattening
  helper, if needed, is added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation precedes the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the quickstart use
  ASCII-only `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, validate, API
  call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
