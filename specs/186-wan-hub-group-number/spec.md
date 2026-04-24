# Feature Specification: WAN Hub Group Number Manager

**Feature Branch**: `186-wan-hub-group-number`
**Created**: 2025-04-22
**Status**: Draft — Clarified (Sessions 2025-07-16, 2025-07-17)
**Input**: User description: "Build a new menu feature for managing WAN Hub Profile group numbers. Query all WAN Hub Profiles (device profiles of type gateway), display alphabetized list for user selection, then prompt to set or clear the WAN Hub Group Number. First menu option to reference code outside the monolithic MistHelper script."

## Clarifications

### Session 2025-07-16

- Q: Is the "WAN Hub Group Number" the `pod` field (int 1-128, default 1) on VPN path objects within Org VPN definitions (`hub_spoke` type)? → A: Yes — the `pod` field on VPN paths is the target field. No `group_number` field exists in the Mist API.
- Q: Should the workflow list VPN paths after profile selection to let the user choose which path's pod to modify? → A: Yes — after selecting a gateway device profile, the system lists associated `hub_spoke` VPN paths showing current pod values, then the user selects which path to modify. *(Superseded by Session 2025-07-17: batch-update all matching paths; individual path selection removed.)*
- Q: What does "clear" mean for the pod field given it has a default of 1 (not nullable)? → A: Clearing resets the pod value to the default (1). The pod field always has a value; "clear" means "reset to default."
- Q: Should the system show VPNs of type `mesh` or only `hub_spoke`? → A: Only `hub_spoke` VPNs — the `pod` field is semantically meaningful only for hub-spoke topologies.

### Session 2025-07-17 (Real API Data Review)

- Q: All VPN paths for a given device profile share the same pod value (~10 paths per profile). Should the system batch-update all paths at once or let the user pick individual paths? → A: Batch-update all matching paths to the same pod value. Individual path selection is unnecessary since all paths per device share the same pod.
- Q: VPN path names follow `{DeviceProfileName}-{PortName}` pattern (e.g., `VREIRV65-HE_WAN1`). Should the system use prefix matching to find paths related to a selected device profile? → A: Yes — match VPN path keys that start with `{selected_profile_name}-` to find all related paths.
- Q: Should the profile listing step show each profile's current pod value (by cross-referencing VPN data)? → A: Yes — display current pod next to each profile name in the alphabetized list for immediate visibility.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View and Select a WAN Hub Profile (Priority: P1)

A NOC engineer needs to view all WAN Hub Profiles in their Mist organization so they can identify which hub profile to modify. The system queries the Mist API for all device profiles of type `gateway`, displays them in an alphabetized numbered list, and allows the user to select one by number.

**Why this priority**: This is the foundational interaction -- without listing and selecting a hub profile, no subsequent operations are possible. This also establishes the first external module pattern outside MistHelper.py.

**Independent Test**: Can be fully tested by running the menu option, verifying the API call retrieves gateway device profiles, and confirming the alphabetized list displays correctly with selectable indices.

**Acceptance Scenarios**:

1. **Given** an authenticated Mist API session with an organization containing 5 gateway device profiles, **When** the user selects the WAN Hub Group Number menu option, **Then** all 5 profiles are displayed in alphabetical order with numbered indices starting at 1.
2. **Given** the alphabetized profile list is displayed, **When** the user enters a valid index number, **Then** the selected profile name and ID are confirmed back to the user.
3. **Given** the alphabetized profile list is displayed, **When** the user enters an invalid index (0, negative, or beyond list length), **Then** an error message is shown and the user is prompted to try again or cancel.
4. **Given** an organization with zero gateway device profiles, **When** the user selects this menu option, **Then** a clear message states no hub profiles were found and the operation exits gracefully.

---

### User Story 2 - Set the WAN Hub Group Number on a Profile (Priority: P1)

After selecting a hub profile, the NOC engineer needs to set (or update) the WAN Hub Group Number (the `pod` field on VPN paths). The system displays the current pod value and the count of matching VPN paths (matched by `{ProfileName}-` prefix in path keys), prompts for a new value, confirms the change, and batch-updates ALL matching paths in the VPN object via the API.

**Why this priority**: Setting the group number is one of the two core actions requested. Combined with User Story 1, this delivers the primary use case.

**Independent Test**: Can be tested by selecting a profile, verifying the correct number of matching paths are found via prefix matching, entering a new pod value, and verifying the API update call sets the same pod value on all matching paths. Verify the updated values are reflected when re-querying the VPN.

**Acceptance Scenarios**:

1. **Given** a selected hub profile "VREIRV65" associated with 10 hub_spoke VPN paths (all prefixed `VREIRV65-`), where current pod is 65, **When** the user enters a new pod of 42, **Then** the system batch-updates all 10 paths to pod=42 via `updateOrgVpn` (one call per VPN object) and confirms "Updated 10 paths in OrgOverlay to pod 42."
2. **Given** a selected hub profile with VPN paths at default pod (1), **When** the user enters a valid pod number (e.g., 5), **Then** the system updates all matching paths and confirms the new value.
3. **Given** a selected hub profile, **When** the user enters an invalid value (non-numeric, 0, negative, or >128), **Then** an error message is shown with the valid range (1-128) and the user is reprompted.

---

### User Story 3 - Clear the WAN Hub Group Number from a Profile (Priority: P1)

After selecting a hub profile, the NOC engineer needs to clear (remove) the WAN Hub Group Number, resetting the `pod` field to its default value of 1 on ALL matching VPN paths. The system confirms the clearing action before executing the batch update.

**Why this priority**: Clearing the group number is the other core action requested. Together with Stories 1 and 2, this completes the full feature.

**Independent Test**: Can be tested by selecting a profile that has a pod value set on its VPN paths, choosing the clear option, and verifying the API update resets `pod` to 1 on all matching paths. Verify the cleared state when re-querying.

**Acceptance Scenarios**:

1. **Given** a selected hub profile "VREIRV65" with 10 VPN paths whose `pod` is 65, **When** the user chooses to clear the group number, **Then** the system confirms "Reset pod from 65 to default (1) on 10 paths in OrgOverlay?" and upon confirmation batch-updates all paths.
2. **Given** a selected hub profile with all VPN paths whose `pod` is already the default (1), **When** the user chooses to clear the group number, **Then** the system informs the user that the pod is already at the default value and no action is needed.

---

### User Story 4 - External Module Architecture (Priority: P2)

This menu option establishes the pattern for moving functionality out of the monolithic MistHelper.py into separate modules under `src/`. The implementation must be importable by MistHelper.py and follow the project's class-based design conventions.

**Why this priority**: While not user-facing, this architectural milestone enables future menu operations to be developed as external modules, reducing the size of the monolith. It is secondary to the functional requirements.

**Independent Test**: Can be tested by verifying the new module imports correctly, the class instantiates without errors, and MistHelper.py can call it via a clean interface without duplicating API session management or utility functions.

**Acceptance Scenarios**:

1. **Given** the new module exists under `src/`, **When** MistHelper.py imports and calls it for the menu operation, **Then** the operation executes identically to if it were defined inline in MistHelper.py.
2. **Given** the new module, **When** it needs API access, org_id, or utility functions, **Then** it reuses existing MistHelper infrastructure (apisession, ConfigUtils, DataExporter) without duplicating code.

---

### Edge Cases

- What happens when the API session token is expired or invalid during the VPN update?
- How does the system handle concurrent modifications to the same VPN object by another user? (Handled by API's last-write-wins semantics; no client-side locking implemented.)
- What happens if the API returns a rate limit error during the update call?
- What happens if the user's Mist account lacks write permissions to VPN objects?
- How does the system handle network timeout during the API update?
- What happens if a selected gateway device profile has no associated `hub_spoke` VPN paths (no path keys start with `{ProfileName}-`)?
- What happens if the organization has multiple `hub_spoke` VPN objects and a profile's paths span more than one? (System should update paths across all matching VPN objects.)
- What happens if a device profile name is a prefix of another profile name (e.g., "DC1" and "DC1-BACKUP")? (Prefix matching must use `{name}-` with trailing hyphen to avoid false matches.)
- What happens if the VPN paths for a profile have inconsistent pod values (e.g., some at 5, some at 1)? (Display a warning and still batch-update all to the new value.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST query the Mist API for all device profiles of type `gateway` in the current organization using `listOrgDeviceProfiles(org_id, type="gateway")`.
- **FR-001a**: System MUST also query Org VPNs using `listOrgVpns(org_id)` and filter to type `hub_spoke` during the listing step, to cross-reference each profile's current pod value for display.
- **FR-001b**: System MUST match VPN paths to device profiles using prefix matching: VPN path keys follow `{DeviceProfileName}-{PortName}` pattern (e.g., `VREIRV65-HE_WAN1`). Paths whose key starts with `{profile.name}-` belong to that profile.
- **FR-002**: System MUST display the retrieved profiles in an alphabetically sorted, numbered list showing profile name and current pod value (or "default (1)" if all matching paths have pod=1).
- **FR-003**: System MUST allow the user to select a profile by entering its displayed index number, with input validation for out-of-range or non-numeric entries.
- **FR-004**: After profile selection, system MUST display the current pod value and the count of matching VPN paths, then prompt the user to choose: (a) Set/update group number, (b) Clear group number (reset to default 1), or (c) Cancel.
- **FR-005**: System MUST validate the group number input against the range 1–128 (integer). The API field is `pod` on VPN path objects within Org VPN definitions (`/orgs/{org_id}/vpns/{vpn_id}`). Clearing resets `pod` to the default value of 1.
- **FR-005a**: System MUST batch-update ALL VPN paths matching the selected profile to the same pod value in a single API call per VPN object. Individual path selection is not offered because all paths per device share the same pod value.
- **FR-006**: System MUST use the `updateOrgVpn` API (via `mistapi.api.v1.orgs.vpns`) to persist `pod` changes on VPN path objects. The `updateOrgDeviceProfile` API is NOT used for this field.
- **FR-007**: System MUST confirm the operation result (success or failure) back to the user with clear messaging, including the number of paths updated and the VPN name.
- **FR-008**: The implementation MUST reside in a new module under `src/` (not inline in MistHelper.py), establishing the external module pattern for future menu operations.
- **FR-009**: The new module MUST reuse existing MistHelper infrastructure (API session, ConfigUtils, safe_input, logging) without duplicating these capabilities.
- **FR-010**: System MUST handle the case where no gateway device profiles exist in the organization with a clear message and graceful exit.

### Key Entities

- **WAN Hub Profile**: A Mist device profile of type `gateway` that configures hub behavior for WAN edge devices. Identified by `id` (UUID) and `name` (e.g., `VREIRV65`). Retrieved via `listOrgDeviceProfiles(type="gateway")`. Contains `port_config` with named ports (e.g., `HE_WAN1`, `HE_WAN2`, `HE_LAN1`, `HE_LAN2`) but `vpn_paths` in port_config is empty — actual pod values live in the Org VPN object.
- **Org VPN**: A VPN definition object at `/orgs/{org_id}/vpns` with `type` of `hub_spoke`. Contains `paths` — a dictionary where keys follow `{DeviceProfileName}-{PortName}` naming convention (e.g., `VREIRV65-HE_WAN1-WAN1`). An organization may have one or more VPN objects (e.g., "OrgOverlay"). Retrieved via `listOrgVpns(org_id)`.
- **VPN Path**: An entry in the Org VPN `paths` dictionary. Key format: `{DeviceProfileName}-{PortName}[-Suffix]`. Value contains `{"pod": <int>}`. All paths for a given device profile share the same pod value (~10 paths per profile, covering WAN/LAN port variants).
- **Pod (Group Number)**: The `pod` field on a VPN path object. Integer, range 1-128, default 1. Determines hub grouping for spoke connectivity within a hub-spoke VPN. Setting `pod` groups the hub; clearing resets to default (1). Real-world values observed: 61-89 range.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: NOC engineers can view all WAN Hub Profiles in their organization within 5 seconds of selecting the menu option.
- **SC-002**: NOC engineers can set or clear a hub group number in 3 or fewer interaction steps (select profile, choose action, confirm).
- **SC-003**: 100% of invalid inputs (out-of-range index, non-numeric group number) are caught and reported with actionable error messages before any API call is made.
- **SC-004**: The new external module pattern is established, reducing future menu operation additions from requiring MistHelper.py edits to requiring only a new module file plus a menu registration line.
- **SC-005**: All API errors (auth failure, rate limit, network timeout, permission denied) are caught and reported with user-friendly messages without crashing the application.

## Assumptions

- The Mist API session (`apisession`) is already authenticated and valid when this menu option is invoked (consistent with all existing menu operations).
- The `org_id` is available via `ConfigUtils.get_cached_or_prompted_org_id()` (existing pattern).
- Gateway device profiles returned by the API include all necessary fields for display (name, id).
- Org VPN definitions of type `hub_spoke` contain `paths` with `pod` fields that represent the "group number."
- VPN path keys follow `{DeviceProfileName}-{PortName}` naming convention. Prefix matching with `{profile.name}-` (trailing hyphen) reliably identifies paths belonging to a profile. **Confirmed with production data.**
- All VPN paths for a given device profile share the same pod value. Inconsistent values (if encountered) are treated as a warning condition but batch-update still proceeds. **Confirmed with production data.**
- A typical profile has ~10 VPN paths (WAN/LAN port variants with optional suffixes like `-WAN1`, `-WAN2`, `-5G`). **Confirmed with production data.**
- The external module will be placed under `src/` and imported by MistHelper.py using standard Python import mechanisms.
- The menu number for this operation is assigned as menu 163 (per plan.md).
- Error handling follows existing MistHelper patterns: log errors, display user-friendly messages, never crash.

## Non-Goals

- This feature does NOT modify gateway templates (only VPN path `pod` values).
- This feature does NOT manage VPN topology, spoke assignments, path preferences, or traffic shaping — it only modifies the `pod` field.
- This feature does NOT create or delete VPN definitions — it only updates existing VPN path pod values.
- This feature does NOT batch-update multiple profiles at once (single profile selection per invocation). However, all VPN paths for the selected profile ARE batch-updated to the same pod value.
- This feature does NOT provide a dry-run mode (setting/clearing a pod value is easily reversible).
- Full decomposition of MistHelper.py into external modules is out of scope -- this establishes the pattern only.

## Dependencies

- `mistapi` SDK v0.59+ (already installed) -- specifically `mistapi.api.v1.orgs.deviceprofiles` (listing hub profiles) and `mistapi.api.v1.orgs.vpns` (reading/updating VPN path `pod` values)
- Existing MistHelper infrastructure: `apisession`, `ConfigUtils`, `safe_input()`, logging
- Python 3.13+ (project requirement)
