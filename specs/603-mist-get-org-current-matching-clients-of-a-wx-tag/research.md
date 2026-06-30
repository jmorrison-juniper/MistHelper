# Phase 0 Research: GetOrgCurrentMatchingClientsOfAWxTag

**Branch**: `603-mist-get-org-current-matching-clients-of-a-wx-tag`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Enriched endpoint doc**: `documentation/api/orgs/GET_orgs_org_id_wxtags_wxtag_id_clients.md`

This file resolves the open design questions raised in the plan's Technical Context so
that Phase 1 (data model, quickstart, contract) can proceed against concrete decisions.

---

## Research Task 1: SDK function signature & behavior

**Decision**: Invoke
`mistapi.api.v1.orgs.wxtags.getOrgCurrentMatchingClientsOfAWxTag(apisession, org_id, wxtag_id)`
exactly once per menu invocation. The function takes three positional arguments -- the
authenticated `mistapi.APISession` and the two path UUIDs -- and returns a
`mistapi.APIResponse` whose `.data` attribute is a JSON array. Each array element is an
object with two required fields, `mac` (string, MAC address without separators, e.g.
`"5684dae9ac8b"`) and `since` (number, epoch seconds, e.g. `1428939600`). The endpoint
is **not paginated** per the enriched doc, so no `mistapi.helper.next_page` / `get_all`
loop is required; one call yields the full result set.

**Rationale**: The enriched per-endpoint doc
(`documentation/api/orgs/GET_orgs_org_id_wxtags_wxtag_id_clients.md`) lists the SDK
binding under `mistapi.api.v1.orgs.wxtags.getOrgCurrentMatchingClientsOfAWxTag()`, the
two required path parameters (`org_id`, `wxtag_id`), no query parameters, no request
body, and a flat array response. The doc explicitly states "Not paginated." The
positional-argument convention matches the rest of `mistapi.api.v1.orgs.wxtags.*`
(verified against the adjacent `getOrgWxTag` / `listOrgWxTags` bindings cited in the
"Related Endpoints" section of the same doc).

**Alternatives Considered**:

- *Driving the call through `mistapi.helper.get_all`*: rejected because the endpoint is
  not paginated; the helper would add an unnecessary loop and confuse future readers
  about whether pagination is expected.
- *Calling the raw HTTP path through `apisession.mist_get(url)`*: rejected because the
  project constitution mandates the `mistapi` SDK as the sole permitted interface to
  Mist Cloud. Direct HTTP calls would bypass the SDK's auth, retry, and rate-limit
  hooks.
- *Batching multiple `wxtag_id` lookups inside one menu invocation*: rejected as scope
  creep -- the spec asks for one operation that retrieves clients for one tag. A
  future bulk variant can be added as a separate spec if demand emerges.

---

## Research Task 2: Primary Key Strategy

**Decision**: Use **`composite_pk`** with the key tuple
`(org_id, wxtag_id, mac)`. The endpoint does not return a stable per-row identifier,
but the triple is guaranteed unique per the WxTag semantics (a given MAC matches a
given tag in a given org at most once at any point in time -- the `since` value is the
time the current match started, not an identity column).

**Rationale**: The Mist response payload defines exactly two fields, `mac` and `since`,
and only `mac` is a stable identity within the scope of the tag. `since` updates each
time the client re-matches the tag, so it cannot be part of the key. The parent
`org_id` and `wxtag_id` are not in the response body itself -- they come from the URL
-- so MistHelper must annotate each row with those two fields on flatten so the
SQLite primary key constraint can be enforced. A composite PK gives clean
`INSERT OR REPLACE` upserts on repeated runs while preserving cross-tag and cross-org
disambiguation in a shared table. The `since` column then carries the most recent
match timestamp returned by the API.

**Alternatives Considered**:

- *`natural_pk` on `mac` alone*: rejected because the same MAC may match multiple
  WxTags or appear in multiple orgs accessible to the same MistHelper user; a single-
  column PK would collide on the second row.
- *`auto_increment_with_unique` on the composite triple*: rejected because the natural
  triple is itself stable -- introducing a synthetic `misthelper_internal_id` would
  add an index for no semantic gain and would prevent direct upserts.
- *Hashing the row to a synthetic UUID*: rejected as obfuscation; the natural triple is
  readable and joinable.

---

## Research Task 3: Output filename and SQLite table

**Decision**:

- **CSV filename**: `data/org_<org_id>_wxtag_<wxtag_id>_matching_clients.csv`
- **SQLite table**: `org_wxtag_matching_clients`
- **ArangoDB collection (when enabled)**: `org_wxtag_matching_clients`
- **Redis key prefix (when enabled)**: `wxtag:clients:<org_id>:<wxtag_id>`

`DataExporter.write_with_format_selection(rows, "org_wxtag_matching_clients", api_function_name="getOrgCurrentMatchingClientsOfAWxTag")`
selects the backend at runtime. The org and tag UUIDs are appended to the CSV filename
so per-tag exports do not clobber each other; the SQLite table is single, with the
composite PK enforcing per-tag separation.

**Rationale**: The naming pattern mirrors existing org-scoped exports in MistHelper
(`org_<id>_*.csv` / shared SQLite table). The CSV filename embeds both UUIDs because a
NOC engineer commonly exports several tags in one session and must be able to
distinguish the resulting files on disk without opening them. The SQLite table is
shared across runs because the composite PK guarantees no collision and analysts
benefit from one queryable table that spans all tags they have ever exported.

**Alternatives Considered**:

- *Per-tag SQLite tables (e.g. `wxtag_<id>_matching_clients`)*: rejected -- generates
  schema sprawl and breaks cross-tag queries; the composite PK already solves
  isolation.
- *Storing the response as raw JSON blob in one column*: rejected -- defeats the
  purpose of normalization and breaks the "junior NOC engineer can SELECT this in
  DBeaver" usability target.

---

## Research Task 4: Menu category placement and next available menu number

**Decision**: Place the new operation at **menu number 59** in the **Safe Org Exports
(1-59)** category, immediately adjacent to other org-scoped read-only WxTag /
infrastructure exports. The full menu inventory will be re-verified by
`/speckit.tasks` against `MistHelper.py` head-of-main at task time; if 59 has been
taken by another in-flight feature branch by then, the next free integer in the same
cluster (60-72 range is also a valid fallback under Interactive Safe -> Site devices,
since the operation is interactive in the sense that it prompts for two UUIDs) is used
and `plan.md` updated to match.

**Rationale**: The `.github/copilot-instructions.md` menu map (cited verbatim:
"1-59 Safe Org Exports") allocates the first sixty operations to non-destructive
org-scope reads. The endpoint is GET-only, requires only org/tag UUIDs, and produces a
small JSON array -- exactly the profile of the Safe Org Exports cluster. WxTag is an
org-scoped resource (`/api/v1/orgs/{org_id}/wxtags/...`), reinforcing the cluster
choice over the site-scoped band (60-72).

**Alternatives Considered**:

- *Place in 60-72 Interactive Safe (site devices)*: rejected because the resource is
  org-scoped, not site-scoped, and the operation requires no site_id.
- *Place in 73-79 Insights*: rejected because the endpoint returns raw match data, not
  derived analytics.
- *Reserve 59 for a future high-priority slot and pick the first free slot >= 56*:
  rejected because the spec asks for *the next available slot*, not slot reservation.
  If a higher-priority feature lands before this one merges, the task step picks the
  next free integer.

---

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: Prompt the user for exactly two values, both via `safe_input()`:

1. **`org_id`** -- prompted first; if `.env` defines `MIST_ORG_ID` and the user accepts
   the default (presses Enter), use the env value. Otherwise validate the input
   against the Mist UUID shape (`^[0-9a-fA-F-]{36}$`) and abort with a logged warning
   on validation failure.
2. **`wxtag_id`** -- prompted second; no `.env` default (tag UUIDs are per-tag, not
   per-environment). Validate against the same UUID shape. On empty input, abort with
   a logged warning -- there is no sensible global default.

The Mist API token (`MIST_API_TOKEN`) and host (`MIST_HOST`) are *not* prompted -- they
are loaded from `.env` by the existing `mistapi.APISession` bootstrap. The
`safe_input()` `context=` argument is set to a stable per-prompt string
(`"org_wxtag_clients:org_id"`, `"org_wxtag_clients:wxtag_id"`) so log scraping can
attribute SSH-EOF exits to the correct prompt.

**Rationale**: The constitution Safety-First principle requires `safe_input()` on
every interactive prompt. The two UUIDs are the only required path parameters per the
endpoint contract; no query parameters exist. `MIST_ORG_ID` is already the
project-wide convention for "the org I work in most often" and is honored by most
existing org-scoped menu items, so reusing it here matches user expectations. WxTag
UUIDs vary far more frequently and have no precedent in `.env`, so no env default is
offered.

**Alternatives Considered**:

- *Prompt only once for a `org_id/wxtag_id` slash-separated pair*: rejected as
  non-discoverable; the two-prompt pattern matches every other multi-UUID menu item
  in MistHelper.
- *Auto-list available WxTags first (chained call to `listOrgWxTags`)*: rejected as
  scope creep for the first iteration. A future enhancement can add an `--interactive`
  flag that pre-fetches tags and offers a selection menu; the current spec is
  intentionally minimal.
- *Accept the `wxtag_id` on the command line via `--wxtag-id` argparse*: deferred --
  out of scope for this spec; the existing test harness uses `--menu N` plus stdin
  feeds, which the two `safe_input()` prompts handle correctly.

---

## Open Questions

None. All five research tasks resolved without `NEEDS CLARIFICATION` markers, per the
plan's constitutional requirement. Phase 1 artifacts proceed against the decisions
above.
