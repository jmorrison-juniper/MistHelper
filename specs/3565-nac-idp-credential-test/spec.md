# Feature Specification: NAC IDP Credential Test

**Feature Branch**: `feat/3565-nac-idp-credential-test`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 285 validate a NAC identity provider credential. Before an Access Assurance cutover an operator wants to prove that Mist can bind to the identity provider with a test user. Mist offers validateOrgIdpCredential, and no MistHelper operation calls it. The operation lists the NAC identity providers of the organization, asks for one, asks for a username and a hidden password, calls the validation endpoint, and prints the verdict with the returned groups or attributes. It writes NacIdpCredentialTest.csv with idp name, username, verdict, and time, and no password."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate an identity provider bind (Priority: P1)

Before an Access Assurance cutover, an operator validates that Mist can bind to one NAC identity provider with one test user.

**Why this priority**: This is the core cutover safety check. It proves the credential path before enforcement changes reach users.

**Independent Test**: A unit test builds the request body, stubs the validation client, and verifies the printed verdict and export row.

**Acceptance Scenarios**:

1. **Given** an organization has NAC identity providers, **When** the operator selects one provider and confirms the test, **Then** MistHelper sends `idp_id`, `username`, and `password` to `validateOrgIdpCredential`.
2. **Given** the API returns success with attributes, **When** the test completes, **Then** MistHelper prints the success verdict and the returned groups or attributes.

---

### User Story 2 - Protect the password (Priority: P1)

The operator enters the test user's password through a hidden prompt, and MistHelper never writes it to logs or files.

**Why this priority**: The feature handles live credentials. Credential exposure would create an unacceptable security risk.

**Independent Test**: A unit test patches the hidden prompt, captures log output, reads the export rows, and asserts that the password is absent.

**Acceptance Scenarios**:

1. **Given** the operator starts the test, **When** MistHelper asks for the password, **Then** the prompt uses hidden input.
2. **Given** the test finishes, **When** MistHelper writes `NacIdpCredentialTest.csv`, **Then** the file contains no password value.

---

### User Story 3 - Handle a rejected credential (Priority: P2)

The operator receives the API rejection reason without a traceback, so the operator can repair the identity provider setting or the test user.

**Why this priority**: Failed credentials are the main troubleshooting path. The tool must make the failure safe and readable.

**Independent Test**: A unit test stubs a failed validation response and asserts that the failure reason is printed without an exception.

**Acceptance Scenarios**:

1. **Given** the API rejects the credential, **When** MistHelper receives the response, **Then** it prints the returned reason and exits cleanly.
2. **Given** the operator declines the confirmation prompt, **When** MistHelper reads `N`, **Then** it sends no credential and writes no result file.

---

### Edge Cases

- If the organization has no identity providers, MistHelper prints a clear message and sends no credential.
- If the API returns fields other than `groups`, MistHelper prints the returned attributes in a safe text form.
- If the selected provider list includes SSO providers that are not NAC providers, MistHelper labels the source and only sends the selected identifier.
- If the export backend fails, MistHelper logs the export failure after the credential test completes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: MistHelper MUST add menu 285 as an `interactive` operation through the deferred wiring manifest.
- **FR-002**: MistHelper MUST list available identity providers before it asks for a username or password.
- **FR-003**: MistHelper MUST ask the operator to select one identity provider by a numbered choice.
- **FR-004**: MistHelper MUST ask for a username with the existing safe input pattern.
- **FR-005**: MistHelper MUST ask for the password with hidden input.
- **FR-006**: MistHelper MUST ask `y` or `N` before it sends the credential to Mist.
- **FR-007**: MistHelper MUST send a request body that matches the OpenAPI schema for `validateOrgIdpCredential`.
- **FR-008**: MistHelper MUST print the validation verdict, the API failure reason, and returned groups or attributes when present.
- **FR-009**: MistHelper MUST write `NacIdpCredentialTest.csv` under `data/` through the shared exporter.
- **FR-010**: The export row MUST include identity provider name, username, verdict, reason, returned attributes, and time.
- **FR-011**: The password MUST NOT appear in a log line, exception message, export row, or output file.
- **FR-012**: The package MUST include model and client tests with no network access.
- **FR-013**: The release note fragment MUST exist at `changelog.d/issue-3565-nac-idp-credential-test.md`.
- **FR-014**: The wiring manifest MUST exist at `specs/3565-nac-idp-credential-test/wiring.md`.

### Key Entities *(include if feature involves data)*

- **IdentityProviderChoice**: One selectable identity provider. It has an identifier, a name, a type, and a source endpoint.
- **CredentialTestRequest**: One request body. It has `idp_id`, `username`, and `password`.
- **CredentialTestResult**: One validation result. It has a verdict, a reason, groups, attributes, and a timestamp.
- **CredentialTestExportRow**: One export record. It has provider name, username, verdict, reason, attributes, and time. It has no password.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can complete one credential validation from menu 285 with five prompts or fewer.
- **SC-002**: Unit tests prove that the request body contains exactly the credential fields required by OpenAPI.
- **SC-003**: Unit tests prove that the password does not appear in captured logs or export rows.
- **SC-004**: A failed validation returns a readable reason and produces no traceback in the operation test.
- **SC-005**: The implementation passes compile, Ruff, Black, mypy, pydocstyle, pytest, vulture, and interrogate gates for the owned package.

## Assumptions

- The operator has a valid Mist API session with permission to read organization NAC identity providers and test one provider.
- The request does not create, update, or delete Mist configuration.
- The integration pull request registers the menu row and the primary key strategy from `wiring.md`.
- The operation writes one result row for each confirmed credential test.
