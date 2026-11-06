# Feature Specification: Reject Profiles from Failed Responses

**Feature Branch**: `jmorrison-juniper-fix-4564-wan-vpn-profile-503`

**Created**: 2026-11-06

**Status**: Draft

**Input**: Issue #4564 reports that the WAN VPN builder accepts gateway profiles from an HTTP 503 response when its body contains a plausible `results` array.

## User Scenarios & Testing

### User Story 1 - Use Profiles from Successful Requests (Priority: P1)

An operator uses the WAN VPN builder to select gateway profiles. The builder must use profile data only when the profile request succeeds.

**Why this priority**: Failed response data can enter a VPN configuration and cause an incorrect production change.

**Independent Test**: Return a mocked HTTP 503 response with a valid-looking profile array. Verify that the builder returns no profiles and does not continue with VPN creation.

**Acceptance Scenarios**:

1. **Given** a successful profile request, **When** the builder reads the response, **Then** it makes the returned profiles available in alphabetical order.
2. **Given** an HTTP 503 response with a plausible profile array, **When** the builder reads the response, **Then** it returns no profiles.
3. **Given** an unsuccessful profile request, **When** the builder handles the failure, **Then** it stops before it can use response data in a VPN configuration.

### Edge Cases

- A failed response has a valid JSON body and a `results` array.
- A failed response has no profile data or has a malformed body.
- A successful response contains no profiles.
- The profile request raises a transport or authentication error.

## Requirements

### Functional Requirements

- **FR-001**: The builder MUST use gateway profiles only when the profile request succeeds.
- **FR-002**: The builder MUST reject all profile data from an unsuccessful response, regardless of its body.
- **FR-003**: The builder MUST stop safely when it has no profiles from a successful request.
- **FR-004**: The builder MUST keep successful profiles in the existing case-insensitive alphabetical order.

### Mist Cloud Transport Requirements

- The feature uses the existing `mistapi` method `listOrgDeviceProfiles` with the gateway profile filter.
- The feature MUST keep SDK authentication and endpoint behavior unchanged. It MUST NOT add direct HTTP calls.
- The mocked response test MUST verify that an HTTP 503 response with plausible profile data yields no profiles.
- The existing endpoint call MUST remain scoped to gateway profiles. The test MUST verify its arguments.
- The change MUST NOT add credentials to logs or output.

### Key Entities

- **Gateway profile**: A profile that the operator may select for a WAN VPN.
- **Profile response**: The result of a gateway profile request, including its success status and body.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A mocked unsuccessful response with any profile array supplies zero profiles to the builder.
- **SC-002**: A successful response supplies the same profiles in alphabetical order.
- **SC-003**: The builder does not create a VPN after a failed profile request.

## Assumptions

- The Mist SDK response exposes the HTTP success status before profile data is used.
- The current graceful failure behavior remains: a failed profile request produces an empty profile list.
- Changes to the endpoint, authentication, and VPN creation behavior are outside this feature.
