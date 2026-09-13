# Implementation Plan: getOrgOauthAppLinkedStatus Menu Item

**Branch**: `628-mist-get-org-oauth-app-linked-status` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/628-mist-get-org-oauth-app-linked-status/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/setting/{app_name}/link_accounts` (operationId
`getOrgOauthAppLinkedStatus`) to retrieve the OAuth linking status for a specific
third-party integration (Zoom, Zscaler, JAMF, Crowdstrike, SentinelOne, VMWare, Prisma,
ZDX, etc.) at the organization level. The menu method prompts the user for `org_id`,
`app_name`, and the mandatory `forward` URL via `safe_input()`, invokes the mistapi SDK,
flattens the response into one org/app summary row plus zero-or-more linked-account
rows, and persists both via `DataExporter.write_with_format_selection()` so CSV,
SQLite, and ArangoDB+Redis backends all receive consistent output. A pair of entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` ensures clean SQLite upserts on repeated polls. The
operation is proposed as menu number **58**, an available slot inside the Safe Org
Exports / Org Settings cluster adjacent to the existing `getOrgSetting`-derived
exports.

## Technical Context

**Language/Version**: Python 3.13+ per constitution Technology & Compatibility
Constraints.
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's SDK, the only permitted
interface to the Mist Cloud); `requests` (SDK transport, transitive); `python-dotenv`
for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend through `DataExporter.write_with_format_selection()`. Local
fallback is SQLite at `data/mist_data.db`; CSV files land in `data/`; the polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item non-interactively
against a known org and `app_name` from `.env`. Quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) is
unaffected -- menu 58 sits inside the default sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
`ghcr.io/jmorrison-juniper/misthelper:latest` for production and SSH-on-2200; both
must work without code change.
**Project Type**: CLI tool, single-file monolith `MistHelper.py` (~28K lines) with an
optional Gunicorn web UI on 8055. This feature is CLI-only.
**Performance Goals**: A single GET returns a small JSON object (one `accounts` array,
one `authorization_url`, one `linked` bool) with no pagination. Round trip <=5 seconds
for typical orgs. Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json`
continue to govern back-off; no endpoint-specific tuning required.
**Constraints**: ASCII-only logging; `safe_input()` on every prompt; API token loaded
from `.env` and never logged; the `forward` URL and `app_name` are ASCII-validated
before the call; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) added to an existing
`OrgSettingsExportUtils` class (created for the adjacent `getOrgSetting`-family menu
items -- reused, not re-created), two new entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (summary + per-account detail), two new CSV/SQLite
tables (`org_oauth_app_link_summary` and `org_oauth_app_link_accounts`), one menu
registration entry, one README menu-table row and operation-count bump, one CHANGELOG
line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_oauth_app_linked_status()` stays
  under 25 lines, takes 4 parameters (`self`, `org_id`, `app_name`, `forward_url`),
  and contains 5 logical blocks (three prompts collapsed into one block via a small
  helper, API call, flatten summary, flatten accounts, DataExporter double-write).
  Hierarchy is unchanged: one new method on an existing class. Two flatten helpers
  live inline as short comprehensions; if either grows past 5 lines during
  implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- Behavior lives as a method on the existing
  `OrgSettingsExportUtils` class (owner of `getOrgSetting` and adjacent org-settings
  exports). No standalone wrapper function is introduced. The main-loop menu dispatch
  references the class method directly. Variable names use full words
  (`linked_accounts`, `oauth_summary_row`); no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` tags (`"org_oauth_link_status:org_id"`,
  `"org_oauth_link_status:app_name"`, `"org_oauth_link_status:forward"`), so
  SSH / container EOF exits with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. The
  `org_id` is validated against the Mist UUID shape via the existing `is_valid_uuid()`
  helper; `app_name` is validated against an ASCII allow-list; `forward` is validated
  as a proper `https://` URL. On any validation failure the method logs `WARNING` and
  returns early. The API token comes from `.env` via the existing `mistapi.APISession`
  and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black
  --check` -> commit `version YY.MM.DD.HH.MM - add menu 58 getOrgOauthAppLinkedStatus`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove
  / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  before the API call (`"Fetching OAuth link status for org %s app %s"`), `DEBUG`
  after (`"OAuth link status: linked=%s accounts=%d"`), `WARNING` on 404 / empty
  payload, `ERROR` on unexpected exception via `logging.exception`. The API token,
  the returned `authorization_url` (which contains a redirect nonce), and any
  `webhook_secret` / `webhook_token` / `password` fields are redacted before logging.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, in the two new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries, and in the menu registration line will
  carry a same-line inline comment explaining *why* the line exists (not merely what
  it does). Blank lines, closing parens, and decorators are exempt per constitution.
  Any uncommented adjacent lines inside the touched org-settings menu cluster get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each prompt, before the SDK call, before each flatten
  pass, and before each `DataExporter` write; `logging.debug(...)` after each with a
  result count or normalized outcome. The `DataExporter` itself already emits per-
  backend log lines and is not duplicated.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/628-mist-get-org-oauth-app-linked-status/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + expected output + quality gates
|-- contracts/
|   `-- get_org_oauth_app_linked_status.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgSettingsExportUtils class + two PK
                         # strategy entries + menu 58 registration. No new modules;
                         # same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir). Two new SQLite tables
                         # created on first run by DataExporter -- no manual migration.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a public
method on the existing `OrgSettingsExportUtils` class in `MistHelper.py` (owner of the
other `getOrgSetting`-family exports). The menu number proposal is **58**, chosen
because it sits inside the Safe Org Exports cluster (1-59) adjacent to the existing
org-settings exports and well clear of the resource-intensive block that begins at
96. The proposal is provisional -- at `/speckit.tasks` time, MistHelper.py is grep'd
for the latest allocated menu integer and 58 is shifted forward if a conflict exists.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The Phase 1 quickstart skeleton confirms
  the method stays <=25 lines with <=5 parameters (`self`, `org_id`, `app_name`,
  `forward_url`) and 5 logical blocks. The two `ENDPOINT_PRIMARY_KEY_STRATEGIES`
  entries are a single dict-literal insert, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All new work lives on
  `OrgSettingsExportUtils`. No wrappers. Optional flatten helpers land as private
  methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms GET only, no
  destructive side effect. `safe_input()` is the sole prompt path. UUID / app_name /
  URL validation happens before the SDK call. Sensitive fields
  (`authorization_url`, `webhook_secret`, `webhook_token`, `webhook_password`,
  `password`) are redacted before any log line.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- All logs are ASCII with `%s` formatting;
  no secret material reaches log lines.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, the two PK strategy entries, and the
  menu registration.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after `INFO`/`DEBUG` pairs for every meaningful action.

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
