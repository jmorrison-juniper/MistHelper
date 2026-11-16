# Feature Specification: README Authentication Guidance

**Feature Branch**: `jmorrison-juniper-readme-authentication-guidance`
**Created**: 2026-11-15
**Status**: Draft
**Input**: Correct README guidance for API token and interactive two-factor login.

## User Scenarios & Testing

### User Story 1 - Choose an authentication method (Priority: P1)

A network operator reads the README and chooses a MistHelper authentication method that fits the operator's access.

**Why this priority**: Operators need correct setup guidance before they can use MistHelper.

**Independent Test**: Review the README Who section and confirm that it describes token use and interactive sign-in.

**Acceptance Scenarios**:

1. **Given** an operator without an API token, **When** the operator reads the Who section, **Then** the operator sees that `--login` accepts an email and password.
2. **Given** an account that requires two-factor authentication, **When** the operator uses `--login`, **Then** the guidance says MistHelper prompts for a verification code.

### User Story 2 - Understand token handling (Priority: P2)

An operator reads where MistHelper runs and learns that MistHelper sends an API token to Mist over HTTPS.

**Why this priority**: Accurate token handling guidance helps operators protect credentials.

**Independent Test**: Review the README Where section and confirm it describes local token storage and HTTPS transmission.

**Acceptance Scenarios**:

1. **Given** an operator who stores a token in `.env`, **When** the operator reads the Where section, **Then** the operator sees that token-based requests send the token to Mist over HTTPS.
2. **Given** an operator who reads about interactive sign-in, **When** the operator reads the Where section, **Then** the operator does not see a claim that the token never leaves the host.

### Edge Cases

- An account may not require a two-factor code.
- The token method and interactive sign-in must remain distinct.
- Local `.env` storage must not imply that MistHelper keeps the token on the host during a request.

## Requirements

### Functional Requirements

- **FR-001**: The README Who section and credential setup MUST state that operators can use an API token or interactive `--login`.
- **FR-002**: The README MUST explain that `--login` uses an email and password and prompts for a verification code when Mist requires two-factor authentication.
- **FR-003**: The README MUST state that token-based requests send the API token to Mist over HTTPS.
- **FR-004**: The README MUST describe `.env` as local storage without claiming that the token never leaves the host.
- **FR-005**: The README MUST link to the command-line reference for additional `--login` details.
- **FR-006**: The change MUST leave runtime behavior, WAN documentation, Menu 164 guidance, and the separate API-page issue unchanged.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The README Who section names both supported authentication methods.
- **SC-002**: The README states that an account may require a two-factor verification code during interactive sign-in.
- **SC-003**: The README states that MistHelper sends the token to Mist over HTTPS and no longer claims that the token never leaves the host.
- **SC-004**: The README links to the command-line reference and changes no unrelated content.

## Assumptions

- The current `--login` flow remains the source of truth for email, password, and conditional two-factor prompts.
- The current Mist API authentication documentation remains the source of truth for token transmission.
- This issue changes documentation only. It does not change authentication behavior or the separate API-page candidate.
