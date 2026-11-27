# Feature Specification: Multi-Site Confirm Page Plan Detail

**Feature Branch**: `fix/3222-multi-site-confirm-details`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #3222. The multi-site confirm page shows counts only, not the sites, the schedule, the phases, or the child plan.

**Input**: Issue #3222 and its twelve comments through 2026-11-13. The base is commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on `main`.

**Record path**: `specs\numbered\0\0\1\0\0\3\4\2\3222-multi-site-confirm-details`

## Context

The multi-site confirm page is the last screen before an organization firmware write. The operator types `CONFIRM` on that screen. On `main`, the page shows the organization, the counts, and raw family tokens. It also shows a combined firmware line, the strategy, the start time, and the advanced values that a child body sends. It shows a scope warning and a pre-check table with site names. It shows no planned device, no child route, and no phase. The stored plan holds all three. Section R-14 to R-24 of `design/research.md` gives the evidence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review each planned device before typing CONFIRM (Priority: P1)

The operator reads each planned device, its site, and its target version before the typed confirmation. Each row names one planned device.

**Why this priority**: Warning: a wrong device or site receives a firmware write. Counts alone do not reveal that error.

**Independent Test**: Save a two-site plan with six planned devices. Open the confirm page. Count the device rows and match each MAC address to the saved plan.

**Acceptance Scenarios**:

1. **Given** a saved two-site plan with six planned devices
   - **When** the operator opens the confirm page
   - **Then** the page shows six device rows. Each row names the site, name, MAC address, model, family, current version, and target version.
2. **Given** a saved plan with a planned device that has no target version
   - **When** the operator opens the confirm page
   - **Then** the page names the missing detail. The start control stays disabled.
3. **Given** a saved plan with the stable build for the switch family
   - **When** the operator opens the confirm page
   - **Then** each switch row shows "The vendor stable build" as its target version.

### User Story 2 - Stop a plan with a missing detail before any write (Priority: P1)

A plan with a missing detail cannot reach the cloud. The server refuses the start. The browser control also stays closed.

**Why this priority**: The typed word alone does not prove that the plan names each site and device. The server must refuse the write.

**Independent Test**: Save a plan with a planned device that has no MAC address. Type `CONFIRM` and submit. Expect HTTP 409 and no call to the upgrade service.

**Acceptance Scenarios**:

1. **Given** a saved plan with a planned device that has no MAC address
   - **When** the operator types `CONFIRM` and submits
   - **Then** the server answers HTTP 409 with the code `org_upgrade_plan_incomplete`.
2. **Given** a saved plan with a planned device that has no MAC address and ready pre-checks
   - **When** the operator opens the confirm page
   - **Then** the typed confirmation field stays disabled.
3. **Given** a saved plan with no child route
   - **When** the operator opens the confirm page
   - **Then** the page keeps the existing AP-only content and shows no new table.

### User Story 3 - Review selected sites, child routes, phases, and cloud calls (Priority: P2)

The operator reads the selected sites, the child routes, the phases, and the cloud call count before the write.

**Why this priority**: The issue names these details as missing. They support the device review, so they follow User Story 1 and User Story 2.

**Independent Test**: Save a canary plan with two sites and three child routes. Open the confirm page. Compare the site table, the child route table, the phase table, and the cloud call count with the saved plan.

**Acceptance Scenarios**:

1. **Given** a two-site plan with one access point organization child route and two switch site child routes
   - **When** the operator opens the confirm page
   - **Then** the page lists both sites with identifiers and planned device counts. It lists each child route with its scope and family.
2. **Given** a canary plan with phases 10 and 100 and a failure limit of 0
   - **When** the operator opens the confirm page
   - **Then** the phase table lists the phase list and the failure limit of each child route that sends them.
3. **Given** a plan with three child routes
   - **When** the operator opens the confirm page
   - **Then** the page states "Cloud calls: 3".

### Edge Cases

- A planned device has no name. The page shows "No name", and the MAC address identifies the row.
- A planned device has no current version. The page shows "Not read". This value does not block the start.
- A selected site has no name. The page shows the site identifier as the site name.
- A device name, site name, or model holds markup. The page escapes the text and shows the characters.
- A plan holds many planned devices. The page shows every row and omits no row.
- A selected site has no planned device. The page names the site and keeps the start control disabled.
- A device family token is not known. The page names the token and keeps the start control disabled.
- A retry plan narrows the selection to sites with planned devices. The page counts the narrowed sites only, as PR #4547 requires.
- A selected family that the stored plan omits. This change cannot show that family. Issue #3394 owns that defect.

### Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The confirm page MUST list each selected site with its name, its site identifier, and its planned device count.
- **FR-002**: The confirm page MUST list each child route with its route name, scope, device family, site names, and planned device count.
- **FR-003**: The confirm page MUST list each planned device with its site, name, MAC address, model, family, current version, and target version.
- **FR-004**: The confirm page MUST list the phase list and the failure limits that each child route sends.
- **FR-005**: The confirm page MUST state the cloud call count, which equals the count of child routes.
- **FR-006**: The confirm page MUST name each device family as AP, switch, gateway, or session smart router.
- **FR-007**: The confirm page MUST show "The vendor stable build" as the target version of each device whose child route sends the stable build.
- **FR-008**: The confirm page MUST name each missing detail and keep the typed confirmation field and start control disabled while any detail is missing.
- **FR-009**: The submit route MUST refuse a stored plan with a missing detail before any record change, site lock, or cloud call.
- **FR-010**: The confirm page MUST keep each existing summary line, schedule control, scope warning, write-disabled caution, pre-check table, and existing test identifier.
- **FR-011**: The confirm page MUST escape each site name, device name, and model as text, so markup in a name stays inert.
- **FR-012**: A stored plan with no child route MUST keep the existing AP-only confirm page and refusal behavior.
- **FR-013**: The change MUST add no Mist cloud request, and each existing confirm read MUST stay unchanged.
- **FR-014**: Each new table, row, and list MUST carry the stable `data-testid` value from the confirm-page contract.
- **FR-015**: Each requirement MUST map to at least one task and at least one test in `tasks.md`.
- **FR-016**: The change MUST update the portal document and add one changelog fragment named for issue 3222.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- This feature names no new mistapi method. The confirm page reads stored plan records and the existing site reads only.
- The existing calls stay unchanged. They are `upgradeOrgDevices`, `upgradeSiteDevices`, `upgradeDevice`, and `upgradeOrgSsrs`. Research R-56 to R-58 cites their SDK source.
- Contract test C3 proves that a refusal makes no write. Contract test C6 proves that the page GET adds no read.
- This change reads no credential, prints no credential, and stores no credential.

### Key Entities *(include if feature involves data)*

- **Planned device**: One device in the saved plan. It has a MAC address, a model, a family, a current version, and a target version.
- **Child route**: One cloud call of the saved plan. It has a route name, a scope, a device family, and a list of planned devices.
- **Selected site**: One site that the operator selected. The saved plan stores its identifier and its name.
- **Phase list**: The canary phase percentages and failure limits that one child route body sends.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The browser journey finds one device row for each planned device of the two-site plan, identified by MAC address.
- **SC-002**: The site table and the child route table show the counts that the saved plan stores. No count is missing.
- **SC-003**: A plan with a missing detail keeps the start control disabled. The control stays disabled after the operator types `CONFIRM`.
- **SC-004**: A submit with a plan that has a missing detail returns HTTP 409 and calls no upgrade service.
- **SC-005**: The confirm page GET adds no cloud call beyond the three existing reads. The contract test counts the calls.
- **SC-006**: The journey test `test_confirm_page_names_the_sites_and_the_schedule` runs without an expected-failure marker and passes.

## Assumptions

- **A-1**: Each stored child route holds its planned devices in `targets`. Each target holds the fields that `_target_record` writes, as research R-27 shows.
- **A-2**: Jinja autoescape stays on for `.html` templates. The Flask default selects it, as research R-62 shows.
- **A-3**: The confirm page keeps its existing reads. The reads run before the new view builds its rows.
- **A-4**: A human completes the safety review that the `needs-human-review` label names before the merge.
- **A-5**: A plan saved before this change keeps its stored shape. No data migration is needed.

## Clarifications

### Session 2026-11-26

- Q: Should the page show device identities, such as MAC addresses? A: Yes. Issue #3222 requires each device name, MAC address, model, family, and target version.
- Q: Does "every option" include an option that no child body sends? A: No. The page keeps the existing rule. It lists each option that a child body sends.
- Q: Should the family words use the options page labels? A: No. The issue names AP, switch, and gateway. Decision D-4 records the choice.
- Q: Should the server refuse an incomplete plan? A: Yes. A disabled browser control does not stop a direct submit. Decision D-2 records the choice.
- Q: May the change add new test modules? A: No. The five-item rule blocks new children in the test folders. Decision D-5 records the choice.
- Q: Should the preserved branch or the local commits seed the work? A: No. Both serve as reference evidence only. Decision D-10 records the choice.
- Q: Does section 6 of the brief require a human decision? A: No category applies. The safety review gate stays before the merge.

## Out of Scope

- The single-site confirm page in `upgrade/confirm.html`.
- The options page, its family labels, and its form.
- The parity pair test `test_confirm_page_pair_has_the_same_review_content`, which covers P-27 and P-28. A follow-up issue must own it.
- Issue #3394. A selected family with no version is omitted from the stored plan.
- Issue #3393. A server fault at the multi-site options save.
- Firmware write logic, the mistapi request bodies, and the start route, except the completeness refusal.
- The preserved branch `fix/3222-confirm-details` and the local commits `c744312c4` and `d2fc3ede8`.
- Any live firmware operation. No task in this record runs a live write.
