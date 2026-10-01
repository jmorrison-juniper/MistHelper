# Feature Specification: Required token resolution

**Feature Branch**: `jmorrison-juniper-required-token-resolution`

**Created**: 2026-10-01

**Status**: Verified locally. Publication requires the parent grant.

**Input**: Repair one required-token slice. Part of [#2861](https://github.com/jmorrison-juniper/MistHelper/issues/2861).

The campaign contains 31 candidates. This slice does not complete the campaign.
Publication position 36 follows the read-only retry slice for issue #2752.
The parent must grant a full verified-main SHA before publication or task-delivery completion.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use the next usable source (Priority: P1)

An operator needs a session when an earlier token source contains no usable credential.

**Why this priority**: A blank source must not block a usable credential from the next source.

**Independent Test**: Import the factory. Inject controlled Redis and Vault values. Replace only the SDK constructor.

**Acceptance Scenarios**:

1. **Given** a blank cache and a usable Vault token, **When** the factory creates a session, **Then** it uses the Vault token.
2. **Given** a blank Vault token and a usable configured environment token, **When** the factory creates a session, **Then** it uses the configured token.
3. **Given** an invalid non-string source, **When** the factory resolves a token, **Then** it reports rejection without the value.

### User Story 2 - Stop when no usable token exists (Priority: P1)

An operator needs a visible failure before the SDK receives an unusable credential.

**Why this priority**: A session with a blank token masks the missing input.

**Independent Test**: Supply missing, blank, and invalid values. Require the existing failure message and zero SDK constructions.

**Acceptance Scenarios**:

1. **Given** three unusable sources, **When** the factory creates a session, **Then** it raises the existing no-token `RuntimeError`.
2. **Given** unusable provider values, **When** resolution fails, **Then** no invalid value enters the token cache.
3. **Given** controlled secret markers, **When** resolution reports rejection, **Then** product diagnostics contain no marker.

### User Story 3 - Preserve healthy behavior (Priority: P2)

An operator needs the same token value, source order, organization scope, and provider failure policy.

**Why this priority**: The repair must not change existing healthy sessions or rate limiting.

**Independent Test**: Assert exact constructor arguments, provider calls, cache writes, and exception identity.

**Acceptance Scenarios**:

1. **Given** a usable cache token, **When** resolution runs, **Then** it bypasses Vault and preserves the exact token.
2. **Given** a usable Vault token, **When** resolution runs, **Then** the cache uses the existing organization key and TTL.
3. **Given** a provider exception, **When** resolution runs, **Then** the existing handler or propagation policy remains unchanged.

### Edge Cases

- `None`, empty strings, ASCII whitespace, and Unicode whitespace contain no usable credential.
- Redis bytes keep the existing decode behavior. An invalid byte sequence still raises its decode error.
- Vault and configured environment bytes remain unsupported. Resolution rejects them without conversion.
- Numbers, booleans, containers, and arbitrary objects must not reach the SDK.
- A nonblank opaque string remains usable. Resolution must not trim, reformat, or classify it.
- A cache read error or cache write error still propagates. Vault lookup errors still permit the existing fallback.
- The configured setting remains the final source. Resolution must not read a different process environment value.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Accept a credential only when it is a string with at least one non-whitespace character.
- **FR-002**: Preserve the exact accepted string. Use whitespace removal only for the usability decision.
- **FR-003**: Preserve cache, Vault, and configured environment precedence. Do not read later sources after success.
- **FR-004**: Reject unusable cache and Vault values before a cache write or SDK construction.
- **FR-005**: Preserve the existing no-token exception type and message.
- **FR-006**: Report unusable sources and final failure without credential values, bodies, or headers.
- **FR-007**: Name `api_token` and `mist_api_token` in the final diagnostic. State the number of checked sources.
- **FR-008**: Preserve Redis byte decoding, the cache key, the cache TTL, and organization scope.
- **FR-009**: Preserve provider exceptions and all existing exception handlers.
- **FR-010**: Preserve the SDK constructor arguments and rate-limiter behavior.
- **FR-011**: Prove the three controlled original failures through the actual imported factory and session boundary.
- **FR-012**: Use isolated local environments and mocked transport. Do not contact live credentials, stores, or Mist services.

### Key Entities *(include if feature involves data)*

- **Credential candidate**: An untrusted provider value. Only a nonblank string can become an accepted token.
- **Organization identifier**: The existing input that selects the Vault path, token cache key, and rate-limit bucket.

This slice adds no persistent entity, schema, setting, or dependency.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The three original controlled cases fail before the repair and pass after the repair.
- **SC-002**: Every all-source rejection constructs zero SDK sessions and writes zero invalid cache records.
- **SC-003**: Every healthy case preserves the exact token and expected source calls.
- **SC-004**: Every changed executable line and branch receives focused test coverage.
- **SC-005**: The backend retains its configured collection floor of 390 and coverage floor of 56 percent.
- **SC-006**: Local evidence records exact gate results and capability limits without baseline or exclusion changes.

## Assumptions

- Only `mist-ops-platform/src/shared/mist/session.py` requires a production change.
- Existing provider methods remain the source boundaries. This slice adds no wrapper, adapter, alias, or class.
- The primary CLI, settings, middleware, manifests, governance, and other owners' files remain read-only.
- A local commit preserves the repair. Publication remains blocked until the parent grants the verified base.
