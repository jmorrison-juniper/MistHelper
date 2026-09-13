# Implementation Plan: getAdminRegistrationInfo Menu Item

**Branch**: `577-mist-get-admin-registration-info` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/577-mist-get-admin-registration-info/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/register/recaptcha` (operationId `getAdminRegistrationInfo`) to retrieve the
reCAPTCHA configuration (flavor, sitekey, required flag) used by the public admin
registration flow. The endpoint takes no path parameters, no required headers, and one
optional query parameter (`recaptcha_flavor`). The menu item prompts the user via
`safe_input()` for an optional flavor override (default: blank -> let the API choose),
invokes the `mistapi` SDK, normalizes the single-object JSON response into a one-row
table, and persists it through `DataExporter.write_with_format_selection()` so CSV,
SQLite, and ArangoDB+Redis backends all receive consistent output. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` so re-running the menu item upserts
cleanly into SQLite without duplicates. The new operation is proposed as menu number
**59** -- the last available slot in the "Misc Safe Org Exports (56-59)" cluster, where
unauthenticated org-adjacent utility endpoints already live.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST`; this specific endpoint is documented as public and does not
require `MIST_API_TOKEN`, but the existing `mistapi.APISession` is still used to keep
host selection, retries, and rate-limit handling uniform).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend. New SQLite table
`admin_registration_info` is created on first run.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. Heavy /
destructive skip list (14, 18, 63-65, 90-100) is unaffected -- new item 59 sits inside
the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=2 seconds (endpoint is
non-paginated; response is a small JSON object: three scalar fields). Adaptive delay
metrics in `delay_metrics.json` and `tuning_data.json` continue to govern back-off; no
special tuning required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`). The endpoint is documented as publicly accessible, so the implementation
must tolerate a missing or unset `MIST_API_TOKEN` without crashing.
**Scale/Scope**: One new public menu method (~18 lines) on the existing
`OrgExportUtils` class (the same class that owns adjacent Misc safe exports 56-58), one
new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
(`admin_registration_info`), one menu registration entry, one README operation-count
bump, one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_admin_registration_info()` stays under 25 lines, takes <=2 parameters (`self`,
  `recaptcha_flavor`), and contains <=5 logical blocks (prompt -> API call -> normalize
  single object to one-row list -> DataExporter call -> log summary). Hierarchy
  unchanged: one new method on an existing class. No new packages, modules, or top-level
  constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgExportUtils` class. No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names use
  full words (`registration_row`, `recaptcha_flavor`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- The single user prompt is collected through `safe_input()` with an
  explicit `context="admin_registration_info:recaptcha_flavor"` string so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. Optional
  flavor input is whitespace-stripped and validated against the documented enum
  (`google`, `hcaptcha`) before being passed to the SDK; on invalid input the method
  logs a warning, ignores the override, and proceeds with the API default.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 59 getAdminRegistrationInfo` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching admin registration reCAPTCHA info, flavor=%s");
  `DEBUG` after the call with the returned fields ("Got reCAPTCHA flavor=%s required=%s
  sitekey_len=%d"); `WARNING` on empty payload; `ERROR` via `logging.exception` on
  unexpected exception. No secrets, tokens, or full sitekey values are logged at INFO
  level (sitekey is non-sensitive but its length is logged instead of the value to keep
  default logs short).

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing Misc safe-export menu cluster) get comments
  added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with the parsed fields, `logging.info(...)` before write, `logging.debug(...)` after
  write. The DataExporter call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/577-mist-get-admin-registration-info/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_admin_registration_info.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgExportUtils class + PK strategy + menu 59
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 59
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 59 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table admin_registration_info created on
                         # first run by DataExporter)
documentation/api/admins/GET_register_recaptcha.md   # Pre-existing enriched reference
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `OrgExportUtils` class in `MistHelper.py` (the same class that
owns the adjacent Misc Safe Org Exports operations 56-58). The menu number proposal is
**59**, chosen because operations 56-59 are the "Misc Safe Org Exports" cluster and 59
is the last available slot before the Interactive Safe block at 60. The full menu list
is re-verified at task generation time; if 59 collides with an in-flight feature branch,
the next free integer in the same cluster (or the next gap before 60) is used. The
implementation must mention `safe_input()` (for the optional flavor prompt),
`DataExporter.write_with_format_selection()` (for the output write), and
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (for the new PK registration) -- all three are listed
as hard requirements in the parent task instructions and are explicitly wired into the
method outline in `quickstart.md`.

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
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgExportUtils`. No
  wrappers introduced. The response normalization is a single dict-to-list-of-one-dict
  comprehension; no helper needed.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. Flavor enum validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include API tokens or full sitekey values at INFO
  level.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
