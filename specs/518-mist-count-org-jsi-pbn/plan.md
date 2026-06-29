# Implementation Plan: countOrgJsiPbn Menu Item

**Branch**: `518-mist-count-org-jsi-pbn` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/518-mist-count-org-jsi-pbn/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/jsi/pbn/count` (operationId `countOrgJsiPbn`) to retrieve
counts of Juniper Support Insights (JSI) Problem Bulletin Notification (PBN) advisories
grouped by a caller-chosen field (`versions`, `models`, `customer_risk`, or `bug_type`).
The new menu method prompts the user for an `org_id`, a `distinct` group-by field, and
optional time-window bounds via `safe_input()`, invokes the `mistapi` SDK exactly once,
flattens the returned `results` array into one row per group bucket, and persists the
output through `DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all receive consistent records. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` to drive clean SQLite upserts on repeated polls of the
same window. The new operation is proposed as menu number **96** -- the next contiguous
slot inside the Safe Org Exports / Interactive Safe cluster, immediately after spec 500's
proposed slot at 95.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the only
permitted interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv`
(for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and the optional `MIST_ORG_ID`
default).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the new menu item in non-interactive
mode using the `MIST_ORG_ID` default and a default `distinct=models` group-by. Local
quality gates: `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy/destructive skip list (14, 18, 63-65,
90-100) is unaffected -- menu 96 sits inside the standard sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both
environments must run the same code path without modification.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
group-by counts (the endpoint returns a small aggregate object, default `limit=100`).
Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue to govern
back-off; aggregate-count endpoints are light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); 5-Item Rule (<=25 lines, <=5 params, <=5 logical blocks) on the new
method.
**Scale/Scope**: One new public menu method (~20 lines) on a new
`JsiAdvisoryExportUtils` class (no existing JSI class today), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV/SQLite table (`org_jsi_pbn_count`), one
menu registration entry, one README operation-count bump, one CHANGELOG line. No new
third-party dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_jsi_pbn_count()` stays under 25
  lines, takes exactly 4 parameters (`self`, `org_id`, `distinct`, `time_window`) which
  is within the 5-parameter cap, and contains <=5 logical blocks (prompt for org ->
  prompt for distinct field -> prompt for time window -> API call -> flatten + write).
  Hierarchy unchanged: one new method on a single new class
  `JsiAdvisoryExportUtils`. The class is added at the same hierarchy depth as the
  existing `LicenseExportUtils`, `SfpTransceiverDataProcessor`, and other export-utility
  classes -- no new directory, no new module. Time-window prompts are collected into a
  small `(start, end)` tuple inside one helper, keeping the entrypoint method block count
  at five.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `JsiAdvisoryExportUtils` class created specifically to own all `Orgs JSI`-tag
  operations (this is the first JSI endpoint MistHelper exposes; future JSI tagged
  endpoints will hang off the same class, matching the pattern used by
  `LicenseExportUtils` for the license cluster). No standalone wrapper function is
  introduced. Menu dispatch calls the class method directly. Variable names use full
  words (`distinct_field`, `time_window_start`, `group_value`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input flows through `safe_input()` with explicit
  `context=` strings (`"jsi_pbn_count:org_id"`, `"jsi_pbn_count:distinct"`,
  `"jsi_pbn_count:start"`, `"jsi_pbn_count:end"`) so SSH and container EOF exit
  cleanly with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. The `org_id` value is validated
  against the Mist UUID shape via the existing `is_valid_uuid()` helper before the SDK
  call; on validation failure the method logs `WARNING` and returns early. The
  `distinct` value is validated against the API enum (`versions`, `models`,
  `customer_risk`, `bug_type`) before the call; an unknown value triggers a `WARNING`
  and early return. The API token is loaded from `.env` by the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 96 countOrgJsiPbn` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs the validation + container build ->
  `gh run watch <run-id>` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container with the documented `podman run` invocation ->
  `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style lazy formatting.
  `INFO` is emitted before the API call (`"Fetching JSI PBN count for org %s distinct=%s"`);
  `DEBUG` after the call with the response `total` and result-bucket count
  (`"JSI PBN count: total=%d buckets=%d"`); `WARNING` on 404 / empty payload; `ERROR`
  on unexpected exception with full traceback via `logging.exception`. No secrets,
  tokens, URLs containing the token, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, the new class header, and the menu registration line carries an
  inline `#` comment explaining *why* the line exists, not merely what it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution. Any
  adjacent uncommented lines in the touched menu-registration block get comments added
  in the same PR so the entire touched region complies.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before each `safe_input()` prompt, `logging.info(...)` before
  the SDK call, the call itself, `logging.debug(...)` after with `total` and
  `len(results)`, `logging.info(...)` before flatten, `logging.debug(...)` after
  flatten with the row count, `logging.info(...)` before the DataExporter write. The
  DataExporter call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/518-mist-count-org-jsi-pbn/
+-- plan.md              # This file
+-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
+-- data-model.md        # Phase 1 - response entity + DDL + PK registration
+-- quickstart.md        # Phase 1 - local run + .env + quality gates + skeleton
+-- contracts/
|   +-- count_org_jsi_pbn.md         # Phase 1 - HTTP + SDK contract
+-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New class JsiAdvisoryExportUtils + export_org_jsi_pbn_count
                         # method + PK strategy entry + menu 96 registration. No new
                         # modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method `export_org_jsi_pbn_count` on a new `JsiAdvisoryExportUtils` class in
`MistHelper.py`. The class is new because no JSI-tagged endpoint is currently exposed
by MistHelper -- creating a dedicated class (rather than dumping the method onto an
unrelated existing class) keeps the 5-Item Rule honored as future JSI endpoints
(`GET .../jsi/pbn/search`, `GET .../jsi/inventory`, etc.) are added. The menu number
proposal is **96**, chosen because operations 51-95 are the Safe Org Exports /
Org-License cluster (spec 500 proposes 95), 96-101 are Resource Intensive, and a
read-only aggregate count fits the "interactive safe" classification; 96 is the next
available integer. The exact number is re-verified at `/speckit.tasks` time by grepping
`MistHelper.py` for the highest-allocated menu integer.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/count_org_jsi_pbn.md`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The skeleton in `quickstart.md` confirms
  <=25 lines, exactly 4 parameters, and 5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary takes a single new entry; the new class
  takes a single method; both stay within the level-5 hierarchy cap.
- **Principle II (Class-Based)**: PASS -- All work lives on the new
  `JsiAdvisoryExportUtils` class. No wrappers. Flattening logic is inlined as a single
  list comprehension; if it grows past 5 lines it is extracted to a private method
  `_flatten_pbn_count_results` on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only with no destructive side effect. `safe_input()` is the documented prompt
  path. Both the org UUID and the `distinct` enum are validated before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with lazy `%s` formatting and never include the API token or full request URL.
- **Principle VI (Inline Comments)**: PASS -- The quickstart skeleton demonstrates the
  required comment density on every executable line, including the PK strategy entry,
  the new class header, and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The quickstart enumerates the
  before/after log pairs for every meaningful action (each prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
