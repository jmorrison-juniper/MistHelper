# Feature Specification: Cisco Converter Full Observed Parity

**Feature Branch**: `jmorrison-juniper-cisco-converter-full-parity-spec`

**Created**: 2026-11-05T17:00:40Z

**Status**: Specified. Implementation and cloud use are not approved.

**Input**: Rebuild the complete migration workflow and compare the original converter with MistHelper.
The selected scope is full observed feature parity, including apply and hardware mappings.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select and inspect a configuration (Priority: P1)

An engineer selects a stored file or uploads a file, then inspects the configuration without cloud credentials.

**Why this priority**: An engineer must understand the input before planning a change.

**Independent Test**: Use original synthetic files and block external requests. Inspect all parsed sections without conversion or persistence of secret values.

**Acceptance Scenarios**:

1. **Given** approved stored files, **When** the engineer opens file selection, **Then** only contained, supported files appear.
2. **Given** a valid upload, **When** the engineer selects display-only review, **Then** structured sections show recognized values and unresolved input.
3. **Given** invalid input, **When** the engineer submits it, **Then** a safe error appears and previous review becomes invalid.
4. **Given** absent cloud credentials, **When** the engineer inspects input, **Then** local review works and cloud checks show unavailable.

### User Story 2 - Select hardware and review a proposal (Priority: P1)

An engineer selects Branch, Hub, or Standalone and SRX or SSR hardware, then verifies the model and proposed changes.

**Why this priority**: A wrong role or port mapping can produce an unsafe deployment.

**Independent Test**: Exercise each role and hardware family with independent fixtures, including an unknown model and conflicting interface assignments.

**Acceptance Scenarios**:

1. **Given** parsed input, **When** the engineer selects a role and model, **Then** the proposal distinguishes supported, omitted, and uncertain settings.
2. **Given** an ambiguous port mapping, **When** conversion runs, **Then** the proposal requires correction and cannot authorize apply.
3. **Given** a reviewed proposal, **When** any input, target, role, model, or setting changes, **Then** previous approval becomes invalid.
4. **Given** a current proposal, **When** the engineer reviews and exports it, **Then** the export matches that proposal and contains no credentials.

### User Story 3 - Apply an approved change (Priority: P1)

An authorized operator selects an organization, site, and gateway, then approves the exact change set.

**Why this priority**: The migration must support cloud use without accidental or duplicate writes.

**Independent Test**: Use simulated cloud responses for success, refusal, stale state, partial failure, and an unknown write result.

**Acceptance Scenarios**:

1. **Given** valid permission and verified contracts, **When** the operator reviews the complete change set and types `APPLY`, **Then** only approved objects change.
2. **Given** absent approval, credentials, permission, or recovery evidence, **When** apply is requested, **Then** no cloud write occurs.
3. **Given** a timed-out write, **When** its outcome is unknown, **Then** the operator sees an indeterminate result and no automatic repeat occurs.
4. **Given** duplicate submission or another operator's change, **When** apply runs, **Then** duplicate creation and stale overwrite are prevented.
5. **Given** a new-site proposal, **When** the operator cancels, **Then** no site, template, profile, network, or service is created.

### User Story 4 - Perform controlled administration and recovery (Priority: P2)

An authorized operator creates backups and reviews restore, delete, or unassign actions with explicit object scope.

**Why this priority**: Administrative parity must not remove production data without a recovery plan.

**Independent Test**: Simulate each administrative operation, damaged backups, conflicting names, and failures during recovery.

**Acceptance Scenarios**:

1. **Given** permitted access, **When** backup runs, **Then** the complete private backup has a verified manifest and UTC timestamp.
2. **Given** a valid backup, **When** restore is reviewed, **Then** the proposal identifies updates, creations, conflicts, and unchanged objects.
3. **Given** delete or unassign scope, **When** either confirmation is rejected, **Then** no write occurs.
4. **Given** partial apply, **When** recovery is proposed, **Then** only recorded changes are reversible and recovery requires fresh approval.

### User Story 5 - Use the integrated visual workflow (Priority: P2)

An engineer uses a clear conversion card, structured review, proposal, confirmation, and status inside the existing portal.

**Why this priority**: The migration must retain the observed workflow without copying protected presentation assets.

**Independent Test**: Exercise desktop and narrow-screen journeys with keyboard input and each configured theme.

**Acceptance Scenarios**:

1. **Given** the pink and charcoal theme, **When** the converter opens, **Then** a centered selection card appears within the existing portal shell.
2. **Given** another configured theme, **When** review and confirmation open, **Then** readable controls retain the portal theme and focus behavior.
3. **Given** pending, unavailable, failed, or successful work, **When** status changes, **Then** text distinguishes these states without color alone.
4. **Given** the converter is unavailable, **When** another portal workflow opens, **Then** its routes, service connections, and behavior remain unchanged.

### Edge Cases

- Reject empty files, invalid encodings, null bytes, unsupported suffixes, traversal, drive paths, and symlink escapes.
- Accept exactly 16 MiB of file content. Reject one additional byte before parsing.
- Detect banner text, malformed masks, overlapping DHCP ranges, excluded addresses, missing hostname, and duplicate source directives.
- Identify ambiguous WAN/LAN classification, unknown ports, unsupported models, VLAN ranges, aggregation, and unmatched gateway inventory.
- Do not reconstruct one-way password hashes. Do not display decoded secrets in ordinary review, export, or logs.
- Distinguish unavailable cloud checks from verified object absence. Never create an object because a lookup failed.
- Handle permission failures, expired sessions, malformed responses, rate limits, pagination, disconnected browsers, and expired reviews.
- Report partial writes and failed recovery. Do not describe them as successful or fully reversible.

## Requirements *(mandatory)*

### Functional Requirements

| ID | Requirement |
| --- | --- |
| FR-001 | The portal must provide contained file listing, prepopulation, selection, and browser upload. |
| FR-002 | The portal must validate file path, suffix, size, and encoding before parsing. |
| FR-003 | The engineer must inspect structured input without conversion or cloud credentials. |
| FR-004 | Review must cover every observed parser family and identify unsupported or ambiguous input. |
| FR-005 | The engineer must select Branch, Hub, or Standalone without inferring the role from a hostname. |
| FR-006 | The engineer must select SRX or SSR and verify a supported model and explicit interface mapping. |
| FR-007 | Conversion must distinguish WAN, LAN, address, VLAN, DHCP, route, and VRF intent without silent assumptions. |
| FR-008 | Review must cover routing, management, identity, security, cellular, and flow-export families, including display-only limits. |
| FR-009 | Every proposal must show changes, omissions, unresolved mappings, target objects, and verification status. |
| FR-010 | Local preview must remain available when cloud credentials or cloud checks are unavailable. |
| FR-011 | Export must contain the exact current reviewed proposal and omit credentials. |
| FR-012 | The portal must distinguish cloud availability, permission, site existence, gateway inventory, and stale lookup results. |
| FR-013 | The operator must explicitly select existing or proposed new sites and assigned or unassigned gateways. |
| FR-014 | The proposal must distinguish role-appropriate templates, device profiles, site settings, variables, and device assignments. |
| FR-015 | The operator must approve the exact organization, site, gateways, and change set before any cloud write. |
| FR-016 | Apply must require exact typed `APPLY`, permission, current review, verified contracts, and recovery evidence. |
| FR-017 | A change to input, proposal, target, role, hardware, model, or current cloud state must invalidate approval. |
| FR-018 | Apply must prevent duplicate submission, stale overwrite, duplicate creation, and unsafe retries. |
| FR-019 | Apply must report each changed object and distinguish failure, partial completion, and indeterminate results. |
| FR-020 | Recovery must use complete verified backups, preserve unrelated changes, and require fresh approval. |
| FR-021 | Administrative mode must provide scoped backup and backup listing for policies, services, and networks. |
| FR-022 | Administrative mode must provide reviewed restore for policies, services, and networks. |
| FR-023 | Administrative mode must provide scoped service, network, and template deletion and template/device unassignment. |
| FR-024 | Administrative writes must require permission, scope review, two confirmations, exact typed `CONFIRM`, and verified recovery backups. |
| FR-025 | Converter views must retain the observed selection, structured review, proposal, and confirmation journeys in the existing portal. |
| FR-026 | Configured themes must cover the observed pink, red, neon, and green visual intentions without copied assets. |
| FR-027 | Health, status, loading, empty, error, cancel, and success states must remain distinct and accessible. |
| FR-028 | Input, backups, browser state, downloads, responses, and logs must obey credential and privacy controls. |
| FR-029 | The migration must preserve deployed portal behavior and shared storage, authentication, and services. |
| FR-030 | Each observed capability must retain traceable coverage, independent tests, and an explicit unsupported decision when parity is impossible. |
| FR-031 | No protected source expression may be reused without legal and owner approval. |
| FR-032 | Every contract and workflow test must use synthetic data and simulated responses without live credentials or cloud writes. |

Acceptance for FR-001 through FR-032 is defined by the story scenarios and the row-specific checks in [the comparison](design/research.md).

### Mist Cloud Transport Requirements

Use MistHelper's supported SDK transport for every Mist REST operation.
Do not add direct HTTP or a separate WebSocket transport.
The exact method inventory and pending payload evidence are in [the cloud contract](design/contracts/mist.md).
An available method is not proof that a proposed payload or hardware mapping is correct.
Missing contract evidence blocks the associated write.

### Key Entities

- **Source configuration**: Validated input, source identity, digest, and private content.
- **Parsed review**: Structured observations, source locations, redacted values, and unresolved items.
- **Proposal**: Target scope, role, model, mappings, object changes, omissions, and version.
- **Approval**: Operator permission, proposal identity, target identity, confirmation, and expiry.
- **Operation record**: Object identities, before-state evidence, write outcomes, and recovery status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every comparison row has a target decision, acceptance check, and remaining task. No observed workflow disappears from scope.
- **SC-002**: All six role/family combinations complete local review or show an explicit unsupported decision without cloud credentials.
- **SC-003**: Every apply and administrative write test proves zero writes after rejected, missing, expired, or changed approval.
- **SC-004**: Every simulated ambiguous write stops automatic repetition and exposes an indeterminate result.
- **SC-005**: Every supported input family has a positive and negative test. Unsupported families remain visible without invented output.
- **SC-006**: All four visual intentions pass keyboard, readable-text, desktop, and narrow-screen journey checks using independently authored assets.
- **SC-007**: All existing portal regression journeys retain their expected behavior and use no duplicate data service.
- **SC-008**: Every backup and recovery test verifies object scope and unrelated-state preservation. Every log and export test finds zero secret values.

## Assumptions

Full observed parity means workflow parity, not blind reproduction of source defects or unverified mapping claims.
Observed parser-only families require structured review and explicit limits, not automatic conversion without evidence.
Model-level selection is a required target extension to the observed SRX/SSR family controls.
Use the existing 16 MiB bound and UTF-8 policy unless the owner approves a documented change.
Use explicit operator selection instead of automatic hostname-based site creation.
Uploads use transient storage by default. Persistent prepopulation requires a private, contained area under `data/`.
Keep existing portal theme configuration. Do not introduce a competing theme setting.
The source's four theme labels do not require copied branding, animation, CSS, or names.
Legal review must decide any reuse request. This specification authorizes observation only.
Cloud and destructive operations require later owner authorization and operation-specific operator confirmation.
This work creates documentation only. It does not authorize implementation, publication, deployment, or live testing.
