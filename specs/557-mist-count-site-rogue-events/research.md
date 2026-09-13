# Phase 0 Research: countSiteRogueEvents

This document records the research decisions taken before Phase 1 design. Each task
uses the Decision / Rationale / Alternatives Considered format mandated by the
SpecKit plan template.

## Research Task 1: SDK function signature & behavior

**Decision**: Use
`mistapi.api.v1.sites.rogues.events.count.countSiteRogueEvents(mist_session, site_id, distinct=None, type=None, ssid=None, bssid=None, ap_mac=None, channel=None, seen_on_lan=None, start=None, end=None, duration="1d", limit=100)`.

The function returns a `mistapi.APIResponse` whose `.data` attribute is a single JSON
object with the shape:

```json
{
  "distinct": "type",
  "end": 1719676800,
  "limit": 100,
  "results": [
    {"count": 42, "type": "honeypot"},
    {"count": 17, "type": "lan"}
  ],
  "start": 1719590400,
  "total": 59
}
```

Source: `documentation/api/sites/GET_sites_site_id_rogues_events_count.md` (the
enriched per-endpoint doc generated from the OpenAPI spec). The endpoint is a
server-side aggregation -- it returns one summary block plus one `results` array
sized by the cardinality of the chosen `distinct` attribute.

**Rationale**: The enriched doc, the OpenAPI schema, and the mistapi 0.59 source
agree on the parameter list. `distinct` is optional in the schema; when omitted the
Mist server defaults grouping to `type`. `duration="1d"` is the documented default.
`limit=100` is the documented default and is sufficient for every aggregation key
this endpoint supports (rogue types and channels both have <100 distinct values).
The response shape matches the Mist "count by distinct" family used elsewhere in the
SDK (NAC events count, device events count) so the existing flatten patterns in
`RogueDataProcessor` apply with no new helpers.

**Alternatives Considered**:

1. Call the underlying HTTP endpoint with `requests` directly -- rejected because the
   constitution mandates `mistapi` as the sole interface to Mist Cloud and direct
   `requests` use bypasses session reuse, retry, and rate-limit adaptation.
2. Fetch all rogue events via `searchSiteRogueEvents` and aggregate client-side --
   rejected because it transfers orders of magnitude more data, runs into pagination
   and rate-limit pressure, and produces the wrong primary key (per-event rather
   than per-count-bucket).

## Research Task 2: Primary Key Strategy

**Decision**: `auto_increment_with_unique` with the uniqueness tuple
`(site_id, distinct, distinct_value, start, end)` on the results table and
`(site_id, distinct, start, end)` on the summary table.

```python
ENDPOINT_PRIMARY_KEY_STRATEGIES["countSiteRogueEvents"] = {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique": ["site_id", "distinct", "distinct_value", "start", "end"],
    "indexes": ["site_id", "distinct", "start"],
}
```

**Rationale**: The response is an aggregation, not an entity. There is no stable
server-supplied UUID on a `count_result` row -- the only identity is the tuple
(grouping attribute, distinct value, time window, site). `natural_pk` is wrong
because the API gives no `id`. `composite_pk` would require synthesizing one from
the same tuple, which adds no value over `auto_increment_with_unique` because the
constitution-approved pattern uses an internal surrogate `misthelper_internal_id`
plus a database-enforced UNIQUE constraint that produces the same upsert semantics
on `INSERT OR REPLACE`. The `indexes` list optimizes the two common read paths:
"all counts for site X" and "all counts grouped by attribute Y".

**Alternatives Considered**:

1. `natural_pk` on a server-supplied id -- rejected; no such id exists on a count
   result.
2. `composite_pk` on (site_id, distinct, distinct_value, start, end) -- rejected
   because the constitution-recommended pattern for aggregated/summary data with
   no stable server key is `auto_increment_with_unique`; this also keeps the
   foreign-key ergonomics of a simple integer surrogate when joining to the
   summary table.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV files:
  - `data/site_rogue_events_count_summary_<site_id>_<utc_timestamp>.csv`
  - `data/site_rogue_events_count_results_<site_id>_<utc_timestamp>.csv`
- SQLite tables (auto-created by `DataExporter` on first run):
  - `site_rogue_events_count_summary`
  - `site_rogue_events_count_results`
- ArangoDB collections (when polyglot backend active):
  - `site_rogue_events_count_summary`
  - `site_rogue_events_count_results`
  - Edge `site_to_rogue_event_count` linking site vertex to summary vertex.

**Rationale**: Two tables are required because the response is a one-to-many
structure (one summary, N result rows). Naming follows the existing convention used
by `searchSiteRogueEvents` (singular noun + `_summary` / `_results` suffix). The
`<site_id>_<utc_timestamp>` suffix on CSV filenames matches the pattern set by other
site-scoped exports in `RogueDataProcessor` and keeps re-runs from clobbering prior
output.

**Alternatives Considered**:

1. Single denormalized table with the summary fields repeated on every result row
   -- rejected because it bloats SQLite (the summary block is constant per
   invocation) and complicates the upsert tuple.
2. Use the operationId verbatim as the table name (`countSiteRogueEvents`) --
   rejected because the project naming convention is snake_case for tables and
   files; the operationId is camelCase per the OpenAPI spec.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Menu number **197**. Category: Safe Site Reads / Rogues sub-cluster.

**Rationale**: The current menu range is 1-194 per `.github/copilot-instructions.md`.
194 is the most recent destructive op (clone device config to gateway template).
195-196 are reserved for in-flight parallel specs that may land first in the
extraction sweep. 197 is the first safe integer above the destructive ceiling and
keeps the rogue-related menu items together when sorted. The endpoint is read-only
(GET) so it slots into the safe-exports neighborhood despite the high integer; the
README menu table groups by category, not by raw integer. At `/speckit.tasks` time
the agent must re-verify the current high-water mark; if 197 is taken, use the
next free integer.

**Alternatives Considered**:

1. Slot into the existing rogue cluster around 153 -- rejected because that band is
   already populated and inserting a new integer there shifts every downstream menu
   number, breaking automation that pins to `--menu N`.
2. Bump straight to 200 to leave a gap -- rejected; gaps create ambiguity about
   what was deprecated versus reserved, and the README operation count must equal
   the highest live menu number.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: Prompt the user for `site_id`, `distinct` (default `type`), and
`duration` (default `1d`). Optional filters (`ssid`, `bssid`, `ap_mac`, `channel`,
`seen_on_lan`, `type`) are gathered through a single "advanced filters? (y/N)"
prompt that, on `y`, walks through each filter with an empty-default skip.
`MIST_HOST` and `MIST_API_TOKEN` come from `.env`. `org_id` is loaded from `.env`
only for the existing site-picker helper, not requested again at this prompt.

**Rationale**: `safe_input()` wraps every prompt with named contexts
(`"site_rogue_count:site_id"`, `"site_rogue_count:distinct"`,
`"site_rogue_count:duration"`, `"site_rogue_count:advanced"`,
`"site_rogue_count:<filter_name>"`). The default `distinct=type` matches the API
default and produces the most useful aggregation for NOC engineers (counts of
honeypot vs lan vs spoof vs others). Sensitive material (the API token) is never
prompted; it is loaded by the existing `mistapi.APISession` initializer from
`.env`. The advanced-filters gate exists because asking seven optional prompts on
every invocation creates friction for the common case (operator wants the
one-day breakdown by type).

**Alternatives Considered**:

1. Prompt for every query parameter unconditionally -- rejected; violates the
   safety-first usability principle for junior NOC engineers and adds seven
   prompts that are empty 90% of the time.
2. Take all parameters as CLI flags only and skip prompts -- rejected; the menu
   contract is interactive, and CLI-flag-only would break feature parity with
   adjacent rogue menu items.
