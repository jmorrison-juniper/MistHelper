# Phase 0 Research: getOrgSecPolicy

**Feature**: 636-mist-get-org-sec-policy
**Date**: 2026-06-30
**Endpoint**: `GET /api/v1/orgs/{org_id}/secpolicies/{secpolicy_id}`
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_secpolicies_secpolicy_id.md`

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Use `mistapi.api.v1.orgs.secpolicies.getOrgSecPolicy(apisession, org_id,
secpolicy_id)`, invoked exactly once per menu execution, wrapped by the existing
project-wide retry/backoff decorator and rate-limit accounting.

**Rationale**: The enriched doc at
`documentation/api/orgs/GET_orgs_org_id_secpolicies_secpolicy_id.md` documents the SDK
call path as `mistapi.api.v1.orgs.security_policies.getOrgSecPolicy()` in its narrative
"mistapi SDK" section, but every existing MistHelper reference to this endpoint family
and the URL path itself use `secpolicies` (see `MistHelper.py` line 4761 neighborhood
for adjacent `listOrgServicePolicies` and related entries, and the OpenAPI path token
`/secpolicies/{secpolicy_id}`). The `mistapi` module tree mirrors the URL path
verbatim, so the correct import path is `mistapi.api.v1.orgs.secpolicies`. The
narrative doc appears to normalize the tag name ("Orgs Security Policies") into a
Python-style identifier; the URL path is authoritative and matches the tag underlying
the `listOrgSecPolicies` sibling used elsewhere in the codebase. Implementation must
import from `secpolicies`; if `AttributeError` fires at runtime, fall back to
`security_policies` and log a warning with the actual module used.

- Signature: `getOrgSecPolicy(mist_session: APISession, org_id: str, secpolicy_id: str)
  -> APIResponse`
- Response wrapper: `APIResponse.data` is a single dict (not a list) -- non-paginated.
- Non-paginated per doc "Pagination: Not paginated."
- HTTP method: GET; no request body.

**Alternatives Considered**:

1. Call the raw `requests` library directly with `Authorization: Token ...` header --
   rejected because it violates Constitution Technology Constraint (mistapi is the sole
   permitted interface to Mist Cloud) and duplicates retry / rate-limit logic already
   built into `mistapi.APISession`.
2. Bulk-fetch via `listOrgSecPolicies` and filter client-side to the desired
   `secpolicy_id` -- rejected because it wastes API calls for large orgs (30-100 KB
   payloads vs. ~5 KB per single policy) and does not satisfy the spec's requirement
   to exercise the specific `getOrgSecPolicy` operationId. A separate menu item for
   the list endpoint already exists / can be added via its own spec.

## Research Task 2: Primary Key Strategy

**Decision**: Register `getOrgSecPolicy` as `type: natural_pk` with `primary_key:
["id"]` and `indexes: ["org_id", "name", "site_id"]` in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. Register the child table `org_sec_policy_wlans` as
`type: composite_pk` with `primary_key: ["secpolicy_id", "ssid"]` because a single
policy may contain multiple WLAN blocks and `ssid` is the required, unique key inside
the `wlans[]` array per the OpenAPI schema.

**Rationale**: The response schema documents `id` as a stable server-issued UUID
("Unique ID of the object instance in the Mist Organization") that is `readOnly: true`
-- textbook natural primary key. Adjacent entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
(e.g. `listOrgServicePolicies`, `listOrgServices`, `listOrgSecIntelProfiles`) use the
same natural-pk pattern with `id` -- consistency with neighbors reduces surprise and
matches the existing DataExporter upsert path. The child WLAN array does not carry its
own server-issued `id`, but the `wlan` schema marks `ssid` as `required`, so the pair
`(parent secpolicy_id, ssid)` is a natural composite key that supports clean upserts
on repeated runs.

**Alternatives Considered**:

1. `composite_pk: ["id", "org_id"]` for the parent -- rejected because `id` is already
   globally unique per the schema (Mist UUIDs are v4 with negligible collision risk)
   and adding `org_id` to the PK bloats the index without gaining uniqueness.
2. `auto_increment_with_unique` for the child WLANs -- rejected because the natural
   `(secpolicy_id, ssid)` composite already provides stable upsert semantics and the
   auto-increment path is reserved for aggregated/summary payloads with no stable key.

## Research Task 3: Output Filename and SQLite Table

**Decision**:

- Parent CSV filename: `OrgSecPolicy_<org_id>_<secpolicy_id>.csv` under `data/`.
- Child CSV filename: `OrgSecPolicyWlans_<org_id>_<secpolicy_id>.csv` under `data/`.
- SQLite table names: `org_sec_policy` (parent) and `org_sec_policy_wlans` (child).
- Both tables live in the existing `data/mist_data.db` file created and managed by
  `DataExporter.write_with_format_selection()`. `api_function_name="getOrgSecPolicy"`
  is passed for the parent call; `api_function_name="getOrgSecPolicyWlans"` is passed
  for the child call so each maps to its own PK strategy entry.
- ArangoDB backend uses collections `org_sec_policy` and `org_sec_policy_wlans`; Redis
  cache keys follow the existing `<collection>:<primary_key>` convention.

**Rationale**: MistHelper's naming convention for CSVs (see `OrgGatewayTemplates.csv`,
`OrgClientSecurity*.csv` in existing exporters) is PascalCase, singular for
single-object gets. Including the org and secpolicy UUIDs in the filename lets a NOC
engineer keep multiple concurrent captures on disk without collisions. SQLite table
names follow the existing snake_case convention seen in neighboring entries. The
child-table pattern (parent + `_wlans` suffix) mirrors how other nested-array
endpoints are handled elsewhere in the monolith.

**Alternatives Considered**:

1. Flatten `wlans[]` into JSON-encoded string columns on the parent row -- rejected
   because it prevents SQL querying of individual WLAN attributes and breaks the
   CSV-friendliness principle (NOC engineers pipe CSVs into Excel).
2. Use `data/misthelper.db` -- rejected; the canonical SQLite file is
   `data/mist_data.db` per copilot-instructions.md.

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Assign menu number **195**, placed in the Interactive Safe / Templates
cluster adjacent to the existing template and policy exporters.

**Rationale**: The current menu range documented in `.github/copilot-instructions.md`
tops out at operation 194 (Clone device config to gateway template). Menu 195 is the
next free integer, outside every skip range (heavy/destructive skips are 14, 18,
63-65, 90-100, and 154-194). The endpoint is read-only, so P1 placement is
appropriate. The semantic neighbor is the existing template-export cluster (`class
OrgTemplateExporter` at line ~11052) plus the service-policy and sec-intel-profile
entries already registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` around line 4755-4780.

**Alternatives Considered**:

1. Insert into the safe org export range (1-59) -- rejected because those slots are
   fully allocated and re-numbering existing items breaks external automation that
   invokes `--menu N` directly.
2. Reserve a gap and use 200 -- rejected; sparse menu numbering breaks the "next free
   integer" convention seen in prior specs (500-mist-get-org-license-async-claim-status
   used 95 for the same reason). At task generation time, if 195 is contested by an
   in-flight feature branch, the next free integer is used.

## Research Task 5: Required User Prompts

**Decision**: Two prompts, both wrapped in `safe_input()`:

1. `org_id` -- prompt string `"Enter organization UUID (blank for MIST_ORG_ID from
   .env): "`, `context="org_sec_policy:org_id"`. If the user provides an empty string,
   fall back to `os.environ.get("MIST_ORG_ID")`; if that is also missing, log a
   warning and return early.
2. `secpolicy_id` -- prompt string `"Enter security policy UUID: "`,
   `context="org_sec_policy:secpolicy_id"`. No `.env` fallback -- there is no natural
   default for a specific policy ID, and prompting the user avoids surprising
   selection of the wrong policy.

Both inputs are stripped and validated against the standard Mist UUID shape
(`re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-
[0-9a-fA-F]{12}", value)`). On validation failure, log `WARNING` with the offending
field name (never the raw value if it might contain unexpected characters that would
break the log line) and return early.

**Rationale**: The `.env` fallback for `org_id` matches existing MistHelper behavior
in every org-scoped exporter; NOC engineers running against a single org daily
strongly prefer not to retype the UUID. The `secpolicy_id` has no natural default and
guessing risks pulling the wrong policy -- explicit prompting is safer. `safe_input()`
context labels give the SSH/container EOF handler enough breadcrumb information to log
which menu step aborted.

**Alternatives Considered**:

1. Accept both IDs as command-line flags (`--org-id`, `--secpolicy-id`) -- rejected as
   the primary path because the interactive menu is the documented UX for junior NOC
   engineers per the copilot-instructions.md "Target Audience" section. Command-line
   flag support already exists globally through `--menu N`; adding per-menu flag
   parsing is out of scope for a P1 read-only feature.
2. Prompt for a human-readable policy name and look it up via `listOrgSecPolicies` --
   rejected because it doubles the API call count, adds a failure mode when names are
   ambiguous or duplicated, and does not directly exercise the target operationId.
