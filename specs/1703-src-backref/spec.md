# Feature Specification: Remove source back-references to `MistHelper`

**Feature Branch**: `1703-src-backref`

**Created**: 2026-09-14

**Status**: Draft

**Input**: GitHub issue #1703 asks to remove runtime reads of `MistHelper` from `src`.

## User Scenarios and Testing

### User Story 1 - Source settings do not read the root facade (Priority: P1)

A maintainer can open a source package and see where shared tuning settings live.

**Why this priority**: Settings are low-risk leaf values. They can move before the root alias changes.

**Independent Test**: Run focused unit tests for API fetchers, gateway exporters, and upgrade portal capture readers.

**Acceptance Scenarios**:

1. **Given** a source module needs a page size, **When** it reads the setting, **Then** it imports `src.config.runtime_settings`.
2. **Given** a source module needs a retry setting, **When** it reads the setting, **Then** it imports `src.refactors.fast_mode_constants`.
3. **Given** a source module needs API usage state, **When** it rate-limits a call, **Then** it reads `src.api.api_usage_cache`.

### User Story 2 - Startup keeps source settings synchronized (Priority: P1)

A runtime configuration change during startup must reach source readers.

**Why this priority**: The root facade still owns startup for now, so the source modules need the startup values.

**Independent Test**: Import `MistHelper` and `wsgi` after the slice.

**Acceptance Scenarios**:

1. **Given** startup reads the environment, **When** it publishes runtime settings, **Then** the source settings modules receive the same values.
2. **Given** a source package imports without full startup, **When** it reads a setting, **Then** it gets a safe default.

### Edge Cases

- If a page size is outside the cloud range, the upgrade portal clamps it.
- If a page size is invalid, the upgrade portal uses the fallback size.
- If the root alias remains, source modules that were not in this slice still work.

## Requirements

### Functional Requirements

- **FR-001**: The source packages MUST provide a source-owned module for shared runtime settings.
- **FR-002**: The source packages MUST provide a source-owned module for the API usage cache.
- **FR-003**: The API fetcher MUST read retry settings from `src.config.runtime_settings`.
- **FR-004**: The low-level API fetch helpers MUST read the page limit from `src.config.runtime_settings`.
- **FR-005**: The gateway and pool helpers MUST read fast-mode settings from `src.refactors.fast_mode_constants`.
- **FR-006**: The change MUST NOT modify `MistHelper.py`.
- **FR-007**: The change MUST leave the `sys.modules["MistHelper"]` alias in place.

### Key Entities

- **Runtime settings**: Shared scalar settings that source packages read.
- **API usage cache**: A shared process-local cache for rate limiting.
- **Fast-mode settings**: Shared scalar settings for worker counts and retry budgets.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Executable `importlib.import_module("MistHelper")` calls under `src` drop from 366 to 356.
- **SC-002**: Executable `import MistHelper` imports under `src` drop from 21 to 18.
- **SC-003**: Focused unit tests for the changed areas pass.
- **SC-004**: `import src.api.api_data_fetcher`, `import MistHelper`, and `import wsgi` succeed.
- **SC-005**: `git diff --name-only origin/main...HEAD` does not list `MistHelper.py`.

## Assumptions

- Another agent owns root `MistHelper.py`, so this branch must not change it.
- The root alias removal needs a later issue after all source back-references move.
- This branch delivers the first settings sub-slice, not all of issue #1703.
