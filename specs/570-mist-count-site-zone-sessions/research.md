# Phase 0 Research: countSiteZoneSessions

**Feature**: 570-mist-count-site-zone-sessions
**Date**: 2026-06-29
**Source docs**: `documentation/api/sites/GET_sites_site_id_zone_type_count.md`

The five research tasks below establish enough ground truth for Phase 1 design without
guessing. Each follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK Function Signature and Behavior

**Decision**: Call the endpoint via
`mistapi.api.v1.sites.count.countSiteZoneSessions(apisession, site_id, zone_type, distinct=None, user_type=None, user=None, scope_id=None, scope=None, start=None, end=None, duration="1d", limit=100)`.
The SDK returns a `mistapi.APIResponse` whose `.data` attribute is a JSON object with the
keys `distinct`, `start`, `end`, `limit`, `total`, and `results[]`. Each item in
`results[]` is a `count_result` object with a required integer `count` plus
`additionalProperties` of type string -- in practice the additional string property
carries the value of the `distinct` attribute the caller selected (for example
`zone_id`, `map_id`, or `user`).

**Rationale**: The enriched per-endpoint documentation at
`documentation/api/sites/GET_sites_site_id_zone_type_count.md` lists the exact path,
query parameters, defaults (`duration=1d`, `limit=100`), and the JSON schema for the 200
response. The schema explicitly marks `distinct`, `end`, `limit`, `results`, `start`,
and `total` as required, and the SDK module path is recorded as
`mistapi.api.v1.sites.count`. The schema's use of
`additionalProperties: { type: string }` on each `count_result` confirms that the
distinct attribute appears as an opaque string-typed key on every row, which dictates
the flatten strategy in Phase 1.

**Alternatives Considered**:

- Calling `mistapi.api.v1.sites.zones.*` directly (rejected: the count endpoint sits
  under the `count` submodule per the enriched doc, not under `zones`; the related
  `searchSiteZoneSessions` is the search endpoint, not the count endpoint).
- Building a raw `requests.get()` call against the path template (rejected: violates
  Constitution Principle II by introducing a wrapper outside the `mistapi` SDK; also
  duplicates pagination and auth handling already correct in the SDK).

## Research Task 2: Primary Key Strategy

**Decision**: Register the endpoint with `type="composite_pk"` and
`primary_key=["site_id", "zone_type", "distinct", "distinct_value", "start", "end"]`.
The combination of the site, the zone class, the chosen distinct attribute, the
attribute's literal value for the row, and the time window uniquely identifies one
count measurement. Indexes are placed on `site_id`, `zone_type`, `distinct`,
`distinct_value`, and `total` to support the most likely operator queries (per-site
distribution, top-N by total, drill-down on a single distinct attribute).

**Rationale**: The response carries no server-supplied row UUID and no monotonic
identifier; rows are aggregated counts over a time window, so two invocations with
different `start`/`end` parameters legitimately produce different rows for the same
(site, zone_type, distinct, distinct_value). A pure natural PK would lose history every
re-run; an auto-increment PK would silently create duplicates and break upsert
semantics. Composite PK preserves history while still allowing `INSERT OR REPLACE` to
update a row when the same window is re-queried.

**Alternatives Considered**:

- `natural_pk` on a synthesized concatenation -- rejected because there is no stable
  natural identifier in the payload; the synthesis would be fragile and undocumented.
- `auto_increment_with_unique` -- rejected because the unique constraint would still
  need to match the composite tuple, so it adds an artificial column without solving
  the upsert problem any more cleanly than a true composite PK.

## Research Task 3: Output Filename and SQLite Table

**Decision**: CSV file `data/SiteZoneSessionCounts.csv`; SQLite table
`site_zone_session_counts`. The flattened row schema is
`(site_id TEXT, zone_type TEXT, distinct TEXT, distinct_value TEXT, count INTEGER,
start INTEGER, end INTEGER, limit INTEGER, total INTEGER, retrieved_at TEXT)`.
ArangoDB collection name (when that backend is active) matches the SQLite table name.

**Rationale**: Existing SiteExportUtils outputs follow PascalCase CSV filenames
(`SiteZones.csv`, `SiteDevices.csv`) and snake_case SQLite tables. Embedding both
`site_id` and `zone_type` in every row de-normalizes for analyst convenience and lets
the table hold counts for multiple sites without a JOIN. The added `retrieved_at` column
(UTC ISO 8601 timestamp at write time) preserves run provenance and is excluded from
the PK so an upsert overwrites the count for the same window cleanly.

**Alternatives Considered**:

- Per-site CSV file (`SiteZoneSessionCounts_<site_id>.csv`) -- rejected because
  DataExporter is configured for one canonical filename per operationId and a per-site
  split conflicts with the SQLite single-table model.
- Storing the whole envelope (one row per response) with `results` as a JSON blob --
  rejected because it breaks CSV-friendliness and forces analysts to write JSON-aware
  SQL.

## Research Task 4: Menu Category Placement and Next Menu Number

**Decision**: Menu number **195**, placed at the head of a new Safe Site Exports
continuation band immediately above the existing 154-194 destructive cluster, labelled
in the menu table as `Count Site Zone Sessions (countSiteZoneSessions)`. Dispatch is
through `SiteExportUtils.count_site_zone_sessions()`.

**Rationale**: A scan of the existing menu registry in `MistHelper.py` shows menu
numbers 1-194 are fully assigned (current tail at 194 is Clone Device Config to Gateway
Template). The constitution requires sequential operation numbering, so the next
available integer is 195. The endpoint is read-only and site-scoped, so it logically
belongs near the existing site-zone export at menu 68 (`SiteConfigExporter.zones`).
Because reordering the existing menu would break operator muscle memory and external
documentation, the new operation appends at 195 with a brief cross-reference in the
README menu table pointing back to the zone-listing operation at 68.

**Alternatives Considered**:

- Inserting at 69 and renumbering everything downstream -- rejected because the
  existing operation numbers appear in `--test` skip lists, README, CHANGELOG history,
  external runbooks, and the SSH ForceCommand wrapper. The blast radius is unacceptable
  for a documentation convenience.
- Reserving a future-proof gap such as 200 -- rejected because the constitution calls
  for sequential numbering and any reserved gap is wasted space that a future read-only
  endpoint would want to fill anyway.

## Research Task 5: Required User Prompts

**Decision**: Three required prompts and two optional prompts, all through
`safe_input()`:

1. `site_id` (required) -- accept an empty input to fall back to `MIST_SITE_ID` from
   `.env`; validate the result against the Mist UUID shape; abort with a logged warning
   on failure.
2. `zone_type` (required) -- accept the closed enum `{zones, rssizones}`; default to
   `zones` on empty input; abort with a logged warning on any other value.
3. `distinct` (required for a useful answer) -- accept one of the documented attributes
   (`zone_id`, `map_id`, `user`, `scope`, `scope_id`); default to `zone_id`.
4. `duration` (optional) -- accept the Mist API duration grammar (`1d`, `2w`, `-1d`,
   etc.); default to the SDK default `1d`.
5. `limit` (optional) -- accept an integer 1-1000; default to the SDK default `100`.

Org ID is **not** prompted; the endpoint is site-scoped and the `mistapi.APISession`
already binds to an org via `MIST_HOST` and `MIST_API_TOKEN` from `.env`. The
`user`, `user_type`, `scope`, `scope_id`, `start`, and `end` query parameters are
exposed as keyword arguments on the method signature for programmatic callers but are
not prompted interactively, in order to respect the 5-Item Rule on the prompt block.

**Rationale**: The endpoint requires `site_id` and `zone_type` in the path; without
them no useful call can be made. A sensible `distinct` default (`zone_id`) lets the
operator see per-zone counts on the first run without learning the full attribute
catalogue. Defaulting `duration` to `1d` matches the SDK default and the documented
behavior. Loading `site_id` from `.env` follows the precedent set by adjacent
SiteExportUtils methods, which keeps `--test` non-interactive against a known site.

**Alternatives Considered**:

- Prompting for every query parameter -- rejected because it bloats the prompt block
  past the 5-Item Rule and overwhelms junior NOC engineers, the documented audience.
- Hard-coding `zone_type=zones` -- rejected because RSSI zones are a distinct,
  commonly-used product surface and forcing operators to edit code to access them
  violates the spec's read-only catalogue intent.
