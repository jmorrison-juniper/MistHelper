# Feature Specification: Dashboard data summary performance

**Feature Branch**: `chore/2439-dashboard-summary-performance`
**Created**: 2026-09-10
**Status**: Implemented
**Input**: Issue #2439 asks the dashboard to avoid repeated work when it builds
the data directory summary.

## User Scenarios and Tests

### User Story 1 - Open a dashboard with many data files

A NOC engineer opens the web portal dashboard after many exports exist in
`data/`. The dashboard must show the total file count and the five newest files
without formatting rows that it does not render.

**Why this matters**: A dashboard load is a common read-only path. It must stay
fast when the data directory grows.

**Acceptance tests**:

1. Given a data directory with visible files, hidden files, and a directory, the
   summary counts only visible files.
2. Given more than five visible files, the summary returns the five newest files.
3. Given files with equal timestamps, the summary preserves scan order for ties.
4. Given an absent data directory, the summary returns an empty result.

## Requirements

### Functional Requirements

- **FR-001**: The dashboard summary MUST return the same keys as before:
  `file_count`, `recent_files`, and `data_dir`.
- **FR-002**: The dashboard summary MUST count non-hidden files only.
- **FR-003**: The dashboard summary MUST exclude directories and hidden entries.
- **FR-004**: The recent-file list MUST remain sorted by `last_modified`
  descending.
- **FR-005**: Equal `last_modified` values MUST keep the previous stable order.
- **FR-006**: The absent-directory result MUST stay empty.
- **FR-007**: `_count_data_files()` and `_get_recent_files()` MUST keep their
  helper contracts.

### Performance Requirements

- **PR-001**: The retained change MUST improve the `_build_data_summary()`
  workload by at least 5 percent.
- **PR-002**: The benchmark MUST use a local disposable data directory.
- **PR-003**: The implementation MUST stay sequential. It must not add threads,
  processes, async work, or worker tuning.

## Non-Goals

- This change does not change the dashboard template.
- This change does not change file permissions.
- This change does not add a cache.
- This change does not change the data browser file listing.

## Assumptions

- A 5000-file local data directory is a useful worst-case proxy for a large
  operator export directory.
- The dashboard renders only the five recent files.

