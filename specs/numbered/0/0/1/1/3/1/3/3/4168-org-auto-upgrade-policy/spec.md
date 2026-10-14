# Feature Specification: Organization Auto-Upgrade Policy

**Feature Branch**: `jmorrison-juniper-org-auto-upgrade-settings`

**Created**: 2026-10-13

**Status**: Implemented. Local validation passed. Deployment remains pending.

**Input**: User description: "use the speckit skill to come up with a new menu option number that does two jobs:

1: clears all current site-level auto upgrade settings and sets them to to use the org settings

2: sets new org-wide auto upgrade settings per model.

we can resuse the flow and menus from menu option 168.

we DONT want to trigger real live firmware pushes, just sets the versions and the time of auto-upgrades(if applicable to the hw-type)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Apply Organization Firmware Standards (Priority: P1)

An administrator sets organization firmware standards by model for access points, switches, SSR devices, and SRX devices.

**Why this priority**: Organization standards define the target versions that sites inherit.

**Independent Test**: Set standards for one organization and verify the saved model values and AP schedule.

**Acceptance Scenarios**:

1. **Given** an administrator selects an organization, **When** the administrator sets model versions for AP, switch, SSR, and SRX devices, **Then** Mist stores those values as organization settings.
2. **Given** the administrator configures AP settings, **When** the administrator enters a schedule, **Then** Mist stores the selected day and time with the AP policy.
3. **Given** the administrator configures switch, SSR, or SRX settings, **When** the administrator reviews the schedule fields, **Then** the feature does not request a schedule that the device type does not support.
4. **Given** an MSP administrator selects multiple organizations, **When** the administrator confirms the shared policy, **Then** the feature applies the selected model values to each selected organization.

### User Story 2 - Restore Site Inheritance (Priority: P1)

An administrator removes each AP, switch, SSR, and SRX site-level auto-upgrade override so each site uses its organization policy.

**Why this priority**: A site override can prevent the organization standard from taking effect.

**Independent Test**: Start with sites that have different local auto-upgrade overrides, run the feature, and verify that each site inherits the organization policy.

**Acceptance Scenarios**:

1. **Given** selected organizations contain sites with local AP, switch, SSR, or SRX auto-upgrade settings, **When** the administrator confirms the change, **Then** the feature clears those settings for every site in those organizations.
2. **Given** the site has unrelated settings, **When** the feature clears its auto-upgrade override, **Then** those unrelated settings remain unchanged.
3. **Given** the administrator cancels before confirmation, **When** the workflow ends, **Then** no site or organization settings change.

### User Story 3 - Preview a Safe Configuration Change (Priority: P1)

An administrator previews the full change and applies it only after a typed confirmation.

**Why this priority**: Configuration changes can affect future firmware rollouts across many sites.

**Independent Test**: Run a dry run and a cancelled run, then verify that no Mist settings changed and no firmware upgrade began.

**Acceptance Scenarios**:

1. **Given** the administrator starts a dry run, **When** the workflow completes, **Then** it reports the organizations, sites, model versions, and applicable schedule without changing Mist settings.
2. **Given** the administrator reviews the change, **When** the administrator does not enter the required confirmation word, **Then** the workflow makes no change.
3. **Given** the administrator confirms a change, **When** the workflow applies settings, **Then** it saves configuration without starting an immediate firmware push.
4. **Given** a settings request fails, **When** the workflow reports its result, **Then** it identifies completed and failed work and does not report full success.

### Edge Cases

- An organization has no sites. The workflow reports that no site overrides need clearing.
- A model has no available version. The workflow does not apply an incomplete policy.
- A site or organization settings read fails. The workflow stops before changing that organization.
- An organization update succeeds but a site update fails. The workflow reports the partial result and does not report completion.
- An organization has existing settings outside the firmware policy. The workflow preserves them.
- The operator cancels during organization or MSP selection. The workflow makes no changes.
- A selected MSP organization has no available model versions. The workflow reports the organization and stops its update.
- The dry-run flag is set. No settings write or firmware upgrade request occurs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST register the new operation as menu 305, the first unused menu number after registered menu 304.
- **FR-002**: The system MUST reuse menu 168's organization and MSP selection flow.
- **FR-003**: The system MUST let an administrator set AP, switch, SSR, and SRX firmware versions by model for each selected organization.
- **FR-004**: The system MUST let an administrator set the AP auto-upgrade day and time.
- **FR-005**: The system MUST NOT request a schedule for switch, SSR, or SRX settings when the organization settings schema has no schedule fields for those device types.
- **FR-006**: The system MUST clear the AP, switch, SSR, and SRX site-level auto-upgrade overrides on every site in each selected organization.
- **FR-007**: The system MUST preserve settings outside the firmware policies that the administrator changes.
- **FR-008**: The system MUST show the target organizations, affected sites, selected model versions, and applicable schedule before it changes settings.
- **FR-009**: The system MUST require a typed confirmation before it changes Mist settings.
- **FR-010**: The system MUST support a dry run that reports the planned changes and performs no settings writes.
- **FR-011**: The system MUST save firmware policy and schedule settings only. It MUST NOT start an immediate firmware upgrade or device push.
- **FR-012**: The system MUST stop before changing an organization when required settings or version data cannot be read.
- **FR-013**: The system MUST report partial completion when one or more settings changes succeed and a later change fails.
- **FR-014**: The system MUST report the number of organizations and sites that it examined and the result of each settings change.
- **FR-015**: The system MUST classify this operation as destructive because it changes production cloud settings.
- **FR-016**: The system MUST save and verify the organization policy before it removes site overrides.
- **FR-017**: The system MUST warn that enabled policies can cause later cloud-managed upgrades, even though this menu sends no upgrade request.
- **FR-018**: The system MUST require an explicit enabled or disabled choice for each selected device type. It MUST NOT enable a policy by default.
- **FR-019**: The system MUST let the operator choose supported device types. It MUST preserve unselected organization policies while removing all supported local site overrides.
- **FR-020**: Before any change, the system MUST save each selected organization's complete settings and verify that the backup matches the original.
- **FR-021**: Before any change, the system MUST save every target site's complete settings and verify that each backup matches the original.
- **FR-022**: If any backup write, backup read, or backup comparison fails, the system MUST make zero settings changes.
- **FR-023**: The system MUST provide a complete graphical workflow in the existing numbered-menu operations portal, with dynamic organization, model, and version controls.
- **FR-024**: The portal MUST provide preview, dry run, typed confirmation, backup results, and partial-result reports without using the generic safe-operation execution path.
- **FR-025**: The system MUST protect full settings backups from portal file listing, preview, and download because settings can contain credentials.

### Mist Cloud Transport Requirements

- The implementation MUST use `mistapi.api.v1.orgs.setting.getOrgSettings` and `mistapi.api.v1.orgs.setting.updateOrgSettings` to read and write organization settings.
- The implementation MUST use `mistapi.api.v1.sites.setting.getSiteSetting` and `mistapi.api.v1.sites.setting.updateSiteSettings` to read and clear site auto-upgrade settings.
- The implementation MUST use `mistapi.api.v1.orgs.devices.listOrgAvailableDeviceVersions` and `mistapi.api.v1.orgs.ssr.listOrgAvailableSsrVersions` when those methods provide the required model versions.
- Contract tests MUST verify SDK authentication, endpoint parity, preservation of unrelated settings, failure handling, and secret redaction.
- Contract tests MUST prove that dry-run and confirmed configuration changes do not call any firmware upgrade method.

### Key Entities *(include if feature involves data)*

- **Organization firmware policy**: AP, switch, SSR, and SRX version values by model, with any supported policy controls.
- **Site auto-upgrade override**: A site-level AP, switch, SSR, or SRX setting that can replace an organization policy.
- **Upgrade schedule**: The AP policy day and time. Switch, SSR, and SRX schedules are excluded unless the API schema adds support.
- **Configuration preview**: The organizations, sites, versions, and schedule that the administrator reviews before confirmation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every site in each selected organization has no local AP, switch, SSR, or SRX auto-upgrade override after a successful run.
- **SC-002**: Each selected organization stores the chosen firmware version for every configured model.
- **SC-003**: The preview lists every selected organization and every site whose local override will change.
- **SC-004**: Dry-run and cancelled executions make zero settings changes and zero firmware upgrade requests.
- **SC-005**: A successful run preserves every unrelated organization and site setting that the feature does not target.
- **SC-006**: A failed settings update produces a clear partial-result report and never produces a full-success result.
- **SC-007**: Every organization and site backup matches its complete original settings before the first settings write.
- **SC-008**: A failed backup produces zero Mist settings changes.
- **SC-009**: An operator can complete selection, preview, confirmation, and result review through graphical controls without terminal input.

## Assumptions

- Menu 305 is available because the registry currently ends at menu 304. The existing gap at menu 152 remains unchanged.
- Feature record 4168 is the next numeric specification record. Its route uses the required eight-level base-5 path.
- The supported organization policy types are AP, switch, SSR, and SRX because the current API schema defines auto-upgrade settings for these types.
- The AP policy supports a day and time. The switch, SSR, and SRX policy schemas do not define schedule fields.
- SSR and SRX auto-upgrade settings apply when a device is first onboarded.
- An MSP multi-organization run applies the selected shared model values to each selected organization, following menu 168's multi-organization flow.
- The operation clears local site overrides for every site in each selected organization. It does not offer a partial site selection.
- A settings change affects future policy behavior only. This feature does not run a firmware upgrade.
- The operations portal means the existing numbered-menu portal on port 8055. The separate React application does not run numbered operations.
- Full settings backups can contain credentials. They remain in private ignored local storage, never in logs or browser responses.
