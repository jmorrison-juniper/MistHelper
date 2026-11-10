# Feature Specification: Traceback log redaction

**Feature Branch**: `jmorrison-juniper-traceback-log-redaction`

**Created**: 2026-11-09

**Status**: Approved for local implementation

**Input**: Repair issues #4704 and #4705 at the logging boundary. Preserve safe messages and useful traceback context. Hold publication.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read a safe failure report (Priority: P1)

An operator reads a failure report without credential values from the message or the exception chain.

**Why this priority**: A traceback must not expose credentials that the message filter removes.

**Independent Test**: Emit synthetic credentials through a normal stream handler and the real portal handler.

**Acceptance Scenarios**:

1. **Given** a failure with a synthetic credential, **When** the handler emits the report, **Then** no synthetic credential remains.
2. **Given** linked failures, **When** the handler emits the chain, **Then** each credential is redacted and each failure type remains.
3. **Given** a safe report, **When** the handler emits it, **Then** the message, traceback frames, and portal context remain useful.

### User Story 2 - Read reports with several handlers (Priority: P1)

An operator receives the same protection when a previous handler has already formatted the exception.

**Why this priority**: A previous formatting pass must not bypass credential protection.

**Independent Test**: Format a record before the protected handler receives it, then inspect the complete protected output.

**Acceptance Scenarios**:

1. **Given** cached raw exception text, **When** a protected handler emits the record, **Then** the output contains only redacted credential values.
2. **Given** a formatting failure, **When** redaction cannot complete, **Then** a safe failure diagnostic replaces the unsafe report.

### Edge Cases

- Explicit exception causes and implicit exception context.
- Cached exception text with or without the original exception object.
- Repeated formatting through protected handlers.
- Malformed message arguments and exception rendering errors.
- Safe exception text and ordinary messages.
- A safe exception ending in `Invalid token`, followed by a standard chain separator.
- Case-insensitive authorization headers with a scheme and a synthetic value.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Redact credential-shaped values in exception reports at the logging boundary.
- **FR-002**: Apply the existing credential recognition rules to each exception in a chain.
- **FR-003**: Protect cached exception text from earlier formatting passes.
- **FR-004**: Preserve safe message behavior, failure types, traceback frames, and portal run and site context.
- **FR-005**: Emit a safe diagnostic if redaction fails. Do not expose the original report or the redaction error value.
- **FR-006**: Use synthetic credentials only. Do not contact Mist services or operate containers or firmware.
- **FR-007**: Change only the owned logging source, approved test paths, and unique specification and changelog records.
- **FR-008**: Commit locally with `Refs #4704`. Do not push, create a PR, rebase, merge, or change credentials.
- **FR-009**: Preserve complete safe exception chains. A credential label without a value must not consume the next line.
- **FR-010**: Redact labeled authorization values, including the complete scheme and value, in messages and exception text.
- **FR-011**: Match authorization header names without case sensitivity. Retain ordinary labeled credential protection.
- **FR-012**: Reference #4705 in the local follow-up commit and a unique changelog fragment.
- **FR-013**: Redact the complete labeled authorization value through its line boundary, including quoted and comma-separated Digest and AWS4 parameters.
- **FR-014**: Preserve the next line, including safe diagnostics and standard exception chain separators.
- **FR-015**: Redact the credential-bearing suffix of the exact email verification route in relative and absolute URLs.
- **FR-016**: Preserve unrelated URLs, following diagnostic lines, and exception chain separators.
- **FR-017**: Add a dedicated test file. Do not edit the test file renamed by draft #4358.
- **FR-018**: Treat URL recognition as additional protection only. Unlabeled response details and unprotected handlers require separate repairs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every credential marker is absent from each complete protected output in the regression cases.
- **SC-002**: Every safe diagnostic and expected failure type remains present in the successful regression cases.
- **SC-003**: Both handler paths pass the direct, chained, and previous-formatting regression cases.
- **SC-004**: The regression cases fail against the original implementation and pass after the repair.

## Assumptions

- Protection covers recognized labeled credentials and authorization headers, not arbitrary unlabeled secrets.
- Unprotected handlers remain outside the protection contract.
- Standard traceback formatting remains the required diagnostic format.
- Publication remains held for the serial queue.
- The app-managed branch replaces the branch-creation hook.
- The feature selector remains command-scoped because `.specify/feature.json` is a shared tracked record.
- The URL rule protects the suffix after `/api/v1/self/update/verify/`, including its query and fragment.
- URL suffix boundaries are whitespace only. Punctuation and encoded values remain private without decoding.
- The later source-only handoff does not release the existing test rename or publication holds.
- Direct SDK console output and response details without recognized patterns require separate repairs.
- Ordinary credential labels retain space and tab separators. Credential-word menu preservation remains an unresolved integration requirement.
