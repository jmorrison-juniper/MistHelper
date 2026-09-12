# Implementation Plan: countOrgWiredClients Menu Item

**Branch**: `537-mist-count-org-wired-clients` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/537-mist-count-org-wired-clients/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/wired_clients/count` (operationId `countOrgWiredClients`)
to return a distinct-attribute count of wired clients (devices connected to EX switch
ports) within an organization over a configurable time window. The menu item prompts
the user via `safe_input()` for the org ID (with `MIST_ORG_ID` from `.env` as default),
the `distinct` field to group by, and an optional time range (`start` / `end` /
`duration`) plus `limit`; it then calls the `mistapi` SDK function
`mistapi.api.v1.orgs.wired_clients.count.countOrgWiredClients()`, flattens the
envelope-plus-results payload into one summary row and N result rows, and persists
the data via `DataExporter.write_with_format_selection(data, filename,
api_function_name="countOrgWiredClients")` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeat runs upsert cleanly on the composite
(org_id, distinct, distinct_value, start, end) key. The new operation is proposed
as menu number **88** -- the next available slot inside the Stats cluster (80-91)
where adjacent operations already export per-org count and distinct-attribute data;
the number will be re-verified against the live menu registry at `/speckit.tasks`
time and bumped to the next free integer in the same cluster if a parallel feature
branch has already claimed it.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints; matches the existing `MistHelper.py` runtime baseline).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's SDK -- the only permitted
interface to the Mist Cloud per Constitution); `requests` (HTTP transport,
transitive via mistapi); `python-dotenv` for `.env` loading of `MIST_HOST`,
`MIST_API_TOKEN`, and `MIST_ORG_ID`.
**Storage**: Multi-backend through `DataExporter.write_with_format_selection()`.
Local fallback is SQLite at `data/mist_data.db`; CSV files land under `data/`;
polyglot ArangoDB + Redis containers (see spec 188) handle graph + cache backends.
A new SQLite table `org_wired_clients_count` is created on first run by
`DataExporter` based on the inferred schema plus the registered PK strategy.
**Testing**: `python MistHelper.py --test` exercises the menu item non-interactively
using `MIST_ORG_ID` from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) is
unaffected -- menu 88 sits inside the default automated test sweep.
**Target Platform**: Windows 11 + venv for local development; Podman Linux
container `ghcr.io/jmorrison-juniper/misthelper:latest` for production and the
SSH-on-2200 surface; both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` at ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a typical
distinct-count payload (the endpoint returns an aggregate envelope plus a bounded
`results` array of at most `limit` entries; default limit 100). Adaptive delay
metrics in `delay_metrics.json` and `tuning_data.json` continue to govern back-off;
this endpoint is light enough that no special tuning is required and `--fast` mode
behaves identically to the rest of the stats cluster.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt (with explicit
`context=` strings); no API tokens, secrets, or raw URLs in any log line; all
output under `data/`; Windows-safe path joining via `os.path.join` / `pathlib.Path`;
no Unicode in code, comments, or log strings.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`WiredClientExportUtils` class (the same class that already owns `searchOrgWiredClients`
and related wired-client exports); one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
(composite key); one new SQLite table `org_wired_clients_count`; one menu
registration entry; one README operation-count bump and menu-table row; one
CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_wired_clients_count()` stays
  under 25 lines, takes <=5 parameters (`self`, `org_id`, `distinct`, `time_window`,
  `limit`), and contains <=5 logical blocks (prompt -> validate -> API call ->
  flatten -> DataExporter call). Hierarchy unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are
  introduced. The result-array flattener is a single comprehension; if it
  grows past 5 lines during implementation, it is extracted to a private helper
  `_flatten_count_results()` on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `WiredClientExportUtils` class, which already owns `searchOrgWiredClients` and
  related wired-client exports. No standalone wrapper function is introduced.
  The menu dispatch table in the main menu loop references the class method
  directly via the existing registration pattern. Variable names use full words
  (`distinct_field`, `count_result_row`, `time_window_args`) -- no single-letter
  iterators in the new code.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"wired_clients_count:org_id"`,
  `"wired_clients_count:distinct"`, `"wired_clients_count:duration"`,
  `"wired_clients_count:limit"`) so SSH / container EOF terminates cleanly with
  exit code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. The org UUID is
  validated against the Mist UUID shape before the SDK call; on validation
  failure the method emits `logging.warning(...)` and returns early. API token
  comes from `.env` via the existing shared `mistapi.APISession` instance and
  is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation, the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` -> `python -m black --check MistHelper.py`
  -> commit with `version YY.MM.DD.HH.MM - add menu 88 countOrgWiredClients`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch <id>` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification. No new CI jobs, no new build steps.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style lazy
  formatting. `INFO` is emitted before the API call ("Counting wired clients
  for org %s distinct=%s"); `DEBUG` after the call with summary counts
  ("Wired client count: total=%d distinct_values=%d limit=%d"); `WARNING` on
  404 or empty `results`; `ERROR` on unexpected exception with full traceback
  via `logging.exception(...)`. No tokens, full request URLs, or `Authorization`
  headers are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration
  line will carry an inline comment that explains *why* the line exists, not
  merely what it does. Blank lines, closing parentheses, and decorators are
  exempt per the Constitution. Any uncommented adjacent lines in the touched
  wired-client export block are commented in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after
  pattern: `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with `result["total"]` and `len(result["results"])`,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten with
  row count, `logging.info(...)` before write, `logging.debug(...)` after
  write. The DataExporter call emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/537-mist-count-org-wired-clients/
+- plan.md              # This file
+- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
+- data-model.md        # Phase 1 - response entities + DDL + PK registration
+- quickstart.md        # Phase 1 - local run + .env + quality gates
+- contracts/
|  +- count_org_wired_clients.md   # Phase 1 - HTTP + SDK contract
+- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on WiredClientExportUtils class + PK strategy
                         # registration + menu 88 dispatch entry. No new modules;
                         # same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 88
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 88 addition
data/                    # Runtime output target (existing dir). DataExporter will
                         # create the new SQLite table `org_wired_clients_count` on
                         # first run; no manual schema migration required.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `WiredClientExportUtils` class in `MistHelper.py`
(the same class that already owns `searchOrgWiredClients` and related wired-client
exports). The menu number proposal is **88**, chosen because operations 80-91 are
the Stats cluster -- a natural home for a distinct-attribute count endpoint --
and 88 is the next available slot below the destructive block at 90-100. The
full menu list will be re-verified at `/speckit.tasks` time; if 88 collides
with an in-flight feature branch (parallel SpecKit specs frequently pick
adjacent integers), the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/count_org_wired_clients.md`), the seven principles
are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary insert is a single key-value pair
  (existing dict structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `WiredClientExportUtils`. No wrapper functions introduced. Flattening helper,
  if extracted, becomes a private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET-only with no destructive side effect. `safe_input()` is the
  documented prompt path for every user-facing input. UUID validation happens
  before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
  The new SQLite table is created lazily by `DataExporter` on first run; no
  manual migration step.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token, the full
  Mist API URL, or any header values.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected inline-comment density on every executable line, including the
  PK strategy entry and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
