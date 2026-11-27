# Security Requirements Quality Checklist: Reviewed Restore and Partial-Operation Recovery

**Purpose**: Check that the security and privacy requirements are complete and testable.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Credential and Secret Handling

- [x] CHK001 Backup bodies stay in the private store. Responses and logs exclude them. Covered by FR-023, decision D-24, and test E15.
- [x] CHK002 No credential, token, or session value enters a log, a response, or a record. Covered by the logging rules in `design/contracts/restore-mist.md` and by test E15.
- [x] CHK003 The public view of a backup manifest removes the `objects` mapping. Covered by decision D-27 and the manifest rules in `design/data-model.md`.
- [x] CHK004 Each error response uses the safe shape with a correlation ID and no secret. Covered by `design/contracts/restore-api.md`, section Error shape.

## Authorization and Confirmation

- [x] CHK005 A write-capable approval is refused while the operator identity is unverified. Covered by FR-011, decision D-14, and test E3.
- [x] CHK006 Each approval needs a scope confirmation, and each execution needs the exact typed word `CONFIRM`. Covered by FR-010, decision D-7, and tests E4 and E5.
- [x] CHK007 The administrative gate returns not found while closed. Covered by FR-025, decision D-22, and test E7.
- [x] CHK008 Deletion during recovery needs owner permission and the deletion path of issue 4645. Covered by FR-021, decision D-20, and test R4.
- [x] CHK009 Each recovery action needs a new approval and a new recovery backup. Covered by FR-020 and test R6.

## Request Protection

- [x] CHK010 Each `POST` needs the converter CSRF token. Covered by `design/contracts/restore-api.md`, section Route. Task T014 adds the CSRF failure test.
- [x] CHK011 Each response uses `Cache-Control: no-store`. Covered by `design/contracts/restore-api.md`, section Route, and by task T014.
- [x] CHK012 Each operation identifier matches 32 lowercase hexadecimal characters before any path is built. Covered by `design/data-model.md`, Persistence keys.

## Data Exposure and Testing

- [x] CHK013 No test makes a live Mist call or uses a production credential. Covered by SC-006 and the fake gateway in task T004.
- [x] CHK014 The tests use synthetic backup bodies. Covered by task T004 and by the acceptance of tests E15 and D14.

## Notes

- Items CHK010 and CHK011 depend on the acceptance text of task T014. The text now names the CSRF test.
