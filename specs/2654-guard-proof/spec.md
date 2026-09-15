# Feature Specification: Guard Proof Enforcement

**Feature Branch**: `chore/2654-guard-proof`

**Created**: 2026-09-15

**Status**: Draft

**Input**: User description: "Require a new guard to prove that it fails."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Block a guard that measures nothing (Priority: P1)

A maintainer reviews a pull request that adds a guard. The guard can report
green after it skips every test or reads no input. The maintainer needs a gate
that rejects this state before merge.

**Why this priority**: A green guard that measures nothing hides the exact
failure it claims to prevent.

**Independent Test**: Feed the enforcement a deliberate guard file with a
module-level unconditional skip. Assert that the enforcement blocks the merge.

**Acceptance Scenarios**:

1. **Given** a guard test file with only a module-level unconditional skip,
   **When** the guard proof audit reads it, **Then** the audit fails.
2. **Given** a guard test file with one measured test, **When** the audit reads
   it, **Then** the audit passes.

---

### User Story 2 - Keep environmental skips valid (Priority: P1)

A contributor writes a guard that needs Podman, Playwright, or another local
capability. The test can skip when that capability is absent, but it must print
the reason.

**Why this priority**: The rule must not turn a valid environment condition
into a false failure.

**Independent Test**: Feed the enforcement a guard that uses an environmental
skip. Assert that the enforcement allows it.

**Acceptance Scenarios**:

1. **Given** a guard with `pytest.importorskip`, **When** the audit reads it,
   **Then** the audit passes.
2. **Given** a guard with `pytest.mark.skipif`, **When** the audit reads it,
   **Then** the audit passes.

---

### User Story 3 - Report known no-measurement guards (Priority: P2)

A maintainer runs the audit against the current repository. The audit must name
known guard debt without blocking unrelated work.

**Why this priority**: Issue #2689 needs a separate repair, but this rule must
still expose it.

**Independent Test**: Run the audit against the repository and assert that it
reports `tests/integration/test_mistapi_sdk_compatibility.py` as known debt for
issue #2689.

**Acceptance Scenarios**:

1. **Given** the current SDK compatibility guard, **When** the audit runs,
   **Then** the audit names issue #2689.
2. **Given** a new all-skipped guard without a known issue, **When** the audit
   runs, **Then** the audit fails.

## Edge Cases

- If a guard cannot read its required input, it must fail and print the missing
  input.
- If a guard skips because a local capability is absent, it must print the
  capability name and the reason.
- If a guard file has no test function, the audit leaves it to the normal
  collection gate.
- If a known no-measurement guard exists, the audit prints the issue that owns
  the repair.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST state that each new or changed guard proves a
  failing path.
- **FR-002**: The written rule MUST require output that states a measured count.
- **FR-003**: The written rule MUST state that a required guard fails when it
  cannot read its input.
- **FR-004**: The written rule MUST allow an environmental skip only when the
  skip prints a reason.
- **FR-005**: The enforcement MUST reject a guard test file whose tests all use
  a module-level unconditional skip.
- **FR-006**: The enforcement MUST allow `pytest.importorskip` and
  `pytest.mark.skipif` as environmental skip forms.
- **FR-007**: The enforcement MUST report
  `tests/integration/test_mistapi_sdk_compatibility.py` as known debt for
  issue #2689.
- **FR-008**: The enforcement MUST print the number of guard files that it
  checked.

### Key Entities

- **Guard file**: A pytest file under `tests\guardrails\`, or a test file whose
  name contains `guard` or `compatibility`.
- **Known finding**: A no-measurement guard that already has a separate repair
  issue.
- **Active finding**: A no-measurement guard that does not have a known repair
  issue.

## Evidence

Issue #2654 names three guard failures.

| Pull request | Guard | Silent state |
| - | - | - |
| #2591 | Direct `CHANGELOG.md` edit guard. | A depth-one checkout hid merge parents, so the guard returned early. |
| #2611 | Reopen guard. | The schedule reversed a maintainer decision and made a correct-looking close comment. |
| #2618 | Timeline reader for the reopen guard. | One page held old events, so the guard missed a recent reopen. |

Issue #1924 shows the general pattern. A failure path removed the evidence that
would report the failure.

Issue #2689 shows the live case. The SDK compatibility guard skips all seven
tests with this reason:

```text
Legacy compatibility surface removed with compat_facades deprecation
```

That guard reported green while `mistapi` 0.64.0 removed a module that
`src/org_data_collector.py` imported.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A test that feeds a deliberate all-skipped guard to the
  enforcement fails the guard proof decision.
- **SC-002**: A test that feeds an environmental skip to the enforcement passes
  the guard proof decision.
- **SC-003**: The command-line audit prints the number of guard files checked.
- **SC-004**: The command-line audit reports the SDK compatibility guard as
  known issue #2689.
- **SC-005**: Ruff, Black, mypy, and the targeted pytest file pass locally.

## Assumptions

- Static analysis is enough for the first enforcement step because issue #2689
  uses a module-level unconditional skip.
- Known debt can stay visible without blocking issue #2654 when a separate
  issue owns the repair.
- The rule applies to guard tests, not to every test that can skip for a local
  environment condition.
