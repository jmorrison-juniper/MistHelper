# Feature Specification: mistapi SDK signature guard

**Feature Branch**: `chore/2726-sdk-signature-guard`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "Add a mistapi SDK signature compatibility guard for issue #2726."

## User Scenarios & Testing

### User Story 1 - Detect SDK signature drift (Priority: P1)

A maintainer can run the integration guard and learn when a MistHelper `mistapi` call no longer matches the installed SDK signature.

**Why this priority**: A required parameter change breaks a call as strongly as a removed function.

**Independent Test**: Run `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py -v`.

**Acceptance Scenarios**:

1. **Given** a call that omits a required SDK parameter, **When** the guard runs, **Then** it fails and names the parameter.
2. **Given** a call that passes a keyword the SDK removed, **When** the guard runs, **Then** it fails and names the keyword.
3. **Given** the repository has no static call site, **When** the guard runs, **Then** it fails because it checked zero signatures.

---

### User Story 2 - Report unmeasured dynamic calls (Priority: P2)

A maintainer can see how many `mistapi` call sites the static guard cannot prove.

**Why this priority**: Dynamic dictionaries and module strings hide SDK behavior from static analysis.

**Independent Test**: Run the integration guard and read the summary line.

**Acceptance Scenarios**:

1. **Given** a call uses `**kwargs`, **When** the guard runs, **Then** it counts the call as unverifiable.
2. **Given** a dynamic module import names `mistapi`, **When** the guard runs, **Then** it counts the call as unresolved.

---

### User Story 3 - Preserve keyword and positional semantics (Priority: P3)

A maintainer can trust that the guard treats positional and keyword calls differently.

**Why this priority**: A parameter rename affects a keyword call more than a positional call.

**Independent Test**: Review the comparator tests for required and unsupported parameters.

**Acceptance Scenarios**:

1. **Given** a positional call supplies enough arguments, **When** a parameter name changes, **Then** the call can still pass.
2. **Given** a keyword call uses an old parameter name, **When** the SDK removes that keyword, **Then** the call fails.

### Edge Cases

- If a call uses `*args` or `**kwargs`, the guard reports it as unverifiable and compares only the function name.
- If a registry entry names a function without actual call arguments, the guard reports it as unverifiable for signature checks.
- If the guard finds a real production mismatch, the guard records it as a known issue until a separate repair removes it.
- If the guard checks zero signatures, it fails because a green result would prove nothing.

## Requirements

### Functional Requirements

- **FR-001**: The guard MUST collect each static `mistapi` call from `MistHelper.py` and `src/`.
- **FR-002**: The guard MUST collect installed SDK signatures from the installed `mistapi` package.
- **FR-003**: The guard MUST fail when a static call omits a parameter the SDK requires.
- **FR-004**: The guard MUST fail when a static call passes a keyword the SDK does not accept.
- **FR-005**: The guard MUST print the count of checked signatures and the count of unmeasured call sites.
- **FR-006**: The guard MUST fail when it checks zero call signatures.
- **FR-007**: The guard MUST count dynamic `*args` and `**kwargs` calls as unverifiable.
- **FR-008**: The guard MUST fail only when the unverifiable count grows beyond the recorded baseline.
- **FR-009**: The guard MUST compare positional calls by position and keyword calls by keyword name.
- **FR-010**: The guard MUST keep issue #2741 mismatches visible without changing production code in this pull request.

### Key Entities

- **Call Site**: A file, line, SDK function path, source type, and static argument facts.
- **SDK Signature**: The required parameters, accepted keywords, and dynamic argument support for one SDK function.
- **Guard Report**: The checked, unresolved, unverifiable, known-failure, and resolved counts.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The integration guard prints at least one checked call signature.
- **SC-002**: The integration guard reports `Checked mistapi call signatures: 482` on the current branch.
- **SC-003**: The integration guard reports `Unresolved mistapi call sites: 10` on the current branch.
- **SC-004**: The integration guard reports `Unverifiable mistapi call signatures: 366` on the current branch.
- **SC-005**: Three negative tests prove omitted required parameters, removed parameters, and zero checked signatures fail.

## Assumptions

- The installed SDK is `mistapi` 0.64.0.
- A static guard cannot safely inspect runtime-built dictionaries.
- The guard should report dynamic calls and fail only when their baseline grows.
- A separate issue owns production repairs found by this guard.
