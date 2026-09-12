# Implementation Plan: GetOrgUserMac Menu Item

**Branch**: `650-mist-get-org-user-mac` | **Date**: 2026-07-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/650-mist-get-org-user-mac/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/usermacs/{usermac_id}` (operationId `getOrgUserMac`) to
retrieve a single user-MAC assignment record from an organization. The menu item
prompts the user for `org_id` and `usermac_id` via `safe_input()`, invokes the
`mistapi` SDK, flattens the single JSON object (including the `labels` array as a
delimited scalar column) into one row, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The
new operation is proposed as menu number **58** -- the next available slot in the
Misc / Safe Org Exports cluster (56-59), adjacent to other org-scoped small-payload
reads and well clear of the destructive block at 154-194.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org and usermac from `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 58 sits inside the default
test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint
is non-paginated and returns a single small JSON object (seven fields), so no
special back-off tuning is required. Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern retry cadence.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets
in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~20 lines) on an existing class
(`UserMacUtils` if present, else added to the nearest NAC / client-context class
such as `NacExportUtils`), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`,
one new SQLite table (`org_usermacs`), one menu registration entry, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new modules,
no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_user_mac()` stays under 25
  lines, takes <=3 parameters (`self`, `org_id`, `usermac_id`), and contains
  <=5 logical blocks (prompt org_id -> prompt usermac_id -> API call -> flatten
  single row -> DataExporter call). Hierarchy is unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are
  introduced. The flatten step is inlined as a single dict comprehension; if it
  grows past 5 lines during implementation, it is extracted to a private helper
  on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  user-MAC / NAC export class (e.g. `UserMacExportUtils` or the nearest existing
  class that owns `searchOrgUserMacs` / `listOrgUserMacs` exports). If no such
  class exists yet, a new `UserMacExportUtils` class is introduced (still a
  class, never a wrapper function). The menu dispatch in the main loop
  references the class method directly. Variable names use full words
  (`usermac_row`, `label_list`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_user_mac:org_id"`,
  `"org_user_mac:usermac_id"`) so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Both IDs are validated against the
  Mist UUID shape via the existing `is_valid_uuid()` helper before the API
  call; on validation failure the method logs a warning and returns early. API
  token comes from `.env` via the existing `mistapi.APISession` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 58
  getOrgUserMac` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching user MAC %s for org %s");
  `DEBUG` after the call with summary counts ("User MAC record: mac=%s
  labels=%d vlan=%s"); `WARNING` on 404 / empty payload; `ERROR` on unexpected
  exception with full traceback via `logging.exception`. No secrets, tokens, or
  full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline `#` comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing user-MAC menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result summary, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten, `logging.info(...)` before write. The
  DataExporter call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/650-mist-get-org-user-mac/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_user_mac.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on UserMacExportUtils (existing or newly
                         # introduced class -- never a standalone wrapper) plus
                         # a new PK-strategy entry and menu 58 registration.
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run
                         # by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing user-MAC / NAC export class in
`MistHelper.py`. If no such class currently owns user-MAC exports, a new
`UserMacExportUtils` class is introduced -- classes only, never standalone
wrapper functions (Constitution Principle II). The menu number proposal is
**58**, chosen because operations 56-59 are the Misc bucket inside the Safe
Org Exports range (1-59), which is the correct risk tier for a read-only GET
that returns a single small JSON object. The full menu list is re-verified at
task-generation time; if 58 collides with an in-flight feature branch, the
next free integer in the same cluster is used.

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the user-MAC
  export class (existing or newly introduced `UserMacExportUtils`). No
  wrappers introduced. The flatten helper, if extracted, is a private method
  on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call for both
  `org_id` and `usermac_id`.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
