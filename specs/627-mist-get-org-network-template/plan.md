# Implementation Plan: GetOrgNetworkTemplate Menu Item

**Branch**: `627-mist-get-org-network-template` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/627-mist-get-org-network-template/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/networktemplates/{networktemplate_id}` (operationId
`getOrgNetworkTemplate`) to retrieve the full details of a single organization-level
network (switch) template by ID. The menu item prompts the user for `org_id` and
`networktemplate_id` via `safe_input()`, invokes
`mistapi.api.v1.orgs.networktemplates.getOrgNetworkTemplate()` exactly once, flattens
the large nested response into a summary row plus normalized child rows for the
recurring array/object collections (networks, port_usages, ospf_areas, vrf_instances,
routing_policies, acl_policies, acl_tags, extra_routes, dns_servers, ntp_servers,
remote_syslog servers), and persists every row through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends receive consistent output. New entries are registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts. Proposed menu number is
**96**, the next available slot in the Safe Org Exports / Templates cluster and
adjacent to the existing `listOrgNetworkTemplates` bulk export used by menus 4 and 35.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org and a known template from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`, and
`python -m black --check MistHelper.py`. The heavy/destructive skip list (14, 18, 63-65,
90-100) is unaffected -- proposed menu 96 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a typical
network template. The endpoint is non-paginated; a very large template (many switch
port profiles + VLANs + ACLs) may return a JSON body in the low-hundreds-of-KB range,
which is comfortably within the 5-second budget on a normal WAN link.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`).
**Scale/Scope**: One new public menu method (~25 lines) on the existing
`NetworkTemplateUtils` class (the same class that owns `listOrgNetworkTemplates` /
`getOrgNetworkTemplates` bulk exports); several new entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (one for the summary and one per child sub-table
enumerated in `data-model.md`); one menu registration entry; one README operation-count
bump; one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_network_template_details()`
  stays under 25 lines, takes <=3 parameters (`self`, `org_id`, `networktemplate_id`),
  and contains <=5 logical blocks (prompt -> validate -> API call -> fan-out flatten
  -> multi-write via DataExporter). Hierarchy is unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are introduced. The
  fan-out flatten step is delegated to a set of small private helpers on the same
  class (`_flatten_ntpl_summary`, `_flatten_ntpl_networks`, `_flatten_ntpl_port_usages`,
  etc.); each helper stays under 25 lines and never exceeds 5 nesting blocks. If any
  helper grows past the limit during implementation, it is split further.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `NetworkTemplateUtils` class (the same class that already owns the bulk
  `listOrgNetworkTemplates` export used by menus 4 and 35). No standalone wrapper
  function is introduced. The menu dispatch in the main loop references the class
  method directly. Variable names use full words (`network_template_id`,
  `port_usage_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_network_template:org_id"` and
  `"org_network_template:networktemplate_id"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no
  typed destructive-confirmation gate is required. Both UUIDs are validated against
  the Mist UUID shape via the existing `is_valid_uuid()` helper before the API call;
  on validation failure the method logs a `WARNING` and returns early. API token is
  loaded from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 getOrgNetworkTemplate` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove
  / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Fetching network template %s for org %s"); `DEBUG`
  after the call with summary counts ("Template %s: networks=%d port_usages=%d
  ospf_areas=%d vrf_instances=%d"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception via `logging.exception`. No secrets, tokens, or full request
  URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, in each private
  flatten helper, in the new `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entries,
  and on the menu registration line will carry an inline comment that explains *why*
  the line exists, not merely what it does. Blank lines, closing parentheses, and
  decorators are exempt per the constitution. Any uncommented adjacent lines in the
  touched block (the existing `NetworkTemplateUtils` cluster) get comments added in
  the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a result count,
  `logging.info(...)` before each flatten sub-step, `logging.debug(...)` after each
  flatten sub-step, `logging.info(...)` before each DataExporter write, and
  `logging.debug(...)` after each write. The `DataExporter` call already emits its
  own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/627-mist-get-org-network-template/
|-- plan.md              # This file
|-- research.md          # Phase 0 -- SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 -- response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 -- local run + .env + quality gates
|-- contracts/
|   `-- get_org_network_template.md    # Phase 1 -- HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on NetworkTemplateUtils class + PK strategy
                         # entries + menu 96 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation-count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96
data/                    # Runtime output target (existing dir); DataExporter creates
                         # the new SQLite tables on first write. No schema migration
                         # beyond the new ENDPOINT_PRIMARY_KEY_STRATEGIES entries.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `NetworkTemplateUtils` class in `MistHelper.py` (the same
class that already owns `listOrgNetworkTemplates`, referenced by the enriched docs as
in-use by menus 4 and 35). The menu number proposal is **96**, chosen because
operations 60-96 make up the Interactive Safe cluster and 96 is the last free slot
below the Resource-Intensive block that starts at 97. This placement puts the new
single-template detail export directly adjacent to the existing bulk network-template
list operations, which is the ergonomic pairing a junior NOC engineer expects. The
full menu list will be re-verified at `/speckit.tasks` time; if 96 collides with an
in-flight feature branch (e.g., spec 500 has proposed 95), the next free integer in
the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/get_org_network_template.md`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. Every
  private flatten helper stays under the same limits by handling a single response
  sub-collection. The `ENDPOINT_PRIMARY_KEY_STRATEGIES` additions are dict inserts
  into an existing structure, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `NetworkTemplateUtils`.
  No wrappers introduced. Flatten helpers are added as private methods on the same
  class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including each new PK strategy entry and
  the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
