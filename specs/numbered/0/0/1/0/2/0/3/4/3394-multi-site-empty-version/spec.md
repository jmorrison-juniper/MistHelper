# Feature Specification: Refuse a Checked Device Type With No Target Version

**Feature Branch**: `fix/3394-multi-site-empty-version`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue #3394, priority P1, bug. On the multi-site options page, a checked device type with an empty target version drops each device of that type from the plan. The save shows no message.

## User Scenarios & Testing *(mandatory)*

Each story is a self-contained slice. Each story has its own test. Terms follow the page: "checked device type", "target version", "target version control", "plan", and "selected site".

### User Story 1 - Refuse the save when a checked device type has no target version (Priority: P1)

An operator checks access points and switches. The operator sets an access point target version. The operator leaves each switch at "Do not upgrade this device". The save refuses the plan. The refusal names the switch target version. The form keeps each typed value. No plan is stored.

**Why this priority**: A silent drop removes production switches from a firmware plan. The confirmation page does not show the missing type. The change window can end with the switches on the old release.

**Independent Test**: Post a multi-site options body that checks `ap` and `switch`, sets one access point target, and sends no switch target. The response is HTTP 400 with the code and text in FR-002 and FR-003. No aggregate plan exists afterward.

**Acceptance Scenarios**:

1. **Given** one selected site with one access point and one switch. **When** the operator saves with a target only for the access point. **Then** the save answers 400 with code `org_upgrade_options_invalid` and the text "Choose the switch target version, or clear Switches."
2. **Given** the same site. **When** the browser sends an explicit target list that holds only the access point. **Then** the save answers 400 with the same text.
3. **Given** a refused save. **When** the page reopens. **Then** the access point target version keeps its typed value, and the refusal appears in the flash message.
4. **Given** a refused save. **When** the stored state is read. **Then** no aggregate plan exists and no browser session write occurs.

### User Story 2 - Save a complete mixed-type plan (Priority: P2)

An operator sets a target for each checked device type. Each device keeps its chosen version.

**Why this priority**: The fix must not block a valid plan. A plan with both types is the normal use of the page.

**Independent Test**: Post a body that checks `ap` and `switch` and carries one target for each type. The response is HTTP 200 with the confirmation path. The stored plan holds both device addresses.

**Acceptance Scenarios**:

1. **Given** one access point target and one switch target at the same site, **When** the operator saves, **Then** the save answers 200 with `/upgrade/org/confirm`.
2. **Given** the plan from Scenario 1, **When** the plan is read, **Then** it holds the access point address and the switch address.

### User Story 3 - Keep the valid empty choices (Priority: P3)

An operator can set one device of a checked type to "Do not upgrade this device". The operator can also check a type that no selected site holds.

**Why this priority**: The per-device choice is a control on the page. A refusal for it would block a valid save. A checked type with no device drops no device.

**Independent Test**: Post a body where one of two switches has a target and the other has none. Post a second body that checks a type with no device. Both answer HTTP 200.

**Acceptance Scenarios**:

1. **Given** two switches at one site and a target for only one of them. **When** the operator saves. **Then** the save answers 200 and the plan holds only the targeted switch.
2. **Given** a checked device type that no selected site holds. **When** the operator saves. **Then** the save answers 200 and the plan holds no device of that type.

### Edge Cases

- A checked device type has devices at two selected sites. One site has no target for that type. The save refuses the plan. The rule works per site (D-2).
- A retry narrows the site view to failed devices. A checked device type with a failed device and no target refuses the retry save (FR-009).
- An explicit target names a device address that the site view does not hold. The save ignores that entry, as before.
- The request holds no checked device type. The existing refusal for an empty target list answers, as before.
- The request uses the older type-wide version fields and no target list. The same rule applies (FR-006).
- A device type outside `ap`, `switch`, and `gateway` is not a checked device type. The rule does not apply to it.

### Requirements *(mandatory)*

#### Functional Requirements

- **FR-001**: The save MUST refuse a checked device type that has devices but no target version at a site.
- **FR-002**: The refusal MUST use HTTP status 400 and the error code `org_upgrade_options_invalid`.
- **FR-003**: The refusal text MUST use the form "Choose the {noun} target version, or clear {label}." The noun and label come from D-5.
- **FR-004**: A refused save MUST store no aggregate plan and MUST make no browser session write.
- **FR-005**: A refused save MUST keep each typed value in the form.
- **FR-006**: The rule MUST apply to the explicit target list and to the type-wide version fields.
- **FR-007**: A checked device type with no device at any selected site MUST NOT cause a refusal.
- **FR-008**: A device set to "Do not upgrade this device" MUST stay allowed when another device of its type has a target version.
- **FR-009**: The rule MUST apply to a retry plan. The rule MUST read the narrowed site view.
- **FR-010**: The contract test that expects a version-less switch in the stored plan MUST be replaced by the refusal contract.
- **FR-011**: The change MUST add one changelog fragment named `changelog.d/issue-3394-multi-site-empty-version.md`.
- **FR-012**: The check MUST log before the check, after the check, and on each refusal. The warning MUST name the device type and no device address.
- **FR-013**: The change MUST NOT change a template, a JavaScript file, or a documentation file.
- **FR-014**: Each changed line MUST carry an inline comment that gives its purpose.
- **FR-015**: The branch MUST start from `main`. A human MUST review the pull request before auto-merge.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- No new REST method is added. The check reads the device view that the save already reads. `aggregate_options_view` returns that view at `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py:422-430` [RC31].
- The device view reads the organization inventory through `read_upgrade_inventory` at `src/interfaces/portals/upgrade_portal/upgrade/options.py:704-727`. That function calls the mistapi method `getOrgInventory` [RC36, RC80].
- No owned WebSocket transport is added. The SDK insufficiency contract does not apply.
- The refusal text and each log line hold no token and no device address (FR-012).

### Key Entities *(include if feature involves data)*

- **Checked device type**: one of `ap`, `switch`, or `gateway`, as the page labels them "Access points", "Switches", and "Gateways" [RC46].
- **Device row**: one device in a site view. The row has a device type and a normalized MAC address. The row builder is at `options.py:864` [RC33].
- **Target choice**: one device address and one target version. The explicit list keeps only entries with a non-empty version at `org_upgrade.py:800` [RC24].
- **Plan**: the durable aggregate record. The write happens in `_write_operation` at `org_upgrade.py:1015` [RC30].

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A legacy type-wide body with no switch target returns HTTP 400, the code in FR-002, and the text in FR-003. The contract test proves this.
- **SC-002**: An explicit target body with no switch target returns HTTP 400 and the same text. The contract test proves this.
- **SC-003**: A body with a target for each checked type returns HTTP 200. The stored plan holds both device addresses. The contract test proves this.
- **SC-004**: A checked type with one opted-out device and one targeted device returns HTTP 200. The plan holds the targeted device only. The contract test proves this.
- **SC-005**: A checked type with no device at the selected sites returns HTTP 200. The contract test proves this.
- **SC-006**: A narrowed retry view with a checked type that has no target raises the same refusal. The unit test proves this.
- **SC-007**: The browser test shows the refusal text, keeps the access point target version value, and stores no plan. The Playwright test proves this in CI.

## Out of Scope

- Changes to templates, JavaScript, and documentation (FR-013).
- Naming the site in the refusal text (D-5).
- Changes to the confirmation page. It lists each planned child group [RC95].
- Changes to the single-site option mapper and its label table [RC32, RC34, RC35].
- Splitting `org_upgrade.py` or the `upgrade` package. The remediation is a separate issue [RC81, RC82].
- Rules for the per-device opt-out beyond FR-008 (D-2).
- Mist API behavior changes.

## Assumptions

- Each device of a checked type appears in the site view that the save reads [RC31].
- The save route answers each `ValueError` with HTTP 400 and its text [RC28].
- The browser shows the server text in the flash message and keeps typed values [RC40, RC41, RC44].
- The page sends a target only for an enabled, non-empty device choice [RC43].

## Clarifications

### Session 2026-11-26

- Q: Must a checked device type with no device at any selected site refuse? A: No. No device drops, so the rule does not apply (D-3).
- Q: Does a per-device "Do not upgrade this device" choice refuse? A: No, when another device of the type has a target version at the same site (D-2).
- Q: Must the refusal name the site? A: No. The issue requires the device type and its target version control (D-5).
- Q: Use "Type" or "Choose" in the refusal? A: "Choose". The target version control is a list, not a text field (D-5).
- Q: Keep the existing xfail test? A: No. It expects a switch with no version in the stored plan [RC51, RC52]. Analysis item A6 records the conflict.
