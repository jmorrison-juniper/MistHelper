# Security Requirements Checklist: Guest authorization workflows

**Purpose**: Check the security and privacy requirements in the spec, the plan, and the contracts.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Access and Identity

- [x] Reads require a trusted identity. Reason: FR-004 and D-4. The check is in the contract `portal.md` Section 1.
- [x] The identity header counts only from a trusted proxy peer. Reason: the rule in `web_portal/services/config.py` line 9 (R054). Test: TEST-004.
- [x] The allowlist remains the first network control. Reason: `PORTAL_ALLOWED_IPS` defaults to empty (R055).
- [x] Without a configured proxy, the feature stays disabled. Reason: D-4 risk statement.
- [x] Organization scope stays excluded. Reason: FR-029 and D-5.

## Write Safety

- [x] Each write needs its exact typed word. Reason: FR-005 and D-12. Test: TEST-003.
- [x] Each write needs a matching review digest. Reason: FR-022 and D-12. Test: TEST-022.
- [x] Each write runs one Mist call. Reason: FR-016 and D-15. Test: TEST-013.
- [x] No write retries automatically. Reason: FR-016. Test: TEST-013.
- [x] No delete call exists in the feature. Reason: FR-013. Test: TEST-008.
- [x] Read-only fields never reach a request body. Reason: FR-010 and D-7. Test: TEST-006.
- [x] Revocation reports ended access only after a read-back. Reason: FR-012 and D-10. Test: TEST-012.
- [x] The SDK retry count is known and counted. Reason: R109 and R110. Test: TEST-014.

Warning: the SDK retries HTTP 429 for each PUT and POST. A write can run more than once inside the SDK. The client counts each call. Review the call count before enabling writes.

## Data Exposure and Logging

- [x] Logs hold masked MAC addresses only. Reason: FR-025 and D-17. Test: TEST-028.
- [x] Responses hold masked MAC addresses only. Reason: FR-025 and the response envelope in `portal.md`.
- [x] Logs hold no name, email address, field value, token, or password. Reason: FR-025 and D-17. Test: TEST-028.
- [x] The audit table holds no full MAC address. Reason: `audit.md` Section 7.
- [x] Logs use ASCII text. Reason: constitution Principle V.
- [x] Errors give categories, not raw Mist messages. Reason: `portal.md` Section 2.

## Audit and Recovery

- [x] Each write has an intent row before the call. Reason: FR-017 and FR-018. Test: TEST-015.
- [x] An intent failure stops the write. Reason: FR-018. Test: TEST-015.
- [x] An outcome failure is reported as an audit failure. Reason: FR-019. Test: TEST-016.
- [x] The audit table is never deleted by the feature. Reason: `audit.md` Section 5. Test: TEST-017.
- [x] Open intents block a new write to the same masked target. Reason: D-16. Test: TEST-018.

## Input Validation

- [x] CSV size checks run before parsing. Reason: FR-020. Test: TEST-019.
- [x] CSV headers must match exactly. Reason: `csv-import.md` Section 2. Test: TEST-020.
- [x] Names never select a target. Reason: FR-003 and FR-021. Test: TEST-021.
- [x] Duplicate targets reject. Reason: `csv-import.md` Section 3. Test: TEST-021.
- [x] Formula text keeps its text and receives no escape in this feature. Reason: the feature exports no file.

## Residual Risk

- [x] The access model stays open until D-4 passes. Reason: HUMAN-DECISION-REQUIRED in `research.md` D-4.
- [x] The proxy trust depends on deployment configuration. Reason: U17 in `research.md`.
