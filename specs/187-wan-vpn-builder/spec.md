# Feature Specification: Menu 164 - WAN Hub-Spoke VPN Builder

**Feature Branch**: `187-wan-vpn-builder`
**Created**: 2025-04-22
**Status**: Clarified
**Input**: User description: "Menu 164 - WAN Hub-Spoke VPN Builder: Create new hub-spoke VPN overlay definitions from scratch by fetching gateway device profiles, selecting hub/spoke roles, auto-generating VPN path keys from WAN/LAN interfaces, assigning pod numbers, and creating the VPN via API"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a Hub-Spoke VPN from Gateway Profiles (Priority: P1)

A network engineer needs to create a new hub-spoke VPN overlay definition in Mist Cloud. They launch Menu 164, provide a VPN name, review the list of gateway device profiles in the org, assign hub or spoke roles to selected profiles, review the auto-generated VPN paths and pod numbers, confirm, and the VPN is created via API.

**Why this priority**: This is the core value proposition — automating VPN creation that currently requires tedious manual entry in the Mist Dashboard. Without this, the feature has no purpose.

**Independent Test**: Can be tested by running `--menu 164`, entering a VPN name, selecting profiles as hub/spoke, confirming the preview, and verifying the VPN appears in the org's VPN list via API.

**Acceptance Scenarios**:

1. **Given** an org with 3+ gateway device profiles, **When** the user selects 1 hub and 2 spokes and confirms, **Then** the VPN is created with correct path keys derived from each profile's WAN/LAN interface names and appropriate pod numbers.
2. **Given** an org with existing VPNs, **When** the user enters a name that duplicates an existing VPN, **Then** the system rejects the name and prompts for a different one.
3. **Given** a hub profile with 3 WAN interfaces (WAN1, WAN2, 5G), **When** the VPN is built, **Then** cross-connect paths are generated for each WAN interface to every other WAN suffix (e.g., WAN1-WAN1, WAN1-WAN2, WAN1-5G, WAN1 direct).
4. **Given** a hub profile with LAN interfaces (LAN1, LAN2), **When** the VPN is built, **Then** LAN interfaces generate direct paths only (no cross-connects).
5. **Given** a spoke profile with WAN and LAN interfaces, **When** the VPN is built, **Then** only direct paths are generated (one per interface, no cross-connects).
6. **Given** the user is reviewing the VPN preview, **When** they decline confirmation, **Then** no API call is made and the operation exits cleanly.

---

### User Story 2 - Update Device Profile vpn_paths After VPN Creation (Priority: P2)

After creating the VPN, the engineer optionally updates each selected gateway profile's `port_config` to reference the new VPN's paths in the `vpn_paths` field. This saves them from manually editing each profile in the Dashboard.

**Why this priority**: This completes the end-to-end workflow. Creating the VPN without linking it to profiles still requires manual Dashboard work. However, the VPN creation itself (P1) is independently valuable.

**Independent Test**: Can be tested by creating a VPN (P1), then accepting the prompt to update profiles, and verifying each profile's `port_config` entries have correct `vpn_paths` referencing the new VPN.

**Acceptance Scenarios**:

1. **Given** a VPN was just created with 2 hub profiles, **When** the user opts to update profiles, **Then** each hub profile's WAN/LAN ports in `port_config` are updated with `vpn_paths` entries using format `{PathName}.{VPNName}` and `role: "hub"`.
2. **Given** a VPN was just created with spoke profiles, **When** the user opts to update profiles, **Then** each spoke profile's ports are updated with `vpn_paths` entries using `role: "spoke"`.
3. **Given** the user declines the profile update prompt, **When** the operation completes, **Then** no device profiles are modified and the user sees a success message for VPN creation only.
4. **Given** a profile update fails for one profile, **When** the operation continues, **Then** the failure is logged with context, remaining profiles are still attempted, and a summary shows which updates succeeded and which failed.

---

### User Story 3 - Review Existing VPNs Before Creating (Priority: P3)

Before creating a new VPN, the engineer can view a summary of existing VPNs in the org to understand the current state and avoid naming conflicts or configuration overlap.

**Why this priority**: Informational context that prevents mistakes. Not strictly required for VPN creation but improves the user experience and reduces errors.

**Independent Test**: Can be tested by running Menu 164 in an org with existing VPNs and verifying the list displays names, types, and path counts before prompting for a new VPN name.

**Acceptance Scenarios**:

1. **Given** an org with 3 existing VPNs, **When** Menu 164 launches, **Then** a summary table shows VPN name, type, and number of paths for each.
2. **Given** an org with 0 VPNs, **When** Menu 164 launches, **Then** a message indicates no existing VPNs and proceeds to the creation flow.

---

### Edge Cases

- What happens when the org has 0 gateway device profiles? The system displays a message ("No gateway device profiles found") and exits gracefully.
- What happens when a profile has 0 WAN interfaces? The profile generates no cross-connect paths. Only LAN direct paths (if any) are generated. The user is warned.
- What happens when a profile has only LAN interfaces and no WAN interfaces? Direct LAN paths are generated but no cross-connects. A warning is shown that no WAN paths exist for this profile.
- What happens when the user assigns all profiles as "Skip"? The system warns that no profiles are selected and prompts again or exits.
- What happens when a pod number is out of range (not 1-128)? The system rejects the value and re-prompts.
- What happens when the API call to create the VPN fails? The error is displayed with context, no profile updates are attempted, and the user can retry or exit.
- What happens when the user's session disconnects mid-operation (EOF)? The `safe_input()` wrapper catches EOF and exits cleanly with a log message.
- What happens when a profile name contains special characters? The system uses the profile name as-is for path key generation (Mist API accepts them).

## Clarifications

### Session 2025-04-22

- Q: What confirmation pattern for destructive VPN creation and profile updates? → A: `CREATE` typed confirmation for VPN creation (FR-007); simple `yes/no` prompt for optional profile updates (FR-009). Profile updates are secondary and individually reversible.
- Q: What are the practical scale limits for profiles and paths? → A: Up to 50 gateway profiles per org (typical: 1-20). Path count grows combinatorially with hub cross-connects; warn if generated paths exceed 500 (display count in preview).
- Q: What is explicitly out of scope? → A: Mesh VPN creation, custom path_selection strategies beyond `simple`, editing/deleting existing VPNs, modifying non-port_config profile settings, bulk operations across multiple orgs.

## Non-Goals *(out of scope)*

- Mesh VPN creation (only hub-spoke)
- Custom `path_selection` strategies beyond `{"strategy": "simple"}`
- Editing or deleting existing VPN definitions
- Modifying device profile settings outside of `port_config`
- Bulk operations across multiple orgs
- Network/service policy creation alongside VPN creation

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch all gateway device profiles from the org and display them in a numbered list showing profile name, WAN interface count, and LAN interface count.
- **FR-002**: System MUST allow the user to assign each profile as "Hub", "Spoke", or "Skip".
- **FR-003**: For hub profiles, system MUST generate cross-connect path keys for each WAN interface to every WAN suffix across all selected profiles, plus a direct path per WAN interface, plus direct paths for each LAN interface.
- **FR-004**: For spoke profiles, system MUST generate direct path keys only (one per WAN and LAN interface, no cross-connects).
- **FR-005**: System MUST assign pod numbers per profile (valid range 1-128), auto-suggesting based on profile naming patterns when possible, with user override capability.
- **FR-006**: System MUST validate the VPN name is non-empty and unique within the org before proceeding.
- **FR-007**: System MUST display a preview of the complete VPN definition (name, type, all paths with pod numbers and total path count) and require the user to type `CREATE` to proceed. Any other input cancels.
- **FR-008**: System MUST create the VPN via the Mist API and report success with the returned VPN ID.
- **FR-009**: System MUST optionally update each selected profile's `port_config` WAN/LAN entries with `vpn_paths` referencing the new VPN, using format `{PathName}.{VPNName}`. Prompt is a simple `yes/no` confirmation.
- **FR-010**: System MUST use `safe_input()` for all user input and handle EOF gracefully.
- **FR-011**: System MUST list existing org VPNs at the start of the operation for reference.
- **FR-012**: System MUST follow the `execute()` static entry point pattern with dependency injection, consistent with existing modules.

### Key Entities

- **VPN Definition**: A hub-spoke VPN overlay with a name, type (`hub_spoke`), paths dictionary, and path selection strategy. Created at the org level.
- **Gateway Device Profile**: An org-level profile defining a gateway device's port configuration, including WAN and LAN interface names. Each profile can be assigned a hub or spoke role in the VPN.
- **VPN Path**: A named entry in the VPN's `paths` dictionary. Key format: `{PROFILE_NAME}-{INTERFACE_NAME}` for direct paths, or `{PROFILE_NAME}-{INTERFACE_NAME}-{PEER_SUFFIX}` for cross-connect paths. Each path has a pod number.
- **vpn_paths Reference**: An entry in a device profile's `port_config` that links a port to a VPN path. Key format: `{PathName}.{VPNName}`. Contains a `role` (hub/spoke) and optionally a `key` index for cross-connect ordering.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Engineers can create a hub-spoke VPN with 5 gateway profiles (mix of hub/spoke) in under 5 minutes, compared to 20+ minutes via the Mist Dashboard.
- **SC-002**: All generated path keys match the naming convention used by the Mist Dashboard, ensuring compatibility with existing VPN configurations.
- **SC-003**: 100% of VPN creations via Menu 164 produce valid VPN definitions that are accepted without error.
- **SC-004**: Profile vpn_paths updates correctly link all WAN/LAN ports to the new VPN with appropriate roles (hub/spoke) and cross-connect keys.
- **SC-005**: Unit test coverage for the VPN builder meets or exceeds 70%.

## Assumptions

- The Mist org has at least one gateway device profile for the operation to be useful. The system handles 0 profiles gracefully.
- Path selection strategy defaults to `{"strategy": "simple"}`. Custom strategy selection is out of scope for this feature.
- Pod number auto-suggestion extracts numbers from profile names using regex patterns (e.g., `VREPOL69` -> pod 69). If no number is found, sequential assignment starting from 1 is used.
- Cross-connect "peer suffixes" are derived by stripping the profile-specific prefix from WAN interface names (e.g., `HE_WAN1` -> peer suffix `WAN1`; `HE_5G` -> peer suffix `5G`). The suffix set is the union of all WAN interface suffixes across all selected profiles.
- The `key` field in `vpn_paths` entries for cross-connect paths uses 0-based sequential indexing within each port's vpn_paths.
- When updating device profiles, only `port_config` is modified; other profile settings are preserved.
- The VPN `type` is always `hub_spoke` for this operation. Mesh VPN creation is out of scope.
- This is a destructive operation (creates/modifies cloud configuration) and follows the project's confirmation patterns.
