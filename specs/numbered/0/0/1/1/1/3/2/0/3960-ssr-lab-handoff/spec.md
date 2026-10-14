# Feature Specification: SSR lab runbook validation

**Feature Branch**: `jmorrison-juniper-spec-3960-ssr-lab-handoff`

**Created**: 2026-10-14

**Status**: Specified. Physical validation remains blocked on human lab access.

**Input**: [Issue #3960](https://github.com/jmorrison-juniper/MistHelper/issues/3960)
requires six lab observations for the optic and Mist cloud path runbook.
The current assignment creates and analyzes artifacts only.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify optic guidance by release (Priority: P1)

A lab engineer needs measured command results before a junior engineer uses the optic guidance during an outage.

**Why this priority**: Incorrect command syntax or unsupported fields can delay fault isolation.

**Independent Test**: Review four sanitized observations against the release and fiber-port conditions.
An absent observation must remain `Not run`.

**Acceptance Scenarios**:

1. **Given** an SSR 7.0.x lab router, **When** the engineer tests both optic command forms, **Then** the record preserves both exact errors.
2. **Given** that router, **When** the engineer reads the named interface, **Then** the record confirms or corrects each claimed field.
3. **Given** a fiber port on SSR 7.1.0-50r1 or later, **When** the engineer reads optic statistics, **Then** the record names measured power and threshold fields.
4. **Given** missing lab access, **When** an agent prepares the artifacts, **Then** all four observations remain incomplete.

### User Story 2 - Verify Mist state fields (Priority: P2)

A lab engineer needs to distinguish documented field names from measured output of the detailed Mist state command.

**Why this priority**: The source describes columns of the summary command, not confirmed fields of the detailed command.

**Independent Test**: Compare a sanitized detailed output with the `Agent` and `Connection` claims.

**Acceptance Scenarios**:

1. **Given** a lab SSR, **When** the engineer reads detailed Mist state, **Then** the record confirms or corrects both field names.
2. **Given** an absent or different field, **When** the engineer reviews the output, **Then** the runbook states the measured difference.

### User Story 3 - Verify portal behavior during cloud loss (Priority: P3)

A human lab operator needs evidence about portal `Testing Tools` when the SSR cloud path is blocked.

**Why this priority**: This experiment can interrupt Mist management and requires an independently recoverable lab.

**Independent Test**: Review the approved experiment, the cloud-loss observation, the tool results, and the recovery evidence together.

**Acceptance Scenarios**:

1. **Given** explicit approval and an independent console, **When** a human blocks the lab cloud path, **Then** the record identifies actual portal tool behavior.
2. **Given** a tool that operates during confirmed cloud loss, **When** the engineer updates the runbook, **Then** the last sentence reflects that evidence.
3. **Given** failed recovery, **When** the operator ends the experiment, **Then** the record reports the failure and does not claim completion.

### Edge Cases

- An SSR 7.0.x command succeeds unexpectedly. Record the exact release and output instead of forcing the expected error.
- A port is not a fiber port. Do not use it to confirm optical power or threshold fields.
- The detailed Mist output lacks a claimed field. Record the actual names and preserve the distinction from summary columns.
- The cloud block does not interrupt the agent connection. Treat the experiment as inconclusive, not as proof about tool independence.
- Output contains customer data. Remove addresses, serial numbers, customer names, and secrets before any repository or issue record.
- A required observation is absent. Record `Not run` and its cause without a copied or inferred result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The validation MUST cover all six unchecked observations in issue #3960 without treating artifact creation as lab completion.
- **FR-002**: The SSR 7.0.x record MUST preserve the exact result of `show device-interface <name> optics-statistics`.
- **FR-003**: The SSR 7.0.x record MUST preserve the exact result of `show device-interface name <name> optics-statistics`.
- **FR-004**: The SSR 7.0.x record MUST confirm or correct admin status, operational status, speed, and error-counter claims.
- **FR-005**: A fiber-port observation on SSR 7.1.0-50r1 or later MUST name the actual power-level and threshold fields.
- **FR-006**: The detailed Mist-state observation MUST confirm or correct the `Agent` and `Connection` field claims.
- **FR-007**: A human-approved lab experiment MUST record portal `Testing Tools` behavior during confirmed TCP port 443 cloud loss and subsequent recovery.
- **FR-008**: Each observation MUST identify its release, port type where relevant, UTC timestamp, sanitized output, result, and limitation.
- **FR-009**: Missing evidence MUST remain `Not run` with its cause. Source documentation MUST NOT substitute for a measurement.
- **FR-010**: A later runbook update MUST reconcile measured findings with section 11, step C2, the fallback optic procedure, and step D7.
  The update MUST also reconcile the cloud-path conclusion and section 14 verification rows.
- **FR-011**: The current assignment MUST NOT execute lab commands, block connectivity, change runbooks, edit the protected verifier, implement tasks, or open a pull request.
- **FR-012**: A later publication MUST include one issue-specific release fragment, document checks, and a fresh ownership review.
  Issue #3960 MUST remain open until all six observations and the recovery evidence receive review.

### Key Entities

- **Lab observation**: One of the six issue tasks, with its release conditions, sanitized evidence, status, and reviewer.
- **Lab experiment approval**: Human authorization, isolated target, independent recovery path, and recovery result for the cloud-loss observation.
- **Runbook correction**: A measured finding linked to its specific runbook section and source observation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The plan and task list cover all six issue observations, with zero observations marked complete during artifact preparation.
- **SC-002**: A future reviewer can trace all six observations to a release, timestamp, sanitized result, and runbook destination.
- **SC-003**: All published observations contain zero customer addresses, serial numbers, customer names, or secrets.
- **SC-004**: The future cloud-loss record contains human approval, confirmed loss, portal results, and confirmed recovery.
- **SC-005**: Every future runbook correction passes the repository writing and link checks before publication.

## Assumptions

- This assignment stops after specify, plan, tasks, and analysis. It does not deliver the six lab observations.
- A human will supply authorized lab access and the required software releases later.
- A router with no independent console recovery path cannot satisfy the cloud-loss experiment prerequisites.
- [Issue #3959](https://github.com/jmorrison-juniper/MistHelper/issues/3959) remains the coordination record.
  The parent session already recorded the current claim.
- [PR #4114](https://github.com/jmorrison-juniper/MistHelper/pull/4114) merged verification-status documentation on 2026-10-10.
  That documentation does not complete physical validation.
- Existing release and command claims are hypotheses for measurement, not new verified results.
