# Security Requirements Quality Checklist: Batch target site snapshot

**Purpose**: Confirm that the security-relevant requirements of the snapshot are complete, measurable, and testable.
**Created**: 2026-11-26
**Feature**: `spec.md` and `plan.md` in the parent folder

## Membership and Scope

- [x] FR-007 requires a refusal of a foreign site before any device or resource read. The existing foreign-site test asserts that no device read occurs.
- [x] FR-006 requires a failed read to clear the snapshot and raise. A test covers this path (`test_failed_refresh_clears_the_snapshot_and_raises`).
- [x] The snapshot never returns rows from another organization. Each snapshot belongs to one picker, and the picker reads one organization.
- [x] The fail-closed rule (D-5) names the outcome for each failure. A reviewer can name the expected error.

## Credential and Secret Handling

- [x] The change adds no credential, no token, and no new secret read.
- [x] The log events carry a count or an exception type name only (contract `site-snapshot-interface.md`). No identifier, label, or token enters a log field.
- [x] The error event records the exception type name, as `resources.py` already does for failed reads.

## Request Volume and Limits

- [x] The change reduces the organization reads from N + 1 to one for each discovery (SC-001). This reduction lowers the Mist calls for the same preview.
- [x] Explained: the threshold is documented for an API token in `documentation/api/admins/POST_register.md`, line 213. The live effect is unverified (U-1 in `research.md`).

## Concurrency

- [x] FR-005 requires one shared read for concurrent checks. The lock in D-4 guards the refresh and the read of the rows.
- [x] A concurrency test asserts one read for five threads (`test_concurrent_site_checks_share_one_read`).

## Change Safety

- [x] The change adds no suppression comment, no `# noqa`, and no `# nosec`. The security gate (bandit) runs in T-LOCAL-GATES.
- [x] The change adds no new input path. The site identifier is validated by the existing route (`IdentifierRequest.require_uuid`).
- [x] The change does not alter the `StreamPickerService` behavior for other callers (FR-012).

## Notes

- Checked on 2026-11-26 against `spec.md` FR-005, FR-006, FR-007, and FR-012, and against the contract files.
- The explained item records residual risk. It does not block the spec.
