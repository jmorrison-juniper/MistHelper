# Phase 0 Research: getOrgApiToken

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_apitokens_apitoken_id.md` (enriched
OpenAPI doc), plus direct inspection of the adjacent `listOrgApiTokens` usage
already in `MistHelper.py` at line 11934.

**Decision**:
Invoke the endpoint via the mistapi SDK at:

```python
mistapi.api.v1.orgs.apitokens.getOrgApiToken(apisession, org_id, apitoken_id)
```

The SDK returns a `mistapi.APIResponse` object whose `.data` attribute is the
parsed JSON body. The body is a single JSON object (not a list, not
paginated). Top-level keys per the schema:

- `id` (string UUID -- token unique id)
- `name` (string -- human label)
- `created_by` (string|null -- creator email, null if creator deleted)
- `created_time` (number -- epoch seconds, read-only)
- `key` (string -- truncated/obfuscated preview such as `1qkb...QQCL`; the
  real token is NOT returned by GET; still treated as sensitive)
- `last_used` (number|null -- epoch seconds of last successful auth)
- `org_id` (string UUID -- echoes path param, read-only)
- `privileges` (array of `privilege_org` objects: `role`, `scope`,
  optional `org_id`, `site_id`, `sitegroup_id`, `view` (deprecated), `views`)
- `src_ips` (array of CIDR / IP strings -- allowed source IPs, immutable
  after token creation)

Required path parameters: `org_id` (UUID string), `apitoken_id` (UUID string).
No query parameters. No request body.

**Rationale**:
The enriched per-endpoint doc lists the SDK as
`mistapi.api.v1.orgs.api_tokens.getOrgApiToken()` (note the underscore in
`api_tokens`), but the *existing* MistHelper.py at line 11934 already imports
the sibling list operation as
`mistapi.api.v1.orgs.apitokens.listOrgApiTokens` (no underscore). The mistapi
0.59 SDK generates module paths directly from the URL path segments, and the
URL token is `apitokens` (no underscore). The doc's underscore form is a
documentation cosmetic, not the importable module path. We follow the
verified, in-source convention.

Final verification at implementation time:

```powershell
python -c "from mistapi.api.v1.orgs import apitokens; print([n for n in dir(apitokens) if not n.startswith('_')])"
```

If `getOrgApiToken` is not present, switch the import to the alternate
underscore form and amend the plan.

**Alternatives Considered**:

1. *Direct `requests.get` against the URL with the bearer token from `.env`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method
   exists, and the SDK already wraps retry/backoff and adaptive delay.
2. *Use the underscore SDK path (`...orgs.api_tokens...`) as written in the
   doc.* Rejected -- the existing sibling call in `MistHelper.py`
   (line 11934) uses `apitokens` (no underscore). Mixing the two would break
   on the actual installed SDK.
3. *Reuse `listOrgApiTokens` and filter client-side.* Rejected -- pulls
   every token in the org, wastes API budget against the 5000/hr rate limit,
   leaks unrelated token metadata into MistHelper logs / output, and defeats
   the point of the single-token GET endpoint.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **`natural_pk`** strategy on the token `id` (UUID) for the main token
summary table. Privilege entries fan out into a second table with a composite
PK.

- `org_api_tokens` (existing table from menu 47 `listOrgApiTokens`):
  PK = `[id]`, indexes on `org_id` and `name`. The new menu item writes the
  same shape of row and upserts into the same table.
- `org_api_token_privileges` (new table, one row per (token, privilege scope
  tuple)): PK = `[token_id, scope, scope_target]` where `scope_target` is the
  inner UUID matching `scope` (`org_id` for `scope=org`, `site_id` for
  `scope=site`, `sitegroup_id` for `scope=sitegroup`, or the literal string
  `"orgsites"` for `scope=orgsites`). The composite key guarantees uniqueness
  across a token's full `privileges[]` array.

Two entries are added to `ENDPOINT_PRIMARY_KEY_STRATEGIES`: one keyed
`"getOrgApiToken"` (re-using the same shape as the existing
`"listOrgApiTokens"`), and one keyed `"getOrgApiTokenPrivileges"` (a
MistHelper-internal sub-table id, mirroring the
`"getOrgLicenseAsyncClaimStatusDetails"` precedent in spec 500).

**Rationale**:
The token `id` is documented as a stable UUID assigned by Mist at token
creation time and never changes for the lifetime of the token. That makes it
the canonical natural key. Reusing the same SQLite table as
`listOrgApiTokens` means a single-token GET correctly upserts an
already-known row rather than creating a parallel snapshot table -- the user
who runs menu 47 then menu 195 against one of the listed tokens sees one
consistent record.

The `privileges[]` array is a 1:N fan-out, and a single scope/target pair
cannot appear twice on the same token (Mist enforces uniqueness within the
array; `uniqueItems: true` in the OpenAPI schema). That makes
`(token_id, scope, scope_target)` a valid composite PK without any need for a
surrogate auto-increment.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- repeated runs would accumulate
   duplicate snapshots and defeat the upsert semantics the spec requires.
2. *Single combined table with privileges JSON-encoded in one column.*
   Rejected -- breaks SQL queryability and conflicts with the flatten-on-write
   convention used throughout MistHelper.
3. *Use `(org_id, id)` as a composite PK.* Rejected -- `id` is already
   globally unique across orgs (the Mist UUID guarantee), so adding `org_id`
   to the key adds bytes without adding uniqueness. We still index on
   `org_id` for query speed.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/OrgApiToken_<token_id_short>.csv`, where
  `token_id_short` is the first 8 hex characters of the `apitoken_id` UUID.
- CSV (privileges fan-out): `data/OrgApiTokenPrivileges_<token_id_short>.csv`,
  written only when `privileges[]` is non-empty (the API documents the
  minimum as 1, so this should always emit at least one row).
- SQLite tables: `org_api_tokens` (existing, from `listOrgApiTokens`) for the
  summary row, and `org_api_token_privileges` (new) for the fan-out.

The `api_function_name` passed to `DataExporter.write_with_format_selection()`
is:
- `"getOrgApiToken"` for the summary row (looks up the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES["getOrgApiToken"]` entry).
- `"getOrgApiTokenPrivileges"` for the privilege rows
  (MistHelper-internal sub-table key).

**Rationale**:
The summary filename matches the casing of the existing
`OrgApiTokens.csv` produced by menu 47 (`listOrgApiTokens` -- see line
11935 in `MistHelper.py`). Singular vs plural in the stem distinguishes a
single-token detail file from the all-tokens list. The
`_<token_id_short>` suffix makes the file unique per token without leaking the
full UUID into shell history or log scrollback. The same convention is used
by spec 500's `org_<id_short>_claim_status_summary.csv`.

Using two SQLite tables (one summary, one fan-out) keeps the schema query-
friendly: a NOC engineer can `SELECT * FROM org_api_tokens WHERE name=...`
without joining when they don't need the privilege detail.

**Alternatives Considered**:

1. *Single CSV with privileges JSON-encoded into one column.* Rejected --
   breaks downstream SQL queries and forces every reader to JSON-parse a
   string column.
2. *Append summary rows to `OrgApiTokens.csv` (the list-mode file).*
   Rejected -- a list-mode export is a snapshot of the entire org's tokens;
   appending a single-token detail row would silently corrupt that snapshot.
3. *Full UUID in the filename.* Rejected -- leaks the token UUID into shell
   history. Eight hex chars is enough to disambiguate locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 195** under category label
"Safe Org Read -- API Tokens". The dispatch entry is added immediately after
the existing destructive cluster terminator (entry `"194"`).

**Rationale**:
A grep of `MistHelper.py` for the dispatch dictionary literal returns every
integer between 1 and 194 already allocated (no internal gaps). The next free
integer is 195. The constitution and `.github/copilot-instructions.md`
describe the canonical menu ranges as 1-59 Safe Org Exports, 60-96
Interactive Safe, 97-101 + 153 Resource Intensive, 102-123 WebSocket,
124-152 Interactive, 154-194 Destructive. With every slot filled, the only
options are (a) renumber a future safe-range bucket (expensive and
disruptive), or (b) extend above 194.

Option (b) is chosen, but with the menu table label explicitly prefixed
`"Safe Org Read"` to make clear to a junior NOC engineer that 195 is *not* in
the destructive cluster -- it is a new safe-read overflow slot. The README
menu table will gain a new sub-header "Safe Org Read Overflow (195-)" so the
visual cue is consistent with the existing range conventions.

**Alternatives Considered**:

1. *Insert at the end of the destructive cluster (194-).* Rejected -- 194 is
   filled, and inserting *inside* the destructive cluster (e.g. taking back
   an unused integer) would visually mis-signal the risk level to a junior
   NOC engineer.
2. *Renumber: shift the destructive cluster up by one and insert at 154.*
   Rejected -- breaks every existing automation, CHANGELOG entry, and
   README screenshot that references menu integers 154-194 by number. The
   blast radius is far too large for a single new safe operation.
3. *Block the operation until a free slot opens.* Rejected -- the goal of
   the SpecKit endpoint cataloging effort is to make every Mist GET
   reachable from the menu; refusing to add new operations defeats the
   feature.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via
`safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID) [Enter to use MIST_ORG_ID]: "`,
   context: `"org_api_token_detail:org_id"`. Default: the value of
   `MIST_ORG_ID` in `.env` if present. Validated via the existing
   `is_valid_uuid()` helper before the API call; on failure, log `WARNING`
   and return early.
2. `apitoken_id` -- prompt: `"API Token ID (UUID): "`, context:
   `"org_api_token_detail:apitoken_id"`. Default: the value of
   `MIST_APITOKEN_ID` in `.env` if present (this is a new optional env var
   introduced by this feature for non-interactive `--test` sweeps).
   Validated via `is_valid_uuid()`; failure logs `WARNING` and returns
   early.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g. `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_APITOKEN_ID` -- new, optional default for prompt 2. Used by
  `python MistHelper.py --test` for non-interactive validation. Documented
  in `quickstart.md` and added to `.env.example` if that file exists.

**Rationale**:
The endpoint requires both UUIDs as path parameters. There is no query
parameter and no body. Two prompts is the minimum sufficient set; one would
require hardcoding the token id and break the menu's general utility, and
three would add cognitive load with no operational gain.

Adding a `MIST_APITOKEN_ID` default makes the menu safely reachable from the
default `--test` sweep without requiring a TTY -- otherwise the test would
hang on `safe_input()` waiting for human input.

**Alternatives Considered**:

1. *Single prompt asking for `<org_id>:<token_id>` colon-delimited.* Rejected
   -- error-prone, harder to validate, breaks the existing prompt-per-id
   convention used throughout the menu cluster.
2. *Three prompts: also ask whether to expand `privileges[]` into a separate
   CSV.* Rejected -- the `privileges[]` array is required by the schema
   (`minItems: 1`), so expansion is always useful. Auto-expanding is the
   simpler default.
3. *Pull `apitoken_id` from `listOrgApiTokens` interactively.* Rejected for
   the v1 menu item -- adds a second API call and conflicts with the menu's
   single-purpose design. A future enhancement (separate spec) can layer an
   interactive selector on top.
