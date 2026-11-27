# Specification Analysis Report: Report a Mist transport fault as an unavailable Mist API

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/data-model.md`, the two contracts, and the constitution (version 1.9.0).

**Method**: A read-only pass built the requirement inventory, the test map, and the remote evidence map. The pass reviewed the source of the pinned SDK and the current `main` code paths. The findings below record each defect in existing work and each gap in the plan.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| F-01 | Defect | High | `.venv\Lib\site-packages\mistapi\__api_session.py` L575-603 and `mist-ops-platform/src/shared/services/auth.py` L107-135 | A read timeout during the SDK token check drops the token. The `/self` request then has no Authorization header. The service maps the resulting HTTP 401 to an invalid token. | Fixed by D-1 and D-3. Covered by tests N1 and N10. |
| F-02 | Defect | High | `__api_session.py` L605-616 and `auth.py` L116-119 | Mist rejects a token with HTTP 401 during the SDK check. The SDK raises `ValueError` outside its try block. The service maps that error to HTTP 503. | Fixed by D-1 and D-3. Covered by tests N11 and U1. |
| F-03 | Defect | High | `__api_session.py` L141, L360-364, L563-564 | Warning: when `MIST_HOST` and `MIST_APITOKEN` are set, a login can receive the privileges of the environment token. A read timeout on the supplied token leaves the environment token in place. | Fixed by D-1. Covered by tests N6 and N7. |
| F-04 | Defect | Medium | `__api_session.py` L141, L363-364, L605-616 | With `MIST_HOST` set and an invalid `MIST_APITOKEN`, the constructor raises `ValueError`. Every login then answers HTTP 503. | Fixed by D-1. Covered by test N6. |
| F-05 | Defect | Medium | `auth.py` L133-135 | HTTP 429 maps to empty privileges. The login route then reports an invalid token. | Fixed by D-3. Covered by test N3. |
| F-06 | Risk | Medium | `__api_request.py` L277 and `__api_session.py` L575-576 | The privilege lookup request has no timeout. The SDK validation request had `timeout=30`, which a naive change would remove. | Fixed by D-5. Covered by test N12. |
| F-07 | Defect | Low | `__api_response.py` L43, `endpoints.py` L54, and `auth.py` L116 | A transport failure gives status None. `ApiResult.success` then raises `TypeError`, and the broad handler hides the cause. The classification is correct only by accident. | Fixed by D-3 and task T003. Covered by tests N2 and N14. |
| F-08 | Defect | Medium | `mist-ops-platform/src/shared/mist/endpoints.py` L312-316 | `_extract_list` drops a dict body. The identity object never reaches the service. This is the defect that issue #4749 reports. | Fixed by D-2. Covered by tests N13 and N15. Shared with #4749 (D-8). |
| F-09 | Test gap | Medium | `mist-ops-platform/tests/unit/api/test_auth.py` L213-267 and `test_session_security.py` L338, L369 | The tests patch the SDK class and the endpoint service. The real SDK token path never runs. F-01 and F-02 passed review for that reason. | Fixed by tasks T005 and T010. Tests N10 and N11 run the real SDK path. |
| F-10 | Debt | Low | `auth.py` L34-68 | `auth.py` holds 7 top-level names, and `AuthService` holds 9 methods, before the change. | Recorded in D-10 and in the plan Complexity Tracking. Remediation R-A. |
| F-11 | Risk | Low | `auth.py` L99-100 | `validate_token` writes a cache entry for empty privileges. A caller that passed a Redis client would cache a rejection for 300 seconds. The login route and the middleware build `AuthService` without a Redis client (local read, open item U-5). | Accepted. Recorded for a later change. |
| F-12 | Scope | Medium | `mist-ops-platform/src/shared/mist/session.py` L51-53 | The worker session factory uses the same SDK constructor pattern. It is outside the login path. | Out of scope (D-9). A separate issue must track it (open item U-3). |
| F-13 | Documentation | Low | `mist-ops-platform/.env.example` L5 | The example names `MIST_API_TOKEN`. The SDK reads `MIST_APITOKEN` and `MIST_HOST`. | Out of scope. Recorded in research R1. |
| F-14 | Defect | Low | `mist-ops-platform/docs/operations.md` L112 | The section title "Intermittent 401" can suggest that a session loss gives a 401. The text was not read in full. | Task T013 reads the section and changes it only when it attributes a timeout to an invalid token. |

## Test Mapping

Each planned test has one identifier. The tasks and the plan use these identifiers.

| ID | Test function | File | Kind | Requirements |
|----|---------------|------|------|--------------|
| N1 | `test_fetch_self_read_timeout_reports_unavailable` | `tests/unit/api/test_auth.py` | New | FR-001, FR-011 |
| N2 | `test_fetch_self_connection_error_reports_unavailable` | `tests/unit/api/test_auth.py` | New | FR-001, FR-002 |
| N3 | `test_fetch_self_http_429_reports_unavailable` | `tests/unit/api/test_auth.py` | New | FR-003 |
| N4 | `test_fetch_self_success_without_identity_reports_unavailable` | `tests/unit/api/test_auth.py` | New | FR-005 |
| N5 | `test_fetch_self_identity_object_returns_privileges` | `tests/unit/api/test_auth.py` | New | FR-007 |
| N6 | `test_validation_session_ignores_process_environment` | `tests/unit/api/test_auth.py` | New | FR-008 |
| N7 | `test_validation_session_sends_only_supplied_token_to_self_endpoint` | `tests/unit/api/test_auth.py` | New | FR-009, FR-013 |
| N8 | `test_malformed_token_makes_no_request` | `tests/unit/api/test_auth.py` | New | FR-010 |
| N9 | `test_log_records_never_contain_token` | `tests/unit/api/test_auth.py` | New | FR-012 |
| N10 | `test_sdk_read_timeout_drops_token_contract` | `tests/unit/api/test_auth.py` | New, SDK contract | Failure proof for F-01 |
| N11 | `test_sdk_rejected_token_raises_value_error_contract` | `tests/unit/api/test_auth.py` | New, SDK contract | Failure proof for F-02 |
| N12 | `test_validation_session_bounds_request_with_timeout` | `tests/unit/api/test_auth.py` | New | FR-011 |
| N13 | `test_self_identity_object_shape_returns_one_row` | `tests/unit/mist/test_list_status.py` | New | FR-014 |
| N14 | `test_none_status_result_is_not_success` | `tests/unit/mist/test_list_status.py` | New | FR-015 |
| N15 | `test_object_shape_error_body_never_becomes_row` | `tests/unit/mist/test_list_status.py` | New | FR-014 |
| U1 | `test_fetch_self_returns_empty_privileges_on_401` (add a 403 case) | `tests/unit/api/test_auth.py` | Updated | FR-006 |
| U2 | `test_fetch_self_raises_unavailable_on_503` | `tests/unit/api/test_auth.py` | Updated | FR-004 |
| U3 | `test_fetch_self_direct_service_reports_503` | `tests/unit/api/test_auth.py` | Updated | FR-004 |
| U4 | The test at `test_session_security.py` L338 | `tests/unit/api/test_session_security.py` | Updated patch target | FR-016 |
| U5 | The test at `test_session_security.py` L369 | `tests/unit/api/test_session_security.py` | Updated patch target | FR-004, FR-016 |

Totals: 15 new test functions and 5 updated test functions, which makes 20 planned test functions.

## Coverage Summary

| Requirement | Has task | Task IDs | Tests | Notes |
|-------------|----------|----------|-------|-------|
| FR-001 | Yes | T005, T008 | N1 | Transport fault maps to unavailable. |
| FR-002 | Yes | T008 | N2, N14 | No status code maps to unavailable. |
| FR-003 | Yes | T008 | N3 | HTTP 429 maps to unavailable. |
| FR-004 | Yes | T008, T010 | U2, U3, U5 | HTTP 1xx, 3xx, and 5xx map to unavailable. |
| FR-005 | Yes | T008 | N4 | A 2xx response without identity maps to unavailable. |
| FR-006 | Yes | T008, T010 | U1 | HTTP 401 and other 4xx map to empty privileges. |
| FR-007 | Yes | T008 | N5 | A 2xx response with identity parses as before. |
| FR-008 | Yes | T006 | N6 | The validation session ignores the process environment. |
| FR-009 | Yes | T006 | N7 | Requests go only to `api.mist.com` with the supplied token. |
| FR-010 | Yes | T007 | N8 | A malformed token makes no request. |
| FR-011 | Yes | T006 | N1, N12 | Each request ends within 30 seconds. |
| FR-012 | Yes | T009 | N9 | Logs and results never contain the token. |
| FR-013 | Yes | T006, T012 | N7 | The lookup uses `getSelf` through the registry. |
| FR-014 | Yes | T003, T004 | N13, N15 | The single-object shape returns one row. |
| FR-015 | Yes | T004 | N14 | A None status is not a success. |
| FR-016 | Yes | T010, T011, T012, T013, T014 | U4, U5 | Login and middleware mapping stays unchanged. |
| FR-017 | Yes | T005 | All new tests | Mocked HTTP only. Reviewed in the security checklist. |

SC-006 is a record consistency check, not a code requirement. Authoring self-review confirms it, so no task lists it.

## Constitution Alignment

- Five-Item Rule: Fail, recorded debt (F-10). Remediation R-A is in the plan.
- Class-Based Architecture: Pass. No wrapper function is added.
- Safety-First: Pass. The shape check runs before the request. The log text omits the secret.
- Full Deployment Pipeline: Pass, planned. Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in order.
- Observability and Logging: Pass. The log text is ASCII only.
- Inline Comments and Action Logging: Pass, planned. Tasks T005 to T009 require both.
- Mistapi only: Pass. The lookup calls `getSelf` through the registry.
- Testing: Pass. Mocks only (FR-017).

## Unmapped Tasks

- T001, T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE are process gates. They map to no functional requirement. Each one names a verification command from the local gates table.

## Metrics

- Requirements: 17 (FR-001 to FR-017).
- Success criteria: 7 (SC-001 to SC-007).
- Tasks: 18 (T001 to T014 and four final tasks).
- Tests: 15 new and 5 updated, which makes 20 planned test functions.
- Decisions: 11 (D-1 to D-11). Human decisions: 0.
- Remote checks: 80 (56 for `main` and 24 local SDK rows).
- Findings: 14 (F-01 to F-14). High: 3. Medium: 6. Low: 5.

## Resolution Status

- All High findings have a fix and a test.
- All Medium defects have a fix, except F-12, which is out of scope with an open item.
- F-07 (Low) has a fix in the status classification and a test.
- Findings F-10, F-11, and F-13 are recorded with reasons.

## Unresolved Items

- U-1: The held analyzer finding names missing constructor connection-error coverage in `test_auth.py`. The constructor makes no request in this design. Test N2 covers the connection error on the `/self` request instead. The reviewer must confirm that this satisfies the finding.
- U-2: The issue #4749 owner must confirm that the single-object shape resolves the `/self` part of #4749.
- U-3: A separate issue must track the worker session path in `session.py` (F-12) and the split of `auth.py` (remediation R-A). This record does not file either issue.
- U-4: A separate issue must track the HTTP 429 retry delay across the two retry layers (Caution in the plan).
- U-5: The login route and the middleware build `AuthService` without a Redis client. Only a local read supports this statement. The remote lines were not decoded.
- U-6: Whether a deployment sets `MIST_HOST` and `MIST_APITOKEN` (F-03 and F-04 conditions). The example file does not name them.
- U-7: The `symbol-diff` tool may report each added name as a change. T-LOCAL-GATES must read the tool output and explain each added name in the pull request.
- U-8: The test-quality analyzer may not scan `mist-ops-platform/tests`. T-LOCAL-GATES must confirm the scope.
- U-9: The root Black configuration may not cover `mist-ops-platform`. T-LOCAL-GATES must confirm the scope.
- U-10: The `docs/operations.md` section at L112 may describe a timeout as an invalid token. Task T013 decides whether the text changes.
