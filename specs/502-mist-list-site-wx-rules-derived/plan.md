# Implementation Plan: ListSiteWxRulesDerived Menu Item

**Branch**: `502-mist-list-site-wx-rules-derived` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/502-mist-list-site-wx-rules-derived/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/wxrules/derived` (operationId `ListSiteWxRulesDerived`) to
retrieve the effective (derived/resolved) WxLAN rule set actually enforced at a site --
including rules inherited from org-level WxLAN templates. The menu item prompts the user
for a `site_id` via `safe_input()`, invokes the `mistapi` SDK, flattens the JSON array
of `wxlan_rule` objects (with their list-valued tag fields joined into pipe-delimited
strings for CSV friendliness), and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **96** -- the next available slot in the Interactive
Safe / site-export cluster (60-96), sitting adjacent to other site-scoped read-only
exports and below the Resource Intensive block at 97-101.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer''s Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known site from `.env` (`MIST_SITE_ID`). Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65,
90-100) is unaffected -- new item 96 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a typical site
WxLAN rule set (the endpoint is non-paginated and the response is a flat JSON array,
typically <100 entries). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SiteExportUtils` class (the same class that owns sibling site-scoped read exports such
as `listSiteWlans`, `listSiteWxTags`, and `listSiteDevices`), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV/SQLite table
(`site_wxrules_derived`), one menu registration entry, one README operation-count bump,
one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_site_wxrules_derived()` stays under
  25 lines, takes <=2 parameters (`self`, `site_id`), and contains <=5 logical blocks
  (prompt -> validate UUID -> API call -> flatten list-valued tag fields -> DataExporter
  call). Hierarchy is unchanged: one new method on an existing class. No new packages,
  modules, or top-level constants are introduced. The flatten step joins six list-valued
  fields (`apply_tags`, `blocked_apps`, `dst_allow_wxtags`, `dst_deny_wxtags`,
  `dst_wxtags`, `src_wxtags`) into pipe-delimited strings via a single dictionary
  comprehension; if that comprehension exceeds 5 lines during implementation, the
  per-row transform is extracted to a private `_flatten_wxrule_row()` helper on the
  same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `SiteExportUtils` class (the same class that owns other site-scoped read exports such
  as `listSiteWlans` and `listSiteWxTags`). No standalone wrapper function is
  introduced. The menu dispatch in the main loop references the class method directly.
  Variable names use full words (`derived_rule`, `wxrule_row`, `tag_uuid_list`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with an
  explicit `context=` string (`"site_wxrules_derived:site_id"`) so SSH / container EOF
  exits cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate is required. The `site_id` is
  validated against the Mist UUID shape before the API call; on validation failure the
  method logs a warning and returns early. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 ListSiteWxRulesDerived`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching derived WxLAN rules for site %s"); `DEBUG`
  after the call with the response length ("Received %d derived WxLAN rules for site
  %s"); `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full
  traceback via `logging.exception`. No secrets, tokens, or full request URLs are
  logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing site-export menu cluster) get comments added
  in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with a result count, `logging.info(...)` before flatten, `logging.debug(...)` after
  flatten, `logging.info(...)` before write, `logging.debug(...)` after write. The
  DataExporter call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/502-mist-list-site-wx-rules-derived/
+-- plan.md              # This file
+-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
+-- data-model.md        # Phase 1 - wxlan_rule entity + DDL + PK registration
+-- quickstart.md        # Phase 1 - local run + .env + quality gates
+-- contracts/
|   +-- list_site_wx_rules_derived.md   # Phase 1 - HTTP + SDK contract
+-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SiteExportUtils class + PK strategy entry +
                         # menu 96 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir). DataExporter creates the
                         # new CSV file site_wxrules_derived_<site>_<ts>.csv and the
                         # new SQLite table site_wxrules_derived on first run; no manual
                         # schema migration required.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `SiteExportUtils` class in `MistHelper.py` (the same class that
owns the other site-scoped read exports). The menu number proposal is **96**, chosen
because operations 60-96 are the Interactive Safe site-scoped cluster and 96 is the
next available slot below the Resource Intensive block at 97-101. The full menu list
will be re-verified at task generation time; if 96 collides with an in-flight feature
branch (for example sibling spec branches 500-510 that all target adjacent numbers in
the same cluster), the next free integer in the same cluster is used and the README /
CHANGELOG entries are updated to match.

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
  `quickstart.md` and the entity model in `data-model.md` confirm <=25 lines, <=2
  parameters, <=5 logical blocks. The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is
  a single insert (existing structure), so no level-5 hierarchy explosion. The
  flatten step touches six list-valued fields but does so via a single comprehension.
- **Principle II (Class-Based)**: PASS -- All work lives on `SiteExportUtils`. No
  wrappers introduced. The optional `_flatten_wxrule_row()` helper, if extracted, is a
  private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call. The `wxlan_rule.id` field is the
  natural primary key per the response schema, with `site_id` as the foreign key /
  composite-key partner because the endpoint is site-scoped.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
