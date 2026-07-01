# Phase 0 Research: getOrgOauthAppLinkedStatus

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_setting_app_name_link_accounts.md`
(enriched OpenAPI per-endpoint doc).

**Decision**:
Invoke the endpoint through the mistapi SDK at the URL-derived module path:
`mistapi.api.v1.orgs.setting.link_accounts.getOrgOauthAppLinkedStatus(apisession,
org_id, app_name, forward)`. The SDK returns a `mistapi.APIResponse` whose `.data`
attribute is the parsed JSON body. The body is a single JSON object (not a list, not
paginated) with the top-level keys per the doc:

- `linked` (bool, required) -- whether the OAuth app is currently linked at the org.
- `authorization_url` (string, read-only) -- redirect URL the user hits to complete
  or renew OAuth linking; contains a nonce -- treat as sensitive, do not log.
- `accounts` (array, required) -- zero-or-more `account_oauth_info_account` objects
  describing each linked customer account. Fields per account: `account_id`,
  `auto_probe_subnet`, `client_id`, `cloud_name`, `company`, `enable_probe`, `error`,
  `errors[]`, `instance_url`, `key_id`, `last_status`, `last_sync`, `linked_by`,
  `linked_timestamp`, `max_daily_api_requests`, `name`, `password`, `region`,
  `regions{}`, `service_account_name`, `service_connections{}`, `smartgroup_name`,
  `tsg_id`, `username`, `webhook_auth_type`, `webhook_enabled`, `webhook_password`,
  `webhook_secret`, `webhook_token`, `webhook_url`, `webhook_username`, `zdx_org_id`.

Required path parameters: `org_id` (UUID string), `app_name` (string -- integration
identifier such as `jamf`, `crowdstrike`, `zoom`, `zscaler`, `prisma`, `zdx`,
`sentinelone`, `vmware`).
Required query parameter: `forward` (string -- an `https://` URL the Mist backend
redirects to after OAuth authorization, required to obtain a non-empty
`authorization_url`).

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.orgs.linked_applications.getOrgOauthAppLinkedStatus()`, but the
mistapi SDK is generated from the OpenAPI URL path, not from the tag. The URL
`/api/v1/orgs/{org_id}/setting/{app_name}/link_accounts` maps to the module
`mistapi.api.v1.orgs.setting.link_accounts`. Adjacent endpoints under the same URL
prefix (`GET /api/v1/orgs/{org_id}/setting` -> `mistapi.api.v1.orgs.setting`) confirm
the URL-based path is canonical. The spec.md also names
`mistapi.api.v1.orgs.setting.link_accounts`, which we treat as the authoritative
contract. Final verification is a one-liner at implementation time:
`python -c "from mistapi.api.v1.orgs.setting import link_accounts; help(link_accounts)"`
inside the venv.

**Alternatives Considered**:

1. *Direct `requests.get` against the raw URL.* Rejected -- the constitution forbids
   direct HTTP when a mistapi method exists.
2. *Use the tag-implied module path (`...orgs.linked_applications...`).* Rejected --
   the SDK is generated from URL paths; the tag is documentation metadata.
3. *Omit the `forward` parameter to save a prompt.* Rejected -- the enriched doc
   marks `forward` as **required** and warns the `authorization_url` field will be
   absent otherwise. MistHelper must supply it every call.

## Research Task 2: Primary Key Strategy

**Decision**:
Use **composite primary keys** on two separate output tables:

- `org_oauth_app_link_summary`: PK = `(org_id, app_name)` -- one row per (org,
  integration) pairing that captures the top-level `linked` flag and the
  authorization state.
- `org_oauth_app_link_accounts`: PK = `(org_id, app_name, account_id)` -- one row per
  linked customer account under a given (org, integration). `account_id` is
  guaranteed present per the response schema (`"Linked app account id"`).

Register both in `ENDPOINT_PRIMARY_KEY_STRATEGIES` with type `composite_pk`. Both
`org_id` and `app_name` are supplied by MistHelper before the upsert (they are
prompted inputs, not returned in the body). `account_id` comes from each element of
the API `accounts` array.

**Rationale**:
The endpoint reports the *current* linking state. Re-running the menu against the
same (org, app) must **update** the existing rows rather than append duplicates.
`account_id` is the schema-declared unique identifier per linked account and is
stable across polls. Splitting into a summary table and an accounts table cleanly
handles the empty-accounts case (integration linked but zero accounts subscribed)
and avoids nullable PK columns. `INSERT OR REPLACE` upserts every poll's snapshot.

**Alternatives Considered**:

1. *`auto_increment_with_unique` with a synthetic PK.* Rejected -- would let
   repeated polls accumulate duplicate snapshots, defeating the upsert behavior the
   spec requires.
2. *Single combined wide table with one row per account plus repeated summary
   fields.* Rejected -- when `accounts` is empty (integration linked but no
   accounts) there is no row to write, so the summary is lost. Two tables preserve
   the summary regardless of account count.
3. *`natural_pk` on `account_id` alone.* Rejected -- `account_id` values are unique
   per integration but MistHelper may target multiple integrations, so `app_name` is
   part of the natural key. `org_id` disambiguates across MistHelper orgs.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_<app_name>_oauth_link_summary.csv`
- CSV (accounts): `data/org_<org_id_short>_<app_name>_oauth_link_accounts.csv`
- SQLite tables: `org_oauth_app_link_summary` and `org_oauth_app_link_accounts`
- `org_id_short` is the first 8 hex characters of the org UUID (existing MistHelper
  filename convention).
- `app_name` is inserted verbatim after lowercasing and stripping non-ASCII
  characters, to prevent path-injection weirdness.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgOauthAppLinkedStatus"` for
the summary and `"getOrgOauthAppLinkedStatusAccounts"` for the accounts rows -- the
DataExporter uses those strings as lookup keys into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming convention of adjacent org-settings exports (`getOrgSetting`,
`getOrgSettingJseSetup`, etc.). Two output files / two SQLite tables keeps the schema
queryable and lets a user check `linked=true` without joining when they only need
the summary. Including `app_name` in the filename avoids collision when the operator
polls multiple integrations for the same org.

**Alternatives Considered**:

1. *Single JSON blob file per (org, app) pairing.* Rejected -- breaks SQL
   queryability and conflicts with the flattening convention used everywhere else
   in MistHelper.
2. *Full org UUID in the filename.* Rejected -- leaks the UUID into shell history
   and `ls` output unnecessarily. The short form disambiguates locally.
3. *Store `authorization_url` in the CSV.* Rejected -- the URL contains a redirect
   nonce that can be replayed within its TTL. The value is written to SQLite (under
   controlled file permissions) but omitted from CSV to avoid accidental sharing.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 58**, sitting inside the Safe Org
Exports cluster (1-59) adjacent to the existing `getOrgSetting` and related
org-settings exports. Category label: "Safe Org Exports -- Org Settings".

**Rationale**:
The `.github/copilot-instructions.md` menu-range map: 1-59 Safe Org Exports, 60-96
Interactive Safe, 97-101 + 153 Resource Intensive, 102-123 WebSocket, 124-152
Interactive, 154-194 Destructive. Org-settings exports historically live inside the
Safe Org Exports prefix; 58 is a plausible unallocated slot near the top of that
range (the exact grep for the next free integer happens at `/speckit.tasks` time --
if 58 collides with an in-flight branch, the next contiguous free integer in the
same cluster is used). The number is far removed from the destructive block, which
correctly signals to a junior NOC engineer that this operation is safe.

**Alternatives Considered**:

1. *Append at the end (e.g., 195).* Rejected -- destructive cluster ends at 194 and
   placing a read-only OAuth check above the destructive block visually mis-signals
   the risk level.
2. *Slot inside Interactive Safe (60-96).* Rejected -- this endpoint requires
   moderate user prompting (three inputs) but returns a bounded JSON object with no
   long-running work; it belongs in Safe Org Exports next to peer settings
   endpoints, not among the interactive-workflow menu items.
3. *Slot inside Resource Intensive (96-101).* Rejected -- single non-paginated GET
   returning a small JSON object. Not resource intensive.

## Research Task 5: Required user prompts

**Decision**:
The new method asks the user for **exactly three** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_oauth_link_status:org_id"`. Default: value of `MIST_ORG_ID` in `.env` if
   present (Enter accepts). Validated by the existing `is_valid_uuid()` helper; on
   failure, log `WARNING` and return early.
2. `app_name` -- prompt: `"App name (jamf, crowdstrike, zoom, zscaler, prisma, zdx,
   sentinelone, vmware, ...): "`, context: `"org_oauth_link_status:app_name"`.
   Default: value of `MIST_OAUTH_APP_NAME` in `.env` if present. Normalized to
   lowercase, validated against a compiled regex `^[a-z0-9_-]{2,32}$`; on failure,
   log `WARNING` and return early.
3. `forward_url` -- prompt: `"Forward URL (https:// where Mist should redirect after
   OAuth): "`, context: `"org_oauth_link_status:forward"`. Default: value of
   `MIST_OAUTH_FORWARD_URL` in `.env` if present, otherwise
   `https://manage.mist.com/admin/`. Validated with `urllib.parse.urlparse` to
   ensure `scheme == "https"` and a non-empty `netloc`; on failure, log `WARNING`
   and return early.

`.env` values used (loaded via existing `python-dotenv` bootstrap, never logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_OAUTH_APP_NAME` -- optional default for prompt 2.
- `MIST_OAUTH_FORWARD_URL` -- optional default for prompt 3.

**Rationale**:
The endpoint is org-scoped with two required path parameters and one required query
parameter -- all three are user-visible operational choices. Prompting for them
avoids hard-coding integration names and makes the same menu item work for every
supported OAuth integration. `.env` defaults let automation run non-interactively
(`python MistHelper.py --menu 58 < NUL` accepts every default).

**Alternatives Considered**:

1. *Hard-code `forward` to a fixed sentinel URL.* Rejected -- Mist rejects
   non-whitelisted redirect URLs and different Mist clouds
   (`api.mist.com`, `api.eu.mist.com`, `api.gc1.mist.com`) require different
   forward hosts. Prompting keeps the menu cloud-agnostic.
2. *Auto-enumerate `app_name` values by calling the parent `getOrgSetting`
   endpoint first.* Rejected -- doubles the API budget for every invocation and
   introduces a discovery step that is out of scope for a single-endpoint feature.
   The prompt list in the prompt text names the common integrations; the operator
   can enter any string the org supports.
3. *Add a fourth prompt for CSV/SQLite backend selection.* Rejected -- backend
   selection is a global MistHelper concern configured elsewhere; per-menu-item
   overrides violate the "single source of truth for output backend" convention.
