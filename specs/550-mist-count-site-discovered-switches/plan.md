# Implementation Plan: countSiteDiscoveredSwitches Menu Item

**Branch**: `550-mist-count-site-discovered-switches` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/550-mist-count-site-discovered-switches/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/stats/discovered_switches/count` (operationId
`countSiteDiscoveredSwitches`) to retrieve the number of unmanaged switches discovered at
a site, optionally grouped by a `distinct` attribute (vendor, model, OS version, etc.).
The menu method prompts the user for a `site_id` via `safe_input()`, accepts optional
`distinct`, `start`, `end`, `duration`, and `limit` query parameters using `.env`-backed
defaults, calls the `mistapi` SDK, flattens the count envelope plus its `results` array
into one summary row and zero-or-more per-group rows, then persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. Two new entries are registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated polls. The new
operation is proposed as menu number **91** -- the next available slot in the site-stats
sub-cluster (80-91) of the Interactive Safe range (60-96), sitting adjacent to existing
site device-stats viewers.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv`
(`.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and `MIST_SITE_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend. Two new tables
(`site_discovered_switches_count_summary`, `site_discovered_switches_count_groups`).
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using the `MIST_SITE_ID` configured in `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The skip list (14, 18, 63-65, 90-100) does not
affect menu 91; it sits comfortably below the 90-100 destructive bracket.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both must
work without code change. Paths use `os.path.join` / `pathlib.Path` only.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical sites; the
endpoint is a server-side aggregation and the response is small (one envelope plus the
`results` array, capped by the user-supplied `limit`, default 100). No pagination work is
required on the client side. Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining; the `distinct` value must be
forwarded verbatim to the SDK without client-side filtering (the API owns the enum set).
**Scale/Scope**: One new public menu method (~22 lines) on a new
`DiscoveredSwitchesStatsUtils` class (justification below), two new entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new SQLite tables, one menu registration entry,
one README operation-count bump, one CHANGELOG line. No new third-party dependencies, no
new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_site_discovered_switches_count()` stays under 25 lines, takes <=5 parameters
  (`self`, `site_id`, `distinct`, `duration`, `limit`), and contains <=5 logical blocks
  (prompt -> validate -> API call -> flatten summary + groups -> DataExporter writes).
  Two private flatten helpers on the same class each stay under 25 lines and <=5
  parameters. Hierarchy is unchanged at the package/module level -- everything still
  lives inside `MistHelper.py`. The new class adds one level-4 entry (a class) and at
  most three level-5 entries (the public method plus two private helpers), well inside
  the 5-children-per-level limit.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- A new class `DiscoveredSwitchesStatsUtils` is introduced because
  no existing class owns the "Sites Stats - Discovered Switches" tag cluster. Adjacent
  endpoints (`searchSiteDiscoveredSwitches`,
  `getSiteDiscoveredSwitchesMetrics` per `documentation/api/sites/`) will move under the
  same class as they are catalogued in later specs, giving the cluster a single home.
  No standalone wrapper function is introduced; the menu dispatch in the main loop
  references the class method directly. Variable names use full words (`group_row`,
  `total_count`); no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every user input is collected through `safe_input()` with explicit
  `context=` strings (`"site_discovered_switches_count:site_id"`,
  `"site_discovered_switches_count:distinct"`, etc.) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. `site_id` is validated against
  the Mist UUID shape via the existing `is_valid_uuid()` helper before the API call; on
  validation failure the method logs a `WARNING` and returns early. API token is loaded
  from `.env` by `mistapi.APISession` and never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 91 countSiteDiscoveredSwitches` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  precedes the API call (`"Counting discovered switches at site %s (distinct=%s)"`);
  `DEBUG` after the call summarizes counts
  (`"Discovered switches count: total=%d groups=%d"`); `WARNING` on 404 or empty
  payload; `ERROR` on unexpected exception via `logging.exception`. No secrets, tokens,
  or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the two new PK strategy
  dictionary entries, the new class declaration, and the menu registration line will
  carry an inline `#` comment explaining *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched class scope receive comments in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call; the SDK call itself; `logging.debug(...)` after with a count
  summary; `logging.info(...)` before flatten; `logging.debug(...)` after flatten;
  `logging.info(...)` before each write; `logging.debug(...)` after each write. The
  DataExporter call already emits per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. The Complexity Tracking table remains
empty at this gate.

## Project Structure

### Documentation (this feature)

```text
specs/550-mist-count-site-discovered-switches/
|- plan.md              # This file
|- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|- data-model.md        # Phase 1 - response entities + DDL + PK registration
|- quickstart.md        # Phase 1 - local run + .env + quality gates
|- contracts/
|  \- count_site_discovered_switches.md   # Phase 1 - HTTP + SDK contract
\- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New DiscoveredSwitchesStatsUtils class + menu 91 method +
                         # two ENDPOINT_PRIMARY_KEY_STRATEGIES entries + menu
                         # registration. Same single-file monolith; no new modules.
README.md                # Operation count bump + new row in the menu table for op 91
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 91 addition
data/                    # Runtime output target (existing dir, new SQLite tables
                         # created on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on a new `DiscoveredSwitchesStatsUtils` class in `MistHelper.py`. A new class is
justified because no existing class owns the "Sites Stats - Discovered Switches" tag
cluster, and per Principle II the class must exist before any wrapper-free implementation
can live there. The menu number proposal is **91**, chosen because the site-stats
sub-cluster occupies operations 80-91 and 91 is the next contiguous integer below the
heavy / destructive bracket at 92-101. Final number is re-verified at task generation
time; if 91 collides with an in-flight feature branch, the next free integer in the same
site-stats cluster (89 if free, else 88 backfilled, else 92+ shifted) is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/count_site_discovered_switches.md`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method skeleton in `quickstart.md`
  confirms <=25 lines, <=5 parameters, <=5 logical blocks. The two
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` insertions are single dict-literal entries (existing
  structure), so no level-5 hierarchy explosion. The new class has exactly three
  level-5 members (one public, two private), well inside the 5-children limit.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `DiscoveredSwitchesStatsUtils`. No wrappers introduced. The two flatten helpers are
  private methods on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path for all five prompts. UUID validation happens before the SDK call. The optional
  `distinct`, `start`, `end`, `duration`, and `limit` parameters are forwarded verbatim
  to the SDK; the API rejects bad values with 400, which MistHelper surfaces as a
  `WARNING` log line.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token. ArangoDB / Redis writes inherit
  the DataExporter's existing per-backend log lines.
- **Principle VI (Inline Comments)**: PASS -- The `quickstart.md` skeleton shows the
  expected comment density on every executable line, including the new class header,
  both PK strategy entries, and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The `quickstart.md` skeleton enumerates
  the before/after log pairs for every meaningful action (prompt, validate, API call,
  flatten summary, flatten groups, summary export, groups export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
