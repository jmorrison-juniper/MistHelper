# Feature Specification: RMA Device Replacement

**Feature Branch**: `feat/3567-rma-device-replace`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 287 replace a device for an RMA with replaceOrgDevices. An RMA swap in the Mist UI keeps the site, the name, and the configuration of the old device. Mist offers replaceOrgDevices for the same step, and no MistHelper operation calls it. An operator who swaps by release and claim loses the configuration. The operation asks for the old device by MAC or name from the inventory, shows its site, name, model, and configuration summary, asks for the new device from unassigned inventory devices of the same type, writes a backup of the old device configuration to data/rma_backups/ before any replace request, asks the operator to type REPLACE, sends the replace request, and writes DeviceReplaceLog.csv."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Replace an RMA device safely (Priority: P1)

A NOC operator replaces a failed Mist inventory device with an unassigned replacement device. The operation keeps the old device site, name, and configuration through the Mist replacement API.

**Why this priority**: This is the core destructive workflow. It prevents configuration loss during an RMA swap.

**Independent Test**: Use mocked inventory, device configuration, and replace client calls. Verify selection, backup order, confirmation, request body, and log output without network access.

**Acceptance Scenarios**:

1. **Given** an old device and an unassigned replacement of the same type, **When** the operator types `REPLACE`, **Then** the operation backs up the old configuration before it sends the replace request.
2. **Given** an old device and a replacement of a different type, **When** the operation validates the replacement, **Then** it refuses the replacement and states both device types.
3. **Given** `--dry-run` is active, **When** the operator completes the prompts, **Then** the operation creates the backup and log but sends no replace request.

---

### User Story 2 - Select devices from inventory (Priority: P2)

A NOC operator selects the old device by MAC address or device name. The operator then selects a replacement from unassigned inventory devices of the same type.

**Why this priority**: Correct selection prevents an operator from moving a configuration to the wrong device.

**Independent Test**: Use pure model tests for device lookup, unassigned filtering, and type matching.

**Acceptance Scenarios**:

1. **Given** inventory records with MAC addresses and names, **When** the operator enters a MAC address or name, **Then** the operation resolves exactly one old device.
2. **Given** inventory records with site assignments, **When** replacement choices are built, **Then** only unassigned devices with the old device type appear.

---

### User Story 3 - Record operator evidence (Priority: P3)

A NOC operator receives durable evidence of the RMA operation. The evidence includes the backup file and `DeviceReplaceLog.csv`.

**Why this priority**: Operators need evidence for change records and support follow-up.

**Independent Test**: Use file-system tests under a controlled directory. Verify backup JSON and CSV fields.

**Acceptance Scenarios**:

1. **Given** a device configuration response, **When** the backup step runs, **Then** a JSON backup exists under `data/rma_backups/` before a replace request can run.
2. **Given** a replace result or a dry run, **When** the log step runs, **Then** `data/DeviceReplaceLog.csv` contains the old MAC, the new MAC, and the result.

### Edge Cases

- If the old device selector matches no device, the operation stops before backup and replacement.
- If the old device selector matches multiple device names, the operation asks for a more specific selector.
- If the new device is already assigned to a site, the operation refuses it.
- If the old device has no `site_id`, the operation refuses it because `getSiteDevice` needs a site.
- If backup writing fails, the operation sends no replace request.
- If the operator types any value except `REPLACE`, the operation sends no replace request.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The operation MUST register as menu `287` in the destructive category through the deferred wiring manifest.
- **FR-002**: The operation MUST read organization inventory with `getOrgInventory` and let the operator select the old device by MAC address or name.
- **FR-003**: The operation MUST show the selected old device site, name, model, type, MAC address, serial number, and configuration summary before replacement.
- **FR-004**: The operation MUST filter replacement choices to unassigned inventory devices with the same type as the old device.
- **FR-005**: The operation MUST refuse a replacement device whose type differs from the old device type and state both types.
- **FR-006**: The operation MUST write the old device configuration backup under `data/rma_backups/` before it sends any replace request.
- **FR-007**: The operation MUST require the operator to type `REPLACE` before it sends the replace request.
- **FR-008**: The operation MUST support `--dry-run` and send no replace request when dry-run mode is active.
- **FR-009**: The operation MUST send a request body that follows the `replaceOrgDevices` OpenAPI schema.
- **FR-010**: The operation MUST write `data/DeviceReplaceLog.csv` with the old MAC, the new MAC, and the result.
- **FR-011**: The operation MUST create `specs/3567-rma-device-replace/wiring.md` with each section required by the fleet contract.
- **FR-012**: The change MUST include `changelog.d/issue-3567-rma-device-replace.md` with an `Added` entry that names issue `#3567`.
- **FR-013**: Unit tests MUST prove each acceptance criterion without network access.

### Key Entities

- **InventoryDevice**: A Mist inventory record with `mac`, `serial`, `model`, `type`, `site_id`, `name`, and `inventory_id` fields.
- **DeviceConfigurationBackup**: A saved JSON file that contains the old device configuration, old device identifiers, and backup metadata.
- **ReplaceRequest**: The OpenAPI request body with the old device MAC address, the new device inventory ID, and a discard list.
- **DeviceReplaceLogEntry**: A CSV row with old device identity, new device identity, result, dry-run state, and backup file path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A mocked successful replacement sends exactly one replace request after the backup file exists.
- **SC-002**: A mismatched replacement type sends zero replace requests and returns an error that includes both types.
- **SC-003**: A dry run sends zero replace requests and writes a log row with result `dry_run`.
- **SC-004**: The request body test proves the exact OpenAPI field names for old MAC, new inventory ID, and discard list.
- **SC-005**: The wiring manifest and release note fragment exist in their assigned paths.

## Assumptions

- The operation runs after the integration pull request adds the menu entry and registry metadata.
- The new device is already claimed into organization inventory and is not assigned to a site.
- The Mist API keeps the old device site, name, and configuration during replacement.
- The first implementation uses a conservative empty discard list unless the operator flow later exposes discard choices.
- Tests use mocks and controlled files. They do not call the Mist cloud.
