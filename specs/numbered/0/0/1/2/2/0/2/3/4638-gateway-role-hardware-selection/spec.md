# Feature Specification: Add explicit gateway role and hardware selection

**Feature Branch**: `feat/4638-gateway-role-hardware-selection`

**Created**: 2026-11-26

**Status**: Draft. Implementation waits for issues 4634, 4636, and 4637.

**Input**: GitHub issue 4638, "[Spec]: Add explicit gateway role and hardware selection". This record completes parity tasks T011 and T012 in `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md`, lines 57 and 58. Parent issue: 4224.

## Clarifications

### Session 2026-11-26

- Q: Does the Mist gateway deployment type accept a hub value? A: No. The enum names only `spoke` and `standalone`. Decision D-4.
- Q: Does the Branch role map to the spoke value? A: Not verified. No local text names Branch. Branch stays blocked. Decision D-3.
- Q: Which models can a reviewer verify? A: Models with an inventory sample and complete WAN and LAN evidence. Decision D-5.
- Q: Does the retired `type` form field stay accepted? A: No. The preview returns HTTP 400 and names the role field. Decision D-2.
- Q: Are open-ended port ranges expanded? A: No. Only named ports and closed ranges are selectable. Decision D-7.
- Q: Does the converter call Mist to confirm inventory? A: No. Every evidence row comes from local files. Decision D-13.
- Q: Does this issue enable apply? A: No. Apply belongs to issue 4644 and stays disabled here. Decision D-13.
- Q: Where does the mapping code live? A: In `conversion/hardware/`, which issue 4640 reserves. Decision D-14.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review a verified standalone SRX gateway (Priority: P1)

An engineer selects Standalone, the SRX family, and model SRX300 or SRX320. The engineer maps one WAN port and one LAN port to Cisco interfaces, then reviews the proposal.

**Why this priority**: Only a verified review can pass to a later apply gate.

**Independent Test**: Post one synthetic file with SRX300 and explicit ports. Review and export succeed. No Mist call occurs.

**Acceptance Scenarios**:

1. **Given** the SRX300 fixture in `design/quickstart.md`, Scenario 3, **When** the engineer previews, **Then** `hardware.status` is `verified` and `gateway_template.type` is `standalone`.
2. **Given** a verified preview, **When** the engineer reviews and exports, **Then** the export equals the reviewed proposal.

### User Story 2 - See an explicit decision for each unsupported selection (Priority: P1)

An engineer selects Branch, Hub, the SSR family, a model without inventory evidence, an unknown model, or conflicting ports. The preview lists each blocker. Review and export return HTTP 409.

**Why this priority**: A wrong role or port map can cause an unsafe deployment.

**Independent Test**: Parametrized preview tests cover each blocker code. Each test asserts that review does not approve the proposal.

**Acceptance Scenarios**:

1. **Given** role Branch, **When** the engineer previews, **Then** the blocker `role_unverified` appears and review returns HTTP 409.
2. **Given** role Hub, **When** the engineer previews, **Then** the blocker `role_without_deployment_type` appears and `gateway_template.type` is absent.
3. **Given** model SRX340, **When** the engineer previews, **Then** the blocker `model_without_inventory_sample` appears.
4. **Given** one Mist port in two assignments, **When** the engineer previews, **Then** the blocker `port_duplicate` appears.

### User Story 3 - Invalidate a review after any change and operate with the keyboard (Priority: P2)

An engineer changes the role, family, model, a port, or a Cisco interface after review. The export of the earlier proposal returns HTTP 409. Every new control has a stable `data-testid` value and native keyboard support.

**Why this priority**: The review must match the exact selection that the engineer examined.

**Independent Test**: Route tests change one selection after review. A page test reads each `data-testid` value.

### Edge Cases

- A missing role, family, or model returns HTTP 400.
- A blank model, or a model longer than 32 characters, returns HTTP 400.
- A `ports` value that is not a JSON list returns HTTP 400.
- A Mist port name that does not match the `ge` or `xe` grammar returns HTTP 400.
- A usage value other than `wan` or `lan` returns HTTP 400.
- A port entry without a Cisco interface name returns HTTP 400.
- A Mist port that the evidence row does not list as WAN or LAN returns blocker `port_not_selectable`. This includes HA and OOB ports such as `ge-0/0/1` on SRX300.
- An empty port list returns blocker `port_missing_usage`.
- A Cisco interface that the uploaded file does not contain returns blocker `source_interface_not_found`.
- A model absent from the register, including `VSRX`, returns blocker `model_unknown`.
- SRX1500 returns blocker `model_evidence_conflict`.
- SSR120 returns blocker `port_evidence_absent`.
- A form that still sends the retired `type` field returns HTTP 400.
- A failed preview removes an earlier review. This behavior already exists on main and stays unchanged.

### Out of Scope

- Apply, backup, restore, delete, and unassign actions. Issues 4644 to 4646 own them.
- Any Mist REST request, including inventory and device model reads.
- VSRX, LTE ports such as `cl-1/0/0`, cluster and HA configuration, and VRF support.
- SSR port roles and any SSR model with port evidence.
- Hub VPN configuration and Hub device-profile mapping.
- Shared portal route registration, navigation, and changes to `web_portal/app.py`.
- Structured input review (issue 4637), versioned review (issue 4641), visual journeys (issue 4647), network conversion (issue 4640), and management review (issue 4639).

## Requirements *(mandatory)*

### Functional Requirements

| ID | Requirement | Source |
| --- | --- | --- |
| FR-001 | The converter MUST require one explicit role: Branch, Hub, or Standalone. | Full-parity FR-005, line 111 |
| FR-002 | The converter MUST require one explicit family: SRX or SSR. | Full-parity FR-006, line 112 |
| FR-003 | The converter MUST require one explicit model from the evidence rows of the selected family. | Full-parity FR-006, line 112 |
| FR-004 | The converter MUST map each assigned Mist port to one Cisco interface and one usage. | Full-parity FR-006, line 112, and issue 4640 spec line 150 |
| FR-005 | The converter MUST map a role to a gateway deployment type only when local evidence verifies the mapping. | Full-parity mist contract line 83 |
| FR-006 | The converter MUST block the Hub role because the deployment type enum has no hub value. | OpenAPI lines 80785 to 80790 |
| FR-007 | The converter MUST block the Branch role until issue 4634 records mapping evidence. | Decision D-3 |
| FR-008 | The converter MUST block each model that lacks an inventory sample, has conflicting evidence, or is unknown. | Issue 4638 acceptance criteria |
| FR-009 | The converter MUST block every SSR selection because the register holds no verified port roles. | Decision D-9 |
| FR-010 | The converter MUST accept only named WAN or LAN ports from a verified row. HA and OOB ports stay excluded. | OpenAPI lines 47215 to 47223, and cabling lines 29725 to 29734 |
| FR-011 | The converter MUST block duplicate Mist ports, duplicate Cisco interfaces, missing usage, and interfaces absent from the file. | Issue 4638 test plan |
| FR-012 | The converter MUST block a row whose evidence revision differs from the current revision. | Full-parity portal contract line 61 |
| FR-013 | The converter MUST refuse review and export of a blocked proposal with HTTP 409. | Issue 4638 constraints, and Decision D-11 |
| FR-014 | The converter MUST invalidate an earlier review when any selection or source input changes. | Full-parity FR-017, line 123 |
| FR-015 | The converter MUST keep the DNS output for `ip name-server` input unchanged. | Issue 4638 migration section |
| FR-016 | The converter MUST reject the retired `type` form field with HTTP 400. | Full-parity portal contract line 16, and Decision D-2 |
| FR-017 | Each new interactive control MUST expose a stable `data-testid` value and native keyboard support. | Full-parity portal contract line 95, and copilot instructions line 303 |
| FR-018 | The change MUST NOT register a route, change shared navigation, or edit `web_portal/app.py`. | Issue 4638 migration section, and app.py lines 182 to 235 |
| FR-019 | Tests MUST use synthetic input and mocked data. Tests MUST make no network call and no Mist write. | Issue 4638 security section |
| FR-020 | Each evidence row MUST cite local OpenAPI lines or local mistapi source lines. | Brief rule 6, and full-parity mist contract line 83 |

### Mist Cloud Transport Requirements

- This issue names no mistapi write method. The converter makes no Mist REST request.
- The register cites the OpenAPI operation `listDeviceModels` at line 1863 and the mistapi function at `device_models.py` line 17 as evidence only.
- Model fields cite the inventory schema at OpenAPI line 82192 and the `getOrgInventory` signature at `inventory.py` line 21.
- Missing contract evidence blocks the associated mapping. Full-parity mist contract line 83 and issue 4634 apply.

### Key Entities

- **Hardware selection**: The role, family, model, and port assignments in one preview request.
- **Evidence row**: One family and model with a status, port usages, a blocker code, and an evidence revision.
- **Port assignment**: One Mist port, one usage (`wan` or `lan`), and one Cisco interface name.
- **Hardware decision**: The status (`verified` or `blocked`), the blocker list, and the derived deployment type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each of the six role and family combinations returns a verified proposal or at least one blocker.
- **SC-002**: Each blocked selection returns zero review approvals and zero exports in the route tests.
- **SC-003**: The hardware test module records zero socket connections and zero file writes.
- **SC-004**: Each change to the role, family, model, a port, or a Cisco interface makes the earlier export return HTTP 409.
- **SC-005**: The page exposes one `data-testid` value for each role, family, model, usage, and interface control.
- **SC-006**: The DNS regression test returns the same `dns_servers` list and unsupported item count as before for the same input.
- **SC-007**: Each verified evidence row cites one inventory line and one port line in the local OpenAPI file.

## Assumptions

- **A-1**: Issues 4634, 4636, and 4637 merge before implementation starts. Issue 4634 records field semantics for each verified row.
- **A-2**: Issue 4640 accepts the `conversion/` layout and the reserved `hardware/` slot from its decisions D-1 and D-3.
- **A-3**: OpenAPI blob `b7fc2bfb` and mistapi 0.64.1 stay pinned. A change to either one makes each row stale.
- **A-4**: The operator types each Cisco interface name exactly as the uploaded file shows it.
- **A-5**: Mist port names in this release use the `ge` and `xe` grammar. The LTE name `cl-1/0/0` stays unsupported.
- **A-6**: The SRX300 skill confirms eight 1GbE network ports on the SRX300 chassis.

## Safety Statements

Warning: a Mist write can change production gateways and cannot be undone by this application. This issue enables no write and no apply path.

Caution: a browser page that was loaded before this change still shows the retired `type` field. The operator must reload the page before a new preview.
