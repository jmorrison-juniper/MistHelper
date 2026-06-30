# Phase 0 Research: countOrgTunnelsStats

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each task
follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_stats_tunnels_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL: `mistapi.api.v1.orgs.stats.tunnels.count.countOrgTunnelsStats(apisession,
org_id, distinct=None, type=None, limit=100)`. The SDK returns a `mistapi.APIResponse`
object whose `.data` attribute is the parsed JSON body. The body is a single JSON
aggregation object with the following top-level keys per the enriched doc:

- `distinct` (string -- echoes the requested distinct attribute name)
- `start` (int epoch seconds)
- `end` (int epoch seconds)
- `limit` (int -- echoes the requested limit; default 100)
- `total` (int -- total distinct values matching the query)
- `results` (array of `count_result` objects; each row has a required `count` int plus
  exactly one additional string property whose key is the value of `distinct` and whose
  value is the discriminator value for that count -- e.g. `{"count": 42, "wxtunnel_id":
  "abc-123"}` or `{"count": 5, "mxedge_id": "..."}`)

Required path parameter: `org_id` (UUID string).
Optional query parameters:

- `distinct` (string). Enum depends on `type`:
  - If `type=wxtunnel`: one of `wxtunnel_id`, `ap`, `remote_ip`, `remote_port`, `state`,
    `mxedge_id`, `mxcluster_id`, `site_id`, `peer_mxedge_id`. Default: `wxtunnel_id`.
  - If `type=wan`: one of `mac`, `site_id`, `node`, `peer_ip`, `peer_host`, `ip`,
    `tunnel_name`, `protocol`, `auth_algo`, `encrypt_algo`, `ike_version`, `last_event`,
    `up`.
- `type` (string). The tunnel category whose stats are being counted (`wxtunnel` or
  `wan`).
- `limit` (int, default 100). Caps the number of rows in `results`.

**Rationale**:
The enriched doc lists the SDK as `mistapi.api.v1.orgs.stats_-_tunnels.countOrgTunnelsStats()`
(generator-encoded hyphen-space), but the mistapi SDK historically encodes
hyphen-tag-spaces as nested module paths derived from the URL, not the OpenAPI tag.
Spec.md explicitly names `mistapi.api.v1.orgs.stats.tunnels.count` and that path
matches the URL one-for-one (`/orgs/{org_id}/stats/tunnels/count`), so we follow the
spec. Final verification happens at implementation time via `python -c "from
mistapi.api.v1.orgs.stats.tunnels import count; help(count)"` inside the venv. The
SDK's standard call convention always takes `apisession` first followed by path
parameters then keyword query parameters, matching adjacent endpoints.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/stats/tunnels/count`.* Rejected -- the
   constitution forbids direct HTTP when a mistapi method exists.
2. *Use the path implied by the doc tag (`...orgs.stats_-_tunnels...`).* Rejected --
   the SDK organizes modules by URL path, not OpenAPI tag, and the spec.md (the
   authoritative feature contract) names the URL-based path.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on a single output table
`org_tunnels_stats_count`. Primary key columns: `(org_id, query_type, query_distinct,
distinct_value)`.

- `org_id` is supplied by MistHelper (the API does not echo it in the body).
- `query_type` is the value of the `type` query parameter (`wxtunnel` or `wan`), or
  the literal string `none` when the user did not supply a type filter.
- `query_distinct` is the value of the `distinct` query parameter as echoed in the
  response (`distinct` field).
- `distinct_value` is the string value of the row's discriminator key -- i.e. the
  single non-`count` property on each `count_result` object.

Other columns persisted from the response (`count`, `start`, `end`, `limit`, `total`,
plus a MistHelper-injected `collected_at` epoch) are non-PK payload columns.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk`.

**Rationale**:
The endpoint is an aggregation: each row in `results` represents a count of tunnels
grouped by a single attribute. The natural identity of one such row is the 4-tuple
`(which org, which tunnel type, which group-by attribute, which value of that
attribute)`. Re-running the menu item with the same parameters must update the
existing rows in place (counts change as tunnels come and go). `INSERT OR REPLACE`
on `(org_id, query_type, query_distinct, distinct_value)` delivers that upsert
behavior cleanly across SQLite and ArangoDB backends.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would let repeated polls accumulate
   duplicate snapshots, defeating the upsert behavior the spec requires.
2. *`natural_pk` on `distinct_value` alone.* Rejected -- `distinct_value` is not
   unique across orgs, tunnel types, or distinct attributes (the same `site_id`
   appears under both `wxtunnel` and `wan` rows).
3. *`composite_pk` on `(org_id, query_distinct, distinct_value)` without
   `query_type`.* Rejected -- the same `site_id` group-by under different `type`
   filters returns different counts; merging them under one PK would corrupt the data.
4. *Two separate tables per `type`.* Rejected -- doubles the schema surface for no
   query benefit; a `WHERE query_type = 'wan'` filter is cheaper than a multi-table
   union.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_tunnels_stats_count.csv`
- SQLite table: `org_tunnels_stats_count`
- `org_id_short` is the first 8 hex characters of the org UUID -- the convention used
  by adjacent org-stats exports in MistHelper for human-readable filenames without
  leaking full UUIDs into shell history.

The `api_function_name` argument passed to `DataExporter.write_with_format_selection()`
is `"countOrgTunnelsStats"` (matching the operationId). The DataExporter uses that
string as the lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by `searchOrgTunnelsStats` and
`searchOrgPeerPathsStats` (the two adjacent tunnel/peer-path exports). A single
output file with a `query_type` column is preferable to per-type files because the
user can filter or pivot in their downstream tool without juggling multiple CSVs.

**Alternatives Considered**:

1. *Per-distinct-attribute filenames (e.g. `..._tunnels_count_by_site_id.csv`).*
   Rejected -- creates an explosion of small files and makes diffing across runs
   harder.
2. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell history
   and `ls` output unnecessarily. The short form is enough to disambiguate locally.
3. *JSON-encoded `results` column in a single row.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention used everywhere else in
   MistHelper.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 91**, sitting inside the Stats cluster
(80-91 per `.github/copilot-instructions.md`) immediately after the existing org-stats
search/count operations for BGP, OSPF, peer paths, ports, and tunnels. The category
label is "Safe Org Exports -- Stats / Tunnels".

**Rationale**:
The `.github/copilot-instructions.md` menu range table places stats endpoints in
60-96 (Interactive Safe), with stats specifically clustered at 80-91. Operation 91 is
the next contiguous integer below the Viewer cluster at 92-96, and is far away from
the destructive block at 154-194. Tunnels stats fit naturally beside the existing
search-style stats exports.

The number is provisional: at `/speckit.tasks` time, `MistHelper.py` is grep'd for
the latest allocated menu integer. If 91 collides with an in-flight feature branch
or the existing test skip block (14, 18, 63-65, 90-100) intercepts automated tests,
the implementation either:

1. Shifts the number to 92 (the first Viewer slot, outside the skip range and
   semantically tolerable for a read-only count operation), or
2. Keeps 91 and exempts this operation from the automated `--test` sweep with an
   explicit comment in the test runner.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster ends at 194,
   and placing a read-only count check above the destructive block visually
   mis-signals the risk level to a junior NOC engineer scrolling the menu.
2. *Slot inside Safe Org Exports (1-59).* Rejected -- 1-59 is for one-shot exports
   like sites and inventory; tunnels-stats endpoints already live in the 80s.
3. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint is a single
   GET that returns a small aggregation object, with no pagination beyond `limit`
   and no long-running work. It belongs in the safe stats block.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly four** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"count_org_tunnels_stats:org_id"`. Default: the value of `MIST_ORG_ID` in `.env`
   if present (pressing Enter accepts the default). Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING` and return
   early.
2. `tunnel_type` -- prompt: `"Tunnel type (wxtunnel / wan, blank for both): "`,
   context: `"count_org_tunnels_stats:type"`. Default: blank (let the API decide). On
   non-blank input, validated against the enum `{"wxtunnel", "wan"}`; invalid -> log
   `WARNING`, prompt again once, then return early on a second failure.
3. `distinct` -- prompt: `"Distinct attribute (default wxtunnel_id for wxtunnel /
   mac for wan): "`, context: `"count_org_tunnels_stats:distinct"`. Default depends
   on `tunnel_type`. Validated against the type-specific enum lists from Research
   Task 1.
4. `limit` -- prompt: `"Row limit (default 100): "`, context:
   `"count_org_tunnels_stats:limit"`. Default: `100`. Coerced to `int`, clamped to
   `[1, 1000]`; non-integer input -> log `WARNING`, use default.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint's response shape depends on `distinct`, and `distinct`'s enum depends on
`type`. Asking the user for both, with sensible defaults pulled from the OpenAPI doc,
keeps the menu flow short while still exposing the full query power. `limit` is
optional with a friendly default; clamping to 1000 prevents accidental denial of
service against the user's own org. Org-scoped only -- no site or device prompts are
required by this endpoint.

**Alternatives Considered**:

1. *Hard-code `distinct=wxtunnel_id` and call only once.* Rejected -- removes the
   `wan` tunnel category from the menu's reach, which is the more common production
   case for SRX/SSR-based WAN edges.
2. *Loop over both `wxtunnel` and `wan` automatically in one menu run.* Rejected --
   doubles the API call count and clutters the output with rows that may not be
   relevant; explicit prompts give the user precise control.
3. *Add a fifth prompt for an output filename override.* Rejected -- adds keystrokes
   without operational value. The deterministic filename scheme in Research Task 3
   makes results easy to find under `data/`.
