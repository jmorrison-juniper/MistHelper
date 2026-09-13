# Phase 0 Research: getOrgDeviceUpgrade

**Feature**: 605-mist-get-org-device-upgrade
**Date**: 2026-06-30
**Inputs**: spec.md, `documentation/api/utilities/GET_orgs_org_id_devices_upgrade_upgrade_id.md`, `MistHelper.py`

## Research Task 1: SDK function signature & behavior

**Decision**: Call the endpoint via
`mistapi.api.v1.orgs.devices.upgrade.getOrgDeviceUpgrade(apisession, org_id, upgrade_id)`,
matching the OpenAPI path `/api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}`
and the spec.md SDK module declaration. The SDK returns a
`mistapi.APIResponse` whose `.data` is a single JSON object (not a list),
shaped as the schema in `documentation/api/utilities/GET_orgs_org_id_devices_upgrade_upgrade_id.md`
(top-level fields: `id`, `target_version`, `strategy`, `enable_p2p`,
`force`, plus a nested `upgrades` array, one entry per affected site).

**Rationale**: The path tokens are unambiguous (`orgs / {org_id} / devices /
upgrade / {upgrade_id}`), so the Pythonic SDK accessor must mirror the path
exactly. The enriched doc on disk lists the SDK module as
`mistapi.api.v1.utilities.upgrade.getOrgDeviceUpgrade` -- this is a known
inconsistency in the auto-generated doc index; the path-derived module
`mistapi.api.v1.orgs.devices.upgrade` is authoritative because that is the
module mistapi 0.59+ actually ships (verified by cross-referencing the
sibling `listOrgDeviceUpgrades` operationId which mistapi places under
`orgs.devices.upgrade`). The Phase 2 task list will pin the exact module
path with a one-line `python -c "import ..."` smoke test before menu
registration.

**Alternatives Considered**:
1. Use `mistapi.api.v1.utilities.upgrade.getOrgDeviceUpgrade` per the
   enriched doc index. Rejected -- the `utilities` tag is OpenAPI tag
   metadata, not the SDK module hierarchy; the SDK always mirrors path
   tokens.
2. Hand-roll the HTTP call with `requests`. Rejected -- violates the
   constitution requirement that all Mist API access goes through the
   `mistapi` SDK.

## Research Task 2: Primary Key Strategy

**Decision**: `composite_pk` for the summary row, with
`primary_key = ["org_id", "id"]` (where `id` is the upgrade UUID returned by
the endpoint). For the flattened per-site detail rows, use a separate table
keyed by `composite_pk` with
`primary_key = ["org_id", "upgrade_id", "site_id"]`. Both entries land in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. Both use `INSERT OR REPLACE` semantics so
repeated polling of an in-progress upgrade upserts cleanly without
duplicating rows.

**Rationale**: The API returns a single upgrade record identified by a
stable UUID (`id`). That UUID is unique across the org but NOT globally
across all MistHelper-managed orgs, so the natural PK must include
`org_id`. The nested `upgrades` array has one entry per affected site; each
entry carries a stable `site_id` (UUID). The compound `(org_id, upgrade_id,
site_id)` is the natural business key for the per-site detail row and
admits clean upserts when the user re-polls a long-running upgrade.

**Alternatives Considered**:
1. `natural_pk` with just `["id"]`. Rejected -- collides across orgs in the
   shared `mist_data.db` file.
2. `auto_increment_with_unique` (the strategy used by the sibling
   `listOrgDeviceUpgrades`). Rejected -- this endpoint returns the SAME
   record on every poll (status fields evolve over time), so an
   auto-increment PK would accumulate one row per poll instead of
   updating the in-place row.
3. Single flat table with one row per device MAC. Rejected -- the device
   MACs are inline arrays per phase (`downloaded`, `failed`, etc.); flattening
   to one-row-per-MAC loses the phase semantics and is better deferred to a
   future analytics-focused menu item.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV filenames (one invocation produces two files):
  - `data/org_device_upgrade_<short_org>_<short_upgrade>.csv` -- one
    summary row (the top-level upgrade record minus the nested array)
  - `data/org_device_upgrade_site_details_<short_org>_<short_upgrade>.csv`
    -- N rows, one per affected site, with the per-phase MAC arrays
    serialized as comma-joined strings
- SQLite tables (auto-created on first run by `DataExporter`):
  - `org_device_upgrade` (summary)
  - `org_device_upgrade_site_details` (per-site flatten)
- `<short_org>` and `<short_upgrade>` are the first eight characters of
  each UUID, matching the naming convention used by adjacent menu items
  (e.g. `listOrgDeviceUpgrades` output files).

**Rationale**: Two output artifacts mirror the two SQLite tables, which
mirror the two PK strategies. Short UUID prefixes keep Windows filename
length bounded while preserving disambiguation when the user polls
multiple upgrades in the same session. Lower-snake-case table names match
the existing MistHelper SQLite convention (see `listOrgDeviceUpgrades`
table at MistHelper.py line 3983).

**Alternatives Considered**:
1. Single CSV with the per-site rows denormalized into the summary row.
   Rejected -- breaks CSV column stability when the number of sites
   varies between polls.
2. JSON dump only (no flatten). Rejected -- violates the multi-backend
   contract; ArangoDB and CSV consumers need flat row shapes.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Menu number **96**, placed in the safe Viewers cluster
(92-96 per the `.github/copilot-instructions.md` Menu Categories table).
Sibling read-only firmware-status operations live in the same neighborhood
via `FirmwareUpgradeStatusChecker`.

**Rationale**: The endpoint is strictly read-only (HTTP GET, no side
effects on the Mist cloud). It returns operational status of an existing
upgrade job, which is fundamentally a "viewer" function -- the user is
inspecting progress, not changing it. Menu 96 is the next available
integer that:

1. Does not collide with reference spec 500's proposed menu 95
   (same `/speckit.plan` workflow, currently in flight).
2. Sits inside the documented Viewers cluster (92-96), preserving the
   existing menu taxonomy.
3. Stays far away from the destructive firmware-write block at 154-160
   (where firmware upgrade *initiation* lives), avoiding any user
   confusion between "view upgrade status" (read) and "trigger upgrade"
   (destructive).

The task generation step (`/speckit.tasks`) will re-verify menu 96 against
the live menu registry at the time of implementation; if a sibling 6xx
spec lands first and claims 96, the next free integer in the Viewers
cluster (and then the 80-91 Stats cluster) is selected.

**Alternatives Considered**:
1. Menu in the 154-160 range alongside the firmware-upgrade *initiation*
   menus. Rejected -- the constitution and agent docs treat that range as
   destructive; this endpoint has no destructive effect and must not be
   gated behind destructive confirmation prompts.
2. Menu 90 (per the doc's "MistHelper Notes" hint). Rejected -- 90 is
   already on the heavy/destructive skip list and is reserved by the
   existing `FirmwareManager` cluster.
3. Reusing the existing `FirmwareUpgradeStatusChecker` menu entry rather
   than adding a new number. Rejected -- the existing menu performs a
   broad multi-API status sweep; this endpoint targets a single specific
   upgrade UUID, a distinct user intent that deserves its own menu slot.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: Prompt for two identifiers via `safe_input()`:

| Prompt | Source | Default | Validation |
|--------|--------|---------|------------|
| `org_id` | `safe_input("Org ID [default from .env]: ", context="org_device_upgrade:org_id")` | `MIST_ORG_ID` from `.env` if set, else no default | Mist UUID regex |
| `upgrade_id` | `safe_input("Upgrade ID (UUID, see menu for listOrgDeviceUpgrades): ", context="org_device_upgrade:upgrade_id")` | None -- user must supply | Mist UUID regex |

No other prompts are required. The endpoint has zero query parameters and
no request body. API credentials (`MIST_HOST`, `MIST_API_TOKEN`) load
exclusively from `.env` via the existing `mistapi.APISession` constructor;
they are never collected interactively.

**Rationale**: `org_id` is the universal MistHelper identifier and has a
documented `.env` default for ergonomic single-org operation. `upgrade_id`
is opaque to the user (server-generated UUID) and has no sensible
default, so the prompt explicitly directs the user to the related menu
item (`listOrgDeviceUpgrades`) that surfaces the available IDs. Both
prompts wrap `safe_input()` per Principle III so SSH and container EOF
exits return code 0 without a Python traceback.

**Alternatives Considered**:
1. Auto-select the most recent in-progress upgrade by calling
   `listOrgDeviceUpgrades` first. Rejected for the initial scope --
   couples two endpoints into one menu item and complicates the
   acceptance criteria; a follow-up "interactive picker" menu can be
   added later if user demand emerges.
2. Accept the upgrade ID as a CLI argument only (no interactive prompt).
   Rejected -- breaks the menu-driven UX promised by the spec User
   Story 1 and is inconsistent with adjacent menu items.
