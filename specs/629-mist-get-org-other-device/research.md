# Phase 0 Research: getOrgOtherDevice

Feature: `629-mist-get-org-other-device`
Endpoint: `GET /api/v1/orgs/{org_id}/otherdevices/{device_mac}`

## Research Task 1: SDK Function Signature and Behavior

**Decision**: Invoke the endpoint via
`mistapi.api.v1.orgs.otherdevices.getOrgOtherDevice(mist_session, org_id, device_mac)`.
The call takes exactly two path arguments plus the shared `APISession`. It returns a
`mistapi.APIResponse` whose `.data` attribute is a single JSON object (not a list) with
the fields `created_time`, `device_mac`, `id`, `mac`, `model`, `modified_time`, `name`,
`org_id`, `serial`, `site_id`, `state`, `vendor`, `vendor_api_id`. The response is
non-paginated; there are no `next` / `page` semantics to handle.

**Rationale**: The enriched documentation at
`documentation/api/orgs/GET_orgs_org_id_otherdevices_device_mac.md` confirms the path,
lack of query parameters, single-object response shape, and the SDK module path
(`mistapi.api.v1.orgs.devices_-_others.getOrgOtherDevice()` per the doc, which resolves
to `mistapi.api.v1.orgs.otherdevices` in the installed SDK package because Python does
not permit hyphens in module names -- MistHelper already imports the sibling
`listOrgOtherDevices` via `mistapi.api.v1.orgs.otherdevices` in existing code paths,
confirming the module name).

**Alternatives Considered**:
- **Direct `requests.get()` against the Mist REST URL**: Rejected. Violates the
  constitution's requirement to use `mistapi` as the sole Mist API interface.
- **Batch multiple MACs in a single loop hidden behind one prompt**: Rejected. Out of
  scope for this endpoint (the sibling `listOrgOtherDevices` already exists for bulk
  retrieval). A dedicated single-MAC lookup is a distinct operator workflow (drill-in
  on one device from a search result or ticket).

## Research Task 2: Primary Key Strategy

**Decision**: Register the operationId as `natural_pk` with `primary_key: ["id"]` and
`indexes: ["org_id", "site_id", "mac", "vendor", "model", "state"]`.

**Rationale**: The response schema documents `id` as `"Unique ID of the object instance
in the Mist Organization"` with `readOnly: true` and UUID encoding -- the exact
signature of a stable natural key. The sibling `listOrgOtherDevices` entry (line 4006
in `MistHelper.py`) already uses `natural_pk` on `id`, so this endpoint reuses the
same key shape and produces upsert-compatible rows across the two operationIds. The
indexes cover the fields NOC engineers routinely filter on: `org_id` for tenancy
scoping, `site_id` for site-level joins, `mac` for cross-reference against wired /
wireless client tables, and `vendor` / `model` / `state` for inventory reporting.

**Alternatives Considered**:
- **`composite_pk` on `["id", "org_id"]`**: Rejected. `id` is already globally unique
  within the Mist tenant; adding `org_id` provides no disambiguation and doubles the
  index cost.
- **`auto_increment_with_unique`**: Rejected. `id` is stable and returned by the API,
  so an artificial surrogate key would only add clutter and defeat the upsert benefit
  documented in the copilot instructions (Database Strategy section).
- **Composite on `["org_id", "device_mac"]`**: Rejected. `id` is the canonical Mist
  identifier for the object; keying on the MAC would break if Mist ever reassigned a
  MAC across records (rare but possible during vendor swaps).

## Research Task 3: Output Filename and SQLite Table

**Decision**:
- CSV filename: `data/org_other_device.csv` (singular; single-object endpoint).
- SQLite table: `org_other_device`.
- ArangoDB collection: `org_other_device`.
- Redis cache key prefix: `org_other_device:{id}`.

**Rationale**: The naming pattern matches the existing convention in MistHelper: the
sibling list endpoint writes `org_other_devices.csv` (plural) and the SQLite table
`org_other_devices`; the single-object endpoint uses the singular form to make the
two visually distinct in `data/` listings and in database inspection sessions.
`DataExporter.write_with_format_selection()` derives the SQLite table name and
ArangoDB collection name from the filename stem, so consistent naming is achieved by a
single filename choice.

**Alternatives Considered**:
- **Reuse `org_other_devices.csv` and append**: Rejected. Mixing list and single-lookup
  results in the same file would corrupt the upsert semantics and confuse downstream
  reporting queries; a distinct filename keeps the two operationIds independently
  addressable.
- **Filename keyed on the queried MAC (e.g., `org_other_device_<mac>.csv`)**: Rejected.
  Creates unbounded file churn in `data/` and defeats SQLite upsert (each MAC would
  land in its own table).

## Research Task 4: Menu Category Placement and Next Available Menu Number

**Decision**: Register the new menu item at operation number **96** under the
"Interactive Safe / Viewers" cluster (menu range 92-96 per `agents.md` Menu Categories
table).

**Rationale**: The menu is interactive (prompts for a specific `device_mac`) and
strictly read-only, matching the Viewers-cluster contract. 96 is the last free slot in
the range before the Resource Intensive block begins at 97. Placement adjacent to
existing device viewers keeps the menu discoverable for NOC engineers who reach for
"look up one specific device" workflows. If parallel in-flight branches consume 96
before this feature reaches `/speckit.tasks`, the implementer picks the next free
integer in the same cluster (91 or the tail of the interactive-safe block) and updates
the plan header accordingly.

**Alternatives Considered**:
- **Safe Org Exports (1-59)**: Rejected. That cluster is reserved for non-interactive
  bulk exports keyed on `org_id` only. Requiring a MAC prompt makes this endpoint an
  interactive lookup, not a bulk export.
- **Destructive block (154-194)**: Rejected. The endpoint is a strict GET with no
  side effect.
- **New menu category**: Rejected. The existing "Interactive Safe / Viewers" cluster
  already describes the exact shape of this operation; introducing a new category
  would violate the 5-Item Rule at the menu-category hierarchy level.

## Research Task 5: Required User Prompts

**Decision**: Two prompts, both wrapped in `safe_input()`:

1. `org_id` -- prompt suppressed if `MIST_ORG_ID` is present in `.env` (existing
   `ConfigUtils.get_org_id()` helper already handles this precedence). Context string:
   `"org_other_device:org_id"`. Validated against the Mist UUID shape via
   `ValidationUtils.is_valid_uuid()`.
2. `device_mac` -- always prompted; no reasonable `.env` default because the MAC is
   per-lookup. Context string: `"org_other_device:device_mac"`. Accepted formats:
   `aa:bb:cc:dd:ee:ff`, `aa-bb-cc-dd-ee-ff`, or `aabbccddeeff` (case-insensitive).
   Canonicalized to `aabbccddeeff` (lowercase, no separators) before the SDK call via
   the existing `ValidationUtils.normalize_mac()` helper. On invalid MAC, a WARNING is
   logged and the method returns without invoking the SDK.

**Rationale**: This mirrors the interactive-viewer pattern already used by menu items
in the 92-96 cluster. Loading `org_id` from `.env` when available reduces prompt
fatigue for the common single-tenant NOC deployment; keeping `device_mac` as a live
prompt reflects the per-invocation nature of the lookup. Both prompts route through
`safe_input()` so EOF in SSH or container sessions exits with code 0 and no traceback,
satisfying Constitution Principle III.

**Alternatives Considered**:
- **Ask both from CLI arguments only**: Rejected. Breaks the menu-driven contract that
  junior NOC engineers rely on; interactive mode must remain the primary entry point.
- **Ask `device_mac` from `.env`**: Rejected. A MAC is per-lookup and does not belong
  in a shared config file; encoding it in `.env` would encourage stale reuse.
- **Skip MAC normalization**: Rejected. The Mist API is strict about MAC format;
  passing a hyphen-separated MAC yields a 400 that surfaces as a confusing user
  error. Normalizing upstream keeps error handling predictable.
