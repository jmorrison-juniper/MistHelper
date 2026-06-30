# Implementation Plan: GetOrgMarvisClientInvite Menu Item

**Branch**: `613-mist-get-org-marvis-client-invite` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/613-mist-get-org-marvis-client-invite/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/marvisinvites/{marvisinvite_id}` (operationId
`getOrgMarvisClientInvite`) to retrieve a single Marvis Client Invite object (used
for mobile SDK / MDM provisioning) from an organization. The new method prompts
the user for `org_id` (default sourced from `.env` `MIST_ORG_ID`) and
`marvisinvite_id` via `safe_input()`, invokes the `mistapi` SDK, and persists the
single-object response through `DataExporter.write_with_format_selection()` so
CSV, SQLite, and ArangoDB+Redis backends all receive a consistent row. A new entry
is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the invite UUID for
clean SQLite upserts on repeated runs. The new operation is proposed as menu
number **195** -- the next available slot above the current top-of-range (194:
`cloneDeviceConfigToGatewayTemplate`) and a natural placement adjacent to other
Marvis / Org admin reads.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints; minimum supported runtime for MistHelper).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transitive transport
dependency); `python-dotenv` for `.env` loading of `MIST_HOST`,
`MIST_API_TOKEN`, and the optional default `MIST_ORG_ID`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback target; CSV output lands
at `data/org_marvis_client_invite.csv`; polyglot ArangoDB + Redis containers
handle the graph + cache backend when configured. No schema migration is
required beyond the new PK strategy entry -- the SQLite table is created on
first run.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using `MIST_ORG_ID` and a known `marvisinvite_id` seeded
in `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`.
The heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected --
menu 195 sits outside those bands.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200
deployment. Both targets must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with an optional Gunicorn web UI on 8055. This feature lives entirely in the
CLI path. No web UI surface area changes.
**Performance Goals**: Single GET request completes in <=5 seconds. The
endpoint is non-paginated -- the response is a single JSON object. Adaptive
delay metrics in `delay_metrics.json` and `tuning_data.json` continue to govern
back-off; this endpoint is light enough that no per-endpoint tuning is
required.
**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()`
wraps every prompt; API token never logged; all output written under `data/`;
Windows-safe path joining via `os.path.join` / `pathlib.Path`; UUID shape
validation on both `org_id` and `marvisinvite_id` before the SDK call.
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`MarvisOperations` class (or, if absent, a small new `MarvisInviteOperations`
class adjacent to it -- see Structure Decision below). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new SQLite table
(`org_marvis_client_invite`). One menu registration entry. One README
operation-count bump. One CHANGELOG line. No new third-party dependencies, no
new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_marvis_client_invite()`
  stays under 25 lines, takes <=3 parameters (`self`, `org_id`,
  `marvisinvite_id`), and contains <=5 logical blocks (prompt -> SDK call ->
  shape result into a single-row list -> DataExporter call -> success log).
  Hierarchy is unchanged: one new method on an existing (or single new) class.
  No new packages, modules, or top-level constants beyond the one
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on an existing
  Marvis-related class in `MistHelper.py`. If no Marvis class exists yet, a
  new `MarvisInviteOperations` class is created (semantic, named class --
  not a wrapper function) and the related list/delete endpoints
  (`listOrgMarvisClientInvites`, `deleteOrgMarvisClientInvite`) are grouped
  under it for future PRs. No standalone wrapper function is introduced. Menu
  dispatch in the main loop references the class method directly. Variable
  names use full words (`invite_record`, `marvisinvite_id`).

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_marvis_client_invite:org_id"`,
  `"org_marvis_client_invite:marvisinvite_id"`) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate is required. Both UUIDs
  are validated against the Mist UUID shape before the SDK call; on validation
  failure the method logs a warning and returns early. API token comes from
  `.env` via `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` -> `python -m black --check MistHelper.py`
  -> commit with `version YY.MM.DD.HH.MM - add menu 195 getOrgMarvisClientInvite`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the SDK call ("Fetching Marvis client invite %s for
  org %s"); `DEBUG` after the call with the invite name and disabled flag
  ("Marvis invite retrieved: name=%s disabled=%s"); `WARNING` on 404 / empty
  payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result summary, `logging.info(...)` before write,
  `logging.debug(...)` after write. The `DataExporter` call already emits its
  own per-backend log lines and is not duplicated here.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/613-mist-get-org-marvis-client-invite/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_marvis_client_invite.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on MarvisInviteOperations class (new or
                         # existing Marvis-related class) + PK strategy + menu
                         # 195 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for
                         # op 195.
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing
                         # menu 195 addition.
data/                    # Runtime output target (existing dir). On first run
                         # DataExporter creates the new SQLite table per the
                         # PK strategy registered in this PR.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on a Marvis-invite-focused class in `MistHelper.py`. If no
such class exists yet (the operationId family
`*OrgMarvisClientInvite*` is new to MistHelper -- see Phase 0 research),
a new `MarvisInviteOperations` class is created in the same file alongside
existing Org-admin classes. The menu number proposal is **195** -- the next
available slot above the current top-of-range (194:
`cloneDeviceConfigToGatewayTemplate`), keeping the new read-only Marvis
operation in a logical Org-admin cluster. The full menu list will be
re-verified at task generation time; if 195 collides with an in-flight feature
branch, the next free integer is used.

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
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert into an
  existing structure, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `MarvisInviteOperations`. No wrappers introduced.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. Both UUIDs are validated before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token, the
  `provision_url`, or any request headers.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, SDK call,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
