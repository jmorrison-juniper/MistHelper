# Implementation Plan: countOrgPskPortalLogs Menu Item

**Branch**: `526-mist-count-org-psk-portal-logs` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/526-mist-count-org-psk-portal-logs/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/pskportals/logs/count` (operationId
`countOrgPskPortalLogs`) to retrieve a count of PSK Portal log events grouped by a
caller-chosen distinct attribute (for example `admin_id`, `psk_id`, `ssid`, or
`status`) over a configurable time window. The menu method prompts the user via
`safe_input()` for the org UUID, the `distinct` attribute, and the time-range knobs
(`start`, `end`, `duration`, `limit`), invokes the `mistapi` SDK once, flattens the
`results[]` aggregate array into one row per distinct bucket, and persists the rows
through `DataExporter.write_with_format_selection(data, filename,
api_function_name=...)` so CSV, SQLite, and ArangoDB+Redis backends all receive
consistent output. A new entry is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
so re-running the menu item over the same window upserts cleanly (no duplicate
buckets). The new operation is proposed as menu number **89** -- a free slot inside
the Interactive Safe cluster (60-96) alongside other PSK / security read items;
the number is re-confirmed at `/speckit.tasks` time by grepping the latest menu
allocations in `MistHelper.py`.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the only
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, and the optional
`MIST_ORG_ID` default from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land under `data/`;
polyglot ArangoDB + Redis containers handle the graph and cache backends.
**Testing**: `python MistHelper.py --test` exercises the new menu method in
non-interactive mode using the org configured in `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The `--test` heavy/destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- menu 89 sits inside the default sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200.
Both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on port 8055. This feature is entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
windows (the endpoint returns a small aggregate object, default `limit=100`,
non-paginated). Adaptive delay metrics (`delay_metrics.json` +
`tuning_data.json`) continue to govern back-off; this endpoint is cheap enough
that no special tuning is required.
**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()` for every
prompt; the API token is never logged; all output written under `data/`;
Windows-safe path joining via `os.path.join` / `pathlib.Path`.
**Scale/Scope**: One new public menu method (~22 lines) on a new
`PskPortalLogExportUtils` class (justified below -- no existing class owns PSK
Portal log analytics), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one
new SQLite table (`org_psk_portal_log_counts`), one menu-registration line, one
README operation-count bump, one CHANGELOG line. No new third-party dependencies,
no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_psk_portal_log_counts()` stays
  under 25 lines, takes <=5 parameters (`self`, `org_id`, `distinct`, `duration`,
  `limit`), and contains <=5 logical blocks (collect prompts -> validate org_id
  -> SDK call -> flatten `results[]` -> DataExporter write). One private helper
  `_flatten_psk_log_count_rows()` is added on the same class to keep the
  comprehension under 5 lines. The new class hosts only the new method and helper,
  so its hierarchy is two methods deep -- well under any 5-level limit.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior lives on a new `PskPortalLogExportUtils`
  class. A new class is justified (rather than reused) because no existing class
  in `MistHelper.py` owns PSK Portal log analytics; the adjacent PSK CRUD
  operations live on a portal-management class focused on writes, not on log
  aggregation reads. The menu dispatch in the main loop calls the class method
  directly -- no wrapper function. Identifiers use full words
  (`distinct_attribute`, `count_bucket_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input flows through `safe_input()` with explicit
  `context=` strings (`"psk_portal_log_counts:org_id"`,
  `"psk_portal_log_counts:distinct"`,
  `"psk_portal_log_counts:duration"`,
  `"psk_portal_log_counts:limit"`) so SSH and container EOF exits cleanly with
  exit code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is needed. `org_id` is validated
  against the Mist UUID shape via `is_valid_uuid()` before the API call; on
  validation failure the method logs `WARNING` and returns early. The API token
  is loaded from `.env` by the existing `mistapi.APISession` and never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- The standard pipeline applies without modification:
  `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check` ->
  commit with `version YY.MM.DD.HH.MM - add menu 89 countOrgPskPortalLogs`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs
  the validation + container build -> `gh run watch` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Counting PSK portal logs for org %s
  by %s"); `DEBUG` after the call with summary counts ("PSK portal log counts:
  distinct=%s buckets=%d total=%d"); `WARNING` on 404 or empty payload; `ERROR`
  on unexpected exception with full traceback via `logging.exception`. No
  secrets, tokens, full request URLs, or PSK secret material is logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new helper,
  the new PK strategy dictionary entry, and the menu-registration line will
  carry an inline comment that explains *why* the line exists. Blank lines,
  closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched menu-registration block get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before each prompt and before the SDK call; the SDK call
  itself; `logging.debug(...)` after the call with bucket and total counts;
  `logging.info(...)` before flatten; `logging.debug(...)` after flatten with
  row count; `logging.info(...)` before write. The DataExporter call emits its
  own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. The Complexity Tracking table at
the bottom of this plan is intentionally empty.

## Project Structure

### Documentation (this feature)

```text
specs/526-mist-count-org-psk-portal-logs/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + expected output + quality gates
|-- contracts/
|   `-- count_org_psk_portal_logs.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New PskPortalLogExportUtils class with one public menu method
                         # and one private flatten helper; new entry in
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES; menu 89 registration line.
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 89
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 89 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
public method on a new `PskPortalLogExportUtils` class in `MistHelper.py`. A new
class is preferred (per Principle II) because the adjacent PSK CRUD classes own
portal management writes, not log-count reads, and bundling unrelated read and
write responsibilities into one class would violate the 5-Item structural rule
on first follow-on log endpoint (`searchOrgPskPortalLogs` is the obvious next
sibling). Menu number proposal is **89**, chosen because the 60-96 Interactive
Safe band hosts the existing PSK / security read items; 89 sits in a free slot
above PSK-portal CRUD reads and well below the resource-intensive boundary at
96. Final menu number is re-verified at `/speckit.tasks` time by grepping
`MistHelper.py` for the highest currently allocated integer in the same band;
on collision, the next free integer in the same band is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/count_org_psk_portal_logs.md`), the seven principles
are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry is a single dict insert (existing
  structure), so no level-5 hierarchy explosion. The new class hosts exactly
  two methods (one public, one private helper), staying well inside the
  5-children-per-node ceiling.
- **Principle II (Class-Based)**: PASS -- All work lives on the new
  `PskPortalLogExportUtils` class. No standalone wrapper functions. Follow-on
  PSK log endpoints (search, single-log read, distinct-list helpers) will be
  added as additional methods on the same class without restructuring.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path for all four prompts. UUID validation runs before the
  SDK call. The endpoint never returns PSK secret material.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
  No new GitHub Actions workflow needed.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token, full URLs,
  or PSK secrets.
- **Principle VI (Inline Comments)**: PASS -- `quickstart.md` shows the expected
  comment density on every executable line, including the PK strategy entry
  and the menu-registration line. The whole touched block is brought to
  100 percent inline-comment coverage in the same PR.
- **Principle VII (Action Logging)**: PASS -- `quickstart.md` enumerates the
  before/after log pairs for every meaningful action: each prompt, the SDK
  call, the flatten step, and the export call.

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce the implementation task breakdown.
