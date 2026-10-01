# Feature Specification: Bounded numeric inputs

**Feature Branch**: `jmorrison-juniper-bounded-numeric-inputs`

**Created**: 2026-10-01

**Status**: Specified

**Input**: Repair [issue #3395](https://github.com/jmorrison-juniper/MistHelper/issues/3395).
Limit this repair to the picker offset, capture tier, and client page limit.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open a damaged picker link (Priority: P1)

An operator opens an organization picker link with a damaged offset.
The portal shows the first page instead of a server error.

**Why this priority**: A damaged link must not prevent organization selection.

**Independent Test**: Send a real picker request with each damaged offset.
Check status 200, the first page rows, and the preserved search filter.

**Acceptance Scenarios**:

1. **Given** a signed-in operator, **When** the offset contains non-ASCII digits,
   **Then** the picker shows the first page.
2. **Given** a signed-in operator, **When** the offset contains 5000 digits,
   **Then** the picker shows the first page without integer conversion.
3. **Given** a valid offset, **When** the operator opens the link,
   **Then** the picker keeps its existing page and filter rules.

### User Story 2 - Refuse a damaged capture tier (Priority: P1)

An operator submits an unsupported capture tier.
The portal returns the existing tier refusal and starts no capture.

**Why this priority**: A damaged field must not start work or produce a server error.

**Independent Test**: Send real JSON and form capture requests.
Check status 400, the complete refusal body, and zero capture starts.

**Acceptance Scenarios**:

1. **Given** an authorized site, **When** a tier contains non-ASCII or excessive digits,
   **Then** the portal returns `bad_tier`.
2. **Given** an authorized site, **When** a tier is 2 or 3,
   **Then** the portal keeps its existing capture start contract.
3. **Given** no authorized site, **When** a client submits a damaged tier,
   **Then** the existing authentication and site refusal takes precedence.

### User Story 3 - Use the existing page limit fallback (Priority: P2)

An operator sets an invalid `MIST_PAGE_LIMIT` value.
The client reader uses `DEFAULT_PAGE_LIMIT` and reports the invalid field safely.

**Why this priority**: An invalid setting must not stop a read-only capture.

**Independent Test**: Set the variable and call the real page limit reader.
Check the exact result and diagnostics without a cloud call.

**Acceptance Scenarios**:

1. **Given** invalid non-ASCII or excessive digits, **When** the client reads the setting,
   **Then** it returns `DEFAULT_PAGE_LIMIT`.
2. **Given** ASCII digits, **When** the client reads the setting,
   **Then** it keeps the existing lower and upper page limit decisions.

### Edge Cases

The tests cover superscript digits, Arabic decimal digits, mixed digits, empty values,
5000 nines, and 5000 zeros.
They also cover signs, fractions, separators, ordinary leading zeros, and each field's whitespace rule.
The offset permits one leading plus sign after whitespace removal.
The tier permits no sign or surrounding whitespace.
The page limit removes surrounding whitespace but permits no sign.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each text reader must accept ASCII digits `0` through `9` only.
- **FR-002**: Each reader must reject excessive text before integer conversion, including excessive leading zeros.
- **FR-003**: The offset must use the sequence index bound, not a new arbitrary application limit.
- **FR-004**: A damaged offset must select the first page and preserve the search filter.
- **FR-005**: A damaged tier must return the existing status 400 `bad_tier` refusal.
- **FR-006**: A refused tier must invoke neither capture work nor firmware work.
- **FR-007**: An invalid page limit must use the named fallback with standard diagnostics.
- **FR-008**: Valid values must keep the existing leading zero, whitespace, default, and page limit clamp rules.
- **FR-009**: Diagnostics must state the field, reason, character count, and checked count without raw input.
- **FR-010**: Required regression and property tests must execute without network access or environmental skips.
- **FR-011**: The repair must not change authentication, organization scope, firmware controls, or the option mapper.

### Key Entities

The input field carries text or an existing JSON value.
The checked number carries a usable nonnegative integer or an explicit missing result.
The caller owns the fallback or HTTP refusal.
This repair adds no stored entity and changes no schema.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three readers return their exact required decisions for the complete invalid input corpus.
- **SC-002**: The regression run proves at least one original failure for each reader.
- **SC-003**: Oversized input causes zero integer conversions in every reader.
- **SC-004**: Refused capture requests cause zero capture starts and zero firmware starts.
- **SC-005**: Every changed reader and every new reader branch has complete focused coverage.
- **SC-006**: The unchanged configured quality gates report their exact local results.

## Assumptions

The Python backend's default integer text limit supplies the representation bound.
A stricter active backend limit remains authoritative.
Leading zeros remain valid within that representation bound.
The offset's usable number bound is `sys.maxsize`.
Tier membership remains 2 or 3.
The client page limit remains between its existing named bounds.
No template, browser control, or browser interaction changes.
Request tests therefore prove the repair without a new browser journey.
Publication remains blocked until the parent grants the full verified main SHA after position 22.
