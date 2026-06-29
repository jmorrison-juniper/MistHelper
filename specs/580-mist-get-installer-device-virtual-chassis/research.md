# Phase 0 Research: getInstallerDeviceVirtualChassis

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Authoritative endpoint reference**: `documentation/api/installer/GET_installer_orgs_org_id_devices_fpc0_mac_vc.md`

## Research Task 1: SDK function signature & behavior

**Decision**: Invoke the endpoint through the `mistapi` SDK module
`mistapi.api.v1.installer.orgs.devices.vc` (path-aligned module, matching the spec's
declared module path), calling
`getInstallerDeviceVirtualChassis(apisession, org_id, fpc0_mac)`. The call returns a
`mistapi.APIResponse` whose `.data` attribute is a single JSON object containing the
combined VC topology and per-member runtime stats.

**Rationale**: The enriched endpoint reference at
`documentation/api/installer/GET_installer_orgs_org_id_devices_fpc0_mac_vc.md` confirms
the HTTP contract is `GET /api/v1/installer/orgs/{org_id}/devices/{fpc0_mac}/vc` with
two required path parameters (`org_id` UUID, `fpc0_mac` 12-hex MAC), no query
parameters, no request body, and a single non-paginated 200 response. The mistapi SDK
exposes the function under the path-aligned module per the spec.md "mistapi SDK module"
field; the enriched doc's alternate alias
(`mistapi.api.v1.installer.installer.getInstallerDeviceVirtualChassis()`) reflects the
tag-grouped re-export that mistapi sometimes provides, but the path-aligned module is
the canonical and stable import path used elsewhere in MistHelper.

**Alternatives Considered**:

- Direct `requests`-based HTTP call: Rejected. Violates the project rule that mistapi is
  the sole permitted interface to the Mist Cloud (constitution: Technology &
  Compatibility Constraints). Loses adaptive delay metrics, retry, and session reuse.
- Tag-grouped import (`mistapi.api.v1.installer.installer`): Rejected as primary. The
  doc's "mistapi SDK" line uses the tag-grouped alias which historically has been less
  stable across mistapi releases; the path-aligned module declared in spec.md is the
  contract MistHelper standardizes on across all 580+ catalogued endpoints.

## Research Task 2: Primary Key Strategy

**Decision**: Use **composite_pk** for both output tables:

- `installer_device_vc_summary`: primary_key `['id']` (the VC chassis UUID returned in
  the top-level `id` field).
- `installer_device_vc_members`: primary_key `['vc_id', 'fpc_idx']` where `vc_id` is
  the parent chassis UUID and `fpc_idx` is the integer slot index of the member in the
  stack.

**Rationale**: The top-level response object carries `id` (UUID, marked readOnly), which
is the stable Mist-assigned chassis identifier and qualifies as a natural primary key.
However, the response contains a `members` array where each element has its own runtime
stats; flattening that array produces N child rows per parent, and each member's
`fpc_idx` is the natural slot index that uniquely identifies it within the chassis.
Composite (vc_id, fpc_idx) gives idempotent upserts when the user re-runs the menu to
refresh runtime data (CPU, memory, fan, PoE stats) without spawning duplicate rows.
Both tables therefore qualify as composite_pk under the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` schema, with the summary table being the degenerate
single-column case.

**Alternatives Considered**:

- `natural_pk` with `['id']` only and storing `members` as a single JSON blob column:
  Rejected. Loses the ability to query individual member health (CPU, temperatures,
  PoE) from SQL without JSON_EXTRACT gymnastics; defeats the value of the SQLite
  backend.
- `auto_increment_with_unique`: Rejected. The Mist API supplies stable natural
  identifiers (`id`, `fpc_idx`); synthesizing an autoincrement key would needlessly
  re-duplicate rows on every refresh and break the no-duplicate acceptance criterion in
  spec.md.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV summary file: `data/installer_device_vc_summary_<org_id>_<fpc0_mac>.csv`
- CSV members file: `data/installer_device_vc_members_<org_id>_<fpc0_mac>.csv`
- SQLite table names (created by `DataExporter`): `installer_device_vc_summary` and
  `installer_device_vc_members`.

**Rationale**: The filename pattern `<entity>_<scope_ids>.csv` matches the existing
convention used by adjacent menu items (e.g. site-scoped device exports include
`<site_id>` in the filename). Including both `org_id` and `fpc0_mac` in the filename
avoids overwriting prior runs for different chassis when a NOC engineer is comparing
multiple stacks. SQLite table names omit the scope IDs because rows are differentiated
by their primary key columns (the table is meant to accumulate data across many runs
and many chassis). The `installer_` prefix mirrors the API path's Installer scope and
disambiguates from the admin-scope VC tables that the existing menu 92-94 cluster
populates.

**Alternatives Considered**:

- Single combined file with members embedded as JSON: Rejected. Breaks CSV
  consumability; one of the main user values of the CSV backend is opening the file in
  Excel for triage.
- Append-only timestamped filenames (`..._YYYYMMDDHHMMSS.csv`): Rejected. The user-
  facing value is "current state of this VC"; historical snapshots are better served
  by the SQLite backend's row-level timestamp columns (added by DataExporter) than by
  filesystem clutter.

## Research Task 4: Menu category placement and next available menu number

**Decision**: Menu number **96**, placed at the tail of the **Interactive Safe (60-96)**
cluster, immediately after the existing VC viewers at menu 92-94.

**Rationale**: The MistHelper menu taxonomy documented in
`.github/copilot-instructions.md` reserves 60-96 for interactive safe operations
including "Site devices (60-72)", "Insights (73-79)", "Stats (80-91)", and "Viewers
(92-96)". Menu 92-94 already hosts the admin-scope VC viewers, and the enriched
endpoint doc's "MistHelper Notes" section explicitly cross-references that cluster. Op
96 keeps the installer-scope VC read visually adjacent to its admin-scope siblings so a
NOC engineer doing VC triage finds all VC-related reads in one neighborhood. Op 96 is
the highest slot in the Viewers sub-cluster and is the safest pick before the resource-
intensive block at 97-101.

**Alternatives Considered**:

- Place in the 60-72 Site devices sub-cluster: Rejected. Those operations are
  site-scoped reads; this endpoint is org-scoped under the Installer permission tree
  and does not require a site_id.
- Create a new "Installer" category at 195+: Rejected. The 154-194 block is reserved
  for destructive operations; placing a read-only installer read above the destructive
  block would break the "safe before destructive" ordering principle that protects
  junior NOC engineers from accidental selection.
- Append at the very end (op 195): Rejected for the same destructive-boundary reason.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: Two prompts via `safe_input()`:

1. `org_id` -- default sourced from `.env` (`MIST_ORG_ID`); user may press Enter to
   accept the default or type a different UUID to override.
2. `fpc0_mac` -- always prompted (no `.env` default); the user must supply the FPC0
   MAC of the VC they want to inspect. Input is normalized to lowercase, separators
   stripped, then validated as 12 hex characters before the API call.

API token (`MIST_API_TOKEN`) and host (`MIST_HOST`) come from `.env` via the existing
`mistapi.APISession` factory; they are never prompted and never logged.

**Rationale**: Org ID benefits from a default because most MistHelper users operate
against one primary org; making it Enter-to-accept matches the UX of adjacent menu
items (e.g. menu 92-94). FPC0 MAC has no sensible default -- it identifies a specific
switch stack, and any default would risk pulling data from the wrong chassis. MAC
normalization (lowercase, no separators) matches the canonical form the Mist API
expects and accepts whatever notation the user types (colons, dashes, dots, or none).
Validation before the SDK call satisfies the Safety-First principle by surfacing
malformed input as a logged warning instead of a 400 traceback from the SDK.

**Alternatives Considered**:

- Prompt for `fpc0_mac` with a default from `.env`: Rejected. There is no single "the"
  FPC0 MAC for an org; defaulting would encourage misuse.
- Auto-discover the FPC0 MAC by listing org devices first: Rejected for v1. Would
  multiply the API call count, contradict the "single GET <=5s" performance goal in
  the spec, and turn a simple read into a two-step interactive flow. A follow-up
  feature can add a "pick from list" affordance once the basic read is in production.
- Skip prompting entirely and rely on `--menu 96 --org-id ... --fpc0-mac ...` CLI args:
  Rejected as the sole input path. CLI args will be supported for `--test` automation,
  but interactive prompts via `safe_input()` remain the primary UX per the spec.
