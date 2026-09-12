# Implementation Plan: GetMspSle Menu Item

**Branch**: `587-mist-get-msp-sle` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/587-mist-get-msp-sle/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}/insights/{metric}` (operationId `getMspSle`) to retrieve
Service Level Expectation (SLE) aggregates at MSP scope across all managed organizations.
The menu item prompts the user for `msp_id` and `metric` via `safe_input()`, optionally
collects query-window selectors (`sle`, `duration`, `interval`, `start`, `end`) using the
same prompt path with sensible defaults, invokes the `mistapi` SDK once, augments the
returned aggregate object with the path parameters and query window so each row is
self-describing, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on `(msp_id, metric, start, end, interval)` so
repeated runs with the same query window upsert cleanly into SQLite. The new operation
is proposed as menu number **59** -- the next available slot in the Misc cluster (56-59),
adjacent to the existing SLE cluster (51-55) and the org-level SLE exporters at 57-62.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend when configured.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known MSP ID and a default metric from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65,
90-100) is unaffected -- new item 59 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint is
non-paginated, returns a single aggregate object with a `results` array sized by the
chosen `interval` over the chosen window (typically <100 KB for a 1-day window at 1-hour
intervals). Existing back-off via `delay_metrics.json` and `tuning_data.json` applies
unchanged; the `--fast` flag caps retries.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); the `results` field is a heterogeneous array (numbers OR objects
depending on the metric) and must be persisted as a JSON string so SQLite/CSV can carry
the variable shape without schema migration per metric.
**Scale/Scope**: One new public method (~22 lines) on a new lightweight class
`MspSLEExporter` (justified below under Structure Decision), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV/SQLite table (`msp_sle`), one menu
registration line, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_msp_sle()` stays under 25 lines and
  takes <=5 parameters (`self`, `msp_id`, `metric`, optional `sle`, optional `window`
  dict carrying `duration`/`interval`/`start`/`end` as a single grouped param). The
  method body contains <=5 logical blocks (validate IDs / build query window / API call
  / build row / DataExporter call). Hierarchy adds one new class (`MspSLEExporter`) with
  one method, one new dict entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, and one new menu
  registration line. The new class introduces one level-4 unit (the class itself) and
  one level-5 unit (the method), well within the 5-per-level limit at every tier.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new dedicated class
  `MspSLEExporter`, parallel to the existing `OrgSLEExporter` (operations 57-62). A new
  class is justified because MSP scope is semantically distinct from org scope (it
  aggregates across orgs rather than within one), the input contract differs (`msp_id`
  vs `org_id` and a free-form `metric` path param), and the output table differs
  (`msp_sle` vs `org_sle`). No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names use
  full words (`msp_identifier`, `sle_metric_name`, `msp_sle_row`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"msp_sle:msp_id"`, `"msp_sle:metric"`, `"msp_sle:duration"`,
  `"msp_sle:interval"`, `"msp_sle:start"`, `"msp_sle:end"`, `"msp_sle:sle"`) so SSH and
  container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. The
  `msp_id` is validated against the Mist UUID shape; the `metric` string is validated
  against a non-empty length and absence of path separators (rejects `..`, `/`, `\`)
  before being passed to the SDK. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 59 getMspSle` -> `git push origin
  main` -> `.github/workflows/container-build.yml` runs validation + build -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching MSP SLE metric %s for msp %s window=%s");
  `DEBUG` after the call with result-count summary ("MSP SLE response: results=%d
  start=%d end=%d interval=%d"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. The full `results`
  array contents are *not* logged at INFO -- only the count and time-window summary. No
  secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new class definition,
  the new PK strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched block (the existing SLE-exporter menu
  cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a count summary,
  `logging.info(...)` before write, `logging.debug(...)` after write. The DataExporter
  call already emits its own per-backend log lines; the new method does not duplicate
  them. Validation failures and 4xx responses log a `WARNING` line with the failure
  reason and the offending identifiers (never the token).

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/587-mist-get-msp-sle/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_msp_sle.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New class MspSLEExporter with method export_msp_sle() +
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry for getMspSle +
                         # menu 59 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 59
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 59
                         # addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a method
on a new class `MspSLEExporter` that lives alongside the existing `OrgSLEExporter`
class in `MistHelper.py`. A new class is justified under Principle II because MSP scope
is a distinct domain (cross-org aggregation) with a distinct input contract (`msp_id` +
free-form `metric` path param) and a distinct output table (`msp_sle`). The constitution
permits new classes when scope/concern is distinct; collapsing MSP-level methods into
the org-level exporter would muddy the class purpose and force every method body to
re-branch on scope, which is the kind of conditional sprawl the class-based architecture
principle exists to prevent. The menu number proposal is **59**, chosen because it sits
in the Misc cluster (56-59) adjacent to the org-level SLE exporters at 57-62 and the
SLE cluster proper at 51-55, making the operation easy to find for users already
exploring SLE data. The full menu list will be re-verified at task generation time; if
59 collides with an in-flight feature branch, the next free integer in the same cluster
(or the next contiguous free integer above 50) is used.

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
  `quickstart.md` confirms <=25 lines, <=5 parameters (after grouping the four optional
  query-window selectors into a single `window` dict), <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on a single new class with one
  method. No wrappers introduced. The query-window builder is two `.get()` calls inline
  -- no extraction needed.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path for all required and optional selectors. UUID validation on `msp_id` and
  shape/length validation on `metric` happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token. The `results` array is logged
  only at DEBUG and only by item count.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry, the class
  definition, and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompts, API call, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
