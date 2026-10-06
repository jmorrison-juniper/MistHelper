# Feature Specification: Remove Deprecated Mist Edge WebSocket Channels

**Feature Branch**: `fix/3737-remove-deprecated-mxedges`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issue #3737. Remove the deprecated `site.mxedges` and `org.mxedges` WebSocket
catalog channels. Keep `site.stats.mxedges` and `org.stats.mxedges` with their statistics paths.

## User Scenarios & Testing

### User Story 1 - Select supported Mist Edge streams (Priority: P1)

A network operations center engineer needs the WebSocket catalog to offer only Mist Edge streams
that Mist accepts, so live monitoring starts without a deprecation error.

**Why this priority**: Deprecated channels fail at runtime and block the engineer from monitoring
Mist Edge data.

**Independent Test**: Inspect the catalog entries and verify that the two deprecated keys are
absent while both statistics keys remain available with their supported paths.

**Acceptance Scenarios**:

1. **Given** the WebSocket channel catalog, **When** an engineer views the organization channels,
   **Then** `org.mxedges` is not listed and `org.stats.mxedges` remains listed with
   `/orgs/{org_id}/stats/mxedges`.
2. **Given** the WebSocket channel catalog, **When** an engineer views the site channels,
   **Then** `site.mxedges` is not listed and `site.stats.mxedges` remains listed with
   `/sites/{site_id}/stats/mxedges`.
3. **Given** a request for either supported statistics key, **When** the catalog builds paths for
   valid organization or site identifiers, **Then** it returns the matching statistics path.
4. **Given** a request for either removed key, **When** the catalog performs a lookup, **Then** it
   returns no channel definition and does not build a deprecated path.

### User Story 2 - Preserve supported SDK channel parity (Priority: P2)

A maintainer needs the supported statistics catalog entries to remain aligned with the public
Mist WebSocket channel classes, so the catalog does not silently drift from the SDK.

**Why this priority**: Path drift can cause a supported channel to fail even after deprecated
entries are removed.

**Independent Test**: Compare the catalog paths for `org.stats.mxedges` and `site.stats.mxedges`
with the corresponding public SDK channel paths using valid test identifiers.

**Acceptance Scenarios**:

1. **Given** the organization statistics catalog entry, **When** its path is compared with
   `orgs.MxEdgesStatsEvents`, **Then** both paths match.
2. **Given** the site statistics catalog entry, **When** its path is compared with
   `sites.MxEdgesStatsEvents`, **Then** both paths match.

### Edge Cases

- The catalog contains no deprecated organization or site Mist Edge event key.
- A lookup for a removed key returns no definition.
- A supported statistics key still requires the correct organization or site identifier.
- A supported key must not lose its `stats/mxedges` path during catalog changes.
- The catalog entry count and page order must reflect the two removed entries.

## Requirements

### Functional Requirements

- **FR-001**: The WebSocket channel catalog MUST NOT expose the `org.mxedges` key.
- **FR-002**: The WebSocket channel catalog MUST NOT expose the `site.mxedges` key.
- **FR-003**: The catalog MUST retain the `org.stats.mxedges` key with the path
  `/orgs/{org_id}/stats/mxedges`.
- **FR-004**: The catalog MUST retain the `site.stats.mxedges` key with the path
  `/sites/{site_id}/stats/mxedges`.
- **FR-005**: A catalog lookup for either removed key MUST return no channel definition.
- **FR-006**: The retained organization statistics entry MUST build paths from a valid
  organization identifier without changing the path shape.
- **FR-007**: The retained site statistics entry MUST build paths from a valid site identifier
  without changing the path shape.
- **FR-008**: Contract coverage MUST verify that each retained statistics entry matches its public
  Mist WebSocket SDK channel path.
- **FR-009**: Catalog coverage MUST verify that the removed keys are absent and that the catalog
  entry count decreases by two from the current 18-entry catalog.
- **FR-010**: This feature MUST change only the WebSocket catalog behavior and its directly related
  verification. It MUST NOT change Mist Edge REST operations or statistics data handling.

### Mist Cloud Transport Requirements

- The supported organization stream uses the public SDK WebSocket channel
  `mistapi.websockets.orgs.MxEdgesStatsEvents` and the path
  `/orgs/{org_id}/stats/mxedges`.
- The supported site stream uses the public SDK WebSocket channel
  `mistapi.websockets.sites.MxEdgesStatsEvents` and the path
  `/sites/{site_id}/stats/mxedges`.
- The deprecated `mistapi.websockets.orgs.MxEdgesEvents` and
  `mistapi.websockets.sites.MxEdgesEvents` channels are out of scope for catalog exposure.
- Verification MUST use synthetic identifiers and MUST NOT require a live Mist credential or
  start a production WebSocket stream.

### Key Entities

- **Channel catalog entry**: A selectable WebSocket stream identified by a catalog key, scope,
  display text, and Mist channel path.
- **Statistics stream**: A supported organization or site WebSocket channel that reports Mist
  Edge statistics through the `stats/mxedges` path.
- **Deprecated event stream**: A removed organization or site channel that uses the rejected
  `mxedges` path without the `stats` segment.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Zero catalog entries use the deprecated keys `org.mxedges` or `site.mxedges`.
- **SC-002**: Exactly two retained Mist Edge statistics entries remain available, and both use
  their required `stats/mxedges` paths.
- **SC-003**: Catalog lookup tests return no definition for both removed keys.
- **SC-004**: SDK parity tests pass for both retained statistics entries with synthetic identifiers.
- **SC-005**: The catalog contains 16 entries after the two deprecated entries are removed, with
  all other entries unchanged in order and behavior.
- **SC-006**: Verification completes without a live Mist credential, a production WebSocket
  connection, or a change to Mist Edge REST behavior.

## Assumptions

- Issue #3737 defines the deprecated channels as the organization and site event keys without
  the `stats` segment.
- The existing public SDK statistics channel classes remain the source for supported path parity.
- Existing catalog ordering remains unchanged except for the removal of the two deprecated entries.
- Existing channel validation and identifier rules remain unchanged for retained entries.
- This specification covers the catalog and its direct contract verification only. It does not
  authorize changes to production code or tests in the specification phase.
