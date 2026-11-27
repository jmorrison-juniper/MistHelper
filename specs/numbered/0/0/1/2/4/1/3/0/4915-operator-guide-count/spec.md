# Feature Specification: Operator Guide Operation Count

**Feature Branch**: `docs/4915-operator-guide-count`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue #4915, "Docs: operator guide operation count is stale".

**Record Location**: `specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count`

## Clarifications

### Session 2026-11-26

- Q: Does the generated menu reference list menus up to 308, as issue #4915 states? A: No. It states 308 actionable menu operations, numbered 1 to 309 with a gap at 152. Evidence: R-03 and R-05.
- Q: Should the operator guide state the corrected count? A: No. The guide states no count and links to the menu reference. Decision: D-1.
- Q: Does a test already check the operator guide count? A: No. The destructive menu guard reads no operator guide. Evidence: R-72.
- Q: Does continuous integration (CI) grade the operator guide with the STE gate? A: No. The STE workflow grades five files. Evidence: R-47. Decision: D-5.
- Q: Does this change need a release-note fragment? A: Yes. The guide is operator-facing text. Decision: D-4.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operator reads a correct pointer to the menu operations (Priority: P1)

An operator reads the operator guide to find the menu operations. The guide states no operation count. The guide links to the menu reference, which lists every menu operation.

**Why this priority**: The stale count gives operators a wrong number. Operators in a network operations center need one correct source.

**Independent Test**: Open the operator guide and search for a number followed by the word "operations". The search finds nothing. Select the menu reference link. The link opens `documentation/menu_reference.md`.

**Acceptance Scenarios**:

1. **Given** the operator guide on `main`, **When** the operator reads the section "The menu", **Then** the section states no operation count and no numbering range.
2. **Given** the changed operator guide, **When** the operator selects the menu reference link, **Then** the target file exists and lists the menu operations.

---

### User Story 2 - Maintainer gets a guard against a repeated count (Priority: P2)

A maintainer edits the operator guide. A guard test fails when the guide states an operation count again. The guard test also fails when the guide stops linking to the menu reference.

**Why this priority**: Issue #4155 closed on 2026-10-09 with the same stale count. The count returned. A guard detects the drift without a person who reads every sentence.

**Independent Test**: Run the guard test on the original guide. It fails and names each matched phrase. Run the guard test on the changed guide. It passes.

**Acceptance Scenarios**:

1. **Given** the guide states `303 operations`, **When** the guard test runs, **Then** the test fails and names each matched phrase.
2. **Given** the guide states no count and links to the menu reference, **When** the guard test runs, **Then** the test passes and logs the number of checked phrases.

---

### Edge Cases

- The guide states a count in bold text, such as `**303 operations**`. The guard test matches that phrase.
- The guide counts the operations of one menu, such as `3 operations`. The guard test matches that phrase, and the author rewords the sentence.
- The guide names endpoint operations, such as `152 unique simple endpoint operations`. The guard test does not match that phrase, because a number must directly precede the word `operations`.
- The guide removes its link to the menu reference. The guard test fails.
- The menu reference file is missing. The guard test fails, because the link target does not exist.
- The guide states a count in words, such as `three hundred operations`. The guard test does not match that phrase. Analysis item A-9 records this residual risk.
- Continuous integration runs the STE linter without a user dictionary. The guide still scores 80 or above in the structural mode.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The operator guide MUST NOT state an operation count or a menu numbering range.
- **FR-002**: The operator guide MUST link to `documentation/menu_reference.md` for the full list of menu operations.
- **FR-003**: The operator guide MUST score 80 or above with `ste-linter --min-score 80`.
- **FR-004**: The change MUST NOT alter a generator input, a generated page, or runtime code.
- **FR-005**: The change MUST add one release-note fragment with one Fixed bullet that names issue #4915.
- **FR-006**: The existing guard tests that read the operator guide MUST pass.
- **FR-007**: The new guard test MUST fail on the original guide and pass on the changed guide.
- **FR-008**: The record MUST pass the existing specs structure guard and the spec route contract guard.

### Key Entities

Not applicable. The change stores no entity, key, or state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The guard test reports two count phrases on the original guide and zero count phrases on the changed guide.
- **SC-002**: The STE linter scores the operator guide at 80 or above in the structural mode. The guide also scores 80 or above in the dictionary mode when a dictionary exists.
- **SC-003**: Each applicable local gate prints its expected result. No applicable local gate fails.
- **SC-004**: Each required continuous integration check passes before the auto-merge label is added.
- **SC-005**: The merged pull request closes issue #4915.

## Out of Scope

- The stale count in `documentation/wiki/Home.md`. Analysis item A-3 tracks it.
- The instructions that still name a README operation count. Analysis item A-4 tracks them.
- A continuous integration STE check for the operator guide. Decision D-5 defers it.
- Any change to `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md`, or `scripts/generate_menu_wiki.py`.
- The folder debt of `tests/guardrails` and `changelog.d`. Analysis item A-8 tracks it.
- The Windows guard failures tracked in issue #4917.
- The wording of constitution Principle IV for a documentation-only change. Decision D-6 covers it.

## Assumptions

- Remote `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` is the baseline. Local HEAD matched that commit during research.
- The menu reference keeps 308 actionable menu operations, numbered 1 to 309, when the change merges. The guard test does not depend on that number.
- No open pull request edits `documentation/operator-guide.md`. The implementer checks open pull requests before creating the branch.
- The orchestrator authorizes the merge after continuous integration passes.
