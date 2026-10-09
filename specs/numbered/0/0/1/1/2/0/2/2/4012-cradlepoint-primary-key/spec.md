# Feature Specification: Cradlepoint Status Primary Key

**Feature Branch**: `issue-4012-empty-export-status`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issue #4012 and measurement of merged pull request #4048.

## Measurement

Pull request #4048 added the strict HTTP 2xx check in
`org_cradlepoint_connection_exporter.py`. It did not add a catalog entry for
`testOrgCradlepointConnection`.

The OpenAPI schema `test_cradlepoint` has no stable row identifier. The
exporter adds `org_id` to every row before it writes the result. One row per
organization therefore has a stable natural key.

## User Story

As an operator, I need repeated Cradlepoint status exports for one organization
to update one row instead of creating rows with artificial identifiers.

## Requirements

- **FR-001**: The strategy catalog MUST contain
  `testOrgCradlepointConnection`.
- **FR-002**: The catalog entry MUST use `natural_pk`.
- **FR-003**: The catalog entry MUST use `org_id` as its primary key.
- **FR-004**: The focused test MUST fail when the entry is absent.
- **FR-005**: The change MUST not alter the HTTP transport gate from #4048.
- **FR-006**: The change MUST not expose response credentials in a key or log.

## Acceptance Scenarios

1. **Given** the strategy catalog, **when** the endpoint name is read, **then**
   the entry exists with type `natural_pk`.
2. **Given** the catalog entry, **when** its primary key is read, **then** it
   contains only `org_id`.
3. **Given** the regression test on the pre-change catalog, **when** it runs,
   **then** it fails with a missing-key error.
4. **Given** the repaired catalog, **when** the regression test runs, **then**
   it passes.

## Scope

This change updates the primary-key catalog, its focused regression test, this
specification, and one changelog fragment. It does not migrate existing rows
created with the fallback strategy.
