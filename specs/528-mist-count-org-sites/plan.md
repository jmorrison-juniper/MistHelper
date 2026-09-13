# Implementation Plan: countOrgSites Menu Item

**Branch**: `528-mist-count-org-sites` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/528-mist-count-org-sites/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/sites/count` (operationId `countOrgSites`) to return the
aggregated count of org sites grouped by a caller-supplied `distinct` attribute (for
example `country_code`, `sitegroup_id`, `rftemplate_id`). The menu method prompts the
user for the `org_id` and the optional `distinct`, `start`, `end`, `duration`, and
`limit` query parameters via `safe_input()`, invokes
`mistapi.api.v1.orgs.sites.countOrgSites()`, flattens the response envelope plus the
nested `results[]` count buckets into rows, and persists everything through
`DataExporter.write_with_format_selection()` so the CSV, SQLite, and ArangoDB+Redis
backends all stay consistent. A new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keeps
SQLite upserts idempotent on repeated runs. The new operation is proposed as menu
number **58**, the next free slot in the safe-org-exports Misc 56-59 cluster, sitting
next to the existing `listOrgSites`-family entries.

## Technical Context

**Language/Version**: Python 3.13+ per the constitution Technology & Compatibility
Constraints. The MistHelper.py monolith is already 3.13 compatible.
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land under `data/`;
ArangoDB + Redis containers provide the polyglot graph + cache backend. Two new
SQLite tables are introduced: `org_sites_count_summary` (one envelope row per call)
and `org_sites_count_results` (one row per `results[]` bucket).
**Testing**: `python MistHelper.py --test` exercises the menu item non-interactively
using `MIST_ORG_ID` from `.env` and a default `distinct=country_code`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- menu 58 sits in the safe sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH on port 2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines) with
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical orgs
(the count endpoint returns one envelope object with a bounded `results[]` array
controlled by `limit`, default 100). The adaptive delay system
(`delay_metrics.json` + `tuning_data.json`) governs back-off; no special tuning is
required because the endpoint is single-page-by-design.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no API token
in any log line or URL trace; all output under `data/`; Windows-safe path joining
via `os.path.join` / `pathlib.Path`.
**Scale/Scope**: One new public method (~20 executable lines) on the existing
`SiteExportUtils` class (the same class that owns `listOrgSites` and
`searchOrgSites` exports), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two
new SQLite tables created on first run by `DataExporter`, one menu registration
line, one README operation-count bump, one CHANGELOG entry. No new third-party
dependencies, no new top-level modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `export_org_sites_count()` stays at <=25
  executable lines, takes <=5 parameters (`self`, `org_id`, `distinct`, `duration`,
  `limit`), and contains <=5 logical blocks (prompt -> validate -> SDK call ->
  flatten envelope + results -> DataExporter call). Hierarchy adds one method to
  an existing class; no new package, module, or top-level constant is created. If
  the flattening grows past five lines during implementation, it is extracted to a
  private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `SiteExportUtils` class (the home of every other `*OrgSites*` export). No
  standalone wrapper function is introduced. Menu dispatch calls the class method
  directly. Variable names use full words (`distinct_field`, `count_bucket_row`,
  `summary_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input flows through `safe_input()` with explicit
  `context=` strings (`"count_org_sites:org_id"`, `"count_org_sites:distinct"`,
  `"count_org_sites:duration"`, `"count_org_sites:limit"`) so SSH / container EOF
  exits cleanly with status 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET); no destructive-confirmation gate is required. The `org_id` is
  validated against the Mist UUID shape before the SDK call; failures log a
  warning and return early. The API token is loaded from `.env` via the existing
  `mistapi.APISession` and is never echoed.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- The standard pipeline applies unchanged after
  implementation: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 58
  countOrgSites` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls are ASCII text using `%s` style formatting.
  `INFO` is emitted before the SDK call ("Counting sites for org %s by distinct=%s");
  `DEBUG` after with the bucket count and `total` value ("countOrgSites returned
  total=%d buckets=%d"); `WARNING` on 404 or empty `results[]`; `ERROR` on
  unexpected exception via `logging.exception`. API token, raw cookies, and full
  URL with query string are never logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line carries
  an inline comment explaining *why* the line exists. Adjacent uncommented lines
  in the touched block of `SiteExportUtils` are commented in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before prompt collection, `logging.debug(...)` after with
  the captured values (UUID redacted to first eight characters);
  `logging.info(...)` before the SDK call, `logging.debug(...)` after with the
  envelope `total` and `len(results)`; `logging.info(...)` before flatten,
  `logging.debug(...)` after with row count; `logging.info(...)` before export.
  `DataExporter` emits its own per-backend log lines, so the method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. The Complexity Tracking table is left
empty at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/528-mist-count-org-sites/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK strategy entry
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_sites.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SiteExportUtils class + PK strategy entry +
                         # menu 58 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58
data/                    # Runtime output target (existing dir, no schema migration
                         # required beyond the two new SQLite tables created on
                         # first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `SiteExportUtils` class in `MistHelper.py` (the home
of every other `*OrgSites*` export). The menu number proposal is **58**, chosen
because the Safe Org Exports band reserves 1-59, the Sites sub-cluster is 1-7 (full),
and 56-59 is the Misc slot for aggregate / count / summary operations. If 58
collides with an in-flight branch at task-generation time, the next free integer in
the same Misc slot (59) is taken without re-planning.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/count_org_sites.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` change is a single dictionary insert; no
  level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `SiteExportUtils`. No
  wrapper functions introduced. Flatten helpers, if needed, are private methods on
  the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET-only with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation runs before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and
  the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, SDK call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
