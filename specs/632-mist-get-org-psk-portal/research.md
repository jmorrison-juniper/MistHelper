# Phase 0 Research: getOrgPskPortal

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-30

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_pskportals_pskportal_id.md`
(enriched OpenAPI doc, 200 OK response schema).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path derived from the
OpenAPI URL: `mistapi.api.v1.orgs.psk_portals.getOrgPskPortal(apisession, org_id,
pskportal_id)`. The SDK returns a `mistapi.APIResponse` object whose `.data`
attribute is the parsed JSON body. The body is a single JSON object (not a list and
not paginated) describing one PSK self-service portal, with the following top-level
keys per the doc:

- `id` (string UUID, read-only, unique ID of the portal)
- `org_id` (string UUID, read-only, echo of the parent org)
- `name` (string, required)
- `ssid` (string, required, the intended SSID)
- `auth` (string enum: `sponsor`, `sso`)
- `type` (string enum: `admin`, `byod` -- personal PSK portal kind)
- `role` (string)
- `bg_image_url`, `thumbnail_url`, `template_url`, `ui_url` (strings, UI customization)
- `cleanup_psk`, `notify_expiry`, `notify_on_create_or_edit`,
  `hide_psks_created_by_other_admins` (booleans)
- `expire_time` (int32, minutes)
- `expiry_notification_time` (int32, days before expiry)
- `max_usage` (int32, 0 means unlimited)
- `notification_renew_url` (string)
- `created_time` (number, epoch seconds, read-only)
- `modified_time` (number, epoch seconds, read-only)
- `vlan_id` (object -- can be a single VLAN or a mapping)
- `required_fields` (array of strings -- required signup fields)
- `passphrase_rules` (nested object -- `alphabets_enabled`, `length`, `min_length`,
  `max_length`, `numerics_enabled`, `symbols`, `symbols_enabled`)
- `sso` (nested object, only meaningful when `auth==sso`: `allowed_roles`,
  `idp_cert`, `idp_sign_algo`, `idp_sso_url`, `issuer`, `nameid_format`,
  `role_mapping`, `use_sso_role_for_psk_role`)

Required path parameters: `org_id` (UUID) and `pskportal_id` (UUID). No query
parameters. No request body. The API doc lists the SDK as
`mistapi.api.v1.orgs.psk_portals.getOrgPskPortal()`; the spec.md names the module
as `mistapi.api.v1.orgs.pskportals` (no underscore). The mistapi SDK uses snake_case
module names for multi-word URL segments (e.g., `psk_portals`), so the enriched-doc
form is authoritative. Final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs import psk_portals; help(psk_portals.getOrgPskPortal)"`
inside the venv; if the SDK exposes it under a different exact name the call site
is adjusted, without changing the plan.

**Rationale**:
The enriched per-endpoint doc explicitly lists the SDK path
`mistapi.api.v1.orgs.psk_portals.getOrgPskPortal()` and the mistapi package uses
Python-legal snake_case module names throughout (verified by inspecting adjacent
snake_case modules such as `mistapi.api.v1.orgs.device_profiles`). Grounding the
plan in the doc keeps implementation cheap and predictable.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/pskportals/{pskportal_id}`.* Rejected --
   the constitution's Technology & Compatibility Constraints forbid direct HTTP
   when a mistapi SDK method exists.
2. *Use the exact module name from the spec (`pskportals`, no underscore).*
   Rejected -- Python module names cannot mix segments arbitrarily and the mistapi
   codebase uses snake_case. If a runtime import error occurs, fall back with a
   `try/except ImportError` and match whichever name the installed SDK exports.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **natural_pk** strategy on the single output table `org_psk_portals`, with
`primary_key = ['id']`. The Mist API returns `id` as a stable read-only UUID that
uniquely identifies the portal within the parent organization and across polls,
matching the reference pattern used by `listOrgSites` (which also natural-keys on
`id`).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration also names secondary indexes on
`org_id` (for cross-org queries when a single MistHelper instance targets multiple
orgs) and `name` (for human-oriented lookups by portal name).

**Rationale**:
The response schema marks `id` as `readOnly: true` with a `uuid` content encoding
and a fixed example, meaning Mist guarantees it is stable for the life of the
portal. `INSERT OR REPLACE INTO org_psk_portals (id, ...)` cleanly upserts on
repeated runs -- the exact upsert behavior the spec and Constitution require. No
timestamp component in the PK is needed because the endpoint returns a single
configuration record, not a time-series snapshot.

**Alternatives Considered**:

1. *`composite_pk` on `(org_id, id)`.* Rejected -- `id` is already a UUID globally
   unique to the Mist tenant; adding `org_id` to the PK is redundant. `org_id` is
   still stored as a regular indexed column and populated by MistHelper before the
   upsert so cross-org queries work.
2. *`auto_increment_with_unique`.* Rejected -- would let repeated runs against the
   same portal accumulate duplicate rows keyed on a synthetic integer, defeating
   the upsert behavior the spec explicitly requires.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_psk_portal_<pskportal_id_short>.csv`
- SQLite table: `org_psk_portals`
- `org_id_short` = first 8 hex characters of the org UUID.
- `pskportal_id_short` = first 8 hex characters of the portal UUID.
- The `api_function_name` argument passed to
  `DataExporter.write_with_format_selection()` is `"getOrgPskPortal"` (matching
  the operationId, which is the key DataExporter uses to look up
  `ENDPOINT_PRIMARY_KEY_STRATEGIES`).

**Rationale**:
The filename pattern mirrors the convention already used by adjacent
per-entity exports (`org_<short>_...` short-UUID prefixes keep filenames
human-scannable without leaking full UUIDs into shell history). A single SQLite
table `org_psk_portals` is enough because the response is a flat-ish object per
portal; nested `passphrase_rules` and `sso` sub-objects are flattened with dotted
key prefixes (`passphrase_rules_length`, `sso_idp_cert`, etc.) into the same row.
This mirrors how MistHelper already flattens WLAN objects.

**Alternatives Considered**:

1. *Store `passphrase_rules` and `sso` as JSON-encoded columns.* Rejected --
   breaks SQL queryability and conflicts with the `flatten_dict()` convention
   used across MistHelper.
2. *Emit two separate tables (`org_psk_portals` + `org_psk_portal_sso_configs`).*
   Rejected as premature normalization for a single-record read: there is one
   `sso` block per portal at most, so a wide row is simpler than a join.
3. *Use the full org and portal UUIDs in the filename.* Rejected -- leaks
   identifiers into shell history and `ls` output; short-UUID prefixes are enough
   to disambiguate locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as **menu number 89**, sitting in the Safe Org Exports
"config and admin" cluster. Category label: "Safe Org Exports -- PSK Portals".

**Rationale**:
The constitution and `.github/copilot-instructions.md` describe the current menu
ranges as: 1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource
Intensive, 102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. PSK-portal
retrieval is a strictly read-only, interactive-safe operation (it prompts the user
for two UUIDs, then does a single GET). 89 is well below the resource-intensive
block at 96 and far from any destructive number. The number is provisional -- at
`/speckit.tasks` time `MistHelper.py` is grep'd for the highest allocated menu
integer and 89 is shifted forward if a conflict exists with any in-flight feature
branch (e.g., other spec-# generation runs happening in parallel).

**Alternatives Considered**:

1. *Append to the end (e.g., 195+).* Rejected -- placing a strictly read-only
   PSK-portal lookup above the destructive block visually mis-signals the risk
   level to a junior NOC engineer scrolling the menu.
2. *Slot inside Resource Intensive (96-101).* Rejected -- this endpoint is a
   single GET returning a small JSON object, with no pagination and no
   long-running work. It belongs in the safe-interactive block.
3. *Slot inside Destructive (154-194).* Rejected -- absolutely inappropriate for a
   read-only endpoint. Would trip the destructive-confirmation gate needlessly.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly two** values via `safe_input()`:

1. `org_id` -- prompt: `"Org ID (UUID): "`, context: `"org_psk_portal:org_id"`.
   Default: the value of `MIST_ORG_ID` in `.env` if present (pressing Enter
   accepts the default). Validated via the existing `is_valid_uuid()` helper
   before the API call; on failure, log `WARNING` and return early.
2. `pskportal_id` -- prompt: `"PSK Portal ID (UUID): "`, context:
   `"org_psk_portal:pskportal_id"`. Default: the value of `MIST_PSK_PORTAL_ID`
   in `.env` if present. Validated via `is_valid_uuid()`; on failure log
   `WARNING` and return early. If the user does not know the portal UUID up
   front, they can run the adjacent `listOrgPskPortals` menu item (already
   catalogued -- see `documentation/api/orgs/GET_orgs_org_id_pskportals.md`) to
   list all portals in the org and copy the desired ID from the resulting CSV
   or SQLite table.

`.env` values used (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.
- `MIST_PSK_PORTAL_ID` -- optional default for prompt 2 (new optional key; not
  currently declared in the shared `.env.example` because it is portal-specific
  and per-user).

**Rationale**:
The endpoint requires exactly two path parameters and no query parameters, so two
prompts are the minimum interactive contract. Both are UUIDs and both are
validated before the SDK call to avoid a wasted API round-trip on malformed
input. Providing `.env` defaults keeps the menu item scriptable
(`echo "" | python MistHelper.py --menu 89`) while still supporting ad hoc
interactive use.

**Alternatives Considered**:

1. *Take only `org_id` and iterate over every portal in the org
   (implicit listOrgPskPortals + per-portal get).* Rejected -- that is a
   different feature (bulk export) with different performance characteristics
   and a different PK / naming decision. Belongs in its own spec.
2. *Skip UUID validation and let the Mist API return 400.* Rejected -- wastes a
   rate-limited API call, produces a harder-to-diagnose error path for the
   junior NOC engineer, and violates the Safety-First principle's early-return
   pattern.
