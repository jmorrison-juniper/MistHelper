# Feature Specification: R0902 and R0903 class design

**Feature Branch**: `chore/4134-r0902-r0903-class-design`

**Created**: 2026-11-26

**Status**: Draft

**Input**: Pylint R0902 and R0903 findings in the Juniper RMA, web portal, and entry-point files at `main` commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca.

**Record**: `specs\numbered\0\0\1\1\3\0\1\4\4134-r0902-r0903-class-design`

## Summary

Pylint reports 25 findings at `main` commit f03c6c9. There are 9 R0902 findings (too many instance attributes) and 16 R0903 findings (too few public methods). Six R0903 findings are resolved by adding one public method to each of six classes. The other 19 findings stay, and each has a recorded reason. No behavior changes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every finding has one recorded decision (Priority: P1)

A maintainer reads the register. Each of the 25 findings has one decision and one reason.

**Why this priority**: The issue expected outcome requires a decision for each listed class.

**Independent Test**: Run the scan in `design\quickstart.md`. The remaining findings equal the 19 register rows.

**Acceptance Scenarios**:

1. **Given** the 25 findings at `main` commit f03c6c9, **When** the record is reviewed, **Then** each finding maps to one of decisions D-1 through D-11.
2. **Given** the change is merged, **When** pylint scans the eleven named files, **Then** the findings equal the 19 register rows.

---

### User Story 2 - Six classes gain behavior they already own (Priority: P2)

A maintainer reads six new public methods. Each method names logic that its class already performs inside another method.

**Why this priority**: Six findings resolve, and no output changes.

**Independent Test**: Run pytest on the four changed test modules. Each new method has tests that fail before the method exists.

**Acceptance Scenarios**:

1. **Given** a settings mapping without the contact e-mail, **When** `missing_names` runs with the contact required, **Then** it returns the contact name only.
2. **Given** a cached token at its expiry time, **When** `is_fresh` runs, **Then** it returns False.
3. **Given** a rate limiter that spent its token and waited 0.25 seconds at 2 requests each second, **When** `refill` runs, **Then** it returns 0.5.

---

### User Story 3 - Large state changes stay in separate records (Priority: P3)

A maintainer reads three follow-up scopes for state-heavy classes. Each follow-up names its files, its risk, and its prerequisite test.

**Why this priority**: These changes cross files or touch many test references, so they need separate review.

**Independent Test**: Read `analysis.md`. Each follow-up names files, a risk, and a prerequisite.

### Edge Cases

- `is_fresh` at the exact expiry time returns False, because the current rule uses `>=`.
- `refill` with no elapsed time keeps the current bucket level.
- `refill` after a long idle period caps the bucket at 1.0.
- `cutoff` with `now` equal to one retention window returns 0.0 for a one-day window.
- `missing_names` with the contact not required omits the contact name.
- `is_automated_run` returns True when runtime test mode is set and no flag appears in argv.
- `to_tickets` drops items that are not objects and keeps the order of the rest.
- A forced token refresh requests a new token, even when the cached token is fresh.

### Out of Scope

- Any change to `MistHelper.py`, `web_portal/`, menu wiring, or generated menu documentation.
- Merging the three menu factory classes.
- Removing the datetime adapter or the optional-dependency fallback classes.
- Grouping attributes of the six frozen records, `GlobalImportManager`, or `OperationExecutor`.
- Any Mist API endpoint, SDK call, token value, rate limit, or export column change.
- Inline pylint pragmas, and any change to lint settings in `pyproject.toml`.

### Functional Requirements

- **FR-001**: The record MUST give one decision for each of the 25 findings.
- **FR-002**: The change MUST add one public method to each of six classes that hold the related logic.
- **FR-003**: Each new method MUST keep the result of the code that it replaces.
- **FR-004**: Each remaining finding MUST keep a recorded reason, with no pylint pragma.
- **FR-005**: The change MUST NOT alter any Mist request, token value, rate limit, retention window, file name, or export column.
- **FR-006**: Each new public method MUST have at least one unit test that fails before the method exists.
- **FR-007**: The change MUST add one release-note fragment under `changelog.d/`.
- **FR-008**: The change MUST NOT modify `MistHelper.py`, `web_portal/`, menu wiring, or generated documentation.
- **FR-009**: The change MUST keep every existing public name and method signature unchanged.

### Key Entities *(include if feature involves data)*

Not applicable. The change adds methods to existing classes and creates no data entity. See `design\data-model.md`.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

Not applicable. The change makes no Mist REST request and no WebSocket transport. The one SDK call in the change scope, `listOrgTickets`, stays unchanged. Evidence: research row RC-56.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The scan of the eleven named files reports exactly the 19 register rows.
- **SC-002**: All 15 pytest cases in the four changed modules pass, and their existing tests still pass.
- **SC-003**: `pylint src/ --fail-under=9.5` reports a score of 9.5 or above.
- **SC-004**: `symbol-diff` reports no module-level name change for each changed source file.
- **SC-005**: The changed-file list equals the change map in `plan.md`.

## Assumptions

- The repository head is `main` commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca. The local blob of each cited file equals its `main` blob.
- Pylint 4.1.4 in `.venv` defines the scan. The issue comment scan used Pylint 4.1.3.
- The CI pylint gate reads `src/` only, so findings in `MistHelper.py`, `web_portal/`, and tests do not block CI.
- Each new method keeps the expression that it replaces, so existing test expectations stay the same.

## Clarifications

- **Q1**: Use inline pylint pragmas for the remaining findings? **Answer**: No. The register holds each reason. The repository has no pragma precedent for these messages (decision D-10).
- **Q2**: Merge the three menu factory classes? **Answer**: No. The merge changes 18 handler lambdas and about 12 generated pages (decision D-1).
- **Q3**: Does an internal refactor need a fragment? **Answer**: Yes. The constitution requires one fragment for each change. Changelog README rule 4 does not override it (decision D-11).
- **Q4**: Group the state of `OperationExecutor` now? **Answer**: No. A follow-up issue owns that change (decision D-5).
- **Q5**: Are the issue line numbers and paths current? **Answer**: No. The issue body is stale. Current lines appear in `design\research.md`.
