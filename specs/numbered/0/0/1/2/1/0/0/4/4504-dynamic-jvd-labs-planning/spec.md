# Feature Specification: Dynamic JVD Labs in the Operations Portal (Planning)

**Feature Branch**: `4504-dynamic-jvd-labs-planning`

**Created**: 2026-10-30

**Status**: Draft (planning only)

**Input**: Issue #4504, "feat(labs): plan dynamic JVD deployment in the operations portal". Related planning: `jmorrison-juniper/vmm-topology-automation#19`.

## Scope Statement

This record is a plan. Issue #4504 authorizes planning only. It does not authorize
a product change, a submodule addition, a deployment, or a live lab operation.
Each implementation task and each live task in `tasks.md` stays unchecked until a
later, separately approved change delivers it.

The target is the existing Flask operations portal on port 8055 (`web_portal/`).
The separate React `ops-portal/` and `mist-ops-platform/` applications are not the
target. No frontend rewrite and no arbitrary executable template is in scope.
Repository visibility and licensing are excluded from this planning scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select a template and review a preview (Priority: P1)

An operator opens the Labs tab, picks a versioned template from the catalog, edits
its parameters in a form, and reads a topology preview and a validation result.
Nothing contacts a service, resolves a secret, or grants authority.

**Why this priority**: Preview is the safe base. Each later journey needs it.

**Independent Test**: Run the Flask test client with a fake engine. Select a
template, submit valid and invalid parameters, and compare the preview with the
engine plan.

**Acceptance Scenarios**:

1. **Given** a catalog with two template versions, **When** the operator opens a template, **Then** the page lists each version with its engine, host, schema, and catalog compatibility.
2. **Given** a valid parameter set, **When** the operator requests a preview, **Then** the page shows the topology, the resource budget, and the plan digest, and shows no approval control.
3. **Given** an invalid parameter, **When** the operator requests a preview, **Then** the page shows a field-level error and no plan digest.

---

### User Story 2 - Import and compose a template (Priority: P1)

An operator imports a YAML or JSON template and composes supported JVD building
blocks. The portal accepts only declarative data that the engine schema allows.

**Why this priority**: The user selected import and composition as part of the
dynamic catalog.

**Independent Test**: Upload valid, oversize, malformed, and executable-style
files. Compose blocks that the engine marks supported and unsupported.

**Acceptance Scenarios**:

1. **Given** a YAML file within the size bound, **When** the operator imports it, **Then** the portal stores it as a draft and shows the same preview as a catalog template.
2. **Given** a file with an unknown key, an anchor bomb, a tag, or an embedded command, **When** the operator imports it, **Then** the portal rejects it and stores nothing.
3. **Given** a composition that needs an unsupported role pairing, **When** the operator requests a preview, **Then** the engine reports the capability as unavailable with a reason.

---

### User Story 3 - Qualify and approve a deployment (Priority: P2)

An operator runs read-only qualification against the target backends, then gives a
typed approval that binds to the exact target and plan digest.

**Why this priority**: Approval is the safety gate for every mutation.

**Independent Test**: Approve a plan, change one parameter, and confirm that the
approval no longer applies.

**Acceptance Scenarios**:

1. **Given** a plan with a passing qualification, **When** the operator types the approval word, **Then** the portal records an approval for the exact action, intent digest, target, backend identity, engine revision, lease, and budget.
2. **Given** a recorded approval, **When** any bound value changes, **Then** the approval is invalid and the portal asks for a new one.
3. **Given** a browser that did not create a proposal, **When** it requests that proposal, **Then** the portal returns the same 404 as for a missing record.

---

### User Story 4 - Deploy and monitor (Priority: P2)

After approval, the portal starts a durable job. The operator watches sanitized
progress, inventory, link state, logs, events, lease time, and evidence freshness.

**Why this priority**: Deployment without observation is not operable.

**Independent Test**: Use the real ArangoDB backend with a fake engine. Restart the
worker in the middle of a job and confirm that status and evidence recover.

**Acceptance Scenarios**:

1. **Given** an approved plan, **When** the operator starts the deployment, **Then** the portal returns a job identifier and the page shows progress.
2. **Given** a browser refresh or an SSE disconnect, **When** the page reloads, **Then** the job continues and the page shows current state.
3. **Given** a worker restart, **When** the portal starts, **Then** each interrupted job shows `recovery-required` and no write repeats automatically.

---

### User Story 5 - Test, impair, and restore (Priority: P3)

The operator runs traffic tests and applies bounded WAN impairments. The portal
restores the prior state and verifies the restored profile.

**Why this priority**: These capabilities need new engine work first.

**Independent Test**: Apply an impairment to an owned fake bridge, force a partial
failure, and confirm that restoration runs and evidence remains.

**Acceptance Scenarios**:

1. **Given** an owned lab, **When** the operator proposes an impairment, **Then** the portal shows the bounded profile, the target identity, and the prior state before approval.
2. **Given** a partial or uncertain impairment write, **When** the job ends, **Then** the portal marks it `recovery-required` and offers a restoration proposal.
3. **Given** a management interface or a foreign qdisc, **When** the operator targets it, **Then** the engine refuses the request.

---

### User Story 6 - Clean up exactly (Priority: P3)

The operator removes a lab. The engine deletes only resources that a fresh
ownership check proves it owns, then verifies the deletion independently.

**Why this priority**: Cleanup protects shared infrastructure.

**Independent Test**: Seed foreign resources with a matching name prefix. Confirm
that cleanup leaves them untouched.

**Acceptance Scenarios**:

1. **Given** a resource with the lab name prefix but no ownership record, **When** cleanup runs, **Then** the engine skips it and reports it.
2. **Given** a deletion that the backend did not confirm, **When** the job ends, **Then** the portal reports `uncertain` and does not report `deleted`.

### Edge Cases

- ArangoDB is unavailable: the portal starts, preview works, and each persistence or action route returns an explicit unavailable error.
- `PORTAL_SECRET_KEY` is unset: browser proofs do not survive a restart. Safe history and new recovery proposals still work.
- Two operators propose overlapping address ranges at the same time: admission serializes them, and one proposal fails with a conflict.
- The engine version and the host version do not form a supported pair: the portal disables mutation and shows the pair.
- A template references a field that the schema later removes: the portal marks the saved draft `incompatible` and does not run it.
- The platform is Windows: the portal offers offline preview only until the project approves a cross-platform lock or a POSIX restriction.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST list a versioned template catalog with engine, host, schema, and catalog compatibility for each version.
- **FR-002**: The portal MUST import YAML and JSON templates under a bounded size, depth, and key count, and MUST reject tags, anchors that expand beyond the bound, unknown keys, and executable content.
- **FR-003**: The portal MUST render parameter forms from the engine-generated schema and MUST apply the engine cross-field checks.
- **FR-004**: The portal MUST compose only the building blocks that the engine capability list marks supported.
- **FR-005**: The portal MUST show a topology preview, a resource budget, and a plan digest, and MUST NOT grant authority from a preview.
- **FR-006**: The portal MUST run read-only qualification before it offers approval, and MUST report capability gates as `available`, `unavailable` with a reason, or `unverified`.
- **FR-007**: The portal MUST bind each typed approval to the exact action, intent digest, target, backend identity, engine revision, lease, resource budget, and permitted shared changes.
- **FR-008**: The portal MUST invalidate an approval when any bound value changes and MUST recheck authority immediately before each write.
- **FR-009**: The portal MUST run deployment, test, impairment, restoration, and cleanup as durable jobs outside request handlers.
- **FR-010**: The portal MUST persist intent and a stable recovery identity before it submits any write, and MUST reconcile an uncertain write before any repeat.
- **FR-011**: The portal MUST keep VMM, Mist, and guest credentials server-side and MUST redact them from responses, logs, SSE events, browser storage, and downloads.
- **FR-012**: The portal MUST return the same 404 for a foreign private proposal or job as for a missing record.
- **FR-013**: The portal MUST show monitoring data (inventory, VM and link state, logs, events, lease, freshness) with bounded pagination and polling.
- **FR-014**: The portal MUST distinguish draft cancellation, approval revocation, traffic cancellation, impairment restoration, and topology teardown, and MUST report an outcome only after remote verification.
- **FR-015**: The engine MUST bound impairment profiles, permit only declared interfaces, capture prior state, verify the observed profile, and restore after a partial or uncertain write.
- **FR-016**: The engine MUST verify ownership freshly before each destructive action and MUST NOT infer ownership from a name prefix alone.
- **FR-017**: The portal MUST store integrated records in the existing ArangoDB backend through host-owned repositories and MUST NOT use a SQLite journal or the generic ingestion router.
- **FR-018**: The portal MUST apply the existing allowlist, trusted-proxy, CSRF, and session mechanisms to every Labs route and MUST add no login or role system.
- **FR-019**: The portal MUST NOT register lab mutations in the generic Operations registry as `safe` operations.
- **FR-020**: The delivery MUST pin the framework as a Git submodule at an exact commit and MUST install only the `framework/` runtime package.
- **FR-021**: The portal MUST NOT import legacy scripts, legacy run records, or legacy guest protocols.
- **FR-022**: Each interactive element MUST carry a stable `data-testid`, and each failed browser flow MUST retain a screenshot or trace artifact.

### Mist Cloud Transport Requirements

- Every Mist REST call from the engine host adapter MUST use a working `mistapi` method that the host session supplies. Direct HTTP to a Mist endpoint is prohibited.
- The host adapter MUST preserve exact PUT replacement semantics and MUST route through the host request allowance.
- Contract tests MUST prove SDK authentication, endpoint parity, failure safety, and secret redaction. No owned WebSocket transport is proposed.
- The exact `mistapi` methods are a planning decision recorded in `design/contracts/engine-contract.md` and confirmed in task T030.

### Key Entities

- **Template**: A versioned declarative definition with a schema version and parameters.
- **Draft**: An immutable saved snapshot of template plus parameters, with a plan digest.
- **Plan**: The deterministic engine output for a draft, with provenance and budget.
- **Approval**: A typed, browser-bound record tied to an exact plan and target.
- **Job**: A durable unit of work with an owner proof, state, and evidence.
- **Lab Run**: The observed resources of one deployment, with ownership records.
- **Capability**: An engine feature with an availability state and a reason.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `spec.md`, `plan.md`, and `tasks.md` exist, and `analysis.md` reports zero unresolved contradictions.
- **SC-002**: Each functional requirement maps to at least one task and one test in the traceability table of `tasks.md`.
- **SC-003**: Each user story has a complete GUI journey with named `data-testid` values in `design/quickstart.md`.
- **SC-004**: Each unchecked implementation and live task in `tasks.md` stays unchecked, and a guard test fails if one becomes checked without an evidence note.
- **SC-005**: Each open implementation decision appears in `analysis.md` with an owner and a blocking task.

## Assumptions

- The Flask portal, its access controls, its Mist SDK session, and its ArangoDB backend stay unchanged by this plan.
- The `vmm_topology` framework at the revision that issue #19 inspected has only a dual-hub compiler, so dynamic composition needs engine work.
- The engine revision, the pinned commit, and all numeric limits are open decisions that later tasks settle.
- Isolated live acceptance needs a separate approval and is outside this plan.
- Repository visibility and licensing are excluded, as the issue directs.
