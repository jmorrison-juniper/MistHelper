# Implementation Plan: Count Catalog Completeness

**Branch**: `3995-sdk-count-catalog` | **Date**: 2026-10-15 | **Spec**: [spec.md](spec.md)

**Input**: Issue #4240

## Summary

Add the two missing organization count operations to the existing operator catalog. Add a persistence strategy for organization variables and preserve the established fingerprint strategy.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: mistapi 0.64.1

**Storage**: Existing CSV and database exporters

**Testing**: pytest with mocked SDK and export calls

**Target Platform**: Windows, macOS, and Linux

**Project Type**: Python command-line application

**Performance Goals**: No additional API calls

**Constraints**: Use supported SDK functions. Do not call a live Mist service in tests.

**Scale/Scope**: Two organization count choices, one primary-key strategy, focused catalog tests, and one release-note fragment.

## Constitution Check

- The timestamp specification uses the managed `specs/live/` root.
- The organization count functions exist in mistapi 0.64.1 and take a session and organization ID.
- The known site fingerprint count remains excluded. Issues #3334 and #3691 establish the organization scope.
- The fingerprint census retains its existing composite key. The new variable count uses the generated count-row key pattern.
- Tests use mocks and do not need a live token or container.
- The release note uses a unique issue-specific fragment. `CHANGELOG.md` remains unchanged.
- No process-folder debt changes outside the managed feature directory.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/1/3/4/3/0/4240-sdk-count-catalog/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md
```

### Source and Tests

```text
src/operations/exporting/export/count_exporter.py
src/foundation/support/refactors/endpoint_primary_key_strategies.py
tests/unit/export/test_count_exporter.py
changelog.d/issue-4240-count-exporter-catalog.md
```

**Structure Decision**: Extend the existing count catalog and its focused unit tests. Do not add a new menu number or API client.

## Complexity Tracking

No constitution violation or new architectural component is required.
