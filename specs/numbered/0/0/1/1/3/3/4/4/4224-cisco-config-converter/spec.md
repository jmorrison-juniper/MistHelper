# Feature Specification: Integrate Mist Cisco Config Converter

**Feature Branch**: `feat/4224-cisco-config-converter`

**Created**: 2026-11-26

**Status**: Draft

**Issue**: #4224, "Integrate Mist Cisco config converter"

**Input**: Issue #4224. Bring the Cisco IOS to Mist gateway conversion into the MistHelper web portal. Keep review before any cloud change. Do not copy source code or assets before a license decision.

**Record role**: This parent record links the child records for issues 4634 to 4649. It replaces the DNS-only legacy text at this path. Research row R-01 to R-32 records the legacy facts.

## Legacy baseline

The merged DNS slice from PR #4226 provides preview, review, and JSON export for global IPv4 `ip name-server` commands. Its blueprint is not registered in the shared portal. The legacy record deferred cloud apply. This parent record replaces that deferral with gated apply (D-3).

## Clarifications

### Session 2026-11-26

- Q: Does the merged DNS slice stay in the repository? A: Yes. It stays unregistered until the license decision and gate G3 close. Reverting it destroys verified tests. (D-2)
- Q: Does this record reuse the legacy folder? A: Yes. The route and the issue number match. One issue holds one record. (D-1)
- Q: Is cloud apply in scope? A: Yes. The issue requires an apply path. Each write family starts disabled. Gates G2, G4, and G5 apply to each family. (D-3)
- Q: Which typed words protect each operation? A: EXPORT protects export. APPLY protects cloud apply. CONFIRM protects administration and restore. (D-5)
- Q: Where do converter tests live? A: Under `tests/integration/web_portal/cisco_config_converter/`, with five or fewer children per folder. Browser evidence extends the existing smoke module. (D-9)
- Q: Which task IDs does this record use? A: The parity IDs T001 to T033. Legacy IDs T001 to T030 retire and appear only as `L-T###`. (D-13)
- Q: Which requirement IDs does this record use? A: FR-001 to FR-036 in this record. A parity requirement appears as "parity FR-###". A child requirement appears as "child FR-###" with its issue number.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview a conversion in the portal tab (Priority: P1)

An operator uploads a Cisco IOS configuration file. The operator selects a gateway role and a hardware model. The operator reviews the parsed source, the unsupported lines, and the proposed Mist settings. No Mist credential is needed.

**Why this priority**: Preview gives the first operator value. It changes no cloud state and needs no credential.

**Independent Test**: Run the isolated browser journey with a synthetic sample and no Mist credential values set. The proposal and the unsupported list render.

**Acceptance Scenarios**:

1. **Given** a valid synthetic sample and no Mist credentials, **When** the operator previews it, **Then** the proposal and the unsupported list render.
2. **Given** an invalid suffix, a path-like name, or invalid UTF-8, **When** the operator uploads the file, **Then** the portal shows an error and stores nothing.
3. **Given** an unsupported hardware model, **When** the operator selects it, **Then** the proposal marks the model as unsupported and offers no apply.

### User Story 2 - Export the reviewed proposal (Priority: P1)

An operator exports the reviewed proposal after typing EXPORT. The export holds no credential and makes no cloud change.

**Why this priority**: Export lets the operator keep and share the reviewed result without a cloud change.

**Independent Test**: Review a proposal, type a wrong word, and confirm that no file is created. Type EXPORT and confirm that the JSON matches the reviewed digest.

**Acceptance Scenarios**:

1. **Given** a reviewed proposal and the word EXPORT, **When** the operator exports, **Then** the JSON holds the request fields, unsupported items, and known gaps.
2. **Given** a proposal edited after review, **When** the operator exports, **Then** the portal refuses the export and asks for a new review.
3. **Given** a missing or wrong word, **When** the operator exports, **Then** no file is created.

### User Story 3 - Review the Mist target before apply (Priority: P2)

An operator selects an organization. The portal reads sites and gateways without writes. The operator chooses an existing or new site and assigned or unassigned gateways.

**Why this priority**: The operator must see the real target before any cloud change.

**Independent Test**: Simulate each lookup state with mocked SDK responses. Each state shows its own message.

**Acceptance Scenarios**:

1. **Given** a credential that cannot read the organization, **When** discovery runs, **Then** the portal shows a denied state and no site list.
2. **Given** two sites with the same name, **When** the operator selects a site, **Then** the portal requires the site identifier.
3. **Given** an incomplete page sequence, **When** discovery ends, **Then** the portal marks the result as unverified.

### User Story 4 - Apply a reviewed proposal after typed APPLY (Priority: P2)

An operator approves the exact organization, sites, gateways, and change set. The operator types APPLY. The portal writes only through enabled write families. Each family starts disabled.

**Why this priority**: Apply delivers the cloud change. It remains gated because it changes production state.

**Independent Test**: Use simulated responses. Each refused approval records zero writes.

**Acceptance Scenarios**:

1. **Given** a disabled write family, **When** the operator types APPLY, **Then** the portal refuses the apply and makes no SDK write call.
2. **Given** an approval older than 15 minutes, **When** the operator submits it, **Then** the portal refuses it.
3. **Given** a write that returns HTTP 429 three times, **When** the run ends, **Then** the outcome is indeterminate, and no retry runs.

### User Story 5 - Administer and recover Mist objects (Priority: P3)

An operator creates a verified backup, restores a reviewed backup, or deletes a scoped object after typing CONFIRM. Each action needs a verified backup and a fresh approval.

**Why this priority**: Administration changes production objects. It follows apply and needs the most evidence.

**Independent Test**: Use a damaged backup and a partial apply. Verify that unrelated objects remain unchanged.

**Acceptance Scenarios**:

1. **Given** an incomplete backup manifest, **When** the operator starts recovery, **Then** the portal blocks recovery.
2. **Given** an object absent from a backup, **When** a restore runs, **Then** the portal preserves that object.
3. **Given** a deletion scope that includes a service policy, **When** the operator reviews it, **Then** the portal refuses it until the owner approves (D-15).

### Edge Cases

- An empty or whitespace-only file is rejected.
- A file of exactly 16 MiB is accepted. A file with one extra byte is rejected.
- Invalid UTF-8 and a null character are rejected.
- A path-like name, a drive path, or a symbolic link name is rejected.
- IPv6, malformed, and unknown commands remain visible as unsupported items.
- Banner text and password-like values are not converted. Their values are omitted.
- The hub role is not offered. The gateway template type enum has no hub value (R-75).
- A proposal edited after review cannot be exported or applied until a new review runs.
- A missing Mist credential does not block preview. Discovery and apply refuse without it.
- A wrong or missing typed word creates no file and makes no write.
- An approval older than 15 minutes is refused.
- A duplicate apply submission is refused.
- HTTP 429 after three retries, a timeout, or a 5xx status on a write reads indeterminate. The portal does not retry the write.
- An incomplete page sequence marks the result unverified.
- A backup without a complete page header blocks recovery.
- A restart without `PORTAL_SECRET_KEY` breaks stored review records (R-46).
- Private converter files in `data/` appear in the shared data browser until the exclusion change lands (R-47).

## Requirements *(mandatory)*

### Functional Requirements

Each FR row names its parity source in parentheses. A parity source is a requirement number in PR #4596. The parity source does not change the meaning of the FR row.

- **FR-001**: The web portal MUST show the converter as one tab. Existing portal routes MUST keep their behavior. (Source: issue. Parity: FR-025, FR-029.)
- **FR-002**: The converter MUST accept six text suffixes up to 16 MiB. It MUST decode strict UTF-8, reject path-like names, and process uploads in memory. (Source: issue constraints. Parity: FR-002.)
- **FR-003**: The operator MUST review the parsed source structure without conversion or credentials. (Source: issue. Parity: FR-003.)
- **FR-004**: The review MUST cover every observed parser family. It MUST show unsupported and ambiguous input. (Parity FR-004)
- **FR-005**: The operator MUST select Branch, Hub, or Standalone. The role MUST NOT come from a hostname. (Parity FR-005)
- **FR-006**: The operator MUST select SRX or SSR and a supported model with an explicit interface mapping. (Source: issue. Parity: FR-006.)
- **FR-007**: The conversion MUST separate WAN, LAN, address, VLAN, DHCP, route, and VRF intent. It MUST NOT make silent assumptions. (Parity FR-007)
- **FR-008**: The review MUST cover routing, management, identity, security, cellular, and flow-export families. Display-only limits MUST stay visible. (Parity FR-008)
- **FR-009**: Each proposal MUST show changes, omissions, unresolved mappings, target objects, and verification state. (Source: issue. Parity: FR-009.)
- **FR-010**: Preview MUST work without Mist credentials or cloud checks. (Source: issue. Parity: FR-010.)
- **FR-011**: Export MUST contain the exact current reviewed proposal and no credential. (Parity FR-011)
- **FR-012**: The portal MUST separate cloud availability, permission, site existence, gateway inventory, and stale results. (Parity FR-012)
- **FR-013**: The operator MUST select an existing or proposed site. The operator MUST select assigned or unassigned gateways. (Parity FR-013)
- **FR-014**: The proposal MUST separate templates, device profiles, site settings, variables, and device assignments. (Parity FR-014)
- **FR-015**: The operator MUST approve the exact organization, sites, gateways, and change set before any cloud write. (Source: issue. Parity: FR-015.)
- **FR-016**: Apply MUST require the typed word APPLY, permission, a current review, verified contracts, and recovery evidence. (Source: issue. Parity: FR-016.)
- **FR-017**: A change to input, proposal, target, role, hardware, model, or cloud state MUST invalidate the approval. (Parity FR-017)
- **FR-018**: Apply MUST prevent duplicate submission, stale overwrite, duplicate creation, and unsafe retry. (Parity FR-018)
- **FR-019**: Apply MUST report each changed object. It MUST separate failed, partial, and indeterminate results. (Parity FR-019)
- **FR-020**: Recovery MUST use complete verified backups. It MUST preserve unrelated changes and require a fresh approval. (Parity FR-020)
- **FR-021**: Administration MUST create a scoped backup and list backups for policies, services, and networks. (Parity FR-021)
- **FR-022**: Administration MUST restore reviewed backups for policies, services, and networks. (Parity FR-022)
- **FR-023**: Administration MUST delete scoped services, networks, and templates. It MUST unassign templates and device profiles. (Parity FR-023)
- **FR-024**: Administrative writes MUST require permission, a scope review, two confirmations, the typed word CONFIRM, and verified recovery backups. (Parity FR-024)
- **FR-025**: The portal MUST keep the selection, review, proposal, and confirmation journeys. (Parity FR-025)
- **FR-026**: The configured themes MUST cover the four visual intentions. The record MUST NOT copy source assets. (Parity FR-026)
- **FR-027**: Health, status, loading, empty, error, cancel, and success states MUST stay distinct and accessible. (Parity FR-027)
- **FR-028**: Input, backups, browser state, downloads, responses, and logs MUST follow the credential and privacy rules. (Source: parity FR-028. Issue security rule.)
- **FR-029**: The integration MUST keep the deployed portal behavior, shared storage, authentication, and services. (Source: parity FR-029. Issue migration rule.)
- **FR-030**: Each observed capability MUST have traceable coverage. It MUST have an independent test or an explicit unsupported disposition. (Parity FR-030)
- **FR-031**: No protected source expression MUST be reused without legal and owner approval. (Source: parity FR-031. Issue license rule.)
- **FR-032**: Contract and workflow tests MUST use synthetic data and simulated responses. They MUST NOT use live credentials or cloud writes. (Source: parity FR-032. Issue test plan.)
- **FR-033**: The integration MUST use the existing runtime, database, and Redis service. It MUST NOT add a database, a Redis service, or a Compose stack. (Issue constraints)
- **FR-034**: Each new interactive control MUST carry a stable `data-testid`. A failed browser run MUST keep a screenshot or trace. (Issue UI expectations)
- **FR-035**: The operator MUST type EXPORT after review before any export file is created. (Source: issue. Parity: FR-011.)
- **FR-036**: The converter MUST show its own supported subset. It MUST show each documented source feature gap, such as flow export. (Source: issue constraints. Source mapping reference.)

### Mist Cloud Transport Requirements

- The record names the gateway template family from mistapi 0.64.1. The functions are `listOrgGatewayTemplates`, `createOrgGatewayTemplate`, `getOrgGatewayTemplate`, `updateOrgGatewayTemplate`, and `deleteOrgGatewayTemplate` (R-80, R-28).
- Child records own the other mistapi methods. Child 4634 reports 22 write rows, including `deleteOrgServicePolicy`, and 18 read rows.
- Direct HTTP to a Mist endpoint is prohibited when a mistapi method exists.
- Contract evidence belongs to the child records. Child 4634 covers SDK insufficiency and endpoint parity. Child 4642 covers SDK authentication. Child 4644 covers failure safety. Child 4639 covers secret redaction.

### Key Entities

- **Source Configuration**: Uploaded Cisco IOS text, its file name, its byte count, and its digest. It has no server path.
- **Conversion Proposal**: The proposed gateway template fields, unsupported items, known gaps, and digest.
- **Review Record**: The digest of the reviewed proposal. A changed proposal invalidates it.
- **Approval Record**: The organization, sites, gateways, change set, typed word, and a 15-minute single-use window.
- **Write Family**: One of eight registered write families. Each family starts disabled.
- **Operation Run**: One run with one outcome for each object. Outcomes are success, failed, partial, or indeterminate.
- **Backup Record**: One verified backup with its organization, family, natural key, checksum, and UTC time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 33 parity tasks map to child issues. Each task has a status and evidence.
- **SC-002**: The preview journey passes in the isolated browser test with no Mist credential variable set.
- **SC-003**: Every apply and administration test with a missing, expired, rejected, or changed approval records zero SDK write calls.
- **SC-004**: Every simulated ambiguous write reports indeterminate and records zero automatic retries.
- **SC-005**: Each supported input family has one positive test and one negative test. Unsupported families show no invented output.
- **SC-006**: The four visual intentions pass keyboard and narrow-screen checks with independently authored assets.
- **SC-007**: Existing portal regression tests pass after integration. The integration adds no duplicate data service.
- **SC-008**: Every log and export test finds zero secret values.
- **SC-009**: A legal decision is recorded before any protected source expression is copied.

## Assumptions

- Operators use the MistHelper web portal on port 8055 (R-54).
- web_portal/app.py defines no login route today (analysis A-12). Operator identity is an open decision (D-16).
- Cloud features use the existing credential names MIST_APITOKEN and MIST_API_TOKEN (R-55).
- The 16 MiB limit is a feature policy. The legacy contract attributes it to observed source behavior (U-08).
- The first apply target is a gateway template in the selected organization (R-28, R-29).

## Out of Scope

- Live Mist writes in this change.
- Enabling any write family without the owner decision in D-15.
- Deleting service policies. The `deleteOrgServicePolicy` operation stays excluded (R-74, D-15).
- The hub gateway role, because the gateway template type enum lists no hub value (R-75).
- Reuse of source code, mapping text, screenshots, or assets before the decision in D-17.
- Changes to the source repository.
- Changes to `web_portal/app.py` or `web_portal/templates/base.html` before gate G3.
- New databases, Redis services, or Compose stacks.

## Child Record Map

| Child issue | State | Parity tasks | Draft record path | Requirements | Planned tests | Human decisions |
|---|---|---|---|---|---|---|
| 4632 | CLOSED | T005 | No draft | Not applicable | Not applicable | 0 |
| 4633 | CLOSED | T001 | No draft | Not applicable | Not applicable | 0 |
| 4634 | OPEN | T003 | specs\numbered\0\0\1\2\2\0\1\4\4634-mist-api-contract-evidence | 21 | 32 | 2 |
| 4635 | OPEN | T002 | specs\numbered\0\0\1\2\2\0\2\0\4635-cisco-converter-licensing-authorship | 18 | 6 | 7 |
| 4636 | OPEN | T004, T006 | specs\numbered\0\0\1\2\2\0\2\1\4636-converter-package-state-model | 23 | 25 | 3 |
| 4637 | OPEN | T007 to T010 | specs\numbered\0\0\1\2\2\0\2\2\4637-safe-cisco-input-review | 22 | 40 | 0 |
| 4638 | OPEN | T011, T012 | specs\numbered\0\0\1\2\2\0\2\3\4638-gateway-role-hardware-selection | 20 | 26 | 0 |
| 4639 | OPEN | T015, T016 | specs\numbered\0\0\1\2\2\0\2\4\4639-cisco-management-security-families | 15 | 17 | 1 |
| 4640 | OPEN | T013, T014 | specs\numbered\0\0\1\2\2\0\3\0\4640-convert-verified-network-routing | 17 | 35 | 1 |
| 4641 | OPEN | T017, T018 | specs\numbered\0\0\1\2\2\0\3\1\4641-proposal-review-export | 23 | 21 | 1 |
| 4642 | OPEN | T019, T020 | specs\numbered\0\0\1\2\2\0\3\2\4642-converter-target-discovery | 20 | 24 | 0 |
| 4643 | OPEN | T023, T024 | specs\numbered\0\0\1\2\2\0\3\3\4643-private-config-backup-catalog | 28 | 27 | 2 |
| 4644 | OPEN | T021, T022 | specs\numbered\0\0\1\2\2\0\3\4\4644-gated-converter-apply-reconcile | 25 | 27 | 3 |
| 4645 | OPEN | T025, T026 | specs\numbered\0\0\1\2\2\0\4\0\4645-cisco-converter-administration | 28 | 26 | 3 |
| 4646 | OPEN | T027, T028 | specs\numbered\0\0\1\2\2\0\4\1\4646-restore-recovery | 28 | 36 | 2 |
| 4647 | OPEN | T029, T030 | specs\numbered\0\0\1\2\2\0\4\2\4647-converter-visual-journeys | 20 | 20 | 0 |
| 4648 | OPEN | T031, T032 | specs\numbered\0\0\1\2\2\0\4\3\4648-converter-privacy-portal-integration | 20 | 28 | 1 |
| 4649 | OPEN | T033 | specs\numbered\0\0\1\2\2\0\4\4\4649-converter-parity-evidence | 13 | 13 | 4 |

The child records hold 403 planned tests and 30 human decisions in total. This record consolidates the human decisions into D-15 to D-18.
