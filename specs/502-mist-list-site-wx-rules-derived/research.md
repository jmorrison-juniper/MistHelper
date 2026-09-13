# Phase 0 Research: ListSiteWxRulesDerived

This document captures the up-front decisions required before Phase 1 design. Each
research task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK Function Signature and Behavior

**Decision**: Use `mistapi.api.v1.sites.wxrules.derived.listSiteWxRulesDerived(apisession,
site_id)` as the single SDK entry point. Returns a `mistapi.APIResponse` whose `.data`
attribute is a JSON array (list of `wxlan_rule` objects).

**Rationale**: The enriched per-endpoint doc at
`documentation/api/sites/GET_sites_site_id_wxrules_derived.md` documents:

- HTTP: `GET /api/v1/sites/{site_id}/wxrules/derived`
- Path parameter: `site_id` (string, required, UUID)
- Query parameters: none
- Request body: none
- Response: array of `wxlan_rule` objects (no pagination envelope)
- SDK call: `mistapi.api.v1.sites.wxrules.listSiteWxRulesDerived()`

The endpoint is non-paginated, so no `mistapi.get_all()` helper is required -- a single
SDK call returns the full result. The `mistapi` 0.59+ SDK wraps the HTTP call and returns
an `APIResponse` whose `.data` is the parsed JSON body (a Python `list[dict]`). The site
is scoped via the path parameter only -- no `org_id` query parameter is needed because
the SDK derives the org context from the API session and the API server resolves the
inherited org-level rules from the site's parent.

**Alternatives Considered**:

- *Call the raw HTTP endpoint via `requests`* -- rejected: the project constitution
  mandates `mistapi` SDK as the sole permitted interface to the Mist Cloud.
- *Use `listSiteWxRules()` (the non-derived sibling endpoint)* -- rejected: that endpoint
  returns only the rules defined directly at the site, not the effective derived set.
  The user need stated in the spec is to see what is *actually enforced* at the site,
  which requires the `/derived` variant.
- *Wrap the call in `mistapi.get_all()` for pagination* -- rejected: this endpoint is
  not paginated (the per-endpoint doc explicitly states "Not paginated"). Calling
  `get_all()` would add an unnecessary loop with no second-page round trip.

## Research Task 2: Primary Key Strategy

**Decision**: `composite_pk` with primary key `["id", "site_id"]` and supplemental
indexes on `["org_id", "template_id", "enabled"]`.

**Rationale**: Each returned `wxlan_rule` object carries an `id` field that is documented
as the "Unique ID of the object instance in the Mist Organization" (UUID, read-only),
which is a natural business key. However, because the endpoint is *derived*, a single
rule definition can appear under multiple sites when inherited from a shared org-level
WxLAN template -- the `id` is unique within the upstream catalog but a SQLite row must
also be partitioned by `site_id` so the user can run the menu against several sites and
have all results coexist in the same `site_wxrules_derived` table without colliding.
Therefore the composite `(id, site_id)` pair is the correct primary key for upsert
semantics. The `site_id` value is supplied at call time (it is the path parameter) and
is back-filled into every row by the flatten step. Indexes on `org_id` (to group across
sites in one org), `template_id` (to trace inheritance back to the WLAN template), and
`enabled` (to filter active vs disabled rules in dashboards) cover the most common
NOC-engineer query patterns.

**Alternatives Considered**:

- *`natural_pk` with `["id"]` alone* -- rejected: see above; multiple sites can return
  the same rule id when it comes from a shared org template, which would cause spurious
  upserts that overwrite a previous site's row.
- *`auto_increment_with_unique` with `misthelper_internal_id`* -- rejected: the endpoint
  exposes a stable natural id (`wxlan_rule.id`), so artificial keys are unnecessary and
  defeat clean re-run upserts.
- *Composite key including `modified_time`* -- rejected: that would prevent updates from
  upserting cleanly because each modification would create a new row.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- CSV filename: `data/site_wxrules_derived_<site_id>_<YYYYMMDD_HHMMSS>.csv`
- SQLite table name: `site_wxrules_derived`
- ArangoDB collection: `site_wxrules_derived` (vertex collection, joined to the existing
  `sites` collection via a `site_has_derived_wxrule` edge collection per the polyglot
  graph convention from spec 188)

**Rationale**: The pattern matches the convention used by sibling site-scoped read
exports (`site_wlans_<site>_<ts>.csv`, `site_devices_<site>_<ts>.csv`). Including
`site_id` in the CSV filename lets the engineer run the menu against multiple sites in
one session without overwriting prior output. The SQLite table name uses the operation's
human-readable noun phrase (`site_wxrules_derived`) -- it is plural for the collection,
singular conceptually for each row. The ArangoDB edge collection is named for the graph
relationship it represents (site -> rule) per spec 188.

**Alternatives Considered**:

- *Per-org filename instead of per-site* -- rejected: the endpoint is site-scoped, so a
  per-site filename gives the engineer one-to-one traceability from output back to the
  invocation context.
- *Single shared `wxrules` table for both derived and non-derived variants* -- rejected:
  the two endpoints have overlapping but distinct semantics (derived vs source-of-truth)
  and conflating them in one table would lose the "which is the enforced set?" signal.

## Research Task 4: Menu Category Placement and Next Available Number

**Decision**: Menu number **96**, in the Interactive Safe / site-export cluster (60-96).

**Rationale**: Per the menu category table in `.github/copilot-instructions.md`:

- 60-72: Site devices (existing)
- 73-79: Insights
- 80-91: Stats
- 92-96: Viewers / safe site exports

The endpoint is a read-only site-scoped export, so it belongs alongside the existing
viewer-class operations at the top of the Interactive Safe range. 96 is the next
available slot before the Resource Intensive block at 97-101. The new method will be
declared on the `SiteExportUtils` class, which already groups other site-scoped reads.

**Alternatives Considered**:

- *Place in 1-59 Safe Org Exports* -- rejected: that range is org-scoped reads; this
  endpoint requires a per-site path parameter and so logically belongs in the
  site-scoped cluster.
- *Place in 124-150 Interactive cluster* -- rejected: that range is for tools requiring
  multi-step prompts, diagnostics, or live device interaction. A single GET with one
  prompt does not warrant inclusion there.
- *Pick a high free number like 195+* -- rejected: the menu is grouped semantically;
  scattering reads to far-out numbers harms discoverability. The CHANGELOG entry will
  re-verify the next free integer at task time in case sibling spec branches 500-510
  beat this one to merge and 96 is taken.

## Research Task 5: Required User Prompts (.env vs Runtime)

**Decision**: Prompt the user for `site_id` at runtime via
`safe_input("Site UUID: ", context="site_wxrules_derived:site_id")`. Read
`MIST_HOST` and `MIST_API_TOKEN` from `.env` via the existing `mistapi.APISession`
bootstrap; do not prompt for them. Optionally accept `MIST_SITE_ID` from `.env` as a
default that pre-fills the prompt (the existing pattern for other site-scoped exports).

**Rationale**:

- Per Constitution Principle III, every interactive `input()` must be wrapped in
  `safe_input()` with an explicit `context=` string so SSH and container EOF return code
  0 cleanly.
- `site_id` is per-invocation and must be supplied by the engineer because it identifies
  which site to query. Forcing it into `.env` would break the multi-site workflow.
- `MIST_HOST` and `MIST_API_TOKEN` are bootstrap credentials managed by the existing
  `EnvironmentConfig` loader and the `mistapi.APISession` constructor. They are
  fungible per session, never per call.
- `MIST_SITE_ID` is an optional convenience default used by `--test` mode and by
  engineers who routinely query the same lab site. When set, the prompt presents it
  as the default (`"Site UUID [default: <env value>]: "`) and a bare Enter accepts it.
- No `org_id` prompt is needed -- the API derives org context from the session token.

**Alternatives Considered**:

- *Read `site_id` exclusively from `.env`* -- rejected: forces the engineer to edit the
  env file between sites, hostile to the interactive use case.
- *Use `getpass.getpass()` for the prompt* -- rejected: the site_id is not a secret;
  echoing it lets the engineer visually confirm the UUID they pasted.
- *Prompt for `org_id` as well* -- rejected: not used by this endpoint. Adding an
  unused prompt would violate the safety principle's "do not ask for what you do not
  use" corollary.
