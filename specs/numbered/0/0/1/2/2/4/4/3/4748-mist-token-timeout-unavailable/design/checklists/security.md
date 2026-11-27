# Security Requirements Quality Checklist: Report a Mist transport fault as an unavailable Mist API

**Purpose**: Validate that the security requirements of the credential path are complete, clear, and testable

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Credential Handling

- [x] The token never reaches a log record (FR-012). Test: `test_log_records_never_contain_token`.
- [x] The token never reaches an exception message or a result (FR-012).
- [x] The process environment never supplies a token or a host to a login (FR-008). Test: `test_validation_session_ignores_process_environment`.
- [x] A malformed token makes no request (FR-010). Test: `test_malformed_token_makes_no_request`.
- [x] Each fake value in a test is clearly fake (FR-017).

## Transport

- [x] Each request goes only to `https://api.mist.com/api/v1/self` (FR-009). Test: `test_validation_session_sends_only_supplied_token_to_self_endpoint`.
- [x] Each request ends within 30 seconds (FR-011). Test: `test_validation_session_bounds_request_with_timeout`.
- [x] No direct HTTP call is added. The lookup uses the mistapi method `getSelf` (FR-013).
- [x] The SDK path that drops a token is proven unsafe by a contract test. Tests: `test_sdk_read_timeout_drops_token_contract` and `test_sdk_rejected_token_raises_value_error_contract`.

## Failure Safety

- [x] A transport fault never becomes an invalid token (FR-001). Tests: `test_fetch_self_read_timeout_reports_unavailable` and `test_fetch_self_connection_error_reports_unavailable`.
- [x] A rejected token never becomes an unavailable Mist API (FR-006). Test: `test_fetch_self_returns_empty_privileges_on_401`.
- [x] A login never reports the privileges of another token (FR-008 and FR-009).

## Data Exposure

- [x] Error results carry no response body (FR-012).
- [x] Logs carry the exception class name and the HTTP status code only (Decision D-6).

## Notes

- Caution: the validation session depends on the private method `_load_env` of mistapi 0.64.1. The plan records the risk, and test N6 detects a change.
- Caution: the timeout adapter depends on the private attribute `_session` of the SDK object. Test N12 detects a change.
- Each item was checked against `spec.md` and `plan.md` on 2026-11-26. No item is unchecked.
