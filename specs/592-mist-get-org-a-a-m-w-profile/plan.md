# Implementation Plan: GetOrgAAMWProfile Menu Item

**Branch**: `592-mist-get-org-a-a-m-w-profile` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/592-mist-get-org-a-a-m-w-profile/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/aamwprofiles/{aamwprofile_id}` (operationId `getOrgAAMWProfile`)
to retrieve a single Advanced Anti-Malware (SkyATP) profile by its UUID. The new menu
method prompts the user for `org_id` and `aamwprofile_id` via `safe_input()`, invokes the
`mistapi` SDK, flattens the response (one summary row plus zero-or-more
`aamw_profile_category` rows extracted from the nested `categories[]` array), and persists
the result through `DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. Two new entries are registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`: a `natural_pk` on the profile `id` for the summary, and
a `composite_pk` for the per-category sub-table. The new operation is proposed as menu
number **58** -- inside the Safe Org Exports / security-profile cluster (alongside
`avprofiles` and `idpprofiles`).

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (`.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB +
Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using a known org and a known AAMW profile UUID from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65,
90-100) is unaffected -- new item 58 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical profile
documents (non-paginated, small JSON object with one nested array of category enums).
Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue to govern
back-off; no special tuning needed for this endpoint.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SecurityProfileExportUtils` class (the same class that owns adjacent `avprofiles` and
`idpprofiles` exports). Two new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. Two new
CSV/SQLite tables (`org_aamw_profile_summary` and `org_aamw_profile_categories`). One
menu registration line, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories. If `SecurityProfileExportUtils` does
not yet exist in the monolith, the implementation extends the closest existing
security-profile class instead (final class selection confirmed at `/speckit.tasks` time
by grepping `MistHelper.py` for `avprofile` / `idpprofile` ownership).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_aamw_profile()` stays under 25
  lines, takes <=3 parameters (`self`, `org_id`, `aamwprofile_id`), and contains <=5
  logical blocks (prompt org_id -> prompt profile_id -> API call -> flatten summary +
  categories -> two DataExporter writes). Hierarchy is unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are introduced. The
  category flattener is a single comprehension; if it grows past 5 lines during
  implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the closest existing
  security-profile-export class (working name `SecurityProfileExportUtils`; the final
  class is confirmed at task time by grepping for the `avprofiles` / `idpprofiles`
  export owners). No standalone wrapper function is introduced. The menu dispatch in the
  main loop references the class method directly. Variable names use full words
  (`profile_row`, `category_rows`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_aamw_profile:org_id"` and
  `"org_aamw_profile:aamwprofile_id"`) so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Both UUIDs are validated against the Mist
  UUID shape via the existing `is_valid_uuid()` helper before the API call; on
  validation failure the method logs a `WARNING` and returns early. The API token comes
  from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 58 getOrgAAMWProfile` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching AAMW profile %s for org %s"); `DEBUG` after the
  call with summary counts ("AAMW profile: name=%s categories=%d fallback=%s");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full traceback
  via `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the two new PK strategy
  dictionary entries, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched security-profile-export block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with a result count, `logging.info(...)` before flatten, `logging.debug(...)` after
  flatten, `logging.info(...)` before each export, `logging.debug(...)` after. The
  DataExporter call already emits its own per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/592-mist-get-org-a-a-m-w-profile/
| - plan.md              # This file
| - research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
| - data-model.md        # Phase 1 - response entities + DDL + PK registration
| - quickstart.md        # Phase 1 - local run + .env + quality gates
| - contracts/
|   | - get_org_a_a_m_w_profile.md   # Phase 1 - HTTP + SDK contract
| - tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SecurityProfileExportUtils class + 2 PK strategy
                         # entries + menu 58 registration. No new modules; same single-
                         # file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the two new SQLite tables created on first write
                         # by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing security-profile-export class in `MistHelper.py` (working name
`SecurityProfileExportUtils` -- the actual owning class is confirmed at task time by
grepping for `avprofiles`/`idpprofiles` export methods). The menu number proposal is
**58**, chosen because it sits inside the Safe Org Exports cluster next to other
security-profile reads (AV, IDP). The full menu list is re-verified at task generation
time; if 58 collides with an in-flight feature branch, the next free integer in the same
cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method skeleton in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The two
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries are simple dict literals (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing security-
  profile-export class. No wrappers introduced. The category flattener, if extracted, is
  a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path for both UUIDs. Both IDs are validated client-side before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows the expected
  comment density on every executable line, including the two PK strategy entries and
  the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (two prompts, API call, flatten
  summary, flatten categories, two exports).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
