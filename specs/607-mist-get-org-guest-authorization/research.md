# Phase 0 Research: GetOrgGuestAuthorization

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document records the Phase 0 research decisions that ground the implementation
plan. Each task uses the Decision / Rationale / Alternatives Considered structure
mandated by the SpecKit plan template. Source-of-truth for the endpoint is the
enriched per-endpoint doc at
`documentation/api/orgs/GET_orgs_org_id_guests_guest_mac.md`.

## Research Task 1: SDK Function Signature & Behavior

### Decision

Invoke the endpoint exclusively through the `mistapi` SDK, using the call signature:

```python
import mistapi
from mistapi.api.v1.orgs.guests import guests as mist_guests

response = mist_guests.getOrgGuestAuthorization(
    mist_session,    # mistapi.APISession constructed once at MistHelper startup
    org_id,          # str UUID supplied by user (validated before this call)
    guest_mac,       # str -- normalized to 12 lower-case hex chars, no separators
)
```

`response` is a `mistapi.models.response.Response`-style object whose `.data`
attribute holds the parsed JSON (a single dict matching the schema in the enriched
doc -- not a list, not paginated).

### Rationale

- The enriched doc (lines 169-171 of
  `documentation/api/orgs/GET_orgs_org_id_guests_guest_mac.md`) names
  `mistapi.api.v1.orgs.guests.getOrgGuestAuthorization()` as the canonical SDK entry
  point.
- The endpoint is non-paginated (enriched doc, line 163 "Pagination: Not paginated"),
  so no `mistapi.get_all` wrapper or cursor handling is required.
- The doc lists only two path parameters (`org_id`, `guest_mac`) and no query
  parameters, so the SDK signature has no optional kwargs that need plumbing through
  the menu method.
- Using the SDK (rather than raw `requests`) keeps adaptive delay, retry, and
  rate-limit handling consistent with every other MistHelper menu item and respects
  the constitution's "mistapi 0.59+ is the sole permitted interface to the Mist
  Cloud" constraint.

### Alternatives Considered

- **Raw `requests.get(...)` against `MIST_HOST + path`**: rejected -- bypasses
  retry, rate-limit, and token-injection logic and duplicates code that already lives
  in `mistapi.APISession`.
- **`mistapi.get_all()` wrapper**: rejected -- this endpoint returns a single object,
  not a paged list, so the wrapper would add complexity without benefit.
- **Calling the search endpoint (`GET /api/v1/orgs/{org_id}/guests/search`) and
  filtering client-side**: rejected -- doubles API quota usage and breaks the
  one-menu-item / one-operationId mapping recorded in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

## Research Task 2: Primary Key Strategy

### Decision

Register the operation in `ENDPOINT_PRIMARY_KEY_STRATEGIES` as a **natural_pk** entry:

```python
"getOrgGuestAuthorization": {
    "type": "natural_pk",
    "primary_key": ["org_id", "mac"],
    "indexes": ["wlan_id", "ssid", "auth_method", "authorized"],
},
```

`mac` is the API-supplied lower-case 12-hex normalized form. `org_id` is injected by
MistHelper before write to disambiguate guests across orgs that share the same MAC
(possible with randomized MACs).

### Rationale

- The response carries no internal UUID, so a single-column `id`-based natural PK
  is not viable.
- `mac` is the stable identifier the Mist API itself uses to address this resource
  (it appears in both the path and the response body).
- The same `mac` can legitimately appear under multiple `org_id` values (a
  contractor visiting two organizations, or a randomized MAC reused across orgs),
  so the composite `(org_id, mac)` is the smallest key that uniquely identifies the
  row in the local store.
- This is not a time-series endpoint (no per-poll history is required by the spec),
  so `composite_pk` with `timestamp` would over-key the table. Each new poll is an
  **upsert** that replaces the prior authorization snapshot, which is exactly what
  `INSERT OR REPLACE` on `(org_id, mac)` delivers.

### Alternatives Considered

- **`composite_pk` with `(org_id, mac, polled_at_utc)`**: rejected -- would retain
  every poll as a separate row, which is useful for trend analysis but is not what
  the spec asks for and would unbounded-grow the table on repeated runs.
- **`auto_increment_with_unique` on `(org_id, mac)`**: rejected -- adds a redundant
  surrogate key for no foreign-key benefit; the natural composite is already short
  and stable.
- **PK on `mac` alone**: rejected -- collides across orgs as described above.

## Research Task 3: Output Filename and SQLite Table

### Decision

- CSV / JSON output filename: `org_guest_authorization.csv` (and matching `.json`
  when JSON backend is selected), written under `data/`.
- SQLite table name: `org_guest_authorization` (singular -- matches one-row-per-guest
  semantic; matches existing naming style of sibling exporter tables such as
  `org_inventory`, `org_licenses_summary`).
- ArangoDB collection: `org_guest_authorization`, with edges from the existing
  `org` and `wlan` collections (when `wlan_id` is non-null) added by the standard
  `DataExporter` graph-link logic.

### Rationale

- MistHelper's convention for org-scoped read endpoints is `org_<noun>` snake_case
  matching the operationId stem (e.g. `org_inventory` for `getOrgInventory`,
  `org_licenses_summary` for `getOrgLicensesSummary`).
- The operationId stem here is `OrgGuestAuthorization` -> `org_guest_authorization`.
- A single shared filename across CSV and SQLite avoids backend-specific
  divergence in user-facing documentation (README menu table cites one name).

### Alternatives Considered

- **`guest_authorization_<org_id>_<mac>.csv` (per-call filename)**: rejected --
  produces unbounded file sprawl in `data/`, breaks the existing upsert-by-PK
  workflow, and complicates downstream joins.
- **Sharing the `org_guests_search` table**: rejected -- the search endpoint returns
  a subset of fields with different semantics (list view vs full detail); merging
  them risks lossy schema unification.

## Research Task 4: Menu Category Placement and Next Available Menu Number

### Decision

- **Category**: Interactive Safe (operations 60-96).
- **Proposed menu number**: **96**.
- **Final number**: confirmed at task generation time via a fresh scan of the menu
  registry in `MistHelper.py`. If 96 is already taken by an in-flight feature
  branch, the next free integer inside the same Interactive Safe cluster is used
  (97 belongs to the Resource Intensive block and is therefore not a fallback --
  the implementer drops back into the unused gap within 60-96 instead).

### Rationale

- The constitution's menu-category guidance (recorded in `.github/copilot-instructions.md`
  Menu Categories table) places interactive lookups that require a user-supplied
  identifier (here: `guest_mac`) in the 60-96 band.
- The endpoint requires a per-call identifier the user must type, so it is not a
  "Safe Org Exports" (1-59) candidate -- those operations enumerate without per-row
  prompts.
- The endpoint is strictly read-only with no destructive side effect, so it is not
  a 154-194 candidate.
- 96 is the highest currently-unused slot in the Interactive Safe band, leaving
  60-95 for in-flight features and keeping the new operation visually adjacent to
  related guest / NAC / client-lookup menu items.

### Alternatives Considered

- **Slot in the 90-100 range (resource intensive)**: rejected -- this endpoint is a
  single non-paginated GET that completes in well under 5 seconds; calling it
  "resource intensive" would mislead the user and exclude it from the default
  `--test` sweep.
- **Append at 195**: rejected -- 154-194 is the destructive block; appending past
  194 would create a new "post-destructive" cluster with no governance rules.

## Research Task 5: Required User Prompts (Which IDs from User, Which from .env)

### Decision

Two prompts via `safe_input()`, both supplied at runtime:

1. `org_id` -- prompted with `safe_input("Enter org UUID (Enter for MIST_ORG_ID from
   .env): ", context="org_guest_authorization:org_id")`. If the user presses Enter,
   the value falls back to `os.environ.get("MIST_ORG_ID")`. If the env fallback is
   also empty, the method logs a WARNING and returns early.
2. `guest_mac` -- prompted with `safe_input("Enter guest MAC (any format -- will be
   normalized): ", context="org_guest_authorization:guest_mac")`. The raw string is
   normalized by `re.sub(r"[^0-9a-fA-F]", "", value).lower()` and validated to be
   exactly 12 hex characters before the SDK call. No env fallback (per-call MAC is
   intrinsically user input; no sensible default).

The `mistapi.APISession` itself is constructed at MistHelper startup using
`MIST_HOST` and `MIST_API_TOKEN` from `.env`; the new method does not re-read those.

### Rationale

- Two and only two parameters are required by the endpoint (per the enriched doc
  Path Parameters table), so the menu method asks for exactly those two.
- Falling back to `MIST_ORG_ID` for `org_id` matches the convention used by other
  org-scoped exporters and makes the menu item usable in non-interactive `--test`
  mode (which supplies the env var).
- No env fallback for `guest_mac` because (a) there is no equivalent canonical env
  var, (b) the value is per-investigation and varies every call, and (c) hard-coding
  it would risk leaking a real guest's MAC into the shared `.env.example`.
- All prompts use `safe_input()` to guarantee clean EOF handling under SSH on
  port 2200 and inside the container's restricted shell (Principle III).

### Alternatives Considered

- **One combined prompt (`org_id/guest_mac`)**: rejected -- harder to validate, less
  forgiving on typos, and breaks the pattern used by every other multi-parameter
  menu item.
- **Read `guest_mac` from a CSV file**: rejected -- introduces an input-file
  dependency for a single-lookup tool. A future bulk-lookup spec can extend this
  pattern if real demand emerges.
- **Auto-discover `guest_mac` by listing guests first**: rejected -- doubles API
  quota usage and conflates this read with the search endpoint, which already has
  its own menu item.
