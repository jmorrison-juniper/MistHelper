# Implementation Plan: countSiteWiredClients Menu Item

**Branch**: `566-mist-count-site-wired-clients` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/566-mist-count-site-wired-clients/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/wired_clients/count` (operationId
`countSiteWiredClients`) to return distinct-attribute counts of wired (Ethernet)
clients at a single site. The new menu method prompts the user for a `site_id`
via `safe_input()`, optionally collects the `distinct`, `mac`, `device_mac`,
`port_id`, `vlan`, `start`, `end`, `duration`, and `limit` query parameters,
calls `mistapi.api.v1.sites.wired_clients.count.countSiteWiredClients()`,
flattens the aggregate response (one summary row plus N per-bucket rows),
and persists it through `DataExporter.write_with_format_selection()` so CSV,
SQLite, and ArangoDB+Redis backends all stay consistent. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` with the
`auto_increment_with_unique` strategy used by every sibling `countOrg*Clients`
endpoint already in the monolith. The new operation is proposed as menu number
**195** -- the next free slot after the current top of the menu range (194),
mirroring the pattern used when the org-scope count endpoints were appended.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints; matches the runtime baked into the container image and the local
venv on Windows 11).

**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
single sanctioned interface to the Mist Cloud);
`mistapi.api.v1.sites.wired_clients.count` submodule for the count call;
`python-dotenv` for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`;
`requests` (transitive transport, no direct use).

**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
Local fallback is SQLite at `data/mist_data.db`; CSV files land in `data/`;
the polyglot backend pushes to ArangoDB graph + Redis cache containers.
A new SQLite table `count_site_wired_clients` is created on first run when
the registered PK strategy is read by `DataExporter`.

**Testing**: `python MistHelper.py --test` exercises the menu item
non-interactively against the org / site IDs loaded from `.env`. Local
quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 195 sits outside the documented
skip list (14, 18, 63-65, 90-100) so the `--test` sweep will execute it.

**Target Platform**: Windows 11 + `.venv` for local development; Podman Linux
container `ghcr.io/jmorrison-juniper/misthelper:latest` for production and
SSH-on-2200 / web UI on 8055. Both targets must work without code change.

**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines)
with an optional Gunicorn web UI. This feature lives entirely in the CLI;
no web UI surface is added.

**Performance Goals**: Single GET request completes in <=5 s for typical
sites. The endpoint is a server-side aggregation and returns a small JSON
object regardless of site size (default `limit=100`, default `duration=1d`),
so pagination is normally one round trip. Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; no
endpoint-specific tuning entry is required.

**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()` for
every prompt with explicit `context=` strings; secrets never logged; all
output lives under `data/`; Windows-safe path joining via `os.path.join` or
`pathlib.Path`; no destructive side effect -- this is HTTP GET only.

**Scale/Scope**: One new public method (~22 lines) on the existing
`SiteClientExporter` class in `MistHelper.py`; one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`; one new SQLite table created on first
write; one row in the menu-dispatch dictionary; one README operations-count
bump and one new menu-table row; one new `CHANGELOG.md` line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `export_site_wired_clients_count()` stays
  under 25 lines with <=5 parameters (`self`, `site_id`, `distinct`,
  `duration`, `extra_filters_dict`) and <=5 logical blocks (prompt -> build
  query kwargs -> API call -> flatten summary + results -> DataExporter
  call). Hierarchy is unchanged: one new method on an existing class. The
  filters dictionary keeps the parameter count at 5 even when the user
  supplies the optional `mac` / `device_mac` / `port_id` / `vlan` / `start` /
  `end` / `limit` filters. If the flatten step grows past five lines during
  implementation it will be extracted to a private `_flatten_count_payload`
  helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added directly to the existing
  `SiteClientExporter` class (defined at MistHelper.py:13063), which already
  owns the related `listSiteWiredClients` / `searchSiteWiredClients` exports.
  No standalone wrapper function is introduced. The menu dispatch references
  the bound method by attribute. Variable names use full words
  (`distinct_field`, `query_kwargs`, `results_rows`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input flows through `safe_input()` with
  explicit context tags such as `"count_site_wired_clients:site_id"`,
  `"count_site_wired_clients:distinct"`, and
  `"count_site_wired_clients:duration"`, so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly HTTP GET so no
  typed destructive-confirmation gate is required. The `site_id` is
  validated against the Mist UUID shape before the SDK call; on validation
  failure the method logs a warning and returns early. The API token is
  loaded from `.env` through `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` ->
  `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 195 countSiteWiredClients` ->
  `git push origin main` -> `.github/workflows/container-build.yml`
  runs -> `gh run watch <run-id>` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `logging.info` is emitted before the API call ("Fetching wired client
  count for site %s distinct=%s"); `logging.debug` is emitted after with
  result counters ("Wired client count payload: distinct=%s total=%d
  results=%d"); `logging.warning` on 404 / empty results; `logging.exception`
  on unexpected exceptions. No tokens, no full URLs containing query strings
  with sensitive identifiers, no Unicode characters.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline `# ...` comment that explains *why* the line exists, not just what
  it does. Blank lines, closing parentheses, and decorators are exempt per
  the constitution. Any uncommented adjacent lines in the existing
  `SiteClientExporter` block touched by the diff will receive comments in
  the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the established before / after
  pattern: `logging.info(...)` before prompt collection, `logging.debug(...)`
  with collected filter summary, `logging.info(...)` before the SDK call,
  `logging.debug(...)` after with result counts, `logging.info(...)` before
  the `DataExporter` call, `logging.debug(...)` after. `DataExporter` emits
  its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception at the pre-research gate. No
entries are required in the Complexity Tracking table.

## Project Structure

### Documentation (this feature)

```text
specs/566-mist-count-site-wired-clients/
├── plan.md                                   # This file
├── research.md                               # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
├── data-model.md                             # Phase 1 - response entities + DDL + PK registration
├── quickstart.md                             # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── count_site_wired_clients.md           # Phase 1 - HTTP + SDK contract
└── tasks.md                                  # Phase 2 - NOT generated by /speckit.plan
```

### Source Code (repository root)

```text
MistHelper.py             # New method export_site_wired_clients_count() on the
                          # existing SiteClientExporter class (line 13063),
                          # new ENDPOINT_PRIMARY_KEY_STRATEGIES entry near the
                          # other countOrg*Clients entries (line ~4561), and
                          # new "195" entry in the MENU_DISPATCH dict
                          # (line ~21945). No new modules.
README.md                 # Operations-count bump (194 -> 195) and a new row
                          # in the menu table under the safe site-export
                          # cluster describing the new option.
CHANGELOG.md              # New "version YY.MM.DD.HH.MM" entry summarizing
                          # the menu 195 addition.
data/                     # Runtime output target (existing dir, no migration
                          # required). DataExporter creates the new SQLite
                          # table count_site_wired_clients on first run from
                          # the PK strategy registered above.
```

**Structure Decision**: Single-file monolith preserved. The new menu item is
added as a new public method on the existing `SiteClientExporter` class
(MistHelper.py:13063), which is the canonical home for site-scope wired /
wireless / NAC client exports. Menu number proposal is **195**, chosen
because (a) the current top of the menu range is 194, (b) the documented
cluster boundaries in `.github/copilot-instructions.md` do not reserve a
slot inside the 60-72 site-cluster for new count endpoints, and (c)
appending mirrors the pattern used when `countOrgWiredClients` was added.
The full menu list will be re-verified at task-generation time; if 195
collides with an in-flight feature branch, the next free integer (196 ...)
is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/count_site_wired_clients.md`), the seven
principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` and the contract in `contracts/count_site_wired_clients.md`
  confirm <=25 lines, <=5 parameters (collapsing optional filters into one
  dict), and <=5 logical blocks. The `ENDPOINT_PRIMARY_KEY_STRATEGIES`
  dictionary is a single insert against an existing structure.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `SiteClientExporter`. No wrappers introduced. Flattening helpers, if
  needed, become private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms GET
  only, no destructive side effect; `safe_input()` is the documented prompt
  path; UUID validation occurs before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline. The `--test` sweep covers menu 195 (outside skip list).
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only, use `%s` formatting, and never include the API token or
  unredacted user identifiers.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and the menu-dispatch registration row.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
