# Feature Specification: Issue 3862 WebSocket Dialog Audit

**Feature Branch**: `jmorrison-juniper-websocket-dialog-testing`

**Created**: 2026-10-04

**Status**: GET-only live dialog inspection implemented and measured; target availability and UX gaps remain

**Input**: [Issue #3862](https://github.com/jmorrison-juniper/MistHelper/issues/3862).
Audit all WebSocket operation dialogs through normal user stories with a Playwright harness.
Use the LIVE Mist organization for READ-ONLY journeys.
Track distinct defects, then repair and verify them through SpecKit in later phases.
Keep the existing app-managed branch. The original invocation created the specification.
Implementation now includes isolated and live GET-only inspection, without any operation execution.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand an Operation and Select Its Target (Priority: P1)

A NOC engineer opens the WebSockets page and selects an operation.
The dialog explains its actual purpose and requests the scope and target that the operation needs.
The engineer can cancel without starting the operation.

**Why this priority**: Misleading purpose text or missing selectors can cause incorrect target selection.

**Independent Test**: Inspect an operation dialog without starting it.
Compare its purpose and fields with verified operation behavior.
Record a result for purpose, required selectors, dependent choices, and cancellation.

**Acceptance Scenarios**:

1. **Given** an available operation, **When** the engineer opens its dialog, **Then** the purpose matches verified behavior and identifies its scope.
2. **Given** an operation requires a site, device, or client, **When** its dialog opens, **Then** each required selector is present and labeled.
3. **Given** required selections are incomplete, **When** the engineer attempts to continue, **Then** the dialog prevents submission and identifies missing selections.
4. **Given** the engineer changes a site or device, **When** dependent choices refresh, **Then** stale selections clear and unrelated targets cannot be submitted.
5. **Given** an open dialog, **When** the engineer cancels, **Then** no operation starts and no pending selection request starts it later.
6. **Given** unsafe or unverified behavior, **When** the dialog is inspected, **Then** execution remains blocked regardless of its displayed purpose.

---

### User Story 2 - Observe and Stop a Verified Read-Only Stream (Priority: P1)

A NOC engineer uses existing local authentication to select current live targets.
The engineer starts only a verified read-only subscription, observes its output, and stops it.
The audit must never authorize a live operation from its name alone.

**Why this priority**: Live evidence matters, but production safety takes precedence over audit coverage.

**Independent Test**: Run one approved read-only journey after capability checks pass.
Record selection, observation, stop behavior, and the evidence source without exposing private data.

**Acceptance Scenarios**:

1. **Given** verified read-only behavior and an available authenticated portal, **When** the engineer selects a target, **Then** choices reflect the selected live scope.
2. **Given** an allowed subscription, **When** it starts, **Then** the engineer sees output or an explicit no-data or failure outcome within the observation limit.
3. **Given** an active subscription, **When** the engineer stops it, **Then** delivery ends within five seconds and the page reports that it stopped.
4. **Given** unavailable portal, browser, authentication, or test dependencies, **When** a live journey is requested, **Then** its result is blocked with a specific reason.
5. **Given** simulated services, **When** a journey passes, **Then** the report labels it isolated evidence and does not claim live success.
6. **Given** an unknown request or subscription, **When** a journey would use it, **Then** the audit blocks it before transmission.

---

### User Story 3 - Record Coverage and Distinct Defects (Priority: P2)

The audit owner can determine which dialogs were inspected, which journeys ran, and which defects need repair.
Each distinct defect links to one GitHub issue under the existing parent issue.

**Why this priority**: Clear records prevent duplicate work and false claims of complete coverage.

**Independent Test**: Review an audit report containing inspected, blocked, skipped, and failed cases.
Confirm that each confirmed defect links to a unique existing or newly created issue in a later authorized phase.

**Acceptance Scenarios**:

1. **Given** the available operation inventory, **When** the report is reviewed, **Then** every operation has a recorded inspection result or explicit blocker.
2. **Given** a confirmed defect, **When** issue tracking begins, **Then** an existing matching issue is reused or one distinct issue is created and linked.
3. **Given** multiple symptoms with one verified cause and repair, **When** they are recorded, **Then** one issue includes all affected operations.
4. **Given** screenshots, traces, or stream output, **When** evidence is reported, **Then** raw artifacts stay local and published summaries contain no private identifiers or secrets.
5. **Given** blocked or skipped cases, **When** totals are reported, **Then** they remain separate from passed cases and explain why execution did not occur.

---

### User Story 4 - Repair a Confirmed Defect Without Changing Operation Meaning (Priority: P3)

In a later authorized phase, a maintainer repairs a linked defect and verifies the original user story.
The maintainer preserves existing operation behavior and records release and review evidence.

**Why this priority**: Repairs depend on inspection evidence, issue tracking, and resolved file ownership.

**Independent Test**: Verify one linked repair with an isolated regression case.
Confirm that the intended purpose, required selectors, and dependent choices are correct without running prohibited live actions.

**Acceptance Scenarios**:

1. **Given** a linked defect, **When** a repair is verified, **Then** a regression case demonstrates the defect before repair and the expected behavior afterward.
2. **Given** a user-visible repair, **When** it is submitted for review, **Then** a unique release-note fragment and exact validation results accompany it.
3. **Given** files owned by another open pull request, **When** a repair needs those files, **Then** work remains blocked until ownership coordination is recorded.
4. **Given** a proposed commit or merge, **When** release work is authorized, **Then** applicable checks pass and the pull request retains the repository template.
5. **Given** a proposed destructive change or production restart, **When** the workflow reaches it, **Then** separate human approval is required.

### Edge Cases

- An organization has no sites, or a site has no compatible devices or clients.
- Authentication expires, access is denied, or a selection request is rate-limited.
- A target disappears or becomes unavailable after the engineer selects it.
- Selection requests complete out of order after rapid scope changes.
- Different targets have identical display names.
- A subscription connects but returns no events during the observation interval.
- A subscription disconnects before output arrives or during cancellation.
- Dialog purpose text implies observation, but verified behavior executes a device utility.
- A dialog opens with saved values that belong to another site.
- A user cancels while choices load, or stops while a connection is opening.
- An operation is visible but lacks verified safety evidence.
- An existing issue already covers the same confirmed defect.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The audit MUST inventory every available WebSocket operation on the selected portal revision.
  Each record MUST identify the operation and evidence revision without private target identifiers.
- **FR-002**: Each dialog inspection MUST compare displayed purpose with verified behavior, not only the operation name.
  It MUST assess scope, required fields, and required site, device, and client selectors.
- **FR-003**: Required selectors MUST contain current choices for the selected scope.
  Scope changes MUST clear invalid dependent selections and prevent submission of stale targets.
- **FR-004**: Empty choices, unavailable targets, and selection failures MUST show distinct, understandable outcomes.
  Missing required selections MUST prevent submission.
- **FR-005**: Canceling a dialog MUST NOT start an operation.
  Stopping an allowed stream MUST terminate delivery and show its stopped state.
- **FR-006**: Live execution MUST use only verified GET requests and verified read-only subscriptions.
  Each allowed action MUST have recorded evidence of its behavior, scope, and absence of prohibited side effects.
- **FR-007**: Unknown or unverified live actions MUST fail closed before transmission.
  Opening a dialog MUST NOT bypass this rule through automatic loading or background actions.
- **FR-008**: Live tests MUST NOT execute shell commands, device utilities, packet capture, or change operations.
  They MUST NOT restart production services or change credentials.
  This restriction concerns remote operations, not local commands used to prepare or run tests.
- **FR-009**: Tests MUST use existing local authentication.
  Credentials, client identifiers, and private network data MUST NOT appear in published reports or GitHub issues.
  Screenshots and traces MUST remain local with access restricted to the audit operator.
- **FR-010**: Selection and connection waits MUST end within 15 seconds each.
  Stream observation MUST end within 30 seconds, and each journey MUST end within 90 seconds, including cleanup.
  The 120-second outer pytest timeout additionally covers fixture/browser startup and report teardown;
  it is not a 120-second observation allowance.
  A timeout MUST report its stage and MUST NOT trigger an unverified fallback.
- **FR-011**: Results MUST distinguish passed, failed, blocked, and skipped journeys.
  Each result MUST identify live or isolated evidence, the exact validation command, its outcome, and its duration.
- **FR-012**: Every confirmed distinct defect MUST have one linked GitHub issue before repair begins.
  Issue records MUST include sanitized reproduction steps, expected behavior, observed behavior, and acceptance criteria.
  Existing matching issues MUST be reused. Issue #3862 MUST NOT be duplicated.
- **FR-013**: Repairs MUST preserve operation meaning and existing supported behavior.
  Each repair MUST have isolated regression evidence and a release-note fragment when user-visible.
- **FR-014**: The original specification phase creates specification artifacts only.
  The implementation phase maps normal-user inspection, distinct issues, repairs, and verification to these requirements.
  The parent handles GitHub updates and publication. This harness session does not commit, push, or merge.
- **FR-015**: Later changes MUST respect open pull request ownership.
  Commit and merge work MUST wait for applicable checks and authorized review.
  Production deployment or restart requires separate authorization.
- **FR-016**: The harness MUST NOT start or change containers.
  The user authorized the parent to start the normal portal on loopback port8055.
  Additional test environments must follow repository test-service lifecycle rules.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

This specification introduces no Mist Cloud transport, endpoint, or subscription.
It audits existing user journeys.
Live authorization requires an operation-specific inventory during planning and verification.

- Record each existing Mist SDK REST method used for live selector reads.
  Verify that each action is a GET and that its scope matches the selected target.
- Use working SDK REST methods. Do not substitute direct Mist REST requests.
- Record each matching SDK subscription path before permitting a live subscription.
  Verify authentication, endpoint scope, output, stop behavior, failure safety, and secret redaction.
- A new or changed owned WebSocket transport is outside this specification.
  Such work requires a separate decision naming the matching SDK path and its failed output contract.
  Contract tests must prove SDK insufficiency before implementation review.
- Do not invent method names or mark operations safe before this evidence exists.
  Missing evidence blocks live execution, not the specification.

### Key Entities *(include if feature involves data)*

- **Operation Inventory Entry**: An available operation, its verified purpose, target requirements, revision, and safety classification.
- **Journey Result**: The operation, inspected behavior, execution status, evidence source, timing, command, and blocker or failure reason.
- **Defect Record**: A distinct confirmed defect, affected operations, sanitized reproduction, acceptance criteria, and linked GitHub issue.
- **Safety Decision**: Verified behavior and scope evidence that permits a GET or read-only subscription, or explains why it remains blocked.
- **Local Evidence Artifact**: Restricted screenshots, traces, and reports linked to a journey. Published summaries omit private data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of inventoried operations have a recorded dialog inspection result or an explicit inspection blocker.
  All blocked inspections must be resolved before claiming a complete audit.
- **SC-002**: 100% of inspected dialogs have results for purpose, required selectors, dependent choices, empty results, and cancellation.
- **SC-003**: Zero prohibited or unverified live actions occur during audit journeys.
  Zero credentials, client identifiers, or private network details appear in published evidence.
- **SC-004**: Each operation inspection remains bounded. The complete serial all-site/map audit ends within 120 seconds.
  Allowed streams stop within five seconds of a stop request.
- **SC-005**: 100% of live-eligible operations have a live result or explicit blocker.
  No isolated result counts as a live pass, and no blocked or skipped result counts as a pass.
- **SC-006**: 100% of confirmed distinct defects have one linked issue before repair.
  Every completed repair has passing regression evidence and meets its issue acceptance criteria.
- **SC-007**: For each repaired dialog, an independent reviewer can identify its purpose and required target without external instructions.
  All reviewer journeys select a valid target or receive a clear explanation that no valid target is available.
- **SC-008**: Every proposed repair pull request includes exact validation results and required review sections.
  No commit or merge occurs before applicable checks pass and authorization is available.

## Assumptions

- The chosen environment is the LIVE Mist organization, with READ-ONLY tests only.
  The operator can use existing local authentication without sharing credentials.
- The user selected Playwright as the browser test tool.
  Its installation and harness design belong to planning, not this specification.
- Default wait limits are 15 seconds per selection or connection, 30 seconds for observation, and 90 seconds per journey.
  The implemented exact-key journey observes for five seconds. The outer pytest bound is 120 seconds.
  The all-parent inspection traversal shares a 90-second deadline inside that outer bound.
  Rate limits and empty event streams are valid outcomes, not proof of a broken dialog.
- Site, device, and client selectors are required only when verified operation scope needs them.
  Do not add unnecessary selectors to organization-wide operations.
- The actual operation inventory and safe live action list are not yet verified.
  Planning must establish both before audit execution.
- Existing simulated browser fixtures provide isolated regression evidence only.
  They do not establish live selector freshness, live authentication, or live subscription behavior.
- Historical evidence: at specification time, `localhost:8055` was unreachable and this worktree had no `.venv`.
  The parent subsequently installed the repository environment and Playwright Chromium.
  The user authorized the parent to start the normal portal. It now serves the authorized loopback8055 origin.
  Default live inspection runs through guarded GET reads.
  A separate user-authorized mode permits only the verified `site.stats.devices` observation lifecycle.
- Restoring live capability requires an available authorized portal, browser, test dependencies, and usable local authentication.
  It also requires verified safety evidence for every requested live action.
- Open PR #3814 owns `src/mist/realtime/websocket_streams/web/static/websockets.js`
  and `tests/e2e/websockets_tab/test_websockets_page.py`.
  This invocation leaves both files unchanged. Future overlapping repairs require ownership coordination.
- Keep `jmorrison-juniper-websocket-dialog-testing` unchanged.
  The specification directory is independent of the branch name.
- Constitution 1.7.1 governs later implementation and quality gates.
  Planning must record existing `specs/` hierarchy debt and a separate incremental remediation action.
- No database migration, credential change, new transport, production restart, or deployment is included.
  Later release work must reconcile the deployment workflow with the separate production authorization requirement.

### Open Planning Decisions and Blockers

1. Identify an authorized, reachable portal and restore browser and test capability without restarting production.
2. Verify the operation inventory, selector-read methods, and subscription behavior. Unverified actions remain blocked.
3. Resolve PR #3814 ownership before any repair touches its files.
4. The user authorized testing, repair, commit, and merge. Passing checks and ownership clearance remain prerequisites.
   The parent publishes changes. This session does not perform those actions.

### Current measured capability and UX evidence

All 72 forms have real live rendered inspection evidence.
All four portal-returned sites and each returned map are inspected serially.
Dependent selector responses stay in memory and are reused only within one audit context.
Default inspection denies unknown reads, redirects, writes, starts, subscriptions, utilities, captures, and shell actions.
The explicit `live-readonly` mode permits one exact `site.stats.devices` start and only its returned session's
message reads and local stop. The verified runner sends observation SUBSCRIBE, not a remote Mist mutation.
The user's read-only authorization includes this journey. No additional whole-server enforcement or approval is imposed.

Availability coverage does not prove complete UX acceptance.
The operation form has no Cancel control. Record this as one shared user-story gap.
SDK/DOM review records four optional client-choice enhancements:
`ex.releaseDhcpLeases`, `srx.releaseDhcpLeases`, `ssr.releaseDhcpLeases`, and `ex.retrieveMacTable`.
The SDK allows other target paths. Typed optional MAC inputs do not prove functional failure.
Do not require individual client selectors for site/map aggregate channels or treat AP MAC as a client target.

Live target availability currently passes for 69 operations.
Three operations have genuine empty choices across all returned scopes.
This is not a complete audit pass. It does not authorize execution of any operation.
The distinct opt-in channel journey does not authorize any utility, capture, shell, or other channel.

The parent verified deployed/local base `2900f56` equality.
The corrected live `site.stats.devices` journey verified subscribed/live and own stopped state.
Observation produced no remote events in its five-second interval: report explicit no-data, not output success.
The initial run failed because the harness expected UUID session IDs instead of production 16-hex IDs;
this harness defect is repaired without production edits.
UX tracking: #3888 cancellation, #3889 optional client choices, #3890 wording (merged PR #3891).
Current base observations are not evidence against the newer merged wording repair.

These are execution prerequisites, not unresolved feature-scope choices.
No feature clarification is required before planning.
