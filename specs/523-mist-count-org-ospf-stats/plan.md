# Implementation Plan: countOrgOspfStats Menu Item

**Branch**: `523-mist-count-org-ospf-stats` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/523-mist-count-org-ospf-stats/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/stats/ospf_peers/count` (operationId
`countOrgOspfStats`) to return aggregate counts of OSPF peer statistics grouped
by a caller-supplied `distinct` attribute (e.g. `neighbor`, `state`, `area_id`,
`vrf_name`, `device_mac`). The new method is added to the existing
`OrgExportUtils` class in `MistHelper.py` -- the same class that already owns
`OrgExportUtils.ospf_stats()` for `searchOrgOspfStats`. User input is collected
via `safe_input()` for the `org_id` (default pulled from `.env` /
`mistapi.APISession`), the `distinct` field, and an optional time window;
results are persisted through `DataExporter.write_with_format_selection()` so
the CSV, SQLite, and ArangoDB+Redis backends all receive a consistent payload.
A new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` already exists for
`countOrgOspfStats` (line 4456 of `MistHelper.py`) but is currently unused; the
plan formalises and verifies it. The new operation is proposed as menu number
**195** -- the next available integer immediately after the current cap of 194
(see `MistHelper.py` line ~"194":) and inside the safe read-only band (counts
are non-destructive, so it does not need to live in the 154-194 destructive
cluster; if a future renumbering moves safe-read items below 154 the item is
re-slotted at task generation time).

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to the Mist Cloud REST API); `requests` (transport,
transitive); `python-dotenv` for loading `MIST_HOST` and `MIST_API_TOKEN` from
`.env`.
**Storage**: Multi-backend through `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend.
The endpoint returns an aggregate envelope (`distinct`, `start`, `end`, `limit`,
`total`, `results[]`); flattened into one summary row plus N detail rows.
**Testing**: `python MistHelper.py --test` exercises the menu item
non-interactively against a known org loaded from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 195 sits in the destructive
numbering band (154-194 reserved), so it is explicitly added to the test sweep
include-list rather than relying on default range coverage.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200.
Both targets must work without code change.
**Project Type**: CLI tool -- single-file monolith `MistHelper.py` (~28K
lines) with optional Gunicorn web UI on port 8055. This feature lives entirely
in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds; full
paginated retrieval (when `search_after` cursor is followed) bounded by the
Mist rate limit of 5000 calls/hour. Aggregate count payload is small
(<<1 MB) so no streaming or memory tuning required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining via
`os.path.join` / `pathlib.Path`; 5-Item Rule respected (<=25 lines, <=5
parameters, <=5 logical blocks per function).
**Scale/Scope**: One new public method (`count_ospf_stats`) on the existing
`OrgExportUtils` class (~22 lines), verification of the existing
`ENDPOINT_PRIMARY_KEY_STRATEGIES["countOrgOspfStats"]` entry, one new SQLite
table set (`org_ospf_stats_count_summary` and `org_ospf_stats_count_results`),
one menu registration entry at slot 195, one README operation-count bump from
194 -> 195, and one CHANGELOG line. No new dependencies, no new modules, no
new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- `OrgExportUtils.count_ospf_stats()` stays under 25 lines,
  takes <=4 parameters (`self`, `org_id`, `distinct`, `time_range_tuple`), and
  contains <=5 logical blocks (prompt -> validate -> SDK call -> flatten ->
  DataExporter). Hierarchy unchanged: one new method on an existing class. The
  flatten step is a single comprehension; if it grows beyond 5 lines during
  implementation it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behaviour is added as a method on
  `OrgExportUtils` (already houses `ospf_stats()` for the sibling
  `searchOrgOspfStats` endpoint). No standalone wrapper function is added. The
  menu dispatch references the class method directly. Variable names use full
  words (`distinct_field`, `count_row`, `result_rows`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every prompt routes through `safe_input()` with explicit
  `context=` strings (`"count_org_ospf_stats:org_id"`,
  `"count_org_ospf_stats:distinct"`,
  `"count_org_ospf_stats:time_range"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. Endpoint is read-only (HTTP GET); no
  destructive confirmation gate required. `org_id` is validated against the
  Mist UUID shape before the SDK call; on validation failure the method logs
  a warning and returns early. The API token is loaded once via
  `mistapi.APISession` from `.env` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- Standard pipeline applies without modification:
  `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check` ->
  commit with `version YY.MM.DD.HH.MM - add menu 195 countOrgOspfStats` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch <id>` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the SDK call ("Counting OSPF peer stats for org %s
  distinct=%s"), `DEBUG` after the call with the envelope counters
  ("countOrgOspfStats returned total=%d results=%d"), `WARNING` on
  401/403/404, and `ERROR` with `logging.exception` on unexpected exceptions.
  No tokens, full request URLs, or PII are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the verified
  PK strategy entry, and the menu registration line will carry an inline
  comment explaining *why* it exists, not merely *what* it does. Blank lines,
  closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched block (the existing OSPF /
  stats export cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after
  pattern: `logging.info(...)` before each `safe_input()` prompt cluster,
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with `total` and `len(results)`,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write to `DataExporter`. The DataExporter call
  already emits its own per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/523-mist-count-org-ospf-stats/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_ospf_stats.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New count_ospf_stats() method on OrgExportUtils
                         # class + verified ENDPOINT_PRIMARY_KEY_STRATEGIES
                         # entry (already present at line 4456) + menu 195
                         # registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump 194 -> 195 + new row in menu
                         # table for op 195
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry describing
                         # menu 195 addition
data/                    # Runtime output target (existing dir). New SQLite
                         # tables `org_ospf_stats_count_summary` and
                         # `org_ospf_stats_count_results` auto-created on
                         # first run by DataExporter; CSV files
                         # `OrgOspfStatsCountSummary.csv` and
                         # `OrgOspfStatsCountResults.csv` land alongside.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `OrgExportUtils` class in `MistHelper.py`
(the same class housing `ospf_stats()` for the sibling `searchOrgOspfStats`
endpoint at line ~12760). The menu number proposal is **195** -- the next
sequential slot after the current cap at 194. The full menu list will be
re-verified at task generation time; if 195 collides with an in-flight
feature branch, the next free integer is used. The new operation is a safe
read-only count, so it does not require the destructive-confirmation gate
applied to the 154-194 cluster.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks.
  The PK strategy update is a single dictionary entry (already present), so
  no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgExportUtils`.
  No wrappers introduced. Any flatten helper is added as a private method on
  the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms
  the endpoint is GET-only with no destructive side effect. `safe_input()`
  is the documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, validate,
  SDK call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
