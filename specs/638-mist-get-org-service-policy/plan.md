# Implementation Plan: GetOrgServicePolicy Menu Item

**Branch**: `638-mist-get-org-service-policy` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/638-mist-get-org-service-policy/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}` (operationId
`getOrgServicePolicy`) to retrieve the full detail record for a single org-scoped
Service Policy (WAN steering / security rule bundle). The menu item prompts the user
for `org_id` and `servicepolicy_id` via `safe_input()`, invokes the `mistapi` SDK,
flattens the nested response (top-level policy fields + `ewf` rule array) into a
parent row plus zero-or-more child rows, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **94** -- the next available slot inside the
Interactive Safe cluster (60-96), adjacent to the existing safe org-scope viewers
and immediately below the Resource Intensive block starting at 97.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and the
optional `MIST_ORG_ID` default).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend. Two new tables are
created on first write: `org_service_policy` (parent) and `org_service_policy_ewf`
(nested rule array).
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org and servicepolicy from `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- new item 94 sits inside the default test sweep
range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both
must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a typical
policy (the endpoint is non-paginated and the response is a single JSON object of
modest size). Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json`
continue to govern back-off; this endpoint is light enough that no special tuning
is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets
in logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); the `ewf` nested array must be flattened rather than stored as
JSON-in-a-column so SQL queryability is preserved.
**Scale/Scope**: One new public menu method (~22 lines) on the existing service
policy export class (or the closest org-config export class -- see Structure
Decision below), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for the parent
plus one MistHelper-internal sub-table entry for the `ewf` array, two new
CSV/SQLite tables (`org_service_policy` and `org_service_policy_ewf`), one menu
registration entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_service_policy_detail()`
  stays under 25 lines, takes <=3 parameters (`self`, `org_id`,
  `servicepolicy_id`), and contains <=5 logical blocks (prompt org_id -> prompt
  servicepolicy_id -> API call -> flatten parent + ewf children -> two
  DataExporter calls). Hierarchy is unchanged: one new method on an existing
  class. No new packages, modules, or top-level constants are introduced. The
  parent flattener and the ewf-array flattener are inlined as single
  comprehension blocks; if either grows past 5 lines during implementation, it
  is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  org-config export class that owns the sibling `listOrgServicePolicies` menu
  item (Menu 4 per the enriched endpoint doc's "MistHelper Notes"). No
  standalone wrapper function is introduced. The menu dispatch in the main loop
  references the class method directly. Variable names use full words
  (`policy_row`, `ewf_rule_rows`, `service_policy_id`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_service_policy:org_id"`,
  `"org_service_policy:servicepolicy_id"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. Both UUIDs are
  validated against the Mist UUID shape via the existing `is_valid_uuid()`
  helper before the API call; on validation failure the method logs a warning
  and returns early. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 94 getOrgServicePolicy` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop
  / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching service policy %s for org
  %s"); `DEBUG` after the call with summary counts ("Service policy: name=%s
  action=%s ewf_rules=%d services=%d tenants=%d"); `WARNING` on 404 / empty
  payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the two new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entries, and the menu
  registration line will carry an inline comment that explains *why* the line
  exists, not merely what it does. Blank lines, closing parentheses, and
  decorators are exempt per the constitution. Any uncommented adjacent lines
  in the touched block (the existing service policy list menu cluster) get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each prompt, `logging.info(...)` before the SDK
  call, the call itself, `logging.debug(...)` after with a result summary,
  `logging.info(...)` before each flatten step, `logging.debug(...)` after
  each flatten with a row count, `logging.info(...)` before each write. The
  DataExporter call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/638-mist-get-org-service-policy/
+-- plan.md              # This file
+-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
+-- data-model.md        # Phase 1 - response entities + DDL + PK registration
+-- quickstart.md        # Phase 1 - local run + .env + quality gates
+-- contracts/
|   +-- get_org_service_policy.md   # Phase 1 - HTTP + SDK contract
+-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on existing org-config export class
                         # (the class that owns listOrgServicePolicies, referenced
                         # by the endpoint doc as Menu 4) + two PK strategy entries
                         # + menu 94 registration. No new modules; same single-file
                         # monolith. If no class matches directly, extend the
                         # closest safe-org-export class (justification below).
README.md                # Operation count bump + new row in the menu table for op 94
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 94 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables created on first run
                         # by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing org-config / service-policy export class in
`MistHelper.py` -- the same class that owns `listOrgServicePolicies` (Menu 4 per
the enriched endpoint doc). If that class is not clearly demarcated in the current
source, the method is added to the nearest safe-org-export class that already
handles per-object detail retrievals (natural PK on `id`), preserving Principle II
(no standalone wrappers). The menu number proposal is **94**, chosen because
operations 60-96 are the Interactive Safe cluster (this endpoint requires the user
to supply a specific `servicepolicy_id`, which is inherently interactive) and 94 is
the next available integer below the Resource Intensive cluster that begins at 97.
The full menu list will be re-verified at task generation time; if 94 collides
with an in-flight feature branch, the next free integer in the same cluster is
used.

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

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary additions are two adjacent inserts
  (existing structure), so no level-5 hierarchy explosion. The parent+child
  split of the response matches the pattern already used elsewhere in
  MistHelper for endpoints with nested arrays.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing
  service-policy export class. No wrappers introduced. Flattening helpers, if
  needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path for both UUIDs. `is_valid_uuid()` validation happens
  before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the two PK
  strategy entries and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt org_id, prompt
  servicepolicy_id, API call, flatten parent, flatten ewf, export parent,
  export ewf).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
