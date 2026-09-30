# Feature Specification: Test the guest portal SMS provider

**Feature Branch**: `feat/3564-sms-provider-test`  
**Created**: 2026-09-29  
**Status**: Draft  
**Input**: User description: "menu 284 test the guest portal SMS provider."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Send a provider test safely (Priority: P1)

A NOC engineer selects an SMS provider, enters the required credentials with hidden input, enters the destination number, confirms the send, and receives a clear verdict.

**Why this priority**: This is the core repair action when a guest cannot receive an SMS code.

**Independent Test**: Mock the client, run the operation prompt flow, and verify that it asks `y` or `N` before the call.

**Acceptance Scenarios**:

1. **Given** an engineer chooses `Twilio`, **When** they enter the required values and answer `y`, **Then** MistHelper sends the Twilio body that the OpenAPI schema requires.
2. **Given** an engineer answers `N` at the confirmation, **When** the operation continues, **Then** MistHelper sends no API request and writes no result file.
3. **Given** Mist returns a non-2xx response, **When** the operation reports the result, **Then** the message includes the status code and response text without a traceback.

---

### User Story 2 - Preserve credentials (Priority: P1)

A NOC engineer can test SMS delivery without exposing provider credentials in terminal echoes, logs, or CSV output.

**Why this priority**: SMS provider tokens are secrets, and a troubleshooting tool must not disclose them.

**Independent Test**: Patch the secret prompt function and logger, run each provider path, and assert that the secret values do not appear in logs or output rows.

**Acceptance Scenarios**:

1. **Given** the operation asks for a provider token or secret, **When** the prompt runs, **Then** it uses hidden input.
2. **Given** a successful or failed provider test, **When** `SmsProviderTest.csv` is read, **Then** it includes provider, destination, verdict, and time only.

---

### User Story 3 - Test every supported provider body (Priority: P2)

A NOC engineer can test `Twilio`, `SMSGlobal`, or `Telstra` and MistHelper sends only the fields that provider expects.

**Why this priority**: Each provider has a different credential schema, so one generic body can fail.

**Independent Test**: Unit tests build each provider body and compare the keys to the OpenAPI schema.

**Acceptance Scenarios**:

1. **Given** the selected provider is `SMSGlobal`, **When** the request body is built, **Then** it contains `smsglobal_api_key`, `smsglobal_api_secret`, and `to`.
2. **Given** the selected provider is `Telstra`, **When** the request body is built, **Then** it contains `telstra_client_id`, `telstra_client_secret`, and `to`.

---

### Edge Cases

- The engineer enters an unknown provider number.
- The engineer leaves a required public value blank.
- The engineer leaves a required secret blank.
- The API response contains JSON instead of plain text.
- The API response has no status code.
- The export writer refuses to write the result row.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST add menu 284 as an `interactive` operation through the deferred wiring manifest.
- **FR-002**: The operation MUST support `Twilio`, `SMSGlobal`, and `Telstra`.
- **FR-003**: Every credential prompt MUST use hidden input.
- **FR-004**: The operation MUST never write credentials to logs, terminal output, CSV rows, or database rows.
- **FR-005**: The operation MUST ask the engineer to enter `y` before it sends the test message.
- **FR-006**: A refusal or any answer other than `y` or `Y` MUST stop before the API request.
- **FR-007**: The Twilio request body MUST contain `from`, `to`, `twilio_sid`, and `twilio_auth_token`.
- **FR-008**: The SMSGlobal request body MUST contain `smsglobal_api_key`, `smsglobal_api_secret`, and `to`.
- **FR-009**: The Telstra request body MUST contain `telstra_client_id`, `telstra_client_secret`, and `to`.
- **FR-010**: A non-2xx response MUST print the status code and response text without a traceback.
- **FR-011**: A successful send MUST write `SmsProviderTest.csv` under `data/` through the standard exporter.
- **FR-012**: The output row MUST contain provider, destination, verdict, HTTP status, response text, and time.
- **FR-013**: The wiring manifest MUST include menu entry, registry comment, primary key strategy, category table change, and import line.
- **FR-014**: The release note fragment MUST exist at `changelog.d/issue-3564-sms-provider-test.md`.

### Key Entities *(include if feature involves data)*

- **SMS Provider Selection**: The selected provider and its display name.
- **Provider Credentials**: Secret or public values needed by the provider test endpoint. Secret fields are never persisted.
- **SMS Test Request**: The OpenAPI-aligned body sent to `/api/v1/utils/test_*`.
- **SMS Test Result**: The provider, destination, verdict, HTTP status, response text, and run time.

## Assumptions

- The shared Mist API session is available through `SourceDependencyResolver.apisession`.
- The operation does not require an organization ID or a site ID because the endpoints are under `/api/v1/utils/`.
- A `2xx` status means Mist accepted the provider test request.
- The integration pull request wires menu 284 into `MistHelper.py` and `OperationRegistry`.

## Clarifications

### Session 2026-09-29

- Q: Which menu category applies? -> A: Menu 284 is `interactive`.
- Q: Which providers are in scope? -> A: `Twilio`, `SMSGlobal`, and `Telstra`.
- Q: Where do forbidden wiring changes go? -> A: `specs/3564-sms-provider-test/wiring.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Unit tests prove that each provider body has exactly the schema keys required by the OpenAPI document.
- **SC-002**: Unit tests prove that secret values do not appear in result rows or captured log messages.
- **SC-003**: Unit tests prove that a refusal at confirmation sends zero API requests.
- **SC-004**: Unit tests prove that a non-2xx response returns a handled verdict with the HTTP status and response text.
- **SC-005**: Validation gates pass for the new package and its tests.
