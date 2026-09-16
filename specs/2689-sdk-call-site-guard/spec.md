# Feature Specification: mistapi SDK call-site guard

**Feature Branch**: `test/2689-sdk-call-site-guard`

**Created**: 2026-09-16

**Status**: Draft

**Input**: GitHub issue #2689: "test: the mistapi SDK compatibility guard skips every test, so SDK drift reaches CI unmeasured"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Measure SDK call sites (Priority: P1)

A maintainer needs the SDK compatibility test to read the calls that MistHelper makes to `mistapi`.

**Why this priority**: This stops a green test from hiding a removed SDK function.

**Independent Test**: Run `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py -v`.

**Acceptance Scenarios**:

1. **Given** MistHelper source calls installed SDK functions, **When** the guard runs, **Then** it reports the count of resolved call sites.
2. **Given** one source calls a missing SDK function, **When** the guard runs, **Then** it fails and names the file and line.

---

### User Story 2 - Reject unmeasured green runs (Priority: P1)

A maintainer needs the guard to fail when it resolves zero call sites.

**Why this priority**: A zero-count pass is the defect that issue #2689 repairs.

**Independent Test**: Run the zero-call-site unit path in the compatibility test file.

**Acceptance Scenarios**:

1. **Given** a source map with no `mistapi` call, **When** the guard evaluates it, **Then** the guard returns a failure message.

---

### User Story 3 - Track dynamic SDK references (Priority: P2)

A maintainer needs dynamic SDK module paths to stay visible even when static analysis cannot name the function.

**Why this priority**: Dynamic module strings can hide SDK use from a direct attribute scan.

**Independent Test**: Run the unresolved dynamic import test in the compatibility test file.

**Acceptance Scenarios**:

1. **Given** a source imports a `mistapi` module through `import_module`, **When** the guard runs, **Then** it reports the unresolved count.
2. **Given** the unresolved count grows beyond the baseline, **When** the guard runs, **Then** it fails.

### Edge Cases

- If the installed `mistapi` package cannot be located, the guard fails.
- If a call uses an import alias, the guard resolves the alias before it checks the SDK.
- If a registry stores the module and function as strings, the guard resolves the pair.
- If a dynamic import names only a module, the guard reports it as unresolved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The guard MUST walk `MistHelper.py` and every Python file under `src/` with `ast`.
- **FR-002**: The guard MUST collect direct `mistapi` attribute call sites and supported import aliases.
- **FR-003**: The guard MUST collect supported string registry call sites that name an SDK module and function.
- **FR-004**: The guard MUST walk the installed `mistapi` package with `ast` and collect defined SDK functions.
- **FR-005**: The guard MUST fail when a resolved call site has no matching SDK function.
- **FR-006**: The missing-function failure MUST name the caller file, caller line, and missing function.
- **FR-007**: The guard MUST fail when it resolves zero call sites.
- **FR-008**: The guard MUST report the resolved call-site count and unresolved call-site count.
- **FR-009**: The guard MUST fail if unresolved dynamic SDK references grow beyond the recorded baseline of 10.
- **FR-010**: The guard MUST not perform a live Mist API request.

### Key Entities

- **MistapiCallSite**: A source file path, line number, SDK function path, and discovery source.
- **MistapiGuardReport**: The resolved call sites, unresolved call sites, SDK function set, and failure messages.
- **MistapiSdkSurfaceCollector**: The scanner for functions defined by the installed SDK package.
- **MistapiSourceCallCollector**: The scanner for SDK calls in MistHelper source files.

## Decisions

### Unresolved call-site decision

The guard reports dynamic SDK module references and fails only if their count grows beyond the baseline of 10.
This keeps the guard useful today, and it blocks new unmeasured SDK paths.

### Signature-check decision

This change does not add a signature check. The current issue requires function existence at call sites.
A signature check needs a separate design for optional parameters, `*args`, and SDK session name differences.
The known 0.64.0 changes affect `mistapi.device_utils`, and MistHelper does not call those functions today.
Follow-up issue #2726 tracks the signature guard.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The compatibility test runs at least one measured guard test and has no module-level skip.
- **SC-002**: The installed SDK guard reports 848 resolved call sites and 10 unresolved call sites on current main.
- **SC-003**: The negative missing-function test fails the guard decision and names `src/example.py:2`.
- **SC-004**: The zero-call-site test fails the guard decision with `FAIL resolved mistapi call sites: 0`.
- **SC-005**: `python -m tools.guard_proof_audit` no longer reports this file as known unmeasured debt.

## Assumptions

- The installed SDK version for this change is `mistapi` 0.64.0.
- The guard can use AST parsing because it must not run MistHelper source or SDK API calls.
- The project accepts a recorded baseline for dynamic SDK module references until those paths are refactored.
