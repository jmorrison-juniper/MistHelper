# Implementation Plan: Report a Mist transport fault as an unavailable Mist API

**Branch**: `fix/4748-mist-token-timeout-unavailable` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification at `specs/numbered/0/0/1/2/2/4/4/3/4748-mist-token-timeout-unavailable/spec.md`. The route is the base-5 encoding of 4748. Research R14 shows the derivation.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Issue #4748 shows that a Mist transport fault during login can be reported as an invalid token. The SDK token check drops a read timeout, and the privilege lookup then runs without credentials. The repair has five parts. It adds a validation session that ignores the process environment. It reads the identity object through the registry with a single-object shape. It maps each HTTP result and each transport fault to one outcome. It bounds each request with a 30-second timeout. It adds no module and no dependency.

## Technical Context

**Language/Version**: Python 3.15. The ops platform sets `requires-python = ">=3.15"` (`mist-ops-platform/pyproject.toml` L13). CI sets `PYTHON_VERSION` to `'3.15'` (`.github/workflows/ci.yml` L77).

**Primary Dependencies**: `mistapi==0.64.1` (`mist-ops-platform/requirements.txt` L99). The SDK requires `requests>=2.32.3` (installed METADATA L23). `anyio` runs the blocking lookup in a worker thread (`mist-ops-platform/src/api/routes/health.py` L236).

**Storage**: None for this change. The login route builds `AuthService` without a Redis client, so the Redis privilege cache stays off on that path.

**Testing**: pytest in `mist-ops-platform/`. The pyproject sets `testpaths = ["tests"]` and `asyncio_mode = "auto"` (L124-125). CI passes `--timeout=120` to pytest (`ci.yml` L1188).

**Target Platform**: Linux container for the ops platform. The code also runs on Windows 11 for local work, as `AGENTS.md` requires for each code path.

**Project Type**: Web service. The login route and middleware live under `mist-ops-platform/src/api/`.

**Performance Goals**: Each privilege lookup request ends within 30 seconds (FR-011). A throttled lookup adds the SDK retry delay (Caution in Risks).

**Constraints**: Mist REST calls use mistapi methods only. New functions keep the five-item limits. Each existing violation that the change touches is recorded in Complexity Tracking.

**Scale/Scope**: Two source modules (`auth.py`, `endpoints.py`), one registry module (`types.py`), three test modules, and one changelog fragment.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Fail, recorded debt | `auth.py` holds 7 top-level names and `AuthService` holds 9 methods before the change. The change adds one module-level class and three methods. Complexity Tracking records each item with remediation R-A. |
| II. Class-Based Architecture | Pass | New behavior lives in `TokenValidationSession` and `AuthService` methods. The change adds no wrapper function. |
| III. Safety-First | Pass | The token shape check runs before any request (FR-010). No `input()` call is added. The log text omits every secret. |
| IV. Full Deployment Pipeline | Pass, planned | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in order. |
| V. Observability and Logging | Pass | New log text uses ASCII only. Structured logs are not required, because the change adds no service and no module. |
| VI. Inline Comments | Pass, planned | Each new executable line receives an inline comment. Tasks T005 to T008 require it. |
| VII. Action Logging | Pass, planned | Each privilege lookup logs before the request and after the result. Each exception logs its type and status. |
| Mistapi only for Mist REST | Pass | The lookup calls `getSelf` through the registry (FR-013). |
| Owned WebSocket transport | Not applicable: the feature owns no WebSocket transport. |
| Package manager and dependencies | Not applicable: no dependency changes. |
| Container runtime and test containers | Not applicable: this record starts no container. |
| File paths | Not applicable: the change handles no file path. |
| Output backends and export boundary | Not applicable: the change exports no data. |
| Operational store and database keys | Not applicable: the change adds no table and no key. |
| Data directory and container security | Not applicable: the change writes no product output. |
| Zscaler and proxy | Not applicable: the change builds no image and pushes no image. |
| Testing | Pass | 15 new and 5 updated test functions use mocked HTTP only (FR-017). |
| Security findings | Pass | The plan adds no suppression comment. The bandit gate runs in T-LOCAL-GATES. |
| Complexity-driven escalation | Pass | The change touches more than three files, so this specification is required. |
| Multi-agent git workflow | Pass | The issue carries the `in-progress` label. The branch starts from `main`. No open pull request touches the same files (research R13). |

Mist Cloud gate:

- Every REST request uses a working mistapi method. Pass: `getSelf` sends the request.
- An owned WebSocket transport is not proposed. Not applicable.
- Contract tests prove that the SDK path is insufficient. Pass: `test_sdk_read_timeout_drops_token_contract` and `test_sdk_rejected_token_raises_value_error_contract`.
- The owned transport preserves SDK authentication. Not applicable: no owned transport exists.
- Tests cover output, failure handling, safety, and secret redaction. Pass: tests N1 to N12 cover these areas.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/4/4/3/4748-mist-token-timeout-unavailable/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      login-status.md
      validation-service.md
    checklists/
      requirements.md
      security.md
```

The route folder `specs/numbered/0/0/1/2/2/4/4/3/` does not exist on `main` (research RC-56). The new record adds one direct child to that folder. The folder holds five children at most.

### Source change map

| Action | Exact path | Change |
| - | - | - |
| Modify | `mist-ops-platform/src/shared/services/auth.py` | Add class `TokenValidationSession` with nested `_BoundedTimeoutAdapter`. Add static method `_is_valid_token_shape`. Add methods `_request_identity` and `_identity_from_result`. Change `_fetch_self` and `_handle_self_failure`. Import `HTTP_TOO_MANY_REQUESTS`. |
| Modify | `mist-ops-platform/src/shared/mist/types.py` | Add field `single_object: bool = False` to `MistEndpoint`. Set `single_object=True` on the `self_identity` entry. |
| Modify | `mist-ops-platform/src/shared/mist/endpoints.py` | Return False from `ApiResult.success` when the status is None. Add a single-object branch in `list_all_entities`. Add static method `_single_object_rows`. |
| Modify | `mist-ops-platform/tests/unit/api/test_auth.py` | Update 3 tests. Add 12 tests. |
| Modify | `mist-ops-platform/tests/unit/api/test_session_security.py` | Update the patch targets of 2 tests (L338 and L369). |
| Modify | `mist-ops-platform/tests/unit/mist/test_list_status.py` | Add 3 tests. |
| Modify when needed | `mist-ops-platform/docs/operations.md` | Change the text of the section at L112 only when it attributes a timeout to an invalid token. |
| Add | `changelog.d/issue-4748-mist-token-timeout-unavailable.md` | One `Fixed` bullet that names issue 4748. The fragment is a required unique process record. |

Unchanged, verified by a test run: `mist-ops-platform/src/api/routes/health.py`, `mist-ops-platform/src/api/middleware/auth.py`, `mist-ops-platform/src/shared/mist/session.py`, `mist-ops-platform/tests/unit/mist/test_consumer_registry_usage.py`, `mist-ops-platform/tests/unit/api/test_health.py`, the requirements files, the pyproject files, and `.github/workflows/ci.yml`.

### Implementation outline

1. Add the single-object flag and the `None` status check (`types.py`, `endpoints.py`). Tests N13 to N15 go first.
2. Add `TokenValidationSession`, the token shape check, and the timeout adapter (`auth.py`). Tests N6 to N12 go first.
3. Change the classification in `_fetch_self` and `_handle_self_failure` (`auth.py`). Tests N1 to N5 and U1 to U3 go first.
4. Update the patch targets in `test_session_security.py`. Run the unchanged tests.
5. Add the changelog fragment and check the docs section at L112.

## Dependencies and Ownership

- Pinned dependency: `mistapi==0.64.1`. A version change requires a new specification.
- Shared files with issue #4749: `auth.py`, `endpoints.py`, `types.py`, `test_auth.py`, and `test_list_status.py`. One pull request owns all of them (decision D-8).
- No open pull request touches these files (research R13).

## Risks and Mitigations

- Caution: The validation session overrides the private method `_load_env` of mistapi. A mistapi upgrade can rename it. Test N6 fails when the override stops working. The pin stays at 0.64.1.
- Caution: The timeout adapter mounts on the private attribute `_session` of the SDK object. Test N12 proves that the timeout reaches `HTTPAdapter.send`.
- Caution: The SDK retries HTTP 429 in two layers. A throttled login waits longer. The delay is out of scope, and a separate issue tracks it (open item U-4).
- Warning: A login with a supplied token can receive the privileges of the environment token when both `MIST_HOST` and `MIST_APITOKEN` are set (research R1, F-03). The repair removes this path. Until the repair merges, do not set both variables on a login server.
- Caution: The #4749 owner must confirm that the single-object shape meets the #4749 acceptance criteria (open item U-2). List entities keep their current behavior, so other callers are not affected.

## Complexity Tracking

Each row records an existing violation that the change touches or extends.

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `auth.py` holds 7 top-level names. The change adds `TokenValidationSession`, which makes 8. | The validation session must subclass the SDK class at module level. The tests patch it by module path. | A nested class would add members to `AuthService`, which already exceeds the method limit. |
| `AuthService` holds 9 methods. The change adds 3, which makes 12. | Helper methods keep `_fetch_self` within 25 lines and keep each block within five logical blocks. | One long method breaks the 25-line limit in the constitution. |
| `MistEndpointService` gains the static method `_single_object_rows`. | The single-object branch stays out of `list_all_entities`, which keeps its block count within the limit. | An inline branch raises the block count above five. |

Remediation action R-A: Split `auth.py` into a service module and a validation module after `mist-ops-platform/src/shared/services/` holds five children. A separate issue tracks this action. The issue is not yet filed (open item U-3 lists the related filing).

## Rollback Steps

1. Revert the merged squash commit on a new branch from `main`, and open a new pull request. Do not force-push `main`.
2. The previous classification returns. Transport faults again report an invalid token. This result is a known defect.
3. No data migration exists. The cache key format is unchanged, so no cache cleanup is needed.
