# Feature Specification: Token Refusal Messages

**Feature Branch**: `jmorrison-juniper-token-refusal-messages`

**Created**: 2026-10-01

**Status**: Implemented locally. Publication awaits the parent release.

**Input**: User description: "Fix token refusal messages for existing MistHelper issue #3290. Preserve authentication behavior and credential safety."

**Issue**: [MistHelper #3290](https://github.com/jmorrison-juniper/MistHelper/issues/3290)

**Feature Directory**: `specs/3290-token-refusal-messages`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the Correct Token Refusal (Priority: P1)

An operator selects token-variable or browser-token sign-in.
If the portal refuses the token attempt, the message tells the operator to check the token.
It does not tell the operator to check an address or password.

**Why this priority**: The current message names the wrong credentials and gives the operator the wrong action.

**Independent Test**: Refuse each token mode with nonsecret test values.
Check the complete sentence for browser users and automated callers.

**Acceptance Scenarios**:

1. **Given**: The operator selects token-variable sign-in and meets its existing prerequisites.
   **When**: The token attempt fails.
   **Then**: The portal returns the token refusal sentence from FR-001.

2. **Given**: The operator selects token-variable sign-in and meets its existing prerequisites.
   **When**: No token variable contains a token.
   **Then**: The portal returns the same token refusal sentence.

3. **Given**: Startup permits browser-token sign-in.
   **When**: The portal refuses a nonempty token attempt.
   **Then**: The portal returns the token refusal sentence from FR-001.

4. **Given**: Startup does not permit browser-token sign-in.
   **When**: A caller submits that mode with an empty or nonempty token field.
   **Then**: The portal returns the same token refusal sentence.

---

### User Story 2 - Correct an Empty Token Field (Priority: P1)

An operator needs a clear action when the browser-token field contains no token.
The server names the empty field and tells the operator to type a token.
The normal browser form keeps its existing empty-field validation.

**Why this priority**: An empty field needs an action, not advice about an address or password.

**Independent Test**: Submit an empty browser-token field to the isolated seeded portal.
Use automated requests and a real browser submission that bypasses only client validation.

**Acceptance Scenarios**:

1. **Given**: Startup permits browser-token sign-in.
   **When**: An automated caller submits an absent, empty, or space-only token field.
   **Then**: The server returns the empty-field sentence from FR-004 without starting a token attempt.

2. **Given**: Startup permits browser-token sign-in on the isolated seeded portal.
   **When**: A real browser submits an empty form past client validation.
   **Then**: The server returns the exact empty-field sentence on the existing sign-in page.

3. **Given**: The operator uses the normal browser-token form.
   **When**: The operator tries to submit an empty token field.
   **Then**: Existing client validation still prevents submission.

---

### User Story 3 - Keep Existing Sign-In Behavior Safe (Priority: P2)

Operators keep the same sign-in choices, refusal results, and successful journeys.
The wording change exposes no token value or internal failure cause.

**Why this priority**: Correct wording must not change authentication decisions or expose credentials.

**Independent Test**: Repeat provider-login and accepted-token journeys with isolated test values.
Compare their existing outcomes and capture response content, cookies, and logs.

**Acceptance Scenarios**:

1. **Given**: The operator uses provider login.
   **When**: The provider refuses the address/password pair or the password field is empty.
   **Then**: The portal retains the applicable existing sentence from FR-009.

2. **Given**: The portal accepts a token in either token mode.
   **When**: The operator completes sign-in.
   **Then**: The portal retains the existing session behavior and next destination.

3. **Given**: The operator uses provider login successfully or reaches a second-factor or rate-limit result.
   **When**: The portal responds.
   **Then**: The existing response and journey remain unchanged.

4. **Given**: A token attempt raises an exception whose text contains a fake token.
   **When**: The portal refuses the attempt.
   **Then**: The response uses the token refusal sentence and exposes no fake token in responses, cookies, or logs.

---

### Edge Cases

- Startup denial takes precedence over an empty browser-token field.
  The response uses the generic token sentence, not the empty-field sentence.

- An absent, empty, or space-only browser-token field receives the empty-field sentence only when startup permits the mode.

- An absent environment token and a rejected environment token receive the same refusal sentence.

- A browser-token attempt can fail during token acceptance, identity lookup, or session registration.
  Each failure receives the same generic token sentence.

- An exception can contain a fake token.
  The portal must not copy that text into responses, cookies, or logs.

- Browser and automated clients receive different existing response formats.
  They receive the same applicable refusal sentence and failure status.

- Token-variable requests still pass the existing address check.
  This change does not alter a refusal from that common check.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Token-variable refusals MUST use this exact sentence:
  `The portal could not sign you in. Check the token, then try again.`
  This sentence applies when the token is absent or the token attempt fails.

- **FR-002**: Startup-disabled browser-token requests MUST use the sentence from FR-001.
  This rule applies to empty and nonempty token fields.

- **FR-003**: Failed nonempty browser-token attempts MUST use the sentence from FR-001.
  This rule includes failures during token acceptance, identity lookup, and session registration.

- **FR-004**: An enabled browser-token request with an absent, empty, or space-only token field MUST use this exact sentence:
  `The token field is empty. Type your token, then try again.`
  The portal MUST NOT start a token attempt for that request.

- **FR-005**: Every token refusal MUST retain HTTP 400.
  JSON refusals MUST retain `error.code="bad_credentials"` and the existing response shape.

- **FR-006**: The portal MUST retain its existing JSON/browser negotiation.
  Browser refusals MUST retain the sign-in page and the existing `Warning: ` alert prefix.
  The normal browser form MUST retain its existing client validation.

- **FR-007**: Environment-token absence and rejection MUST remain indistinguishable in refusal wording.
  Startup denial and browser-token rejection MUST share the generic token sentence.
  Token attempt failures MUST NOT disclose their internal cause.
  Only an empty field in enabled browser-token mode may receive the empty-field sentence.

- **FR-008**: Tokens MUST NOT appear in response bodies, headers, rendered pages, logs, or cookies.
  This rule includes token values inside exception text and applies to refusals and successful sign-ins.

- **FR-009**: Provider login MUST retain its existing validation, refusal wording, second-factor handling, and rate-limit behavior.
  A refused address/password pair MUST keep:
  `The portal could not sign you in. Check the address and the password, then try again.`
  An empty password MUST keep:
  `The portal received no password. Type your password, then try again.`

- **FR-010**: Accepted token sign-ins and provider sign-ins MUST retain their current session handling and next destination.
  Refusals MUST NOT create a signed-in session.

- **FR-011**: The change MUST affect refusal wording only.
  It MUST NOT change authentication decisions or input validation.
  It MUST NOT add cloud access, guards, fields, settings, or schemas.

- **FR-012**: Route evidence MUST cover every refusal branch for browser users and automated callers.
  Each case MUST compare the complete refusal sentence with its specified text.
  Regression evidence MUST cover provider login and accepted tokens in both token modes.

### Acceptance Evidence

All four rows require both existing response forms.
Test each listed cause independently.

| Mode | Refusal branch and cases | Required sentence |
| --- | --- | --- |
| Token-variable | The token is absent, rejected, or unusable during the token attempt. | FR-001 |
| Browser-token | Startup denies the mode, with an empty or nonempty field. | FR-002, identical to FR-001 |
| Browser-token | Startup permits the mode, with an absent, empty, or space-only field. | FR-004 |
| Browser-token | Startup permits the mode, but a nonempty token attempt fails. | FR-003, identical to FR-001 |

Record genuine failing route/message assertions before changing product code.
Fixture or environment failures do not count.
After the wording change, all required cases must pass.
Use the existing isolated seeded portal for real browser evidence.
Keep server checks active when the browser test bypasses client validation.
Prove that the normal client still prevents empty-token submission.

### Key Entities *(include if feature involves data)*

- **Sign-in mode**: The existing mode identifies the operator's credential choice.
  The choices remain token-variable, browser-token, and provider login.
- **Token**: The existing secret permits token sign-in.
  The portal must not expose its value.
- **Refusal result**: The existing result carries a failure status, failure classification, and operator message.
  This feature changes only the applicable operator message.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four refusal branches show the specified sentence to browser users and automated callers.
  All eight branch/client combinations pass exact-text checks.

- **SC-002**: In 100% of enabled empty-field cases, operators receive text that names the token field and directs them to type a token.

- **SC-003**: Secret exposure equals zero in tested refusals and successful sign-ins, including faults that contain a fake token.

- **SC-004**: All provider-login and accepted-token regression cases retain their existing outcomes, wording, and next destination.

- **SC-005**: The normal browser form still prevents empty-token submission.
  A direct browser submission receives the server's exact empty-field sentence.

## Assumptions

- The issue and supplied fixed sentences define the complete wording change.
  The feature adds no stored data.

- Token-variable scenarios meet the existing address requirement before reaching token refusal handling.
  Common address validation remains unchanged.

- The existing startup decision keeps precedence over the browser-token empty-field check.

- Existing input rules treat absent, empty, and space-only browser-token fields as empty.

- Tests use the existing isolated seeded portal with nonsecret test values.
  The feature needs no live cloud or production dependency.
