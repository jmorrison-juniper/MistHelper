# Phase 0 Research: GetOrgSkyAtpIntegration

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and
implementation. Each task follows the Decision / Rationale / Alternatives
Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_setting_skyatp_setup.md` (enriched
per-endpoint OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK using the module path named in
spec.md: `mistapi.api.v1.orgs.setting.skyatp.setup.getOrgSkyAtpIntegration(
apisession, org_id)`. The SDK returns a `mistapi.APIResponse` object whose
`.data` attribute is the parsed JSON body. The body is a single JSON
object (not a list, not paginated) with three top-level keys per the
enriched doc:

- `secintel` (object)
  - `third_party_threat_feeds` (array of string; unique items) -- third-
    party threat-intelligence feed identifiers the org has enabled.
    Documented ip-based feeds: `block_list`, `threatfox_ip`,
    `feodo_tracker`, `dshield`, `tor`. Documented url-based feeds:
    `threatfox_url`, `urlhaus`, `open_phish`. Documented domain-based
    feeds: `threatfox_domains`. Juniper native secintel feeds
    (`infected_host`, `geo_ip`, `attacker_ip`, `command_and_control`) are
    enabled by license tier, not by this array.
- `secintel_allowlist_url` (string, read-only) -- signed S3 URL exposing
  the org allowlist; example
  `https://papi.s3.amazonaws.com/secintel_allowlist/xxx...`.
- `secintel_blocklist_url` (string, read-only) -- signed S3 URL exposing
  the org blocklist; example
  `https://papi.s3.amazonaws.com/secintel_blocklist/xxx...`.

Required path parameter: `org_id` (UUID string). No query parameters. No
request body.

**Rationale**:
The enriched per-endpoint doc lists the SDK path as
`mistapi.api.v1.orgs.integration_skyatp.getOrgSkyAtpIntegration()`, which
does not mirror the OpenAPI URL. spec.md lists
`mistapi.api.v1.orgs.setting.skyatp.setup`, which mirrors the URL
`/orgs/{org_id}/setting/skyatp/setup` exactly. The Mist mistapi SDK
historically generates module paths from the URL, not the tag; the spec
follows that convention. Final module-path verification happens at
implementation time via:

```powershell
python -c "from mistapi.api.v1.orgs.setting.skyatp import setup; help(setup)"
```

If the SDK version installed exposes the integration under
`mistapi.api.v1.orgs.integration_skyatp` instead, the implementation
imports both aliases in a try/except and picks whichever resolves -- this
is a known SDK-generation quirk and does not change any behavior visible
to MistHelper.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/setting/skyatp/setup`.* Rejected
   -- the Constitution forbids direct HTTP when a mistapi method exists.
2. *Follow only the enriched doc's SDK path
   (`mistapi.api.v1.orgs.integration_skyatp`) verbatim.* Rejected --
   spec.md is the authoritative feature contract and it names the URL-
   based path. The try/except fallback covers the doc's alternate path
   without requiring us to pick one blindly.

## Research Task 2: Primary Key Strategy

**Decision**:
Use two `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries corresponding to two
output tables:

- `org_sky_atp_integration`: strategy `natural_pk`, primary key
  `['org_id']`. One row per org because the API returns a singleton
  configuration per org.
- `org_sky_atp_threat_feeds`: strategy `composite_pk`, primary key
  `['org_id', 'feed_name']`. Zero-or-more rows per org, one per element of
  the `secintel.third_party_threat_feeds` array.

`org_id` is not returned in the body but MistHelper always knows which org
the call targeted, so it is injected before the upsert.

**Rationale**:
The endpoint returns a single configuration object per organization -- the
only stable identifier at the summary level is `org_id`. `natural_pk` on
`org_id` gives `INSERT OR REPLACE` upsert semantics so repeated polls of
the same org do not create duplicate summary rows. The nested
`third_party_threat_feeds` array is a set of strings (unique per the
schema), so `(org_id, feed_name)` is the natural composite key and lets
SQL queries answer "which orgs have `tor` enabled?" without a
JSON-decoding pass.

**Alternatives Considered**:

1. *Single table with JSON-encoded feeds column.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention used
   everywhere else in MistHelper.
2. *`auto_increment_with_unique` on both tables.* Rejected -- lets
   repeated polls accumulate duplicate snapshots, defeating the upsert
   behavior the spec (FR-005 + Acceptance Scenario 3) requires.
3. *`composite_pk` of `(org_id, polled_at_utc)` on the summary.* Rejected
   -- creates a new row on every poll instead of upserting. Configuration
   state does not need per-poll history in MistHelper's local store; if
   history becomes a requirement it lives in a separate audit table.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_sky_atp_integration.csv`
- CSV (feeds): `data/org_<org_id_short>_sky_atp_threat_feeds.csv`
- SQLite tables: `org_sky_atp_integration` and `org_sky_atp_threat_feeds`
- `org_id_short` is the first 8 hex characters of the org UUID -- the
  convention used by adjacent org-scoped exports so that filenames are
  human-readable and full UUIDs never leak into shell history / `ls`
  output.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is
`"getOrgSkyAtpIntegration"` for the summary call and
`"getOrgSkyAtpIntegrationThreatFeeds"` (MistHelper-internal sub-table
identifier) for the feeds call. `DataExporter` uses that string as the
lookup key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Naming follows the pattern used by other `getOrgSetting*` and
`getOrg*Integration` exports (settings, aamwprofiles, idpprofiles). Two
output files / two SQLite tables keep the schema flat and let a user
query the top-level integration state without joining when the feed list
is not needed.

**Alternatives Considered**:

1. *Full org UUID in the filename.* Rejected -- leaks the org UUID into
   shell history unnecessarily; the short form is enough to disambiguate
   locally.
2. *Single output file with `feeds` column holding a comma-separated
   string.* Rejected -- breaks the SQL / ArangoDB queryability
   requirement and forces string-parsing on every downstream query.
3. *Include the two signed URLs as separate output files.* Rejected --
   the signed URLs are attributes of the summary row and belong in the
   same table; splitting them into their own files provides no analytical
   value.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 96**, sitting in the Safe Org
Exports / Interactive Safe cluster (the 60-96 band described in
`.github/copilot-instructions.md`), immediately before the Resource-
Intensive block that starts at 97. The category label is
"Safe Org Exports -- Security Integrations".

**Rationale**:
The Constitution and `.github/copilot-instructions.md` document the menu
ranges as: 1-59 Safe Org Exports (Config/Admin at 42-50, Misc at 56-59),
60-96 Interactive Safe, 97-101 + 153 Resource Intensive, 102-123
WebSocket, 124-152 Interactive, 154-194 Destructive. A read-only settings
retrieval that requires one user prompt (org_id) is a natural fit for the
Interactive Safe band. Slot 96 is the last integer before the resource-
intensive block and is far from the destructive block, matching the
safety signal a junior NOC engineer expects when scrolling. The number is
provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd for the
latest allocated menu integer and 96 is shifted forward if a conflict
exists with another in-flight feature branch.

**Alternatives Considered**:

1. *Append to the end (e.g., 195).* Rejected -- the destructive cluster
   ends at 194; placing a read-only settings retrieval above the
   destructive block visually mis-signals the risk level.
2. *Slot inside Resource Intensive (97-101).* Rejected -- this endpoint
   is a single non-paginated GET returning a small JSON object; there is
   no long-running work and no bulk retrieval.
3. *Slot inside 42-50 Config/Admin.* Rejected -- that band houses
   configuration operations for the running MistHelper instance itself
   (backend selection, credential rotation), not remote Mist config
   retrieval. The 60-96 Interactive Safe band is the correct home.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly one** value via
`safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_sky_atp_integration:org_id"`. Default: the value of
   `MIST_ORG_ID` in `.env` if present (pressing Enter accepts the
   default). Validated via the existing `is_valid_uuid()` helper before
   the API call; on failure, log `WARNING` and return early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap,
never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for the prompt.

No site ID, device ID, or template ID is required -- the endpoint is
strictly org-scoped. No query parameters exist on this endpoint, so no
additional Boolean or filter prompts are needed.

**Rationale**:
Mist's Sky ATP setup endpoint is org-scoped only. The path parameter
`org_id` is the sole required input. Adding a second prompt would violate
the "minimum keystrokes" ergonomic bar that adjacent read-only menu items
already meet. Keeping the prompt count to one also keeps the
non-interactive smoke test (`echo "" | python MistHelper.py --menu 96`)
trivial: press Enter, accept the `.env` default, done.

**Alternatives Considered**:

1. *Add a "confirm before write" prompt.* Rejected -- the endpoint is
   read-only; there is no destructive side effect requiring a
   confirmation gate (Constitution Principle III).
2. *Add an "output filename override" prompt.* Rejected -- adds
   keystrokes without operational value; the deterministic filename
   scheme from Research Task 3 makes results easy to find under `data/`.
3. *Skip the prompt entirely and read `org_id` only from `.env`.*
   Rejected -- SSH / container operators frequently need to target an
   org other than the default; an interactive prompt with a default is
   the correct balance.
