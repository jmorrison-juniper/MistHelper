# Implementation Plan: GetOrgIdpProfile Menu Item

**Branch**: `608-mist-get-org-idp-profile` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/608-mist-get-org-idp-profile/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/idpprofiles/{idpprofile_id}` (operationId
`getOrgIdpProfile`) to retrieve a single Intrusion Detection and Prevention (IDP)
profile by its UUID, including any per-rule overwrites that customize the base
profile (`critical`, `standard`, `strict`) for SRX gateways. The menu item prompts
the user for an `org_id` and an `idpprofile_id` via `safe_input()`, invokes the
`mistapi` SDK, flattens the nested response into a summary row plus zero-or-more
overwrite rows, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. Two new entries are registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean upserts on repeated runs. The new
operation is proposed as menu number **96** -- the last available slot in the
Interactive Safe range (60-96), adjacent to the existing `listOrgIdpProfiles`
PK strategy already registered at line 3923 of `MistHelper.py`.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using `MIST_ORG_ID` and a discovered `idpprofile_id` from
`.env` or a prior `listOrgIdpProfiles` run. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy/destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 96 sits inside the default test
sweep range (96 is Interactive Safe; the skip list begins at 97).
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
profiles (non-paginated; response is one JSON object whose `overwrites` array
typically contains 0-50 rules). Adaptive delay metrics in `delay_metrics.json`
and `tuning_data.json` continue to govern back-off; no special tuning needed.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets
in logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); `idpprofile_id` validated as a UUID before the SDK call.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgClientSecurityExporter` class, two new entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (`getOrgIdpProfile` summary +
`getOrgIdpProfileOverwrites` sub-table), two new CSV/SQLite tables
(`org_idp_profile_summary` and `org_idp_profile_overwrites`), one menu
registration entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_idp_profile()` stays under
  25 lines, takes <=3 parameters (`self`, `org_id`, `idpprofile_id`), and
  contains <=5 logical blocks (prompt org -> prompt profile id -> API call ->
  flatten summary + overwrites -> two DataExporter calls). Hierarchy is
  unchanged: one new method on an existing class. No new packages, modules, or
  top-level constants are introduced. The two flatteners (`_flatten_idp_summary`
  and `_flatten_idp_overwrites`) are private helpers on the same class, each
  under 20 lines and <=4 logical blocks.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgClientSecurityExporter` class (line 11267 of `MistHelper.py`), which
  already owns adjacent security exports (`security_events`, NAC and AV
  surrounds). No standalone wrapper function is introduced. The menu dispatch
  in the main loop references the class method directly. Variable names use
  full words (`overwrite_row`, `profile_summary`, `idp_id`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_idp_profile:org_id"`,
  `"org_idp_profile:idpprofile_id"`) so SSH / container EOF exits cleanly with
  code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no
  typed destructive-confirmation gate is required. Both `org_id` and
  `idpprofile_id` are validated against the Mist UUID shape (`is_valid_uuid()`
  helper) before the API call; on validation failure the method logs a warning
  and returns early. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 96 getOrgIdpProfile` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching IDP profile %s for org %s");
  `DEBUG` after the call with summary counts ("IDP profile: name=%s
  base_profile=%s overwrites=%d"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets,
  tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the two new PK
  strategy dictionary entries, and the menu registration line will carry an
  inline `#` comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing `OrgClientSecurityExporter` cluster) get comments added in the same
  PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each prompt, `logging.info(...)` before the SDK
  call, the call itself, `logging.debug(...)` after with a result summary,
  `logging.info(...)` before each flatten, `logging.debug(...)` after each
  flatten, `logging.info(...)` before each DataExporter write. The DataExporter
  call already emits its own per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/608-mist-get-org-idp-profile/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_idp_profile.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method export_org_idp_profile() on existing
                         # OrgClientSecurityExporter class (line ~11267)
                         # + two PK strategy entries near line 3923
                         # + menu 96 registration in main dispatch loop
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the new SQLite tables created
                         # on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `OrgClientSecurityExporter` class in
`MistHelper.py` (line 11267) -- the same class that already owns the security
events export and is the natural home for IDP profile reads. The menu number
proposal is **96**, chosen because operations 60-96 are the Interactive Safe
cluster and this endpoint requires the user to supply two identifiers (`org_id`
plus `idpprofile_id`), placing it firmly in the interactive band. Slot 96 is
the last available integer below the Resource Intensive cluster (97-101). The
number is provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd
for the latest allocated menu integer; if 96 collides with an in-flight feature
branch, the next free integer in the same cluster is used.

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
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  two `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries are single inserts (existing
  structure), so no level-5 hierarchy explosion. The two private flattening
  helpers each stay under 20 lines.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `OrgClientSecurityExporter`. No wrappers introduced. Flattening helpers
  added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens on both inputs before the SDK
  call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entries and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten summary, flatten overwrites, export summary, export overwrites).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
