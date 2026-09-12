# Phase 0 Research: getOrgMarvisClientInvite

**Feature**: 613-mist-get-org-marvis-client-invite
**Date**: 2026-06-30
**Source docs**: `documentation/api/orgs/GET_orgs_org_id_marvisinvites_marvisinvite_id.md`

## Research Task 1: SDK Function Signature & Behavior

**Decision**: Invoke the endpoint through
`mistapi.api.v1.orgs.marvis_invites.getOrgMarvisClientInvite(apisession, org_id, marvisinvite_id)`.
The SDK returns a `mistapi.APIResponse` whose `.data` attribute is a single
JSON object (dict) -- not a list. The response shape is:

```text
{
  "id":            str (UUID, readOnly),
  "name":          str,
  "disabled":      bool (default false),
  "provision_url": str (readOnly, used by MDM install command)
}
```

The endpoint is **non-paginated**. There is **no request body**. Path is
`GET /api/v1/orgs/{org_id}/marvisinvites/{marvisinvite_id}` -- both path
parameters are required. Authentication is the standard
`Authorization: Token <api_token>` header that `mistapi.APISession` injects
automatically.

**Rationale**: The enriched per-endpoint markdown
(`documentation/api/orgs/GET_orgs_org_id_marvisinvites_marvisinvite_id.md`)
documents the SDK module path as
`mistapi.api.v1.orgs.marvis_invites.getOrgMarvisClientInvite()` and lists both
path parameters as required. Constitution Principle II (Class-Based) and
project convention require routing every Mist call through the official
`mistapi` SDK -- no direct `requests` usage.

**Alternatives Considered**:
- *Direct `requests.get()` with manual headers*: Rejected. Violates the
  project's sole-SDK rule, bypasses the existing token-injection / rate-limit
  / retry handling baked into `mistapi`.
- *Iterating the list endpoint and filtering by id*: Rejected. Adds an
  unnecessary `listOrgMarvisClientInvites` call, wastes API quota, and
  defeats the purpose of having a single-resource GET.

## Research Task 2: Primary Key Strategy

**Decision**: `natural_pk` keyed on the `id` field (the Marvis invite UUID
returned by the API).

```python
"getOrgMarvisClientInvite": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["name"],
}
```

**Rationale**: The response schema declares `id` as a `readOnly` UUID
("Unique ID of the object instance in the Mist Organization"). UUIDs are
stable across reads, so `INSERT OR REPLACE` on `id` gives correct upsert
behavior on repeated runs. `name` is added as a secondary index for the
common lookup pattern (NOC engineer searching by invite label). `org_id`
is the parent scope and is added as a stored column on the row but not used
as a primary key, since the SDK call already scopes by `org_id`.

**Alternatives Considered**:
- *composite_pk on `[org_id, id]`*: Rejected. The invite `id` is a UUID and
  globally unique in Mist; adding `org_id` to the PK adds no uniqueness and
  costs index space.
- *auto_increment_with_unique*: Rejected. There is a stable natural key
  (`id`) -- using a synthetic ID would create duplicates on every re-run.

## Research Task 3: Output Filename and SQLite Table

**Decision**:
- CSV filename: `data/org_marvis_client_invite.csv`
- SQLite table name: `org_marvis_client_invite`
- ArangoDB collection: `org_marvis_client_invite`

**Rationale**: Follows the established MistHelper naming convention --
snake_case form of the resource that the endpoint returns, singular noun
because this endpoint returns a single object. Existing precedents include
`org_licenses_summary`, `org_claim_status_summary`. The single CSV / table
captures all four response fields plus a stored `org_id` parent column for
join-back to org records.

**Alternatives Considered**:
- *`marvis_invites.csv`*: Rejected. Too generic -- collides with the future
  list endpoint (`listOrgMarvisClientInvites`) which will need its own
  identifier-free table. Prefixing with `org_` and including the resource
  family (`marvis_client_invite`) keeps the namespace tidy.
- *`org_marvis_invites_get.csv`*: Rejected. The operation suffix is
  unnecessary noise -- the table is already scoped to a single resource.

## Research Task 4: Menu Category Placement & Number

**Decision**: Menu number **195**, placed in the "Org Admin / Marvis" cluster
above the current top-of-range (194: `cloneDeviceConfigToGatewayTemplate`).

**Rationale**: Per `.github/copilot-instructions.md` the menu currently spans
1-194. Read-only org admin / Marvis operations are clustered with the safe
org exports band (1-59) and the interactive safe band (60-96); the next
sequential slot for a new safe-read Marvis operation is the first integer
above the current ceiling -- 195. Picking 195 avoids:

- The destructive band (154-194) -- this endpoint is read-only.
- The WebSocket band (102-123) -- this is plain HTTPS.
- The continuous-monitoring band (151-152) -- this is one-shot.

If the related list and delete endpoints
(`listOrgMarvisClientInvites`, `deleteOrgMarvisClientInvite`) are added in
follow-up PRs, they will be placed at 196 (list, safe) and inside the
destructive band (delete) respectively, keeping family grouping informal but
intuitive.

**Alternatives Considered**:
- *Insert at 90-96 (Marvis-adjacent safe slot)*: Rejected. Existing
  numbering is stable and renumbering ripples through tests, README, and
  user documentation.
- *Defer numbering to task phase*: Rejected. The constitution requires the
  plan to propose an explicit menu number to drive review.

## Research Task 5: Required User Prompts

**Decision**: Two `safe_input()` prompts, in order:

1. `org_id` -- prompt: `"Enter org_id (or press Enter for MIST_ORG_ID from .env): "`,
   context: `"org_marvis_client_invite:org_id"`. Defaults from `.env`
   `MIST_ORG_ID` if the user presses Enter and `MIST_ORG_ID` is set.
2. `marvisinvite_id` -- prompt:
   `"Enter marvisinvite_id (UUID of the Marvis client invite): "`,
   context: `"org_marvis_client_invite:marvisinvite_id"`. No `.env` default;
   the user must supply this (it is the resource the call retrieves).

Both inputs are validated against the Mist UUID shape before the SDK call.
On UUID-validation failure the method logs `WARNING` and returns early --
no SDK call is made.

**Rationale**: `MIST_ORG_ID` is already a documented `.env` convention used
by other org-scoped menu items, so reusing it minimizes friction for the
common single-org user. `marvisinvite_id` is the resource itself -- caching
it in `.env` would obscure the per-invocation intent and would not match how
the related list endpoint will be used to discover invite IDs.

`MIST_HOST` and `MIST_API_TOKEN` are not prompted -- they come from `.env`
via `mistapi.APISession()` initialization (project standard).

**Alternatives Considered**:
- *Prompt for both UUIDs unconditionally*: Rejected. The `.env` default
  pattern for `org_id` already exists project-wide and reducing prompt count
  is a small UX win for SSH / container sessions.
- *Discover `marvisinvite_id` by running the list endpoint first inside
  this menu*: Rejected. That belongs to the future
  `listOrgMarvisClientInvites` menu item; coupling the two adds an extra API
  call and exceeds the 5-block / 25-line limit.
