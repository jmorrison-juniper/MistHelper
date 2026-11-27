# Feature Specification: Multi-site stable word and router channel lab verification

**Feature Branch**: `3392-multisite-stable-channel-lab`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #3392, "Upgrade portal: verify the stable word and the router channel in a lab organization (multi-site parity)". The owner runs the lab checks. The repository code follows the posted lab answers.

## Key Terms

- **Organization access point route**: `POST /api/v1/orgs/{org_id}/devices/upgrade`. It upgrades access points for an organization.
- **Router route**: `POST /api/v1/orgs/{org_id}/ssr/upgrade`. It upgrades session smart routers for an organization.
- **Site route**: `POST /api/v1/sites/{site_id}/devices/upgrade`. It upgrades devices of one site.
- **Stable word**: the value `stable` in a version field.
- **Stable build**: the vendor build that the cloud selects for the stable word.
- **Channel**: the field that names the release train of a router. Its values are `alpha`, `beta`, and `stable`.
- **Router**: a session smart router. The abbreviation SSR appears only inside identifiers and quoted text.
- **Multi-site page**: the organization options page of the upgrade portal. The file is `org_options.html`.
- **Single-site page**: the site options page of the upgrade portal. The file is `options.html`.
- **Refusal**: a rule that stops a plan before the typed confirmation.
- **Lab check**: one upgrade that the owner sends to a lab organization. This record names four lab checks.
- **Lab answer**: the sanitized record of one lab check. The owner posts it on issue #3392.
- **Job read**: a GET call that reads the state of an upgrade job.
- **Verdict**: the result of one lab check. Its values are accepted, refused, and unknown.
- **Owner**: the account holder of the repository. The owner runs every lab check.
- **Operator**: a network operations center engineer who uses the upgrade portal.

## Clarifications

### Session 2026-11-26

- Q: Who runs the lab checks? A: The owner runs them, only on identified lab devices, after exact targets and one typed confirmation. Source: issue #3392 comment IC_kwDOQltU8c8AAAABeA-lUg.
- Q: Is a lab run authorized now? A: No. The same comment states that no firmware request is authorized yet.
- Q: Which typed phrase protects a lab write? A: The phrase CONFIRM, the word that the portal requires (RC-52). See D-3.
- Q: Can the multi-site page send the stable word to an access point? A: No. The save refuses the stable word for a plan with an access point (RC-41, RC-42, RC-43). See D-14.
- Q: Which code path does the record cite? A: The current main path (RC-27). The path in issue #3392 is absent on main (RC-58). See D-5.
- Q: Where does the record live? A: At the numbered route for issue 3392 (RC-13 to RC-15, RC-112). See D-6.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record the answer for the stable word on the organization access point route (Priority: P1)

The owner sends one organization upgrade of one lab access point with the version `stable`. The owner reads the job and posts one lab answer on issue #3392. The repository does not change in this story.

**Why this priority**: The access point refusal is the parity gap of this issue. The answer decides which code path the repository follows.

**Independent Test**: The owner posts one lab answer with one verdict. A reader finds the answer on issue #3392 without a repository change.

**Acceptance Scenarios**:

1. **Given** one lab access point and one lab site, **When** the owner runs the lab check L-AP-STABLE, **Then** the owner posts one lab answer.
2. **Given** a submit error that names another field, **When** the owner reads it, **Then** the verdict is unknown and the owner repeats the check once.

### User Story 2 - Record the answer for each router channel value (Priority: P1)

The owner sends one router upgrade for each channel value: `stable`, `beta`, and `alpha`. The owner reads each router job and posts one lab answer for each value.

**Why this priority**: The multi-site page offers three values. Each value needs one answer before the repository keeps it.

**Independent Test**: Three lab answers exist on issue #3392, one for each channel value. Each answer names one verdict.

**Acceptance Scenarios**:

1. **Given** one lab router and the value `beta`, **When** the owner runs the lab check L-SSR-BETA, **Then** the owner posts one lab answer for `beta`.
2. **Given** a router job that ends failed for a channel reason, **When** the owner reads the job, **Then** the verdict records a refusal.

### User Story 3 - Offer the stable build for access points only after an accepted answer (Priority: P2)

When L-AP-STABLE has an accepted verdict, the multi-site page offers the stable build for access points, and the save accepts it. When L-AP-STABLE has a refused verdict, both refusals stay, and the record states the refused answer.

**Why this priority**: The operator must not send a build that the cloud refuses. The operator must not see a build that differs from the single-site page.

**Independent Test**: On the refused branch, the existing refusal test passes. On the accepted branch, the new access point test passes, and the access point body carries version `stable`.

**Acceptance Scenarios**:

1. **Given** L-AP-STABLE has an accepted verdict, **When** an operator selects the stable build for access points, **Then** the access point body carries `stable`.
2. **Given** L-AP-STABLE has a refused verdict, **When** an operator selects the stable build for access points, **Then** the save refuses it and names the control.

### User Story 4 - Offer only the router channel values that the cloud accepts (Priority: P2)

When a channel value has a refused verdict, the multi-site page, the single-site page, and the CLI prompt stop offering it. When every value has an accepted verdict, no control changes.

**Why this priority**: A refused value sends a failing upgrade to a router. The operator cannot read the cause from the page.

**Independent Test**: The single-site channel tests and the multi-site channel tests pass with the accepted values only.

**Acceptance Scenarios**:

1. **Given** a refused answer for L-SSR-ALPHA, **When** an operator opens the multi-site page for a router, **Then** the channel list holds `stable` and `beta` only.
2. **Given** accepted answers for all three values, **When** an operator opens the page, **Then** the channel list holds all three values.

### User Story 5 - Keep the record and the parity fixture accurate (Priority: P3)

The record cites only paths and lines that exist on main. The parity fixture shows the access point stable word as a gap until L-AP-STABLE has an accepted verdict.

**Why this priority**: A stale citation or a stale verdict misleads the next change.

**Independent Test**: The remote citation audit finds each cited path on main with the stated blob SHA. The parity page test passes with the corrected rows.

**Acceptance Scenarios**:

1. **Given** the record, **When** a reader checks each row of the remote table, **Then** the blob SHA and the line match main.
2. **Given** the parity fixture, **When** a reader opens row C17, **Then** the access point family shows a gap until an accepted answer exists.

## Edge Cases

- EC-1 (field error): The submit call returns a field error that names another field. The verdict is unknown. The owner repeats the check once with the named field and keeps both answers.
- EC-2 (status not named): The submit call returns a status that the contract does not name, such as 429. The verdict is unknown. The owner repeats the check only after earlier jobs reach a final state.
- EC-3 (split result): One lab router accepts a channel value and another lab router refuses it. The value stays only when every lab router accepts it. Otherwise the system removes the value, and the owner reports the split.
- EC-4 (queued job): Caution: a lab device can stay offline, and its job stays queued. The owner waits for a final state, or cancels the job with the cancel operation of the same route before the device starts.
- EC-5 (router reboot): Caution: a router can reboot during its job, and the site network can drop during the reboot. Use lab devices only.
- EC-6 (wrong organization): Warning: an accidental run against a production organization can change production devices. Stop the run at once. Decision D-18 limits targets to lab devices.
- EC-7 (posted secret): Warning: a token or an identifier in an issue comment stays in the issue history. The owner removes the value and rotates the credential.
- EC-8 (job read by cancel path): Caution: the installed mistapi function getOrgSsrUpgrade requests the cancel path (RC-117). The owner uses listOrgSsrUpgrades for router job reads.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST keep both organization access point refusals until an accepted lab answer exists for L-AP-STABLE.
- **FR-002**: The agent MUST NOT call the Mist cloud, and MUST NOT request or read a credential, for issue #3392.
- **FR-003**: The owner MUST type the phrase CONFIRM before each lab write starts.
- **FR-004**: Each lab answer MUST hold only the sanitized fields of the lab answer contract. It MUST NOT hold an identifier, a token, or a full response body.
- **FR-005**: If L-AP-STABLE has an accepted verdict, the system MUST remove both refusals and offer the stable build for access points on the multi-site page. The system MUST send the stable word in the access point body.
- **FR-006**: If L-AP-STABLE has a refused verdict, the system MUST keep both refusals and MUST record the refused answer in design/research.md.
- **FR-007**: The system MUST offer only the channel values that every lab router accepts, on the multi-site page, the single-site page, and the CLI prompt.
- **FR-008**: The system MUST send a channel only in router bodies. A site body and an access point body MUST NOT carry a channel.
- **FR-009**: The parity fixture MUST show the access point stable word as a gap until L-AP-STABLE has an accepted verdict.
- **FR-010**: Each remote citation in the record MUST match the blob SHA and the line on main at the audit time. The remote check count MUST match in STATUS.json, in design/research.md, and in the summary.
- **FR-011**: The record MUST use the managed numbered route. It MUST NOT add a direct child to a noncompliant parent.
- **FR-012**: Each changed file MUST pass each local gate that applies to it before the pull request opens.

### Key Entities

- **Lab check**: one owner-run upgrade. Its key is the check identifier: L-AP-STABLE, L-SSR-STABLE, L-SSR-BETA, or L-SSR-ALPHA.
- **Lab answer**: one sanitized answer for one attempt of a lab check. Its key is the check identifier and the UTC time of the attempt.
- **Channel value**: one value of the channel field. Its key is the word itself.
- **Access point rule**: the refusal that keeps the stable word away from the access point route. Its key is the rule identifier R-AP-STABLE.
- **Parity row**: one row of the parity fixture. Its key is the row identifier, C17 or C21.
- **Remote check**: one claim checked against main. Its key is the path and the reference.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Issue #3392 holds four lab answers after the owner runs the lab checks.
- **SC-002**: Each functional requirement maps to at least one task and at least one TST item in analysis.md.
- **SC-003**: The number of refusals removed without an accepted answer for L-AP-STABLE is zero.
- **SC-004**: The remote check count is 120 in STATUS.json, in the table of design/research.md, and in the summary.
- **SC-005**: Each applicable local gate passes on the changed files of the branch that the lab answers select.
- **SC-006**: The record and issue #3392 hold no token, no lab identifier, and no response body. The evidence audit finds zero such values.

## Assumptions

- The owner controls the lab organization, the lab devices, and the credential source (decision D-18).
- The pinned mistapi package 0.64.1 is installed in the owner environment (RC-120).
- The local OpenAPI file describes the documented fields of the cloud. The lab answers decide each undocumented word.
- Caution: a lab device can reboot and can lose service. This risk applies to each lab check. Lab devices carry no production traffic.

## Out of Scope

- Production organizations and production devices.
- Any cloud call by the agent.
- The switch and gateway stable word on the site route. PR #3391 names its live check as separate work.
- The stable word in the version field of the router route (unresolved item U-4 in analysis.md).
- The mistapi pin and the constitution text (analysis item A-5).
- The operator guide entry for ORG_UPGRADE_WRITES_ENABLED (analysis item A-11).
- Edits to issue #3392 and to PR #3391. The owner performs these edits.
