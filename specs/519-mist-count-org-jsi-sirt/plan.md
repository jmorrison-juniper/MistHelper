# Implementation Plan: countOrgJsiSirt Menu Item

**Branch**: `519-mist-count-org-jsi-sirt` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/519-mist-count-org-jsi-sirt/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/jsi/sirt/count` (operationId `countOrgJsiSirt`) to return
the count of Juniper Security Incident Response Team (SIRT) advisories grouped by a
caller-selected field (`jsa_updated_date`, `models`, `severity`, or `versions`). The new
menu method prompts the operator for the `org_id` and the `distinct` grouping field --
plus optional `limit`, `start`, `end` window controls -- via `safe_input()`, calls
`mistapi.api.v1.orgs.jsi.countOrgJsiSirt()`, flattens the dynamic `results` array
(each row has a guaranteed `count` integer plus one additional string property whose
name matches the `distinct` value), and persists the data with
`DataExporter.write_with_format_selection()` so the CSV, SQLite, and ArangoDB+Redis
backends all receive the same rows. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` to make repeated runs upsert cleanly. The operation is
proposed as menu number **219**, the next sequential slot in the SIRT/JSI catalog
cluster being filled by the parallel "Mist API endpoint cataloging" branch series; the
exact integer is re-verified at task generation time and bumped to the next free value
if it collides with an already-merged feature branch.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend when active.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy/destructive skip list (14, 18, 63-65, 90-100) is unaffected --
proposed menu 219 is read-only and safe to include in the default test sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical SIRT
result sets (the `count` endpoint returns a bounded aggregate, not paginated raw
records). Adaptive delay in `delay_metrics.json` and `tuning_data.json` continues to
govern back-off; this endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` / `pathlib`).
**Scale/Scope**: One new public menu method (~22 lines) on a new lightweight
`JsiSirtExportUtils` class (the existing JSI cluster is small enough that a dedicated
class keeps the Five-Item Rule satisfied as additional JSI operations land); one new
entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`; one new SQLite table
(`org_jsi_sirt_count`); one menu registration entry; one README operation-count bump;
one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `export_org_jsi_sirt_count()` stays under 25 lines,
  takes <=5 parameters (`self`, `org_id`, `distinct`, `limit`, `start`, `end` -- the
  optional window args are collapsed into a single `**window` mapping if the count would
  exceed five), and contains <=5 logical blocks (collect prompts -> validate -> API
  call -> flatten results -> DataExporter call). The new class `JsiSirtExportUtils`
  starts with one method; the cluster will grow as adjacent JSI endpoints are cataloged
  but will be split into separate classes well before a fifth method is added.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- All behavior is added as a method on the new `JsiSirtExportUtils`
  class. No standalone wrapper function is introduced. Menu dispatch in the main loop
  references the class method directly. Variable names use full words
  (`distinct_field`, `count_row`, `window_start`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All four prompts (`org_id`, `distinct`, optional `start`, optional
  `end`) go through `safe_input()` with explicit `context=` strings
  (`"org_jsi_sirt_count:org_id"`, `"org_jsi_sirt_count:distinct"`,
  `"org_jsi_sirt_count:start"`, `"org_jsi_sirt_count:end"`). EOF in SSH / container
  contexts exits cleanly with code 0. The endpoint is strictly read-only (HTTP GET), so
  no typed destructive-confirmation gate is required. `distinct` is validated against
  the four-value enum before the SDK call and an out-of-range value is rejected with a
  warning and an early return. `org_id` is checked against the Mist UUID shape. API
  token loads from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 219 countOrgJsiSirt` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  before the API call ("Fetching JSI SIRT count for org %s distinct=%s"); `DEBUG` after
  the call with summary counts ("JSI SIRT count: total=%d groups=%d"); `WARNING` on
  404 / empty results; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line carries an inline comment that
  explains *why* the line exists. Blank lines, closing parentheses, and decorators are
  exempt per the constitution. Any uncommented adjacent lines in the touched menu
  cluster get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before prompt collection, `logging.debug(...)` after with the
  collected (non-sensitive) parameters, `logging.info(...)` before the SDK call, the
  call itself, `logging.debug(...)` after with `total` and `len(results)`,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write, `logging.debug(...)` after write. The DataExporter
  call already emits per-backend log lines and is not duplicated.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/519-mist-count-org-jsi-sirt/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_jsi_sirt.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New JsiSirtExportUtils class with export_org_jsi_sirt_count()
                         # method + ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 219
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 219
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 219 add
data/                    # Runtime output target (existing dir, no schema migration
                         # beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a method on
a new lightweight `JsiSirtExportUtils` class in `MistHelper.py`. A dedicated class is
justified because the JSI/SIRT cluster currently has no owning class in the codebase --
creating one now establishes the seam for adjacent JSI catalog endpoints (search SIRT,
JSI inventory, JSI device metrics) that other parallel specs in the 500-525 branch
series will populate, and keeps each class well under the Five-Item Rule's five-method
guideline. The menu number proposal is **219**, chosen as the next sequential slot above
the current top-of-menu 194 inside the JSI/security catalog cluster being filled by
specs 500-525+. If 219 collides with an already-merged sibling branch at task time, the
next free integer is used and the README / CHANGELOG entries are updated accordingly.

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
  `quickstart.md` confirms <=25 lines, <=5 explicit parameters with the optional window
  args collapsed when needed, and <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion. The new class starts with one method.
- **Principle II (Class-Based)**: PASS -- All work lives on `JsiSirtExportUtils`. No
  wrappers introduced. Flattening helpers, if needed, become private methods on the
  same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID and `distinct` enum validation both happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates the
  before/after log pairs for prompt, validation, API call, flatten, and export.

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
