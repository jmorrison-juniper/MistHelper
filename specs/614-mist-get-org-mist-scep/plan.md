# Implementation Plan: GetOrgMistScep Menu Item

**Branch**: `614-mist-get-org-mist-scep` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/614-mist-get-org-mist-scep/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/setting/mist_scep` (operationId `getOrgMistScep`) to retrieve
the organization's Mist SCEP (Simple Certificate Enrollment Protocol) settings -- the
configured cert providers (`intune`, `jamf`, `byod`), provider-specific SCEP / webhook
URLs, the read-only `enabled` flag, and the `suspended` flag. The menu item prompts the
user for one identifier (`org_id`) via `safe_input()`, invokes the `mistapi` SDK exactly
once, flattens the small response object (one row per org, with the `cert_providers`
array joined into a comma-separated string) and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
keyed by `org_id` so repeated runs upsert cleanly into SQLite. The new operation is
proposed as menu number **88** -- a free slot inside the Safe Org Exports / Org Settings
sub-cluster, adjacent to other org setting reads and well clear of the resource-intensive
(97-101) and destructive (154-194) ranges.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to the Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for
`.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and the optional `MIST_ORG_ID` default).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB +
Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using the org defined in `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. Heavy /
destructive skip list (14, 18, 63-65, 90-100) is unaffected -- new item 88 sits inside the
default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH on port 2200; both
must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single non-paginated GET completes in <=5 seconds. The response is
one small JSON object (single-digit kilobytes) regardless of org size, so no adaptive
tuning beyond the existing `delay_metrics.json` / `tuning_data.json` mechanism is needed.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; the API token must
never appear in any log line; SCEP provider URLs and the `jamf_access_token` field MUST be
treated as sensitive and SHOULD NOT be logged at INFO or above; all output under `data/`;
Windows-safe path joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`OrgSettingsExportUtils` class (or the nearest existing settings-export class -- new class
only if no semantically appropriate class exists, justified in Structure Decision below).
One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
(`org_setting_mist_scep`), one menu registration entry, one README operation-count bump,
one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_mist_scep_setting()` stays under 25
  lines, takes <=2 parameters (`self`, optional `org_id`), and contains <=5 logical blocks
  (prompt -> validate -> API call -> flatten -> DataExporter call). Hierarchy is unchanged:
  one new method on an existing class. No new packages, modules, or top-level constants
  are introduced. The flatten step is a single dict comprehension; if it grows past 5
  lines during implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing org-settings
  export class (current placeholder name `OrgSettingsExportUtils` -- the actual class is
  resolved at task-generation time by grep for the nearest sibling settings-read method
  such as `getOrgSetting`). No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names use full
  words (`scep_response`, `cert_providers_csv`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with an explicit
  `context="org_mist_scep:org_id"` string so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. The `org_id` is validated against the Mist
  UUID shape via the existing `is_valid_uuid()` helper before the API call; on validation
  failure the method logs a `WARNING` and returns early. The API token is loaded from
  `.env` via `mistapi.APISession` and never logged. The `jamf_access_token` field returned
  by Mist is treated as sensitive: written to the configured backend but never echoed to
  stdout or to log lines above `DEBUG`, and the `DEBUG` summary log includes only field
  presence flags, not values.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check` ->
  commit with `version YY.MM.DD.HH.MM - add menu 88 getOrgMistScep` -> `git push origin
  main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run container ->
  `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching Mist SCEP setting for org %s"); `DEBUG` after the
  call with field-presence summary ("Mist SCEP: enabled=%s suspended=%s providers=%d
  has_jamf_token=%s"); `WARNING` on 404 / empty payload; `ERROR` on unexpected exception
  with full traceback via `logging.exception`. No secrets, tokens, or full response bodies
  are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing org-settings menu cluster) get comments added
  in the same PR per the "comment the entire block being touched" rule.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with a field-presence summary, `logging.info(...)` before flatten, `logging.debug(...)`
  after flatten with the row count (always 1 for this endpoint), `logging.info(...)`
  before write. The DataExporter call emits its own per-backend log lines; the new method
  does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/614-mist-get-org-mist-scep/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_mist_scep.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the existing org-settings export class +
                         # PK strategy entry + menu 88 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 88
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 88 addition
data/                    # Runtime output target (existing dir). New SQLite table
                         # `org_setting_mist_scep` is created on first run by
                         # DataExporter via CREATE TABLE IF NOT EXISTS.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing org-settings export class in `MistHelper.py`. At task-generation
time the implementer will grep for the nearest existing settings-read method (for example
`getOrgSetting`, `listOrgNacRules`, or another org-scope settings export) and place the
new method on the same class to satisfy Principle II (No Wrappers, No new class without
justification). If grep shows no semantically appropriate class exists, a new class named
`OrgSettingsExportUtils` is justified in the Complexity Tracking table during the
implementation PR. The menu number proposal is **88**, chosen because the safe-org-exports
cluster runs 1-95, the settings-adjacent slots in the 80s have free integers per the
README menu table, and 88 is well clear of the resource-intensive block at 96-101 and the
destructive block at 154-194. The number is provisional -- at `/speckit.tasks` time,
MistHelper.py is grep'd for the latest allocated menu integer and 88 is shifted forward
if a conflict exists.

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
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure), so
  no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing org-settings
  export class. No wrappers introduced. The flatten step, if extracted, is added as a
  private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is GET
  only, with no destructive side effect. `safe_input()` is the documented prompt path.
  UUID validation happens before the SDK call. The `jamf_access_token` sensitivity rule
  is documented in both `plan.md` and `contracts/get_org_mist_scep.md`.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token or the `jamf_access_token` value.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
