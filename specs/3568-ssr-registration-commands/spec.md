# Feature Specification: SSR registration commands

**Feature Branch**: `feat/3568-ssr-registration-commands`  
**Created**: 2026-09-29  
**Status**: Draft  
**Input**: Menu 288 shows the SSR registration commands from `getOrg128TRegistrationCommands`.

## User Scenarios and Testing

### Primary User Story

A NOC engineer manually onboards a Session Smart Router. The engineer opens menu 288 and receives the organization registration commands on the console. The command text can include a registration code, so the read action does not prompt. The operation asks for consent before it writes the same command text to `data/SsrRegistrationCommands.txt`.

### Acceptance Scenarios

1. **Given** a successful Mist API response with registration commands, **when** the engineer runs menu 288, **then** the operation prints the commands to the console without a prompt before the read.
2. **Given** a successful Mist API response, **when** the engineer answers `y` to the write prompt, **then** the operation writes `data/SsrRegistrationCommands.txt` and logs the file path without the registration code.
3. **Given** a successful Mist API response, **when** the engineer answers `N` or presses Enter at the write prompt, **then** the operation leaves the file unchanged.
4. **Given** a non-2xx API response, **when** the engineer runs menu 288, **then** the operation prints the status code and exits without a traceback.
5. **Given** captured log output, **when** the response contains a registration code, **then** the log output contains no registration code.

## Requirements

### Functional Requirements

- **FR-001**: The operation MUST call `getOrg128TRegistrationCommands` for the active organization.
- **FR-002**: The operation MUST print the returned command text to the console without prompting before the read.
- **FR-003**: The operation MUST ask `Write registration commands to data/SsrRegistrationCommands.txt? (y/N):` before it writes the file.
- **FR-004**: The operation MUST write only after the engineer answers `y` or `Y`.
- **FR-005**: The operation MUST log the destination file path and MUST NOT log the command text or registration code.
- **FR-006**: The operation MUST print a non-2xx status code and exit without a traceback.
- **FR-007**: The operation MUST register as `interactive_safe` with a skip reason that names the write prompt.
- **FR-008**: The wiring manifest MUST state the deferred menu and registry changes for integration.
- **FR-009**: The release note fragment MUST name issue #3568.

## Key Entities

- **Registration commands**: The SSR onboarding command text returned by Mist. It can include a registration code.
- **Write confirmation**: The y/N prompt that protects the command text before a file write.
- **Wiring manifest**: The deferred integration data for menu 288 and registry metadata.

## Success Criteria

- **SC-001**: Unit tests prove the successful console print path and no pre-read prompt.
- **SC-002**: Unit tests prove that a file write occurs only after a `y` answer.
- **SC-003**: Unit tests prove that logs do not contain the registration code.
- **SC-004**: Unit tests prove that a non-2xx response prints the status code and exits cleanly.
