# Phase 0 Research: countSiteWiredClients

Research outputs for the new menu item that wraps
`GET /api/v1/sites/{site_id}/wired_clients/count`. Each section follows the
Decision / Rationale / Alternatives Considered format mandated by the
SpecKit plan template.

Reference enriched docs:
`documentation/api/sites/GET_sites_site_id_wired_clients_count.md`.

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Call the mistapi SDK function

```python
from mistapi.api.v1.sites.wired_clients import count as wired_clients_count

response = wired_clients_count.countSiteWiredClients(
    apisession,                # APISession from .env
    site_id,                   # required path param (UUID)
    distinct=distinct_field,   # optional query string
    mac=mac_filter,            # optional query string
    device_mac=device_mac,     # optional query string
    port_id=port_id,           # optional query string
    vlan=vlan_filter,          # optional query string
    start=start_epoch,         # optional integer epoch seconds (or relative "-1d")
    end=end_epoch,             # optional integer epoch seconds (or relative "now")
    duration=duration_str,     # optional duration, e.g. "1d", default "1d"
    limit=row_limit,           # optional integer, default 100
)
payload = response.data        # dict with distinct/end/limit/results/start/total
```

The SDK module mirrors the OpenAPI path: `mistapi.api.v1.sites.wired_clients.count`.
The function returns a `mistapi.APIResponse` whose `.data` attribute is the
parsed JSON object. The 200 schema (from the enriched doc) is:

```json
{
  "distinct": "string",
  "end": "int32",
  "limit": "int32",
  "start": "int32",
  "total": "int32",
  "results": [
    { "count": "int32", "<distinct field>": "string" }
  ]
}
```

`results[]` is a uniqueItems array; each entry has a mandatory `count` plus
`additionalProperties` (the actual `distinct` field name, e.g. `mac` or
`device_mac`). Pagination is supported via `limit` and `page` but the default
`limit=100` is sufficient for typical wired-client distributions.

**Rationale**: The mistapi SDK is the only sanctioned client (Constitution
Technology Constraints). The signature matches the surrounding `countOrgWired
Clients` / `countSiteWirelessClients` patterns already in `MistHelper.py`
(see lines ~4561 / ~4575 for the org analogs), so a NOC engineer reading the
new method will find no surprises.

**Alternatives Considered**:

- Direct `requests.get(...)` against the REST URL -- rejected: violates the
  "single SDK" rule and bypasses the SDK's built-in pagination, retry, and
  rate-limit hooks.
- Reusing `searchSiteWiredClients` plus `len()` -- rejected: returns per-row
  client records rather than a server-side aggregate; defeats the purpose
  of the count endpoint and burns the API quota.
- Hand-rolling a wrapper around the mistapi subpackage -- rejected: violates
  Principle II ("Class-Based Architecture (No Wrappers)").

## Research Task 2: Primary Key Strategy

**Decision**: `auto_increment_with_unique` -- one synthetic
`misthelper_internal_id` integer primary key, indexed by `site_id` and
`distinct`. No unique constraints beyond the synthetic key.

Concrete entry to insert into `ENDPOINT_PRIMARY_KEY_STRATEGIES` near the
existing `countOrgWiredClients` block (MistHelper.py:~4561):

```python
"countSiteWiredClients": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "indexes": ["site_id", "distinct"],
    "unique_constraints": [],
    "description": "Site-scope wired client count aggregates",
},
```

**Rationale**: The endpoint returns an aggregate snapshot whose composition
changes every time the user picks a different `distinct` field or time
window. There is no stable business key on the rows -- `count` plus a
distinct value is not unique across runs because the distribution shifts
minute-to-minute. Every sibling `countOrg*Clients` endpoint in the codebase
(`countOrgWanClients`, `countOrgWiredClients`, `countOrgWirelessClients`,
`countOrgWirelessClientsSessions`) already uses this strategy with the same
shape; keeping the new entry identical (swapping `org_id` for `site_id`)
preserves cognitive consistency for whoever maintains the registry next.

**Alternatives Considered**:

- `natural_pk` on `["site_id", "distinct", "<distinct_value>"]` -- rejected:
  the `<distinct_value>` field name varies (mac / device_mac / port_id /
  vlan), so the natural PK would have to change shape per call, which the
  current `DataExporter` cannot model.
- `composite_pk` on `["site_id", "distinct", "start", "end"]` -- rejected:
  the API does not require start / end (`duration` defaults to "1d"), so
  these fields can be NULL, which violates `composite_pk` semantics in
  `DataExporter`. Also the user typically wants every historical snapshot
  retained, which `auto_increment_with_unique` provides naturally.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV / multi-row export filename: `data/count_site_wired_clients.csv`.
- SQLite table name: `count_site_wired_clients`.
- ArangoDB collection name: `count_site_wired_clients` (consistent with the
  CSV/SQLite naming; edges to the `sites` collection created by the
  existing graph-edge map on `site_id`).

`DataExporter.write_with_format_selection(data, "count_site_wired_clients",
api_function_name="countSiteWiredClients")` is the exact call site.

**Rationale**: Snake-case singular operation name mirrors the operationId
in lowercase. This is identical to the convention used by
`count_org_wired_clients.csv` (see existing `countOrgWiredClients` export
path), which guarantees the polyglot ArangoDB / Redis backend recognizes
the collection prefix and routes accordingly.

**Alternatives Considered**:

- `data/site_wired_client_count.csv` -- rejected: word order does not match
  the operationId; sorting and pattern-grepping the `data/` directory by
  operation becomes harder.
- Embedding `site_id` in the filename (`count_site_wired_clients_<site_id>
  .csv`) -- rejected: the same operation may run across many sites in one
  session, which would explode the `data/` directory with one file per
  site. The CSV / SQLite row already carries `site_id`, which is the
  correct place for the discriminator.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Menu number **195**, registered in the `MENU_DISPATCH`
dictionary in `MistHelper.py` (currently ending at "194"):

```python
"195": (
    SiteClientExporter.export_site_wired_clients_count,
    "Count site wired clients (distinct/aggregate)",
),
```

Category: a virtual extension of the **Interactive Safe Site Clients** block
(currently 60-72) but appended to the tail of the dispatch dictionary because
the in-cluster slots are already filled. The README menu table will list it
under the same "Site clients" group with a "(new)" annotation and a note that
appended slots will be merged into the cluster during the next renumbering
sweep.

**Rationale**: The current top of the dispatch dictionary is "194" (see the
support-ticket / device-config-clone block). Inserting at 73 would force
renumbering of every menu item above 73 (~122 entries) -- a massive,
risky, conflict-prone diff for what is effectively a one-method addition.
Appending follows the precedent set when the `countOrg*Clients` cluster
itself was appended rather than renumbered.

**Alternatives Considered**:

- Insert as menu **70a** or **70.5** -- rejected: the dispatch dict keys are
  strings but the menu UI parses them as integers; non-integer keys would
  require a code change in the menu renderer.
- Renumber every item from 73 upward to insert at 73 -- rejected: enormous
  diff, breaks every other open feature spec's proposed number, breaks
  every `--menu N` automation script in the wild.
- Use a six-digit reserved range starting at 100000 -- rejected: visually
  ugly in the menu, no precedent in the codebase.

## Research Task 5: Required User Prompts

**Decision**: Three required prompts and one optional prompt, all collected
via `safe_input()` with explicit `context=` strings.

| Prompt order | Field | Source | Default | safe_input context |
| - | - | - | - | - |
| 1 | `org_id` | `.env` (`MIST_ORG_ID`); only re-prompt if absent | `.env` value | `count_site_wired_clients:org_id` |
| 2 | `site_id` | user input -- required UUID | none | `count_site_wired_clients:site_id` |
| 3 | `distinct` | user input -- enum-ish string (mac / device_mac / port_id / vlan) | empty (server picks) | `count_site_wired_clients:distinct` |
| 4 | `duration` | user input -- optional override of API default "1d" | "1d" | `count_site_wired_clients:duration` |

`mac`, `device_mac`, `port_id`, `vlan`, `start`, `end`, and `limit` are
exposed only via the optional "advanced filters" branch that prompts the
user once with "Apply advanced filters? [y/N]" through `safe_input()` and,
on `y`, walks a single dict-driven loop that collects values without
exceeding the 5-block / 25-line limit. This keeps the simple path simple
for junior NOC engineers (Fred-Rogers-meets-NASA tone) while preserving
power-user access to the full query surface.

**Rationale**: The endpoint is keyed on `site_id`; the `org_id` is only
needed to scope which sites the operator is allowed to choose from. Pulling
`org_id` from `.env` matches the surrounding interactive site menu items
(60-72) and avoids re-typing the same value every run. The `distinct` field
is the one knob a NOC engineer is likely to flip per run (mac vs vlan vs
port_id), so it sits in the simple path. Optional filters are off by
default to satisfy Principle I (5-block budget) without surrendering the
ability to inspect them on demand.

**Alternatives Considered**:

- Prompt for every query parameter every run -- rejected: 9 prompts is
  user-hostile, blows the 5-block budget, and the API treats most as
  optional with sensible defaults.
- Read every parameter from `.env` -- rejected: `distinct` and `duration`
  change per run, which is the whole point of having a count endpoint;
  pinning them to `.env` would defeat the purpose.
- Read query parameters from a YAML / JSON config file -- rejected: adds a
  new dependency surface (file path, schema validation, race conditions in
  SSH sessions) for no proportional benefit at one menu item.
