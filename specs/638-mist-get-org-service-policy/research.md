# Phase 0 Research: getOrgServicePolicy

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_servicepolicies_servicepolicy_id.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at:
`mistapi.api.v1.orgs.servicepolicies.getOrgServicePolicy(apisession, org_id,
servicepolicy_id)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object (not a list,
not paginated), with the following top-level keys per the doc:

- `id` (string UUID -- unique object instance ID, `readOnly`)
- `org_id` (string UUID -- owning org, `readOnly`)
- `name` (string -- human-friendly policy name)
- `action` (string enum: `allow`, `deny`)
- `local_routing` (bool -- access within same VRF)
- `path_preference` (string -- optional WAN path steering)
- `services` (string[] -- unique service names bound to the policy)
- `tenants` (string[] -- unique tenant scopes)
- `created_time` (number epoch, `readOnly`)
- `modified_time` (number epoch, `readOnly`)
- `aamw` (object -- SRX-only Advanced Anti-Malware config)
- `antivirus` (object -- SRX-only AV config)
- `appqoe` (object -- SRX-only AppQoE config)
- `secintel` (object -- SRX-only Security Intelligence config)
- `ssl_proxy` (object -- SRX-only SSL proxy config)
- `idp` (object -- IDP config sub-record: `alert_only`, `enabled`,
  `idpprofile_id`, `profile`)
- `ewf` (object[] -- Enhanced Web Filtering rule array; each item:
  `{alert_only, block_message, enabled, profile}`)

Required path parameters: `org_id` (UUID), `servicepolicy_id` (UUID). No query
parameters. Not paginated.

**Rationale**:
The enriched per-endpoint doc lists the SDK module (line 256) as
`mistapi.api.v1.orgs.service_policies.getOrgServicePolicy()`, spelled with an
underscore. However, the spec.md and the OpenAPI URL both use the token
`servicepolicies` (no underscore), and the mistapi SDK organizes modules by URL
path, not by tag or by the doc's occasionally-normalized spelling. Adjacent
endpoints under the same URL (`GET /orgs/{org_id}/servicepolicies` and
`PUT /orgs/{org_id}/servicepolicies/{servicepolicy_id}`) follow the URL-based
`mistapi.api.v1.orgs.servicepolicies` module path. Final verification happens at
implementation time via
`python -c "from mistapi.api.v1.orgs import servicepolicies; help(servicepolicies)"`
inside the venv; if the SDK exposes only the underscore variant, the call is
updated to match without any other code change.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/servicepolicies/{servicepolicy_id}`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method
   exists.
2. *Use the underscore variant `service_policies` verbatim from the doc.*
   Deferred -- treated as an implementation-time fallback rather than the
   primary path, because the URL-based path is canonical for adjacent endpoints
   in this same family. Both forms are one-line fixes if the SDK differs.

## Research Task 2: Primary Key Strategy

**Decision**:
Use **natural_pk** on the parent table and **composite_pk** on the child rule
table:

- `org_service_policy`: PK = `['id']` (the API-provided UUID -- stable across
  calls, `readOnly`). Registration key: `getOrgServicePolicy` -- one entry in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
- `org_service_policy_ewf`: PK = `['org_id', 'servicepolicy_id', 'rule_index']`
  (the ewf array elements have no natural stable ID in the response schema;
  MistHelper synthesizes `rule_index` from the array position). Registration
  key: `getOrgServicePolicyEwfRules` -- a MistHelper-internal sub-table
  identifier (the Mist API has no operationId for it -- it is a flattened
  sub-array of the parent response).

`INSERT OR REPLACE` upserts each poll's view of the policy, and ewf rules are
overwritten per-policy on each poll because their array position defines the
identity.

**Rationale**:
The parent policy carries `id` (UUID) which is the canonical Mist-side stable
identifier. This maps directly onto MistHelper's `natural_pk` strategy exactly
as sibling endpoints like `getOrgSite` do. The nested `ewf` array has no
per-item UUID and no unique field combination guaranteed by the schema, so
`rule_index` (integer position within the array) is the only viable
disambiguator. Pairing `(org_id, servicepolicy_id, rule_index)` guarantees one
row per rule per policy per org and safely re-runs. Splitting parent and
children into two tables preserves SQL queryability instead of packing the ewf
array as a JSON blob column.

**Alternatives Considered**:

1. *`composite_pk` on `(org_id, id)`.* Rejected -- `id` alone is a UUID and
   already globally unique across orgs; adding `org_id` is redundant and would
   diverge from the pattern used by other natural-PK entities.
2. *Single combined table with all parent fields plus one nullable row per ewf
   entry.* Rejected -- forces nullable PK columns and inflates row count for
   the common query "what does this policy look like today?". The two-table
   design cleanly handles the "parent + zero-or-more children" case.
3. *`auto_increment_with_unique` on the parent.* Rejected -- would let repeated
   polls accumulate duplicate snapshots, defeating the upsert behavior the
   spec requires.
4. *Store the `ewf` array as a JSON-encoded column on the parent.* Rejected --
   breaks SQL queryability and conflicts with the flattening convention used
   throughout MistHelper.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (parent): `data/org_<org_id_short>_service_policy_<policy_id_short>.csv`
- CSV (ewf children):
  `data/org_<org_id_short>_service_policy_<policy_id_short>_ewf.csv`
- SQLite tables: `org_service_policy` (parent) and `org_service_policy_ewf`
  (child)
- `org_id_short` / `policy_id_short` are the first 8 hex characters of the
  respective UUIDs -- the convention used by adjacent detail exports in
  MistHelper for human-readable filenames without leaking full UUIDs into shell
  history.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"getOrgServicePolicy"` for the
parent write and `"getOrgServicePolicyEwfRules"` for the child write. The
DataExporter uses that string as the lookup key into
`ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
Matches the naming pattern used by other single-object detail exports in
MistHelper (e.g., `getOrgSite`, `getOrgLicensesSummary`) and matches the
parent+children pattern used by the reference plan 500. Two output files / two
SQLite tables keeps the schema clean and lets a user query the parent policy
without joining when they don't need the ewf rules.

**Alternatives Considered**:

1. *Single output file with JSON-encoded `ewf` column.* Rejected -- breaks SQL
   queryability.
2. *Full org UUID and full policy UUID in the filename.* Rejected -- leaks
   UUIDs into shell history / `ls` output unnecessarily. Short forms are
   enough to disambiguate locally.
3. *File named by policy `name` field.* Rejected -- policy names may contain
   spaces, slashes, or non-ASCII characters; UUIDs are safe filenames.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 94**, sitting inside the
Interactive Safe cluster (60-96). The category label is "Interactive Safe --
Org Service Policy Detail".

**Rationale**:
The `.github/copilot-instructions.md` menu-range map:

- 1-59 Safe Org Exports
- 60-96 Interactive Safe (Site devices 60-72, Insights 73-79, Stats 80-91,
  Viewers 92-96)
- 97-101 + 153 Resource Intensive
- 102-123 WebSocket
- 124-152 Interactive
- 154-194 Destructive

This endpoint is a read-only GET but requires the operator to supply a specific
`servicepolicy_id` -- inherently interactive input beyond what the safe-org
bulk-export cluster typically demands. Slot 94 lives inside the Viewers
sub-cluster (92-96), which is the ideal home for per-object detail retrievals.
94 is far from the destructive block (154-194) and immediately below the
Resource Intensive cluster (97+), matching this endpoint's risk profile
(read-only) and cost profile (single small JSON response). The number is
provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd for the
latest allocated menu integer and 94 is shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Slot inside 1-59 Safe Org Exports (e.g., near menu 4 which owns the
   listOrgServicePolicies sibling).* Rejected -- the 1-59 cluster is
   conventionally reserved for non-interactive bulk exports where the operator
   supplies only the org context. Requiring a specific `servicepolicy_id`
   makes this endpoint fit the Interactive Safe (Viewers) cluster better.
2. *Slot inside 97-101 Resource Intensive.* Rejected -- this endpoint is a
   single GET returning a small JSON object; no pagination, no long-running
   work. It does not belong in the resource-intensive block.
3. *Append after 194.* Rejected -- placing a read-only viewer above the
   destructive cluster visually mis-signals the risk level to a junior NOC
   engineer scrolling the menu.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via
`safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"org_service_policy:org_id"`. Default: the value of `MIST_ORG_ID` in
   `.env` if present (pressing Enter accepts the default). Validated via the
   existing `is_valid_uuid()` helper before the API call; on failure, log
   `WARNING` and return early.
2. `servicepolicy_id` -- prompt: `"Service Policy ID (UUID): "`, context:
   `"org_service_policy:servicepolicy_id"`. No `.env` default (policy IDs
   vary per lookup). Validated via `is_valid_uuid()` before the API call; on
   failure, log `WARNING` and return early. A helper hint printed above the
   prompt suggests running the sibling menu item (`listOrgServicePolicies`,
   Menu 4) first to discover valid IDs.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

**Rationale**:
The endpoint is scoped to a single org and a single policy; both path
parameters are required by the OpenAPI schema. Site and device IDs are not
involved. There are no query parameters that could optionally alter the
response, so no third prompt is needed. Keeping the prompt count to two
matches sibling per-object detail menu items and keeps the UX simple for a
junior NOC engineer.

**Alternatives Considered**:

1. *Auto-discover and iterate over all policies in the org (no
   `servicepolicy_id` prompt).* Rejected -- that behavior belongs to the
   list-all endpoint (`listOrgServicePolicies`, already Menu 4). This menu
   item's purpose is single-policy detail retrieval; auto-fanning-out would
   duplicate the list endpoint and confuse the user.
2. *Add a third prompt for an output filename override.* Rejected -- adds
   keystrokes without operational value. The deterministic filename scheme in
   Research Task 3 makes results easy to find under `data/`.
3. *Cache the last-used `servicepolicy_id` in a small state file to prefill
   the second prompt.* Rejected -- adds a new persistent state artifact
   outside `data/` and `.env`, out of scope for this feature.
