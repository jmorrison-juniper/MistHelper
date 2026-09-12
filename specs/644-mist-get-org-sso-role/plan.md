# Implementation Plan: getOrgSsoRole Menu Item

**Branch**: `644-mist-get-org-sso-role` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/644-mist-get-org-sso-role/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/ssoroles/{ssorole_id}` (operationId `getOrgSsoRole`) to
retrieve the full detail of a single SSO role, including its IdP-attribute-to-Mist-RBAC
privilege mapping. The menu prompts the user for `org_id` and `ssorole_id` via
`safe_input()`, calls the `mistapi` SDK, flattens the response (one summary row for the
role plus zero or more privilege rows) and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
receive consistent output. A new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` guarantees
clean SQLite upserts on repeated runs. The new operation is proposed as menu number
**46** -- the next available slot in the Config/Admin cluster (42-50) alongside existing
`OrgAdminExporter` operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org and a known SSO role id from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 46 sits inside the default test sweep
range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both
must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint is
non-paginated and returns a single JSON object with an inline `privileges` array.
Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue to
govern back-off; this endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining via `os.path.join()` or
`pathlib.Path`.
**Scale/Scope**: One new public method (~20 lines) on the existing `OrgAdminExporter`
class in `MistHelper.py`, one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new
SQLite tables (`org_sso_role_summary` and `org_sso_role_privileges`), one menu
registration entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_sso_role()` stays under 25 lines,
  takes <=3 parameters (`self`, `org_id`, `ssorole_id`), and contains <=5 logical
  blocks (validate ids -> API call -> flatten role summary -> flatten privileges ->
  DataExporter call). Hierarchy unchanged: one new method on an existing class. No new
  packages, modules, or top-level constants introduced. If the privilege flattener
  grows past 5 lines during implementation, it is extracted to a private helper on the
  same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgAdminExporter` class (line ~11857 in `MistHelper.py`), which already owns the
  org admin/token exporters. No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names use
  full words (`sso_role_row`, `privilege_row`, `privilege_records`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_sso_role:org_id"`, `"org_sso_role:ssorole_id"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. Both
  UUIDs are validated against the Mist UUID shape via `ValidationUtils` before the
  API call; on validation failure the method logs a warning and returns early. API
  token comes from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 46 getOrgSsoRole` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  before the API call ("Fetching SSO role %s for org %s"); `DEBUG` after with
  privilege count ("SSO role fetched: name=%s privileges=%d for_site=%s");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full
  traceback via `logging.exception`. No secrets, tokens, or full request URLs are
  logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented
  adjacent lines in the touched block (existing `OrgAdminExporter` methods) get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result summary, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten, `logging.info(...)` before write,
  `logging.debug(...)` after write. The `DataExporter` call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/644-mist-get-org-sso-role/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_sso_role.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgAdminExporter (line ~11857) + PK strategy
                         # + menu 46 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 46
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 46
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `OrgAdminExporter` class in `MistHelper.py` (the same
class family that already owns org admin/token exporters -- SSO roles are the
IdP-side counterpart of admin RBAC). The menu number proposal is **46**, chosen
because operations 42-50 form the Config/Admin cluster per
`.github/copilot-instructions.md` and 46 is the next available slot adjacent to
existing admin operations. The full menu list will be re-verified at task
generation time; if 46 collides with an in-flight feature branch, the next free
integer in the same cluster (47, 48, 49, or 50) is used.

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

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgAdminExporter`. No
  wrappers introduced. The privilege flattener, if extracted, is added as a
  private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. Both UUIDs are validated before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
