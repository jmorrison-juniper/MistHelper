# Feature Specification: Gateway History After an Ordinary Refresh

**Feature Branch**: `jmorrison-juniper-4200-migrate-mistwanperformance` (repair source, pull request #4208)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Issue #4795, "Runtime: WAN gateway history disappears after an ordinary refresh". Labels: `bug`, `web-portal`, `in-progress`.

## Clarifications

### Session 2026-11-26

- Q: Does GitHub `main` contain the defect? A: No. `main` has no `LiveHistory` class and no `live_routes.py`. The defect exists only before commit `d7a706d`. See research.md R06 and R17.
- Q: Which commit holds the repair? A: Commit `d7a706d`, dated 2026-11-13. Pull request #4208 head `843be63` keeps the repair. See research.md R01 and R04.
- Q: Does the reconstruction commit `15c69b1` in the issue exist? A: No. GitHub returns HTTP 422, and the local checkout lacks it. This record does not depend on it. See R02.
- Q: Does this record authorize publication of the candidate? A: No. The issue states that it does not authorize publication. An owner decision is required (D-2).
- Q: Does merging pull request #4208 close this issue? A: No. Its body says `Refs #4795`. The publication body must say `Closes #4795` (D-3).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep gateway history visible after an ordinary refresh (Priority: P1)

An operator refreshes one gateway in scope. The cache then holds that gateway history. An ordinary organization refresh replaces the cache with port and peer rows only. The gateway page still shows the retained history of that gateway.

**Why this priority**: Operators lose the gateway history after each routine refresh. This is the reported defect.

**Independent Test**: Run the gateway resolution unit tests and the scoped-then-ordinary route regression. Each test passes with mocked stores and no Mist request.

**Acceptance Scenarios**:

1. **Given** a cache with circuit records of one gateway only, **When** the gateway history is read, **Then** the read resolves that gateway and reads its history once.
2. **Given** a cache with peer records of one gateway only, **When** the gateway history is read, **Then** the read resolves that gateway and reads its history once.
3. **Given** a scoped refresh followed by an ordinary refresh, **When** the operator opens the gateway page, **Then** the page shows the retained daily history of that gateway.

### User Story 2 - Refuse an ambiguous or foreign gateway selection (Priority: P1)

The selected records name two gateways, name no gateway, or name a gateway of another organization. The read refuses the request with the gateway refusal message. The read never calls the history store.

**Why this priority**: A wrong gateway history misleads the operator. It can also cross a tenant boundary.

**Independent Test**: Run the refusal unit tests. Each test checks the exact message and zero history reads.

**Acceptance Scenarios**:

1. **Given** selected records for two gateways, **When** the gateway history is read, **Then** the read returns no summaries and the gateway refusal message.
2. **Given** selected records for a gateway of another organization, **When** the gateway history is read, **Then** the read returns the gateway refusal message and makes no history read.
3. **Given** no selected records, **When** the gateway history is read, **Then** the read returns the gateway refusal message.

### User Story 3 - Keep port and peer history unchanged (Priority: P2)

A port page or a peer page reads history only when exactly one selected record exists. Otherwise, the page shows the existing port-or-peer message.

**Why this priority**: The repair must not change port and peer pages that work today.

**Independent Test**: Run the port and peer regression test. Each message matches the message in the parent commit.

**Acceptance Scenarios**:

1. **Given** two selected records on a port page, **When** the history is read, **Then** the read returns the message `Select one port or peer path to read history.`
2. **Given** one selected circuit record on a port page, **When** the history is read, **Then** the read reads that circuit history once.

### Edge Cases

- Two sites share one gateway MAC address. The read treats them as two gateways and refuses.
- The selected records mix a gateway record, a circuit record, and a peer record of one gateway. The read accepts that one gateway.
- The history store is absent. The read returns the store-unavailable message and no summaries.
- The history store raises a storage error from the listed error types. The read logs the exception and returns the store-error message.
- The gateway page receives an unknown gateway or site. The route returns HTTP 404, as it does today.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST resolve one gateway identity from selected gateway, circuit, or peer records.
- **FR-002**: The system MUST refuse a gateway selection that names zero or more than one gateway identity, with the gateway refusal message.
- **FR-003**: The system MUST refuse a gateway selection whose gateway belongs to another organization, with the same refusal message.
- **FR-004**: The system MUST read the retained history of the resolved gateway once, over the thirteen-month window.
- **FR-005**: The system MUST keep gateway history readable after a scoped refresh followed by an ordinary refresh.
- **FR-006**: The system MUST keep the port and peer single-record rule and its message unchanged.
- **FR-007**: The history read MUST NOT send a Mist request and MUST NOT change the snapshot cache.
- **FR-008**: Each executable line of each changed function MUST carry an inline comment. The history read MUST log before and after its action.
- **FR-009**: The system MUST keep the exact text of each refusal message and each unavailable message.
- **FR-010**: The documentation MUST state the gateway resolution rule and the refusal rule.

### Mist Cloud Transport Requirements

Not applicable. This change adds no Mist REST request and no WebSocket transport. The history read uses the history store only. This change edits no collection file, and commit `d7a706d` edits none either (research.md, R89).

### Key Entities

- **Gateway identity**: One gateway of one site in one organization. Its natural key is the organization, the site, and the gateway identifier.
- **Circuit record**: A selected record whose identity names one gateway port. The identity carries its gateway identity. The user interface shows the port name.
- **Peer record**: A selected record whose identity names one peer path. The identity carries its gateway identity.
- **Selected record**: One hourly record that the page passes to the history read.
- **Retained history**: Hourly and raw observations that the history store keeps for one identity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Circuit-only and peer-only selections read history once in each unit test run (N1 and N2 in tasks.md).
- **SC-002**: Each refusal case returns the exact gateway message and makes zero history reads (N4, N5, and N6).
- **SC-003**: Port and peer selections keep their messages and read counts (N7).
- **SC-004**: The scoped-then-ordinary route regression passes on the publication head (E1 in tasks.md).
- **SC-005**: Each changed function has inline comments and action logs, verified by N8 and by review.
- **SC-006**: `main` contains the repair after publication. The same regressions pass on the merged revision.

## Assumptions

- The owner decides whether pull request #4208 is published (D-2).
- The candidate head `843be63` is the review base. A later commit can change the repair, so the blob SHA must be checked again before publication.
- The tests use mocked history stores and the in-process Flask test client. No container starts for these tests.
- The local `.venv` holds mistapi 0.64.1, which satisfies the pinned range.
- The history store is the existing `HistorySelection` backend, either SQLite or ArangoDB.

## Out of Scope

- Publishing the #4200 candidate. The owner decides this (D-2).
- Splitting pull request #4208 into one pull request per issue (D-11).
- Changing port or peer selection rules.
- Changing a Mist SDK call or the ordinary refresh flow.
- Fixing the pre-existing function length, version pin drift, or branch name (D-12).
- Closing issues #4793, #4794, #4797, or #4798.

Warning: publishing pull request #4208 places 82 files on `main` in one squash commit. A revert needs a new commit and a new review.
