# Feature Specification: Ordered Multi-Site Firmware Families

**Feature Branch**: `feat/4021-ordered-multi-site-firmware-phases`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4021, child 3 of parent #3332. The multi-site aggregate service sends access points before gateways and switches. It also continues after a refusal. This feature enforces one family order and one gate between families.

## Terms

Each term below names one concept. Use the same term in every record file.

- **Family**: One device group in the submission order. The families are gateway, switch, and access point (AP).
- **Gateway family**: Junos gateways and session smart routers (SSR). An SSR child keeps the device family `ssr` and belongs to the gateway family.
- **Child**: One durable cloud-call record inside the parent record.
- **Parent record**: The durable aggregate operation record. Its key is `operation_id`.
- **Family gate**: The wait that ends when one family settles. It returns `settled`, `failed`, or `unknown`.
- **Upstream proof**: The `settled` family gate result of the family above.
- **Background run**: The thread that submits families after the HTTP request returns.
- **Stop record**: The durable evidence of one stop. It names the family, the reason, and the child identities.
- **Refusal**: A cloud reply that proves that no job exists. The child status is `rejected`.
- **Unknown outcome**: A cloud reply that proves neither a job nor a refusal. The child status is `submission_unknown`.
- **Phase watch**: The read-only observer in `org_cascade/walk.py`. The word phase stays only in the existing names `PHASE_ORDER`, phase limit, and phase watch.

## Clarifications

### Session 2026-11-26

- Q: Which families receive firmware, and in which order?
  A: Gateway, then switch, then AP. An SSR child belongs to the gateway family. Clients receive no firmware. Source: owner decision on #4020, comment of 2026-10-07.
- Q: Does a refusal stop only its child?
  A: No. A refusal stops the rest of its family and every later family. Source: owner decision 1 on #4020 and the single-site rule in `wiring.py`.
- Q: Does the family gate need a new timeout?
  A: No. The family gate uses the existing phase limit of 1800 seconds. Source: owner decision 1 on #4020.
- Q: Does an unknown outcome allow a retry?
  A: No. The run stops, and the child keeps the status `submission_unknown`. Source: owner decision 3 on #4020.
- Q: Does an empty family need a gate?
  A: No. An empty family skips the gate and every cloud call. Source: owner decision 2 on #4020.
- Q: Does this change implement resume?
  A: No. Durable resume belongs to issue #4022.
- Q: Does the phase watch control the order of writes?
  A: No. The background run controls the writes. The phase watch reads the stored family gate result.
- Q: Does any decision need a human decision under section 6 of the brief?
  A: No. No decision falls in the categories of section 6.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit families in one order across sites (Priority: P1)

An operator selects access points, switches, and gateways at several sites. The portal sends the gateway family first. It sends the switch family after the gateway family settles. It sends the AP family last.

**Why this priority**: The current order sends access points first. An access point can lose its upstream path during its own firmware write.

**Independent Test**: Use three mocked sites with one device of each family. Run the aggregate service with stand-ins. Record each cloud call in order.

**Acceptance Scenarios**:

1. **Given** access points, switches, and gateways at three sites, **When** the run starts, **Then** the first cloud call targets the gateway family.
2. **Given** a settled gateway family, **When** the run continues, **Then** the switch call happens before the AP call.
3. **Given** an SSR child and a Junos gateway child at one site, **When** the plan builds, **Then** both belong to the gateway family.

---

### User Story 2 - Stop the run on a refusal, an unknown outcome, or a failed family gate (Priority: P1)

A cloud reply refuses a gateway call. The run stops the rest of the gateway family and every later family. The run writes a stop record before it ends. No later family receives a firmware call.

**Why this priority**: A later write after a refused upstream write can leave devices without a path to the cloud.

**Independent Test**: Use a mocked gateway call that returns a refusal. Verify that no switch or AP call happens and that the stop record reads back from the store.

**Acceptance Scenarios**:

1. **Given** a refused gateway child, **When** the family gate is not reached, **Then** no switch child and no AP child receive a call.
2. **Given** an unknown outcome for a switch child, **When** the run stops, **Then** the switch child keeps `submission_unknown` and no retry happens.
3. **Given** a family gate that returns `failed` or `unknown`, **When** the run reaches the next family, **Then** the run stops before the next family.

---

### User Story 3 - Keep the phase watch and the operator view consistent (Priority: P2)

The phase watch reads the stored family gate result. It does not start a second wait for a family that the background run already settled. The operator sees a running state during each family gate and an attention state after a stop.

**Why this priority**: Two gate waits for one family double the cloud reads. Two results for one family confuse the operator.

**Independent Test**: Use a stored `settled` family result and a mocked gate. Verify that the phase watch makes no gate call for that family.

**Acceptance Scenarios**:

1. **Given** a stored `settled` gateway result, **When** the phase watch reaches the gateway family, **Then** it makes no gate call.
2. **Given** a stop record, **When** the phase watch reads the later families, **Then** it marks them as not submitted and makes no gate call.
3. **Given** a background run waits for a family gate, **When** the operator reads the status, **Then** the state shows running with the family name.

---

### User Story 4 - Skip empty families and never send client firmware (Priority: P3)

A selection with no switch targets skips the switch family without a gate wait. A client never receives a firmware call.

**Why this priority**: An empty family must not block the run. A client call would exceed the approved scope.

**Independent Test**: Use a mocked selection with gateways and APs but no switches. Verify that the switch family records `skipped` and that no client child exists.

**Acceptance Scenarios**:

1. **Given** no switch target, **When** the run reaches the switch family, **Then** the run records the switch family as skipped and makes no gate call.
2. **Given** any selection, **When** the run builds the children, **Then** no child has the client family.

---

### Edge Cases

- A refused child in the middle of a family stops the remaining children of that family.
- A family gate that reaches the phase limit of 1800 seconds returns `failed` and stops the run.
- A cancellation request during a family gate wait stops the run before the next family.
- A lock loss between two families stops the run before the next family.
- A background run that ends during a family gate wait leaves no resend. The next status read records the stop reason `process_lost`.
- A site with a Junos gateway and an SSR child keeps the build order inside the gateway family.
- A family with two AP versions uses site children. Every child of that family keeps the family rule.
- A selection with one site and no AP target creates no AP child.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The aggregate service MUST order the children in the families gateway, switch, and AP. An SSR child belongs to the gateway family.
- **FR-002**: The aggregate service MUST send no child of a later family before the earlier family has an upstream proof.
- **FR-003**: The aggregate service MUST define a portal-neutral family gate interface. The upgrade portal MUST supply the implementation.
- **FR-004**: The family gate MUST reuse the existing phase limit of 1800 seconds. The change MUST add no independent timeout.
- **FR-005**: The aggregate service MUST treat a missing, failed, unknown, or late family gate result as a stop.
- **FR-006**: An empty family MUST skip its gate wait and its cloud calls. An empty family MUST NOT count as a failure.
- **FR-007**: A refusal MUST stop the rest of its family and every later family.
- **FR-008**: An unknown outcome MUST stop the rest of the run. The child MUST keep the status `submission_unknown`.
- **FR-009**: The aggregate service MUST NOT resend a child with a status other than `planned`. The change MUST add no automatic retry.
- **FR-010**: A stop MUST write a stop record through compare-and-set before the background run ends.
- **FR-011**: A lock loss or a cancellation request MUST stop every later write. The stop MUST be durable.
- **FR-012**: The run MUST send no firmware to clients. The client phase MUST remain observation only.
- **FR-013**: The aggregate service MUST hold the parent claim only while it sends one family. It MUST hold no parent claim during a family gate wait.
- **FR-014**: The site locks MUST remain held until a final state. The background run MUST renew the site locks during each family gate wait.
- **FR-015**: The HTTP route MUST validate the request and start the background run. The route MUST NOT wait for a family gate.
- **FR-016**: The phase watch MUST read the stored family gate result. It MUST NOT start a second wait for that family.
- **FR-017**: Each stop sentence MUST name the family and the next operator action. A stop sentence MUST NOT contain a host, a token, or a cloud body.
- **FR-018**: The change MUST NOT implement resume. The stop record MUST stay readable by issue #4022.
- **FR-019**: A wait marker older than the claim lease MUST end the run as `process_lost` on the next status read. The status read MUST NOT resend any child.
- **FR-020**: Each existing test that asserts the defect MUST change in the same commit. Each changed test MUST name the replaced behavior in its docstring.

### Mist Cloud Transport Requirements

- The change reuses the existing mistapi calls. The organization access point call is `upgradeOrgDevices`. The site call is `upgradeSiteDevices`. The single-device call is `upgradeDevice`. The SSR call is `upgradeOrgSsrs`.
- The change adds no direct HTTP request to a Mist endpoint.
- The change adds no owned WebSocket transport.
- Contract evidence uses doubles. No test sends a live Mist request.

### Key Entities

- **Parent record**: The operation key, the site names, the children, the family gate results, the stop record, and the claim fields.
- **Child**: The route, the scope, the family, the targets, the status, and the cloud identity.
- **Family gate result**: The family, the state, the count of devices that did not return, and the record time.
- **Stop record**: The stopped family, the reason code, the child identities, the operator sentence, and the stop time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In every mocked run with three families, the cloud calls follow the order gateway, switch, AP.
- **SC-002**: After one refused gateway call, the mocked run records zero switch calls and zero AP calls.
- **SC-003**: With a gate that settles after three polls, no switch call happens before the third poll.
- **SC-004**: After one unknown outcome, the mocked run records exactly one call for that child and no later call.
- **SC-005**: The stop record reads back after a JSON round trip with every field of the contract.
- **SC-006**: The change adds no new Mist endpoint and no new Python module.

## Out of Scope

- Durable resume and resume actions. Issue #4022 owns them.
- Any firmware call to a client.
- Any change to the single-site driver. Issue #4020 owns it.
- The stale mistapi version comment in `upgrade_service.py`. A separate issue owns it.
- A change to the destructive confirmation word or the registry category of menu 239.

## Assumptions

- The owner decisions 1, 2, and 3 on #4020 apply to this change without change.
- The phase limit of 1800 seconds stays unchanged.
- The `RunStore` compare-and-set contract stays unchanged.
- The operator reads the stop record in the existing run page. No new page is required.

## Safety

Warning: a wrong family order can remove the upstream path of many devices at once. A multi-site failure takes longer to repair than a single-site failure.

Caution: a stopped run keeps its site locks until the run reaches a final state. Read the run before any new action.
