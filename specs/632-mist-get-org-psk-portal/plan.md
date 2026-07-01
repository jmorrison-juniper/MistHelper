# Implementation Plan: getOrgPskPortal Menu Item

**Branch**: `632-mist-get-org-psk-portal` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/632-mist-get-org-psk-portal/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/pskportals/{pskportal_id}` (operationId `getOrgPskPortal`)
to retrieve the configuration record of a single PSK (pre-shared key) self-service
portal in an organization. The menu item prompts the user for `org_id` and
`pskportal_id` via `safe_input()`, invokes the `mistapi` SDK, flattens the returned
JSON object (including nested `passphrase_rules` and `sso` sub-objects) into a single
CSV/SQLite row, and persists the result through
`DataExporter.write_with_format_selection()` so the CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **89** -- the next available slot in the Safe
Org Exports "config and admin" cluster (42-50 currently, extended by adjacent
PSK-related additions), sitting well below the resource-intensive block at 96-101
and far from the destructive block at 154+.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution "Technology & Compatibility
Constraints"; matches the existing `MistHelper.py` monolith).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
sanctioned interface to the Mist Cloud); `requests` (transitive HTTP transport);
`python-dotenv` (loads `MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. Local
fallback: SQLite file `data/mist_data.db`. CSV files land under `data/`. Polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item non-interactively
using the org and (optional) PSK portal identifiers from `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 89 sits inside the default test sweep
range (the heavy/destructive skip list is 14, 18, 63-65, 90-100 and 154-194).
**Target Platform**: Windows 11 + `.venv` for local development; Podman Linux
container (`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH on
port 2200. Both must run this feature without code change.
**Project Type**: CLI tool -- single-file monolith `MistHelper.py` (~28K lines) with
optional Gunicorn web UI on port 8055. This feature is CLI-only.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
portals (endpoint returns one JSON object, is not paginated, and the response body
is small -- a few KB at most). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; no endpoint-specific tuning needed.
**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()` for every
prompt; API token never logged; all output written under `data/`; Windows-safe path
joining via `os.path.join` / `pathlib.Path`; no direct `requests.get` -- all Mist
API traffic routes through the `mistapi` SDK.
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`WLANExportUtils` class (which already hosts adjacent WLAN/PSK exports; if that
class is absent at implementation time, `OrgExportUtils` is the confirmed fallback
home per the codebase convention -- see Structure Decision below). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new CSV/SQLite table (`org_psk_portals`).
One menu registration entry. One README operation-count bump. One CHANGELOG line.
No new dependencies, modules, packages, or directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_psk_portal()` stays under
  25 lines, takes <=3 parameters (`self`, `org_id`, `pskportal_id`), and contains
  <=5 logical blocks (prompt org_id -> prompt pskportal_id -> validate -> API call
  -> flatten -> DataExporter write). Hierarchy is unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are introduced.
  Nested-object flattening (`passphrase_rules`, `sso`) is a single dict-comprehension
  block; if it grows past 5 lines during implementation it is extracted to a
  private helper `_flatten_psk_portal_row()` on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on an existing class
  that already owns adjacent PSK / WLAN exports (`WLANExportUtils`, or
  `OrgExportUtils` if the confirmed target class name differs -- see Structure
  Decision). No standalone wrapper function is introduced. The menu dispatch in
  the main loop references the class method directly. Variable names use full
  words (`psk_portal_row`, `portal_id`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_psk_portal:org_id"`,
  `"org_psk_portal:pskportal_id"`), so an SSH or container session that hits EOF
  exits cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate is required. Both UUIDs
  are validated via the existing `is_valid_uuid()` helper before the API call; on
  validation failure the method logs a `WARNING` and returns early. The API
  token is loaded from `.env` by the existing `mistapi.APISession` bootstrap and
  is never included in any log line, prompt, or output row.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> `git commit -m "version YY.MM.DD.HH.MM - add menu 89
  getOrgPskPortal"` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII-only text with `%s` style
  formatting. `INFO` is emitted before the API call
  ("Fetching PSK portal %s for org %s"); `DEBUG` after the call with the count
  and portal name ("Received PSK portal: name=%s ssid=%s type=%s"); `WARNING`
  on 404 / empty payload ("No PSK portal %s in org %s"); `ERROR` with full
  traceback via `logging.exception` on unexpected exceptions. No API token,
  no full request URL, no `Authorization` header value ever appears in logs.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line will
  carry an inline `#` comment explaining *why* the line exists, not just what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. If neighboring lines in the touched menu-registration block lack
  comments, they are commented in the same PR (block-wide coverage rule).

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each `safe_input()` prompt, `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a result
  summary, `logging.info(...)` before flatten, `logging.debug(...)` after
  flatten with row count (1), `logging.info(...)` before the DataExporter write.
  The DataExporter emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/632-mist-get-org-psk-portal/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates + method skeleton
|-- contracts/
|   `-- get_org_psk_portal.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on WLANExportUtils (or OrgExportUtils fallback)
                         # + new ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 89
                         # registration. No new modules; same single-file monolith.
README.md                # Operation-count bump + new row in the menu table for op 89
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 89 addition
data/                    # Runtime output target (existing directory). No schema
                         # migration needed beyond the new SQLite table created on
                         # first write by DataExporter.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing class that owns PSK / WLAN exports in `MistHelper.py`.
The primary target class is `WLANExportUtils`; if a grep at implementation time
shows PSK-portal-related exports living on `OrgExportUtils` or `PSKExportUtils`
instead, the method is added there without introducing a new class (Principle II
forbids wrapper classes / functions). Under no circumstance is a standalone
function created outside a class. The menu number proposal is **89**, chosen
because the Safe Org Exports config-and-admin cluster (42-50) has been extended by
adjacent per-endpoint feature additions and 89 is the next available integer below
the resource-intensive block at 96 and well below any destructive number. The
number is provisional and re-verified at `/speckit.tasks` time by grepping
`MistHelper.py` for the highest currently-allocated menu integer; if 89 collides
with an in-flight feature branch the next free integer in the same cluster is
used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method skeleton in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` insert is a single dict-literal entry (no
  level-5 hierarchy explosion). Nested `passphrase_rules` / `sso` flattening
  stays under 5 lines by using `flatten_dict()` prefix keys.
- **Principle II (Class-Based)**: PASS -- All work lives on the identified
  existing class. No wrappers introduced. Any helper (e.g.,
  `_flatten_psk_portal_row`) is added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET-only with no destructive side effect. `safe_input()` is the
  documented prompt path. Both UUIDs are validated before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline
  documented in Constitution Principle IV.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or full
  request URL.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu-registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
