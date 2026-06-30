# Implementation Plan: GetOrgJseInfo Menu Item

**Branch**: `609-mist-get-org-jse-info` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/609-mist-get-org-jse-info/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/setting/jse/info` (operationId `getOrgJseInfo`) to retrieve the
Juniper Sky Enterprise (JSE) integration metadata associated with an organization -- the
linked JSE cloud name, the list of JSE org names visible to the account, and the JSE
username currently bound to the integration. The menu item prompts the user for an
`org_id` via `safe_input()` (defaulting to `MIST_ORG_ID` from `.env` when present),
invokes the `mistapi` SDK, augments the singleton response object with the caller's
`org_id` so the row is self-describing, flattens the `org_names` string array into a
deterministic comma-joined column for CSV/SQLite friendliness, and persists the result
through `DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on `org_id` (natural_pk) so repeated runs upsert
cleanly with no duplicate rows. The new operation is proposed as menu number **58** --
the next available slot in the Safe Org Exports / Misc cluster (1-59), sitting adjacent
to other org-scoped configuration read operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend. New SQLite table `org_jse_info`
is created lazily on first invocation by the DataExporter.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected
-- new item 58 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change. SSH session prompts must tolerate EOF via `safe_input()`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI; no web
UI changes are required.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint is
non-paginated and returns one small JSON object (three fields), so no special tuning,
batching, or concurrency is required. Adaptive delay metrics in `delay_metrics.json`
and `tuning_data.json` continue to govern back-off uniformly with adjacent menu items.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; API token never
logged; all output under `data/`; Windows-safe path joining via `os.path.join` /
`pathlib.Path`; inline comments on every executable line; action logging before and
after every meaningful step.
**Scale/Scope**: One new public menu method (~18 lines) on the existing
`OrgConfigExportUtils` class (or, if that class is at capacity per the Five-Item Rule,
on a sibling class in the same Safe Org Exports cluster -- to be confirmed during
`/speckit.tasks`). One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new
CSV/SQLite table `org_jse_info`. One menu registration entry. One README operation-
count bump and one menu-table row. One CHANGELOG line in the
`version YY.MM.DD.HH.MM` format. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_jse_info()` stays under 25 lines,
  takes <=2 parameters (`self`, `org_id`), and contains <=5 logical blocks (resolve
  org_id default -> log+invoke SDK -> guard empty payload -> flatten org_names list and
  inject org_id -> DataExporter call). Hierarchy is unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on an existing class in
  the Safe Org Exports cluster (target class: `OrgConfigExportUtils`, confirmed at
  `/speckit.tasks` time against the live `MistHelper.py`). No standalone wrapper
  function is introduced. The menu dispatch in the main loop references the class
  method directly. Variable names use full words (`jse_info_row`, `org_names_joined`)
  -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with an
  explicit `context="org_jse_info:org_id"` string so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no
  typed destructive-confirmation gate is required. The `org_id` is validated against
  the Mist UUID shape before the API call; on validation failure the method logs a
  warning and returns early. The API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black
  --check` -> commit with `version YY.MM.DD.HH.MM - add menu 58 getOrgJseInfo` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs validation +
  build -> `gh run watch` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run container ->
  `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style lazy formatting.
  `INFO` is emitted before the API call ("Fetching JSE info for org %s"); `DEBUG`
  after the call with payload summary ("JSE info: cloud=%s username=%s org_count=%d");
  `WARNING` on 404 / empty payload ("getOrgJseInfo returned no payload for org %s");
  `ERROR` on unexpected exception via `logging.exception`. No secrets, tokens, or
  full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line
  will carry an inline comment that explains *why* the line exists, not merely what
  it does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  org-config export menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before resolving the org_id, `logging.info(...)` before the SDK
  call, the call itself, `logging.debug(...)` after with a payload summary,
  `logging.info(...)` before the DataExporter write, `logging.debug(...)` after the
  write with row count. The DataExporter call already emits its own per-backend log
  lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/609-mist-get-org-jse-info/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_jse_info.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgConfigExportUtils class + new
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 58
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 add
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new org_jse_info SQLite table created on
                         # first run by DataExporter)
documentation/api/orgs/GET_orgs_org_id_setting_jse_info.md
                         # Enriched per-endpoint reference (already exists; cited)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `OrgConfigExportUtils` class in `MistHelper.py` (the
class that owns sibling org-setting read operations in the Safe Org Exports cluster).
If that class is at capacity per the Five-Item Rule at task time, the method moves to
a sibling class in the same cluster -- the `/speckit.tasks` step confirms the host
class against the live source. The menu number proposal is **58**, chosen because the
Safe Org Exports cluster occupies 1-59 and 58 is the next available slot in the Misc
sub-band (56-59) adjacent to other org-scoped configuration reads. The full menu list
will be re-verified at task generation time; if 58 collides with an in-flight feature
branch, the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/get_org_jse_info.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing
  `OrgConfigExportUtils` class. No wrappers introduced. The list-flattening step is a
  single comprehension; it does not require its own helper method.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- All log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or full request
  URLs.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows the
  expected comment density on every executable line, including the new PK strategy
  entry and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt resolution, API call,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
