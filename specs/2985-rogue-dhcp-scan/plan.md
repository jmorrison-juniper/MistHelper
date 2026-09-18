# Implementation Plan: Org-wide rogue DHCP server scan

**Branch**: `feat/2985-rogue-dhcp-scan` | **Date**: 2026-09-18 | **Spec**: [spec.md](./spec.md)

**Issue**: #2985

## Summary

Add menu operation 269. It scans one Mist organization for every rogue DHCP
server signal in a 30-day window, across alarms, switch events, and Marvis config
actions. It queries the organization first, then it queries only the sites that
the organization results named. It merges the records into one table, prints the
table, writes a CSV file, and writes the same rows to the configured database
backend. The operations web dashboard on port 8055 runs the same operation and
shows the same output file.

## Technical Context

**Language**: Python 3.13 or newer.

**Dependencies**: `mistapi` 0.64 (installed). No new dependency.

**Storage**: CSV under `data/`, SQLite at `data/mist_data.db`, and the polyglot
ArangoDB and Redis backend. All three go through
`DataExporter.write_with_format_selection`.

**Testing**: `pytest`, `pytest-cov`, and `hypothesis`.

**Target platform**: Windows 11 for local work, Linux container for deployment.

**Project type**: Single Python project with a Flask operations portal.

**Performance goal**: Three organization queries, then three queries for each
affected site. An organization with 200 sites and 3 affected sites issues 12
queries, not 600.

**Constraints**: Read-only endpoints only. The 5-Item Rule caps each function at
5 parameters, 5 blocks, and 25 lines. `ruff` and `mypy` skip `web_portal/`, so
the scan logic lives under `src/`.

**Scale**: Up to 10,000 records held in memory.

## Constitution Check

| Principle | Verdict | How this plan complies |
| - | - | - |
| I. Five-Item Rule | Pass | The new package holds 5 files. Each class holds 5 or fewer public methods. Each function stays under 25 lines with 5 or fewer parameters. |
| II. Class-Based Architecture | Pass | Five named classes. No wrapper function. The menu row points at a class method. |
| III. Safety-First | Pass | The operation reads only. It calls no endpoint that writes. It needs no typed confirmation, because it destroys nothing. |
| IV. Full Deployment Pipeline | Pass | The plan runs every gate locally, then opens one pull request. |
| V. Observability | Pass | Each query logs an action before it and a result summary after it. |
| VI. Inline Comments | Pass | Every executable line carries an inline comment that states the intent. |
| VII. Action Logging | Pass | `logging.info` before each action and `logging.debug` after, with `%s` formatting. |
| Database Keys | Pass | The plan adds the primary key strategy before the implementation writes a row. |
| Data Directory | Pass | The CSV file lands under `data/`. |
| mistapi only | Pass | Every call goes through the `mistapi` SDK. No direct HTTP call. |

No violation. No complexity deviation to record.

## The Mist signal catalog

Research settled the literal strings. The evidence is in
`data/ConstAlarmDefs.csv`, `data/ConstDeviceEvents.csv`, and
`documentation/mist-api-openapi31yaml.yaml`.

| Source | Endpoint | Match rule |
| - | - | - |
| Organization alarm | `mistapi.api.v1.orgs.alarms.searchOrgAlarms` | `type` equals `sw_rogue_dhcp_server_detected` |
| Site alarm | `mistapi.api.v1.sites.alarms.searchSiteAlarms` | `type` equals `sw_rogue_dhcp_server_detected` |
| Organization switch event | `mistapi.api.v1.orgs.devices.searchOrgDeviceEvents` | `type` equals `SW_ROGUE_DHCP_SERVER_DETECTED` |
| Site switch event | `mistapi.api.v1.sites.devices.searchSiteDeviceEvents` | `type` equals `SW_ROGUE_DHCP_SERVER_DETECTED` |
| Marvis self-driving event | the two device event endpoints | `type` equals `SW_CONFIG_CHANGED_BY_MARVIS` and `reason` holds `rogue_dhcp` |
| Marvis config action | `mistapi.api.v1.sites.marvis_configs.searchSiteMarvisConfigActions` | `reason` equals `rogue_dhcp_server_detected` |

A keyword rule runs beside the literal rule. It accepts a record whose `type`
text or detail text holds both `rogue` and `dhcp`, without regard to letter case.
That rule catches a Mist string that does not exist yet.

A reject list blocks a DHCP record that names no rogue server. It holds
`sw_dhcp_pool_exhausted`, `SW_DHCP_POOL_EXHAUSTED`, `infra_dhcp_failure`,
`infra_dhcp_success`, `dhcp_failure`, `minis_dhcp_failure`,
`GW_DHCP_POOL_EXHAUSTED`, and `SW_NON_DHCP_CLIENT_DETECTED`. The reject list runs
before the keyword rule, so a pool exhaustion record never enters the result.

Warning: the Marvis config action endpoint is site-scoped in the installed SDK.
No organization-level equivalent exists. The scan therefore reads Marvis config
actions only for a site that an alarm or an event already named. The scan states
that limit in its summary, so an operator never reads the result as complete
proof that no Marvis action exists elsewhere.

## Project Structure

### New source files

```text
src/security/rogue_dhcp/
├── __init__.py       # Public names: RogueDhcpScanOperation, RogueDhcpFinding
├── signals.py        # RogueDhcpSignalMatcher  -- FR-005 to FR-010
├── records.py        # RogueDhcpFinding, RogueDhcpRecordNormalizer -- FR-015 to FR-020
├── scanner.py        # RogueDhcpScanner  -- FR-011 to FR-014, FR-025 to FR-028
└── operation.py      # RogueDhcpScanOperation -- FR-021 to FR-024, the menu entry point
```

`src/security/` holds `credential_redaction.py` today. A rogue DHCP server is a
network security finding, so the package belongs there. After the change,
`src/security/` holds three children, which respects the 5-Item Rule.

### New test files

```text
tests/unit/security/rogue_dhcp/
├── __init__.py
├── test_signals.py     # matcher: accept, reject, keyword, case
├── test_records.py     # normalizer, merge, state, column set
├── test_scanner.py     # fan-out order, failure isolation, window
└── test_operation.py   # export call, empty result, summary
tests/property/
└── test_rogue_dhcp_properties.py   # Hypothesis invariants
tests/guardrails/
└── test_rogue_dhcp_portal_exposure.py   # the portal gate admits 269
```

### Changed files

| File | Change |
| - | - |
| `MistHelper.py` | One `menu_actions` row for `"269"`. |
| `src/utils/operation_registry.py` | One entry `"269": {"category": "safe"}`. |
| `src/refactors/endpoint_primary_key_strategies.py` | One strategy for `scanOrgRogueDhcpServers`. |
| `web_portal/services/operation.py` | One explicit allowlist that admits 269 past the numeric bound, plus one category range. |
| `web_portal/menu_registry.py` | One static description row. |
| `tests/unit/test_menu_entry_metadata.py` | The expected count rises from 268 to 269. |
| `README.md` | The operation count and the menu table. |
| `documentation/wiki/Menu-Reference.md` | Regenerated by `scripts/generate_menu_wiki.py`. |
| `changelog.d/issue-2985-rogue-dhcp-scan.md` | The release-note fragment. |

## Design

### RogueDhcpSignalMatcher (`signals.py`)

A stateless matcher. It owns every literal string and the keyword rule, so no
other module repeats a Mist string.

```python
ROGUE_ALARM_TYPES = frozenset({"sw_rogue_dhcp_server_detected"})
ROGUE_EVENT_TYPES = frozenset({"SW_ROGUE_DHCP_SERVER_DETECTED"})
MARVIS_CONFIG_EVENT_TYPE = "SW_CONFIG_CHANGED_BY_MARVIS"
MARVIS_ROGUE_REASON = "rogue_dhcp_server_detected"
REJECTED_DHCP_TYPES = frozenset({...})
KEYWORD_PAIR = ("rogue", "dhcp")
```

Public methods:

- `matches(record)` returns True when the record names a rogue DHCP server.
- `is_rejected(type_text)` returns True for a DHCP record that names no rogue
  server.
- `alarm_type_filter()` returns the value for the `type` query parameter.
- `event_type_filters()` returns the event type values the scan queries.

The matcher reads `type`, `reason`, `text`, and `reasons` from a record. It
lower-cases the text one time and tests the keyword pair against that copy.

### RogueDhcpFinding and RogueDhcpRecordNormalizer (`records.py`)

`RogueDhcpFinding` is a frozen dataclass. It declares the column set one time, so
an alarm row, an event row, and a Marvis action row share one shape.

Columns: `org_id`, `site_id`, `site_name`, `device_name`, `device_mac`,
`device_model`, `device_type`, `port_id`, `vlan`, `source`, `signal_type`,
`state`, `severity`, `first_seen`, `last_seen`, `occurrence_count`, `details`,
`record_id`, `scan_started_at`.

`RogueDhcpRecordNormalizer` converts a raw Mist record into a
`RogueDhcpFinding`. It holds one method for each source shape, because the field
names differ.

| Source | Device field | Port field | Time fields |
| - | - | - | - |
| Alarm | `switches` list, first entry | `port_id` | `timestamp`, `last_seen` |
| Device event | `mac` | `port_id` | `first_seen`, `timestamp` |
| Marvis config action | `mac` | `port_id` | `timestamp` |

State rule: a record reads `active` when the source reports it open. An alarm is
open when `acked` is false and no later recovery record exists. An event is
`active` when its last seen time falls inside the most recent 24 hours of the
window. Every other record reads `historical`. The rule lives in one method, so a
test can drive it directly.

Merge rule: the merge key is the tuple
`(site_id, device_mac, port_id, signal_type, last_seen_rounded_to_the_minute)`.
Two records that share that key become one row. The merged row sums the
occurrence counts, takes the earliest first seen and the latest last seen, and
joins the source names with a comma.

### RogueDhcpScanner (`scanner.py`)

The scanner owns the fan-out. It takes the session and an optional callable map,
so a test injects stand-ins and runs with no network.

```python
class RogueDhcpScanner:
    def __init__(self, apisession, org_id, window_days=30, api=None): ...
    def scan(self) -> RogueDhcpScanResult: ...
    def query_organization(self) -> list[RogueDhcpFinding]: ...
    def query_site(self, site_id) -> list[RogueDhcpFinding]: ...
    def resolve_site_names(self, site_ids) -> dict[str, str]: ...
```

`scan()` runs five steps.

1. It builds the window and logs it.
2. It calls `query_organization()`.
3. It reads the distinct site identifiers from those findings.
4. It calls `query_site()` for each identifier, inside a try block that records a
   failure and continues.
5. It merges, resolves the site names, and returns the result.

`RogueDhcpScanResult` is a frozen dataclass. It holds `findings`,
`sites_queried`, `sites_failed`, `source_counts`, `window_start`, `window_end`,
and `marvis_scope_note`.

Each API call passes `start` and `end` as epoch seconds and `limit=1000`. Paging
uses `mistapi.get_all`, which the repository already uses in
`src/api/api_core_fetch_utils.py`.

### RogueDhcpScanOperation (`operation.py`)

The menu entry point. It resolves the organization, runs the scanner, prints the
table, and writes the export.

```python
class RogueDhcpScanOperation:
    @staticmethod
    def run() -> None: ...
```

`run()` resolves the organization with
`ConfigUtils.get_cached_or_prompted_org_id()`. That helper reads the cache, then
the environment, then prompts. It already refuses to prompt under `--test`, so
the web dashboard path and the test path both work without a console.

The export calls:

```python
DataExporter.write_with_format_selection(
    rows,
    "OrgRogueDhcpServers.csv",
    api_function_name="scanOrgRogueDhcpServers",
    fieldnames=RogueDhcpFinding.column_names(),
)
```

`write_with_format_selection` already picks the backend from `OUTPUT_FORMAT` or
from `backend_options.format_override`. It prompts for nothing, so the web
dashboard path needs no special case.

When the scan collects zero records, the operation logs a clear message and
returns without a write, per FR-024.

### Primary key strategy

```python
"scanOrgRogueDhcpServers": {
    "type": "composite_pk",
    "primary_key": ["record_id", "site_id", "last_seen"],
    "indexes": ["org_id", "site_id", "device_mac", "signal_type", "state", "last_seen"],
    "unique_constraints": [],
    "description": "Rogue DHCP server findings merged from alarms, switch events, and Marvis actions",
},
```

A composite key fits, because the data is a time series and one device can report
the same signal on more than one day. A second run over one window rewrites the
same rows, so no duplicate appears, per SC-006.

### Web dashboard exposure

The portal gate in `web_portal/services/operation.py` reads:

```python
allowed = (
    category in PORTAL_RUNNABLE_CATEGORIES
    and num is not None
    and num < DESTRUCTIVE_THRESHOLD
)
```

`DESTRUCTIVE_THRESHOLD` is 90, so the gate refuses 269 today. The comment above
the constant states that removing the bound would widen the portal by 49
operations, and that widening is a separate change. This plan therefore keeps the
bound and adds one explicit allowlist.

```python
PORTAL_EXPLICIT_ALLOWLIST = frozenset({"269"})

allowed = (
    category in PORTAL_RUNNABLE_CATEGORIES
    and num is not None
    and (num < DESTRUCTIVE_THRESHOLD or menu_number in PORTAL_EXPLICIT_ALLOWLIST)
)
```

The registry check still runs first, so the allowlist can never admit an
operation that the registry does not call safe. The gate stays fail-closed.

One category range joins `CATEGORY_RANGES` so the page groups the operation under
a clear name instead of `Other`:

```python
(269, 269, "Network Security Scans"),
```

A guardrail test proves both halves: the gate admits 269, and the gate still
refuses a destructive number and an unparseable key.

The result view needs no new template. The operation writes an output file, the
run record reports it in `output_files`, and the existing data preview modal in
`web_portal/templates/operations.html` renders the rows and exports the CSV file.

The upgrade capture portal in `src/upgrade_portal/` receives no change, per
FR-031.

## Test Strategy

| Area | Test | Proves |
| - | - | - |
| Matcher | accepts each literal alarm type | FR-005 |
| Matcher | accepts each literal event type | FR-006 |
| Matcher | accepts the Marvis event only with a rogue reason | FR-007 |
| Matcher | accepts the Marvis config action reason | FR-008 |
| Matcher | accepts a keyword record with an unknown type | FR-009 |
| Matcher | rejects pool exhaustion and DHCP failure | FR-010 |
| Scanner | queries the organization before any site | FR-011 |
| Scanner | queries only a named site | FR-014, SC-003 |
| Scanner | one failing site does not end the run | FR-025, SC-004 |
| Scanner | the window spans 30 days | FR-003 |
| Records | every source yields one column set | FR-018 |
| Records | the merge collapses a duplicate | FR-016, SC-005 |
| Records | the state reads active or historical | FR-017 |
| Operation | the export receives the right endpoint name | FR-022, FR-023 |
| Operation | an empty result writes nothing | FR-024 |
| Portal | the gate admits 269 and still refuses a destructive number | FR-029 |
| Property | the merge never grows the list | invariant |
| Property | the normalizer always returns the declared columns | invariant |

Every test injects a stand-in for `mistapi`. No test opens a network connection.
The repository pattern is `patch("<module>.mistapi", MagicMock())`, which
`tests/unit/api/test_api_core_fetch_utils.py` already uses.

## Risks

| Risk | Mitigation |
| - | - |
| Mist renames a type string. | The keyword rule in FR-009 catches a new name without a code change. |
| The 30-day window exceeds an endpoint limit. | The scanner catches the refusal, shortens the window for that endpoint, and reports the shorter window it used. |
| A large organization issues too many requests. | The scan queries only a named site. The existing adaptive delay helper paces the calls. |
| The portal allowlist widens the attack surface. | The registry category check runs first and still gates every operation. A guardrail test proves the refusal path. |
| The menu count tests break. | The task list updates the expected count and regenerates the wiki reference. |

## Execution Order

1. Add the primary key strategy, because the constitution requires it first.
2. Build `signals.py` with its tests.
3. Build `records.py` with its tests.
4. Build `scanner.py` with its tests.
5. Build `operation.py` with its tests.
6. Wire the menu row and the registry entry, then repair the count tests.
7. Open the portal gate and add the guardrail test.
8. Update the documentation and add the release-note fragment.
9. Run every gate, repair every failure, and repeat until clean.
10. Commit, push, open the pull request, and merge to `main`.
