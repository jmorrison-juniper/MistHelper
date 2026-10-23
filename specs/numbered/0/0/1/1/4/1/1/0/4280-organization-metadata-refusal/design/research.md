# Research: Organization metadata refusal

## Decision

Check the integer HTTP status before reading metadata.
Accept only object metadata without an error field and with a nonblank string name.
Log status and organization context, never the body or exception text.
Catch `OSError` and `RuntimeError` at the SDK request boundary.
Let unexpected programming exceptions propagate.

## Evidence

Current main returned `Rejected name` for a mocked HTTP 403 with that name.
The module emitted zero warnings.
All 151 existing migration tests passed before the repair.
The existing success mocks omitted status, which allowed the defect to remain hidden.
The installed SDK raises `RuntimeError` for exhausted token rotation.
Request exceptions inherit from `OSError`.

## Rationale

The status proves whether metadata can be trusted.
A plausible name in a refusal body must not label an export.
The explicit `Unknown` result preserves the existing nonfatal contract.
An error field invalidates a nominally successful body.
Exception type names provide context without exposing exception text.

## Alternatives Considered

- Checking only for an error field accepts names in other unsuccessful results.
- Assuming success when status is absent leaves validation incomplete.
- Logging the response or exception text can expose credentials.
- Changing the migration workflow or confirmation boundary exceeds the issue scope.

## Process

The artifacts list endpoint returned HTTP 404, so issue artifacts were unavailable.
The issue had no comments or image references.
The exact-path open pull request scan found no owner for the planned source and test files.
The local branch matched fetched `origin/main` before edits.
