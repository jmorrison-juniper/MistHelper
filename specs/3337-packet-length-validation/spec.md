# Feature Specification: Packet Length Validation

**Feature Branch**: `jmorrison-juniper-packet-length-validation`

**Created**: 2026-09-30

**Status**: Rebased and verified on the coordinator-authorized main revision. Publication, protected merge, and exact-main tests remain incomplete.

**Issue**: [MistHelper #3337](https://github.com/jmorrison-juniper/MistHelper/issues/3337)

**Input**: User description: "Limit both packet-length prompts to 64 through 1536 bytes, inclusive. Preserve existing defaults and safe input handling. Prove the behavior offline."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select a Supported Length in the Shared Prompt (Priority: P1)

A network operator uses the shared packet-length prompt to configure a capture.
This prompt also serves organization captures on Mist Edge devices.
The operator needs a supported length and a correct description of the allowed range.

**Why this priority**: The current prompt accepts unsupported lengths through 2048 bytes.
Early validation prevents an unsupported capture configuration.

**Independent Test**: Supply controlled terminal input to the existing shared prompt without starting a capture.
Check the returned length, prompt text, and error text.

**Acceptance Scenarios**:

1. **Given** the shared prompt, **When** the operator enters any integer from 64 through 1536, **Then** the prompt returns that integer.
2. **Given** the shared prompt, **When** the operator enters 63 or any integer from 1537 through 2048, **Then** the prompt returns no value.
   The range error identifies 64 and 1536 bytes as the inclusive limits.
3. **Given** the shared prompt, **When** the operator enters `64.0`, `1e3`, or `text`, **Then** the prompt returns no value.
   The error identifies an invalid packet length.
4. **Given** the shared prompt, **When** the prompt appears, **Then** it shows 1536 bytes as the maximum and 128 bytes as the default.
5. **Given** the shared prompt, **When** the operator enters a negative integer or 2049, **Then** the prompt rejects the length.
   The prompt does not clamp the length or replace invalid input with a default.

---

### User Story 2 - Select a Supported Length for Wireless Client Capture (Priority: P1)

A network operator selects a packet length during wireless client capture configuration.
The wireless packet-length prompt must apply the same limits as the shared prompt.
The operator must retain the selected duration and packet count when the length is valid.

**Why this priority**: The wireless prompt independently accepts unsupported lengths through 2048 bytes.
Both prompt paths must enforce the corrected maximum.

**Independent Test**: Supply controlled terminal input to the existing wireless prompt and its bounded-number collection sequence.
Check the returned length, complete settings result, and messages without starting a capture.

**Acceptance Scenarios**:

1. **Given** valid duration and packet count, **When** the operator enters a valid length from 64 through 1536, **Then** the settings retain all three values.
2. **Given** valid duration and packet count, **When** the operator enters 63 or any integer from 1537 through 2048, **Then** the sequence returns no settings.
   The range error identifies 64 and 1536 bytes as the inclusive limits.
3. **Given** the wireless prompt, **When** the operator enters `64.0`, `1e3`, or `text`, **Then** the prompt returns no value.
   The error identifies an invalid packet length.
4. **Given** the wireless prompt, **When** the prompt appears, **Then** it shows 1536 bytes as the maximum and 1300 bytes as the default.
5. **Given** valid earlier settings, **When** packet-length validation fails, **Then** the collection sequence stops before later capture actions.
   The sequence does not return partial settings.

---

### User Story 3 - Preserve Defaults and Input Safety (Priority: P2)

A network operator can retain the existing default or enter a length with surrounding whitespace.
A closed terminal stream produces an end-of-file (EOF) condition.
The corrected limit must preserve the existing response to these inputs.

**Why this priority**: A limit correction must not change normal entry or disconnected-session behavior.
Operators must retain the established defaults.

**Independent Test**: Supply blank input, whitespace-only input, padded integers, EOF, and an operator interrupt through the existing input safety handling.
Check the returned values and safety messages without starting a capture.

**Acceptance Scenarios**:

1. **Given** the shared prompt, **When** the operator enters an empty or whitespace-only response, **Then** the prompt returns 128.
2. **Given** the wireless prompt, **When** the operator enters an empty or whitespace-only response, **Then** the prompt returns 1300.
3. **Given** either prompt, **When** a valid integer has surrounding spaces or tabs, **Then** the prompt returns the unchanged integer.
4. **Given** either prompt, **When** the input stream reaches EOF, **Then** the prompt returns its applicable default without an uncaught input error.
   The existing disconnect notice remains available.
5. **Given** a valid caller-supplied shared default, **When** input is blank, whitespace-only, or EOF, **Then** the prompt returns that default.
   This includes the existing 1300-byte caller default.
6. **Given** either prompt, **When** the operator interrupts input, **Then** the prompt returns no value and retains the existing cancellation notice.
7. **Given** a capture mode with fixed packet length, **When** the limit correction applies, **Then** the fixed length remains 1300 or 1500 bytes.
   All unrelated capture settings remain unchanged.

### Edge Cases

- The lower limit, 64 bytes, and the upper limit, 1536 bytes, are valid.
- The adjacent values, 63 and 1537, are invalid.
- Every integer from 1537 through the former 2048-byte limit is invalid.
- Zero, negative integers, 2049, and larger integers remain invalid.
- Fractional text and scientific notation do not become valid integers through rounding or truncation.
- Empty input and whitespace-only input select the applicable default, rather than an invalid-length result.
- Surrounding spaces and tabs do not change a valid integer.
- EOF selects the applicable default through the existing input safety handling.
- An operator interrupt retains the existing cancellation behavior.
- Invalid wireless packet length stops the bounded-number collection sequence, even when the duration and packet count are valid.
- Fixed packet lengths of 1300 and 1500 bytes already satisfy the corrected maximum.
  These fixed values remain unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both packet-length prompts MUST accept every integer from 64 through 1536 bytes, inclusive, and return the selected integer unchanged.
- **FR-002**: Both prompts MUST reject every integer outside that range and return no valid length.
  This includes 63 and every integer from 1537 through 2048.
- **FR-003**: Both prompts MUST reject non-integer input.
  Required examples include alphabetic text, fractional text, and scientific notation.
  The existing invalid-length diagnostic MUST remain available.
- **FR-004**: Both prompt messages MUST identify 1536 bytes as the maximum.
  Range errors MUST identify 64 and 1536 bytes as the inclusive limits.
  Neither message may identify 2048 bytes as the supported maximum.
- **FR-005**: The shared prompt MUST retain its 128-byte default when the caller does not supply another default.
- **FR-006**: The wireless prompt MUST retain its 1300-byte default.
- **FR-007**: Both prompts MUST preserve surrounding-whitespace handling.
  Blank and whitespace-only input MUST select the applicable default.
  Padded valid integers MUST return their unchanged values.
- **FR-008**: Both prompts MUST preserve EOF handling through the existing input safety behavior.
  EOF MUST return the applicable default and retain the disconnect notice.
  An operator interrupt MUST retain the existing cancellation behavior.
- **FR-009**: The shared prompt MUST preserve existing valid caller-supplied defaults, including 1300 bytes.
- **FR-010**: The wireless collection sequence MUST retain valid duration and packet-count values when packet length is valid.
  Invalid packet length MUST return no settings and stop the sequence.
- **FR-011**: Invalid packet-length input MUST NOT produce a usable length through clamping, rounding, or default substitution.
  Existing callers MUST retain their stop behavior after validation fails.
- **FR-012**: The correction MUST preserve fixed packet lengths of 1300 and 1500 bytes.
  All unrelated capture settings and behavior MUST remain unchanged.

### Key Entities *(include if feature involves data)*

- **Packet length selection**: The operator-selected maximum length of each captured packet, measured in bytes.
  Its valid values are integers from 64 through 1536.
  Its default depends on the prompt and any existing caller-supplied default.
- **Capture settings**: The existing duration, packet count, and packet length collected for a capture.
  This correction changes only the allowed packet-length maximum and its messages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each prompt accepts all 1473 integers from 64 through 1536 and returns each value unchanged.
- **SC-002**: Each prompt rejects all 513 required invalid integers: 63 and the 512 integers from 1537 through 2048.
  Negative integers and 2049 also remain invalid.
- **SC-003**: Both displayed prompts identify 1536 as the maximum.
  Every range-error case identifies 64 and 1536 as the limits.
- **SC-004**: All blank, whitespace-only, and EOF cases preserve the applicable 128-byte or 1300-byte default.
  These cases produce no uncaught input error.
- **SC-005**: Both prompts reject all required non-integer examples and preserve correct results for all padded valid inputs.
- **SC-006**: The wireless collection sequence returns the complete, unchanged settings for valid input and no settings for invalid packet length.
- **SC-007**: Operators can identify the supported maximum from either prompt without external instructions.
  One valid entry completes packet-length selection without a correction request.
- **SC-008**: All acceptance evidence comes from local prompt execution with zero real capture requests and zero Mist cloud contacts.
- **SC-009**: Existing fixed-length capture modes retain their 1300-byte or 1500-byte lengths.
  No unrelated capture setting changes.

## Assumptions

- Issue #3337 supplies the authoritative 1536-byte maximum from Mist OpenAPI release `2609.1.0`.
  This maximum applies to the identified site and organization capture contracts.
- The two existing prompt paths and their input safety handling already provide the required validation structure.
  This correction does not introduce a new input policy.
- Integer text retains the existing conversion behavior.
  This feature does not introduce additional restrictions on valid integer text.
- The existing shared default is 128 bytes.
  The wireless default and existing shared wireless caller default are 1300 bytes.
- The existing wireless duration and packet-count defaults remain 60 seconds and 1024 packets.
  Their validation limits remain unchanged.
- Fixed 1300-byte and 1500-byte capture settings need no correction.
  The named sender paths require review, not edits.
- Issue #3338 owns the independent refresh of the bundled specification.
  Issue #3337 does not depend on that refresh and does not change bundled OpenAPI artifacts or upgrade the SDK.
- This documentation-alignment phase updates only existing issue-owned documents.
  The parent owns source, tests, release notes, final validation, and delivery.
  Documentation alignment executes no test, gate, branch, commit, or remote action.
- The explicit issue directory controls this feature's documentation.
  Shared feature selection and extension configuration remain unchanged.
- The requirements checklist records final file ownership, verification gates, and the coordinator's delivery restriction.
  These constraints do not authorize implementation or delivery by the documentation owner.
