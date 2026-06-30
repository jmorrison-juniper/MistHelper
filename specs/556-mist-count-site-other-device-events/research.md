# Phase 0 Research: countSiteOtherDeviceEvents

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Enriched API doc**: `documentation/api/sites/GET_sites_site_id_otherdevices_events_count.md`

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Call the endpoint through the `mistapi` SDK using the function
exported from `mistapi.api.v1.sites.otherdevices.events.count` (operationId
`countSiteOtherDeviceEvents`). The published enriched doc also references the
alias path `mistapi.api.v1.sites.devices_-_others.countSiteOtherDeviceEvents()`,
but Python module identifiers cannot legally contain `-`, so the dotted import
path actually used at runtime is the `otherdevices.events.count` form declared
in the spec.

Expected Python signature, derived from the OpenAPI parameter list and the
mistapi convention of one positional `APISession` plus keyword query params:

```python
mistapi.api.v1.sites.otherdevices.events.count.countSiteOtherDeviceEvents(
    mist_session,            # mistapi.APISession instance from .env-driven login
    site_id,                 # str, required, UUID of the target site
    distinct=None,           # Optional[str] - attribute to group counts by
    type=None,               # Optional[str] - event type filter
    start=None,              # Optional[str] - epoch seconds or relative ("-1d")
    end=None,                # Optional[str] - epoch seconds or relative ("now")
    duration="1d",           # str, default per OpenAPI spec
    limit=100,               # int, default per OpenAPI spec
)
```

Returns a `mistapi.APIResponse` object. The `.data` attribute is a dict shaped
like:

```json
{
  "distinct": "type",
  "start": 1719600000,
  "end": 1719686400,
  "limit": 100,
  "total": 42,
  "results": [
    {"count": 30, "type": "OTHER_DEVICE_EVENT_FOO"},
    {"count": 12, "type": "OTHER_DEVICE_EVENT_BAR"}
  ]
}
```

The `results` array contains objects with one required field (`count`) plus
arbitrary additional string-typed properties whose names depend on the
`distinct` argument the caller passed (e.g. `type`, `mac`, `model`).

**Rationale**: This signature matches the OpenAPI parameter table verbatim and
follows the mistapi convention used by every other count/search endpoint
already wired into MistHelper (e.g. searchSiteDeviceEvents). Defaults
(`duration="1d"`, `limit=100`) come from the OpenAPI doc and must be passed
through unchanged so the menu item's behavior matches the official API
defaults.

**Alternatives Considered**:

1. **Direct `requests.get(...)` call against the documented URL** -- rejected.
   The constitution (Technology & Compatibility Constraints) mandates that the
   `mistapi` SDK is the sole permitted interface to the Mist Cloud API
   whenever a method exists. A direct HTTP call would also bypass session
   reuse, auth header handling, and `mistapi`-level retry instrumentation.
2. **Wrap the SDK call in a custom paginator helper** -- rejected. The count
   endpoint returns a single JSON object (not a long list); no pagination
   loop is needed. The `limit` argument caps the number of distinct groups
   returned, not pages of events.

## Research Task 2: Primary Key Strategy

**Decision**: Use `composite_pk` keyed by
`(site_id, distinct, start, end, group_value)` for the per-group results
table, and use `auto_increment_with_unique` keyed by
`(site_id, distinct, start, end)` for the one-row-per-run summary table.

The `results` array is, by API design, a group-by aggregation. The natural
business key for each row is the tuple `(scope_site_id, the_attribute_we_grouped_on, the_time_window, the_group_value)`.
That tuple guarantees that re-running the same menu invocation with the same
inputs upserts the same row instead of inserting duplicates, while two
different `distinct` choices (e.g. `distinct=type` vs `distinct=mac`) at the
same site/window produce distinct rows.

The summary record (one row capturing `total`, `limit`, `start`, `end`,
`distinct`) has no field that is guaranteed unique on its own across runs --
two users running with identical inputs would otherwise collide -- so it gets
`auto_increment_with_unique` with the same logical key as a `UNIQUE` index.
This keeps SQLite upserts idempotent while still allowing pre-aggregated
summary history if the user opts into historical retention.

**Rationale**: This is the same pattern MistHelper uses for adjacent
`count*` and `search*` endpoints (see `searchOrgDeviceEvents` and
`searchSiteDeviceEvents` registrations in `ENDPOINT_PRIMARY_KEY_STRATEGIES`).
Composite keys avoid duplicate-row growth on repeated runs without inventing
an artificial UUID that the Mist API itself does not supply.

**Alternatives Considered**:

1. **`natural_pk` keyed by a server-supplied ID** -- rejected. The response
   schema does not include any per-row server-side ID; the only required
   field is `count`. There is no natural single-column natural key.
2. **`auto_increment_with_unique` only (no composite key)** -- rejected. That
   strategy would still upsert correctly, but it loses the
   `INSERT OR REPLACE`-via-composite-key semantics that MistHelper relies on
   for fast SQLite writes on adjacent count endpoints. Aligning with the
   established pattern reduces cognitive load for junior NOC engineers.
3. **`composite_pk` on the summary row using `(site_id, distinct, start, end)`** --
   acceptable but slightly more brittle: if the API ever begins returning a
   different `end` value than the caller sent (e.g. clock skew normalization),
   re-runs would create new rows. `auto_increment_with_unique` with a UNIQUE
   index on the same tuple is the safer default for the summary row.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- **CSV filename pattern** (per-run):
  `data/site_<site_id>_other_device_events_count_<distinct>_<YYYYMMDDHHMMSS>.csv`.
  Two CSVs are written per run: one suffixed `_summary` and one suffixed
  `_results`, matching the two-table SQLite layout.
- **SQLite tables**: `site_other_device_events_count_summary` (one row per
  run) and `site_other_device_events_count_results` (one row per group
  returned).
- **ArangoDB collections**: same names as the SQLite tables (snake_case).
- **`api_function_name`** passed to `DataExporter.write_with_format_selection`:
  `"countSiteOtherDeviceEvents"`. This is the lookup key into
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` and ensures the exporter routes to the
  correct PK behavior.

**Rationale**: Names mirror the operationId (`countSiteOtherDeviceEvents`) in
snake_case so they sort next to sibling endpoints in directory listings and
SQLite `.tables` output. Including `site_<site_id>` in the CSV filename keeps
multi-site exports unambiguous on disk. The timestamp suffix follows the
convention of other site-scoped exports already in MistHelper.

**Alternatives Considered**:

1. **One combined table containing both summary and results** -- rejected.
   Mixing a single-row aggregate with N detail rows in the same table forces
   nullable columns and breaks the composite primary key design. Two tables
   keep the schema clean and let the user query each layer independently.
2. **Omitting `site_<site_id>` from the CSV filename** -- rejected. A NOC
   engineer running the menu against multiple sites in a session would
   otherwise have to inspect the file contents to disambiguate; embedding the
   site_id in the filename avoids that step.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Place this operation at **menu 197**, in a new "Read-only
event/count catalog" cluster above the current 194-item ceiling. The cluster
is created by the broader OpenAPI cataloging effort (specs 500-599+) and is
not destructive, so it sits outside the 154-194 destructive range. If 197
collides with an in-flight feature branch at task generation time, the next
free integer above 194 is used.

Within the existing 1-194 layout, count/event-style queries belong logically
near the Interactive Safe stats range (73-91) or the events range (20-26).
However, those slots are already populated, and the cataloging effort adds
many new endpoints in parallel. Extending above 194 is simpler than reshuffling
existing menu numbers and matches what other catalog specs (e.g. 500) already
proposed -- each catalog spec proposes its own number, with the final
authoritative layout reconciled at `/speckit.tasks` time.

**Rationale**: Read-only count endpoints carry no destructive risk and benefit
from being grouped together for discoverability. Extending the menu above 194
also avoids invalidating any documentation, README, or training material that
references existing menu numbers in the 1-194 range.

**Alternatives Considered**:

1. **Squeeze into a gap inside 20-26 (events)** -- rejected. Those numbers
   are stable, well-documented, and visually adjacent to wireless / wired /
   gateway events; injecting an "other devices" count there would force
   renumbering of downstream operations and invalidate user muscle memory.
2. **Place inside the Resource Intensive cluster (96-101)** -- rejected. The
   count endpoint is lightweight (single request, single small JSON object);
   misclassifying it as resource intensive would discourage casual use.
3. **Reuse the next number in the destructive range (154-194)** -- rejected.
   The constitution treats menu 90-100 (and by extension the documented
   destructive cluster) as requiring explicit confirmation; placing a
   read-only endpoint there would be misleading.

## Research Task 5: Required User Prompts

**Decision**: The menu method prompts the user (via `safe_input()`) for the
inputs below, in this order, and pulls the rest from `.env` / SDK defaults.

| Prompt | Source | Required? | `safe_input()` context string | Default if user just hits Enter |
|--------|--------|-----------|--------------------------------|---------------------------------|
| `site_id` | user | Yes | `"site_other_device_events_count:site_id"` | None -- abort with WARNING if blank |
| `distinct` attribute | user | No | `"site_other_device_events_count:distinct"` | omit (let API choose its own default) |
| `type` filter | user | No | `"site_other_device_events_count:type"` | omit |
| time window selector ("last 1d", "last 7d", "custom") | user | No | `"site_other_device_events_count:window"` | `"1d"` -- passed to `duration` |
| `start` / `end` (only if user picks "custom") | user | No | `"site_other_device_events_count:start"`, `":end"` | omit |
| `limit` | user | No | `"site_other_device_events_count:limit"` | `100` |
| `MIST_HOST` | `.env` | Yes | n/a | n/a |
| `MIST_API_TOKEN` | `.env` | Yes | n/a | n/a |
| Active `mistapi.APISession` | reused from existing menu bootstrap | Yes | n/a | n/a |

`site_id` is the only mandatory user-supplied prompt. All query parameters
are optional in the OpenAPI spec; the menu mirrors that, defaulting to "last
1 day across all distinct attributes" so a junior NOC engineer can run the
menu with a single answer (the site UUID) and still get useful output.

**Rationale**: Minimizing the number of mandatory prompts respects the
constitution's audience standard ("Fred Rogers meets NASA/JPL safety
standards") -- junior engineers should be able to run the menu without
memorizing the OpenAPI query-parameter list. Routing all optional parameters
through `safe_input()` with documented `context=` strings keeps SSH and
container EOF handling consistent with adjacent menu items. Loading `MIST_HOST`
and `MIST_API_TOKEN` from `.env` (never prompting for them) prevents secrets
from appearing in shell history or scrollback.

**Alternatives Considered**:

1. **Prompt for `start` and `end` epoch values unconditionally** -- rejected.
   Epoch math is error-prone at a terminal prompt; offering "last 1d" / "last
   7d" / "custom" as a menu first, then only asking for epoch values under
   "custom", reduces the failure surface.
2. **Hard-code `distinct="type"`** -- rejected. Forcing a single grouping
   removes value the API itself offers (the user can group by `mac`, `model`,
   `type`, etc.). The menu collects this as an optional prompt instead.
3. **Pull `site_id` from `.env`** -- rejected. A NOC engineer typically runs
   against multiple sites in one session; `.env` stores the org token, not
   the site identifier. Prompting at runtime is correct.
