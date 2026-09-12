# Implementation Plan: GetOrgAntivirusProfile Menu Item

**Branch**: `594-mist-get-org-antivirus-profile` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/594-mist-get-org-antivirus-profile/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/avprofiles/{avprofile_id}` (operationId
`getOrgAntivirusProfile`) to retrieve a single Antivirus profile configuration
record from a Juniper Mist organization. The menu item prompts the user for an
`org_id` and an `avprofile_id` via `safe_input()`, invokes the `mistapi` SDK
function `mistapi.api.v1.orgs.avprofiles.getOrgAntivirusProfile()`, flattens
the single-object JSON response into one CSV/SQLite row (no pagination), and
persists the result through `DataExporter.write_with_format_selection()` so
CSV, SQLite, and ArangoDB+Redis backends all receive consistent output. A new
entry is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the natural
profile UUID (`id`) for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **96** -- the next available slot in the
Safe Org Exports / Security-Config cluster, sitting adjacent to the existing
IDP and AAMW profile read paths and below the resource-intensive block that
starts at 97.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
The SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache
backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org and avprofile from `.env` /
`tuning_data.json`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`.
The heavy / destructive skip list (14, 18, 63-65, 90-100) places menu 96 just
outside the default sweep -- the operator includes it explicitly when smoke
testing.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200.
Both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for any
valid `(org_id, avprofile_id)` pair (the endpoint is non-paginated and the
response is a single JSON object of <2 KB). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; this
endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SecurityProfileExportUtils` class (or the closest existing org-config class
that already owns sibling profile reads -- see Structure Decision). One new
entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new CSV/SQLite table
`org_avprofile`. One menu registration entry. One README operation-count
bump. One CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_antivirus_profile()`
  stays under 25 lines, takes <=3 parameters (`self`, `org_id`,
  `avprofile_id`), and contains <=5 logical blocks (prompt org_id -> prompt
  avprofile_id -> API call -> flatten single object -> DataExporter call).
  Hierarchy is unchanged: one new method on an existing class. No new
  packages, modules, or top-level constants are introduced. The flatten step
  is a single dict comprehension; if it ever grows past 5 lines during
  implementation it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `SecurityProfileExportUtils` class (the same class that owns sibling reads
  for `getOrgIDPProfile`, `getOrgAAMWProfile`, and the avprofile list
  export). No standalone wrapper function is introduced. The menu dispatch in
  the main loop references the class method directly. Variable names use
  full words (`profile_record`, `flattened_row`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_antivirus_profile:org_id"`,
  `"org_antivirus_profile:avprofile_id"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP
  GET), so no typed destructive-confirmation gate is required. Both UUIDs are
  validated against the Mist UUID shape before the API call; on validation
  failure the method logs a warning and returns early. The API token comes
  from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 96
  getOrgAntivirusProfile` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` -> `podman
  pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching antivirus profile %s for
  org %s"); `DEBUG` after the call with a one-line result summary ("Got
  avprofile id=%s name=%s protocols=%d"); `WARNING` on 404 / empty payload;
  `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu
  registration line will carry an inline comment that explains *why* the line
  exists, not merely what it does. Blank lines, closing parentheses, and
  decorators are exempt per the constitution. Any uncommented adjacent lines
  in the touched block (the existing security-profile export cluster) get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a result summary, `logging.info(...)`
  before flatten, `logging.debug(...)` after flatten, `logging.info(...)`
  before write, `logging.debug(...)` after write. The `DataExporter` call
  already emits its own per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/594-mist-get-org-antivirus-profile/
|-- plan.md              # This file
|-- spec.md              # Pre-existing feature spec (read-only here)
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_antivirus_profile.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SecurityProfileExportUtils class +
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 96
                         # registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table
                         # for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing
                         # menu 96 addition
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the new SQLite table
                         # created on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `SecurityProfileExportUtils` class in
`MistHelper.py` -- the same class that owns the IDP / AAMW / avprofile list
reads. If at implementation time the closest existing class turns out to be
named differently (the codebase has grown organically), the new method joins
whichever existing class already exposes a `getOrgAvprofiles` (list) read so
the per-profile detail read sits next to its sibling. A new class is **not**
justified for one read method. The menu number proposal is **96**, chosen
because it is the next available slot in the Safe Org Exports cluster
(operations 1-96 per `.github/copilot-instructions.md`) immediately before
the resource-intensive block at 97-101. If 96 collides with an in-flight
feature branch at task-generation time, the next free integer in the same
cluster is used; this is verified during `/speckit.tasks`.

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

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` insert is a single dictionary entry
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `SecurityProfileExportUtils`. No wrappers introduced. Any future flatten
  helper is added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect. `safe_input()` is the
  documented prompt path. Both UUIDs are validated before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows
  the expected comment density on every executable line, including the PK
  strategy entry and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action (prompt,
  API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
