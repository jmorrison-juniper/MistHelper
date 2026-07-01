# Implementation Plan: GetOrgSecPolicy Menu Item

**Branch**: `636-mist-get-org-sec-policy` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/636-mist-get-org-sec-policy/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/secpolicies/{secpolicy_id}` (operationId `getOrgSecPolicy`)
to retrieve a single Organization Security Policy definition (WAN-edge firewall rule set
plus associated WLAN blocks) by its UUID. The menu prompts the user through `safe_input()`
for `org_id` (defaulting to `MIST_ORG_ID` from `.env`) and `secpolicy_id`, invokes the
`mistapi` SDK once, flattens the nested response (top-level policy row + zero-or-more
`wlans[]` child rows) and persists the result via
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
receive consistent output. A new entry is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
so repeated runs upsert cleanly in SQLite. The new operation is proposed as menu number
**195**, the first free slot after the existing 1-194 range, which keeps the security /
policy config exports grouped near their neighbors (`listOrgServicePolicies`,
`listOrgSecIntelProfiles`).

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (HTTP transport, transitive); `python-dotenv` (for
`.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB +
Redis containers handle the graph + cache backend when configured.
**Testing**: `python MistHelper.py --menu 195` for direct invocation against a known
`secpolicy_id`; `python MistHelper.py --test` sweep exercises the new item automatically
(menu 195 sits outside the heavy/destructive skip list of 14, 18, 63-65, 90-100). Local
quality gates: `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical secpolicy
records (endpoint is non-paginated and returns a single JSON object; response size varies
with `wlans[]` count but typical policies expose fewer than 20 WLAN blocks). Adaptive
delay metrics in `delay_metrics.json` and `tuning_data.json` continue to govern back-off;
this endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs
or filenames; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); 5-Item Rule enforced (<=25 lines, <=5 params, <=5 nesting blocks per
function).
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`OrgTemplateExporter` class (the closest semantic neighbor -- it already owns org-level
policy / template exports), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new
SQLite tables (`org_sec_policy` for the top-level record and `org_sec_policy_wlans` for
the child WLAN array), one menu registration entry, one README menu-table row and
operation-count bump, one CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `OrgTemplateExporter.export_org_sec_policy()` stays under 25 lines, takes <=3
  parameters (`self` implicit via staticmethod pattern used by neighbors, `org_id`,
  `secpolicy_id`), and contains <=5 logical blocks (prompt / validate -> API call ->
  flatten parent row -> flatten wlans[] children -> DataExporter call). Hierarchy is
  unchanged: one new method on an existing class. If the wlans[] flattener grows past
  5 lines during implementation, it is extracted to a private helper
  `_flatten_secpolicy_wlans()` on the same class, keeping every function within the
  5-Item bounds.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is a method on the existing
  `OrgTemplateExporter` class in `MistHelper.py` (currently owning gateway / network /
  RF / AP / site template exports). Security policy is the semantic peer of these
  templates and belongs in the same class. No standalone wrapper function is
  introduced. Menu dispatch references the class method directly. Variable names use
  full words (`sec_policy_row`, `wlan_child_rows`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_sec_policy:org_id"`, `"org_sec_policy:secpolicy_id"`) so
  SSH / container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only HTTP GET, so no typed destructive-confirmation gate is required.
  Both UUIDs are validated against the Mist UUID shape before the API call; on
  validation failure the method logs a warning and returns early. API token is loaded
  from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 195 getOrgSecPolicy` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs (includes the
  pre-build Python syntax validation job) -> `gh run watch` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run container ->
  `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` / `%d` style formatting.
  `INFO` is emitted before the API call ("Fetching security policy %s for org %s");
  `DEBUG` after the call with summary counts ("Sec policy %s: name=%s wlans=%d");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception via
  `logging.exception`. No secrets, tokens, or full request URLs are logged. Emoji /
  Unicode are prohibited per project rules.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment
  explaining *why* the line exists. Blank lines, closing parentheses, and decorators
  are exempt per the constitution. Any adjacent lines in the touched neighboring
  block (the existing template-export cluster inside `OrgTemplateExporter`) get
  comments added in the same PR if they are missing.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with a result count, `logging.info(...)` before flatten, `logging.debug(...)` after
  flatten with parent + child row counts, `logging.info(...)` before write,
  `logging.debug(...)` after write. `DataExporter.write_with_format_selection()`
  already emits its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/636-mist-get-org-sec-policy/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_sec_policy.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgTemplateExporter class (line ~11052) +
                         # PK strategy entry in ENDPOINT_PRIMARY_KEY_STRATEGIES
                         # (line ~4761 cluster) + menu 195 registration. No new
                         # modules; single-file monolith preserved.
README.md                # Operation count bump 194 -> 195 + new row in the menu table
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 195
data/                    # Runtime output target (existing dir). New SQLite tables
                         # org_sec_policy and org_sec_policy_wlans created on first
                         # run by DataExporter; new CSV files created on demand.
documentation/api/orgs/  # Existing enriched doc GET_orgs_org_id_secpolicies_
                         # secpolicy_id.md consulted (not modified) during research.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `OrgTemplateExporter` class in `MistHelper.py` at approximately
line 11052 (currently owning gateway / network / RF / AP / site template exports --
security policy is the semantic peer of these). The menu number proposal is **195**,
the next available integer after the current maximum of 194. This keeps the new item
adjacent to the recently added policy / template cluster and outside the heavy /
destructive skip lists at 14, 18, 63-65, and 90-100. If 195 collides with an in-flight
feature branch at task generation time, the next free integer above 195 is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified.**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/get_org_sec_policy.md`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` and the two-table split in `data-model.md` confirm the exporter
  method stays under 25 lines with <=3 params and <=5 blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` update is a single dictionary insert (existing
  structure). No level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgTemplateExporter`. No
  wrappers introduced. If the wlans[] flattener needs extraction, it is added as a
  private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call. `.env` supplies the token.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` / `%d` formatting and never include the API token or the raw response body.
- **Principle VI (Inline Comments)**: PASS -- The quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Quickstart enumerates the before/after
  log pairs for every meaningful action (prompt, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
