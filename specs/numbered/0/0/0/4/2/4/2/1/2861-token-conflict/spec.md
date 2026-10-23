# Feature Specification: Reject Conflicting Mist Token Values

**Feature Branch**: `3996-mist-token-conflict`
**Created**: 2026-10-23
**Status**: Implemented
**Input**: Bounded issue #2861 repair for conflicting `MIST_APITOKEN` and `MIST_API_TOKEN` values.

## User Scenarios & Testing

### User Story 1 - Prevent ambiguous Mist identity (Priority: P1)

An operator starts MistHelper with one or two token environment variables. MistHelper must not select an unintended Mist identity when the variables disagree.

**Why this priority**: A conflicting credential can direct an operation to the wrong Mist account.

**Independent Test**: Set each token variable alone, set equal values, set different values, and set delimiters in the canonical variable while the legacy variable has a valid token.

**Acceptance Scenarios**:

1. **Given** one supported token variable has a usable value, **When** MistHelper validates credentials, **Then** it accepts that value.
2. **Given** both token variables normalize to the same token list, **When** MistHelper validates credentials, **Then** it accepts the canonical value during migration.
3. **Given** both token variables normalize to different non-empty lists, **When** MistHelper validates credentials, **Then** it refuses startup before session or organization lookup.
4. **Given** the canonical variable contains only delimiters and the legacy variable has usable tokens, **When** MistHelper parses credentials, **Then** it uses the legacy tokens.
5. **Given** credential validation refuses conflicting values, **When** MistHelper reports the failure, **Then** logs identify the conflicting variable names and contain no token characters.
6. **Given** conflicting values exist in login mode, **When** MistHelper validates credentials, **Then** it refuses the configuration before any authentication path starts.

### Edge Cases

- Treat a missing, empty, or delimiter-only variable as absent.
- Compare token lists after whitespace and delimiter normalization.
- Do not construct a Mist session or resolve an organization after conflict refusal.
- Do not write token values to logs on any conflict path.

## Requirements

### Functional Requirements

- **FR-001**: MistHelper MUST accept a usable value from either supported token variable when the other variable is absent or normalizes to an empty list.
- **FR-002**: MistHelper MUST accept both variables only when their normalized token lists are equal.
- **FR-003**: MistHelper MUST refuse conflicting non-empty token lists before session construction or organization lookup.
- **FR-004**: MistHelper MUST refuse token-variable conflicts in login mode, even when login mode does not require a token.
- **FR-005**: Failure messages MAY name the two environment variables, but MUST NOT include any part of their values.
- **FR-006**: This repair MUST change only the `MistHelper.py` credential path, its focused unit tests, and its issue release note.
- **FR-007**: The repair MUST NOT make a Mist Cloud request during validation.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All six acceptance scenarios have a passing local test.
- **SC-002**: Every conflicting configuration exits before organization lookup and Mist session construction.
- **SC-003**: No configured token value or token substring appears in captured failure logs.
- **SC-004**: Existing supported single-variable and equal-value migration configurations continue to pass.

## Assumptions

- The owner-approved policy for issue #2861 allows equal token values only during migration.
- A delimiter-only value is equivalent to an absent value, consistent with existing token parsing.
- This record covers only the MistHelper.py candidate and does not resolve other issue #2861 candidates.
- The release note is unique to this issue slice. The issue remains open until all candidates and validation are complete.
