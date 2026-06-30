# Phase 0 Research: countOrgNacClientEvents

**Feature**: `521-mist-count-org-nac-client-events`
**Source endpoint doc**: `documentation/api/orgs/GET_orgs_org_id_nac_clients_events_count.md`
**Spec**: [spec.md](./spec.md)

This document resolves the five open research questions that block Phase 1
design. Each task uses the Decision / Rationale / Alternatives Considered
format.

## Research Task 1: SDK function signature and behavior

**Decision**

Use the `mistapi` SDK call

```python
mistapi.api.v1.orgs.nac_clients.events.count.countOrgNacClientEvents(
    mist_session=session,
    org_id=org_id,
    distinct=distinct,
    type=event_type,
    start=start_epoch,
    end=end_epoch,
    duration=duration,
    limit=limit,
)
```

The call returns a `mistapi.APIResponse` whose `.data` attribute is a dict with
the keys `distinct`, `end`, `limit`, `results`, `start`, `total`. The `results`
key is a list of objects of shape `{ "count": int, "<distinct_field>": str }`
where the second key name is whatever value was passed in `distinct`. All other
top-level keys echo back the effective query parameters. Only `org_id` is
required.

**Rationale**

Confirmed against
`documentation/api/orgs/GET_orgs_org_id_nac_clients_events_count.md` which
documents the response schema `{distinct, end, limit, results[], start, total}`
with `count_result` items requiring a `count` integer and arbitrary
`additionalProperties` of type string (the distinct group value). The doc lists
six query parameters (`distinct`, `type`, `start`, `end`, `duration`, `limit`)
all optional, with `duration` defaulting to `1d` and `limit` defaulting to
`100`. The SDK module path
`mistapi.api.v1.orgs.nac_clients.events.count.countOrgNacClientEvents` is taken
from spec.md and the Mist API doc's `## mistapi SDK` line; SDK kwargs mirror
the OpenAPI parameter names exactly.

**Alternatives Considered**

- Use the raw `requests` HTTP path instead of the `mistapi` SDK. Rejected:
  Constitution mandates `mistapi` as the sole permitted Mist Cloud interface;
  it owns retry, rate limit, and token handling.
- Page through results with `limit` + `page`. Rejected: the count endpoint
  returns a single aggregated payload; `total` and `results[]` are already
  consolidated -- `page` is documented for parity with other endpoints but is
  not needed here for a count-by-distinct call bounded by `limit` <= 100.

## Research Task 2: Primary Key Strategy

**Decision**

Use **`auto_increment_with_unique`** with a unique composite index on
`(org_id, distinct_field, distinct_value, start_epoch, end_epoch)`.

```python
"countOrgNacClientEvents": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_index": [
        "org_id",
        "distinct_field",
        "distinct_value",
        "start_epoch",
        "end_epoch",
    ],
    "indexes": ["org_id", "distinct_field", "start_epoch"],
}
```

**Rationale**

The response is an aggregated count, not an individual event. The Mist API
does not provide a stable surrogate or business key for each group row -- the
only natural identifier of a group is the tuple of (the org being queried,
which attribute was used for grouping, the actual group value, and the time
window). That tuple repeats on every re-run with the same parameters, so
`auto_increment_with_unique` lets SQLite upsert via the unique index while
preserving an internal numeric PK for joins. This is the documented strategy
for "Aggregated/summary data without stable keys" (per copilot-instructions
Database Strategy section), exactly matching `getOrgLicensesSummary`.

**Alternatives Considered**

- `natural_pk` on `(org_id, distinct_field, distinct_value)` alone. Rejected:
  two runs with different time windows would collide on the same key and
  overwrite earlier counts, destroying historical comparison data.
- `composite_pk` including `query_executed_at` timestamp. Rejected:
  re-running the exact same query within minutes would create duplicates
  instead of updating the row -- counts for the same window should
  idempotently overwrite, not append.

## Research Task 3: Output filename and SQLite table

**Decision**

- CSV filename: `data/org_nac_client_events_count_<org_id>_<YYYYMMDD_HHMMSS>.csv`
- SQLite table name: `org_nac_client_events_count`
- ArangoDB collection name: `org_nac_client_events_count`

**Rationale**

The naming follows the established MistHelper convention used by adjacent NAC
export operations: snake-case derived from the operationId, prefixed with the
scope (`org_`), suffixed with the entity (`nac_client_events_count`). Including
the `org_id` and an ISO-like timestamp in the CSV name guarantees no overwrite
of prior runs when the user is multi-tenant. The SQLite table drops the
timestamp/org suffix because rows already carry `org_id` and time-window
columns as part of the unique index -- one logical table per endpoint.
`DataExporter.write_with_format_selection(data, filename,
api_function_name="countOrgNacClientEvents")` performs the routing across
backends; the `api_function_name` argument is what wires the call to the
correct entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Alternatives Considered**

- Per-distinct-field table names (e.g. `org_nac_event_counts_by_type`).
  Rejected: explodes table count for low gain; the unique index already
  segments rows by `distinct_field`.
- Drop the timestamp from the CSV name. Rejected: would silently overwrite
  prior exports for the same org -- bad for NOC engineers who diff CSVs.

## Research Task 4: Menu category placement and next available menu number

**Decision**

Menu number **195**, category **Safe Org Exports -> NAC**. Place the menu entry
adjacent to the existing `searchOrgNacClients` and `countOrgNacClients`
operations.

**Rationale**

The repo `.github/copilot-instructions.md` Menu System section documents the
current range as 1-194. Adding to the end of the safe range keeps the
operation outside the destructive band (154-194) and avoids renumbering any
existing operation. NAC client search and count operations have historically
been clustered in the 28-30 / 80-91 read-only stats range, but inserting a new
operation mid-range would shift every subsequent number, breaking automation
that hard-codes `--menu N`. Appending at 195 is the safe append-only pattern.
The label in the menu list will read
`195. Org NAC Client Events - Count by Distinct Attribute`.

**Alternatives Considered**

- Insert at 31 (between gateways and templates) for "thematic" grouping.
  Rejected: shifts every number 31-194; breaks `--menu N` scripts and SSH
  runners (`data/SSH_COMMANDS.CSV` rows that target a specific menu number).
- Reuse a deprecated slot. Rejected: no deprecated slots exist in the
  documented range; reusing one risks colliding with another in-flight
  feature branch.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**

Prompts collected via `safe_input()` (in this order):

1. `org_id` -- if `MIST_ORG_ID` is set in `.env`, default to it and accept
   blank input to confirm; otherwise prompt with no default. Validate against
   the Mist UUID regex before sending.
2. `distinct` field -- prompt with an allow-list shown as a numbered submenu
   (`type`, `nas_vendor`, `vlan`, `ssid`, `port_type`, `auth_type`). Default
   to `type` on blank input.
3. `event_type` filter -- optional free-text; blank skips the parameter.
4. Time window -- prompt user to choose
   `(d)uration | (r)ange` then collect either `duration` (default `1d`,
   accepts `7d`, `2w`, etc.) or `start` / `end` (epoch seconds or relative
   strings like `-1d`, `-2h`, `now`).
5. `limit` -- optional integer prompt; default 100 (matches API default).

Values pulled from `.env`:

- `MIST_HOST` and `MIST_API_TOKEN` -- never prompted; loaded by the existing
  `mistapi.APISession` bootstrap.
- `MIST_ORG_ID` -- optional override that supplies the default for prompt 1.

**Rationale**

`safe_input()` is mandated for every prompt by Constitution III (Safety-First)
and is the only EOF-safe interactive primitive available in the SSH / Podman
container deployment. Defaulting `org_id` from `.env` matches the pattern used
by spec 500 and by every adjacent NAC operation. The allow-list submenu for
`distinct` prevents the user from sending an unsupported field (the API would
reject with 400) and aligns with the documented set of distinct dimensions
supported by NAC events. Mapping the time window to a two-step
duration-or-range prompt keeps the surface simple while preserving the
endpoint's full flexibility.

**Alternatives Considered**

- Single free-text prompt for `distinct`. Rejected: error-prone; the API
  rejects unknown distinct fields with HTTP 400 which would surface to the
  user as a confusing failure.
- Hard-code `distinct=type` and skip the prompt. Rejected: removes the
  primary analytical value of the endpoint (grouping by any attribute).
- Require explicit `start` / `end` only. Rejected: `duration` is the more
  ergonomic default for "events in the last 24h" -- the most common NOC
  workflow.
