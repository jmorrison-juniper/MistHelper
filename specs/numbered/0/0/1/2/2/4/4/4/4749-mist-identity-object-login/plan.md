# Implementation Plan: Mist Identity Object Sign-In

**Branch**: `fix/4749-mist-identity-object-login` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/2/4/4/4/4749-mist-identity-object-login/spec.md`. The eight route digits are the base-5 form of 4749, padded to eight places (research row R58 and the arithmetic in research.md).

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

The change restores the identity object of `GET /api/v1/self` for sign-in. It adds one registry flag, one object read path, and one active-token check. The check runs only after a successful `/self` response. The change edits three existing source files and adds two contract test modules and one changelog fragment.

The issue shows that the identity object is discarded by the list layer. The same layer keeps a Mist error body out of the data. The change keeps that second rule. It adds the flag only to the registry entry `self_identity`.

## Technical Context

**Language/Version**: Python, the interpreter of the `mist-ops-platform` service.

**Primary Dependencies**: mistapi 0.64.1 is installed (research row R87). The brief pins `mistapi>=0.64.0,<0.65`. No dependency changes.

**Storage**: None. The change adds no table, file, or cache key.

**Testing**: pytest with `unittest.mock`, run from the `mist-ops-platform` directory. No network. No live Mist call.

**Target Platform**: The `mist-ops-platform` service and its local test run.

**Project Type**: Bug fix in one existing backend service.

**Performance Goals**: One Mist call for each validation. The change adds no call.

**Constraints**: Five-item rule (research row R50). Functions at most 25 lines and five parameters. Inline comments and action logging (research rows R55 and R56).

**Scale/Scope**: Three edited source files. Two new test modules with 13 tests. One changelog fragment.

## Constitution Check

*Gate: passes before research and after design. Each row names the research row that holds the constitution text.*

| Principle | Result | Evidence |
|-----------|--------|----------|
| I. Five-item rule (R50) | Pass | The change edits existing modules and adds no direct child to `src/shared/mist` (five children, R26) or `src/shared/services` (seven children, R27). The new tests enter `tests/contract`, which grows from two children to four (R25). |
| II. Class-based architecture (R51) | Pass | The new methods belong to `MistEndpointService` and `AuthService`. The change adds no wrapper function. |
| III. Safety first (R52) | Pass | The token check fails closed. The change has no destructive action and no keyboard input. FR-010 keeps token values out of logs. |
| IV. Full deployment pipeline (R53) | Pass with tasks | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the pipeline steps. |
| V. Observability (R54) | Pass | New log text is ASCII. No new log line holds a token or an identity body. |
| VI. Inline comments (R55) | Pass when T011 completes | Each changed line gets an inline comment. |
| VII. Action logging (R56) | Pass when T011 completes | The object read and the token check each log an info line before and a debug line after. |
| mistapi-only (R57) | Pass | The change calls `getSelf` through the registry. It adds no direct HTTP request. The constitution bullet states mistapi 0.59 or later, and the brief pin is 0.64.x. analysis.md records that drift. |

For repository structure and generated files:

- The commit subject uses the Conventional Commit form in Principle IV (R53).
- The change adds one fragment to `changelog.d/`, a process folder with 335 tracked children (R28). Principle I allows unique process records there. Existing debt is listed in the complexity tracking table.
- The change writes no product output. The tests write under pytest temporary paths.
- The change uses no `test-artifacts/` folder.

For a feature that uses Juniper Mist Cloud:

- REST method: `mistapi.api.v1.self.self.getSelf` (research row R80), called through `MistEndpointService`.
- No owned WebSocket transport. The constitution exception does not apply.
- Contract tests: TC-01 to TC-07 for the object path and TG-01 to TG-06 for the token check.
- SDK authentication: the pinned attributes `_apitoken` and `_apitoken_index` (research row R31).
- Output, failure, safety, and redaction: tests TC-01 to TC-07 and TG-01 to TG-06, plus FR-010.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/4/4/4/4749-mist-identity-object-login/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
    checklists/
```

### Source Code (repository root)

| Path | Action | Requirements | Change |
|------|--------|--------------|--------|
| `mist-ops-platform/src/shared/mist/types.py` | Modify | FR-004, FR-011 | Add the field `object_response` after `list_method` (line 21). Set it to true on `self_identity` (line 188). |
| `mist-ops-platform/src/shared/mist/endpoints.py` | Modify | FR-001 to FR-005, FR-009, FR-010 | Add the object branch in `list_all_entities` (line 127), the method `_read_object`, and the static method `_extract_object` beside `_extract_list` (line 309). |
| `mist-ops-platform/src/shared/services/auth.py` | Modify (reserved file) | FR-006 to FR-008 | Add `_identity_from_success` and `_active_token_is_supplied`. Call `_identity_from_success` after the success check (line 120). |
| `mist-ops-platform/tests/contract/test_self_identity_response_contract.py` | Add | FR-001 to FR-005 | Cases TC-01 to TC-07. |
| `mist-ops-platform/tests/contract/test_validation_token_guard.py` | Add | FR-006 to FR-008 | Cases TG-01 to TG-06. |
| `changelog.d/issue-4749-mist-identity-object-login.md` | Add | FR-012 | One heading and one Fixed bullet. |

`auth.py` is reserved for the local repair of issue #4748. Issue comment IC_kwDOQltU8c8AAAABk_UEwg records the reservation. Task T001 checks the release before any edit.

## Structure Decision

The change extends two existing classes and one registry entry. It adds no module to a noncompliant folder.

New tests go into `mist-ops-platform/tests/contract/`. The folders `tests/unit/mist` (17 tracked children, R29) and `tests/unit/api` (11 tracked children, R30) are above five children. The change adds no file to either folder. Placing the tests in a folder for another subject was rejected.

No existing test module changes. The four modules that cover the changed path are `tests/unit/mist/test_list_status.py`, `tests/unit/mist/test_consumer_registry_usage.py`, `tests/unit/api/test_auth.py`, and `tests/unit/api/test_session_security.py`. They pass as written (research rows R19 to R23).

## Complexity Tracking

Existing debt that the change touches or avoids. None of this debt is new.

| Item | Kind | Why it stays | Remediation |
|------|------|--------------|-------------|
| `mist-ops-platform/src/shared/services` holds seven tracked children (R27) | Grandfathered | The change edits `auth.py` and adds no child. | A separate issue splits the folder to five children or fewer. |
| `mist-ops-platform/src/shared/mist` holds five tracked children (R26) | At limit | The change edits two modules and adds no child. | Future modules go into a nested package. |
| `mist-ops-platform/tests/unit/mist` holds 17 tracked children (R29) and `tests/unit/api` holds 11 (R30) | Grandfathered | The change adds no file to either folder. | A separate issue splits both folders. |
| `changelog.d` holds 335 tracked children (R28) | Process folder exception | The change adds one unique fragment, which Principle I allows. | The release coordinator moves fragments into `CHANGELOG.md`. |
| The constitution bullet states mistapi 0.59 or later (R57) | Documentation drift | The code uses 0.64.1 (R87). | A separate documentation issue aligns the bullet with the brief pin. |

New design that needs a reason.

| Item | Why it is needed | Simpler alternative rejected because |
|------|------------------|--------------------------------------|
| Registry flag `object_response` | Marks the one endpoint that returns an object. | A global dictionary wrap restores the defect that issue #1884 fixed (research rows R01 and R19). |
| Token check after the success check | Fails closed without changing the 4xx and 5xx paths. | A check before the SDK call breaks the call assertions in the existing 4xx and 5xx tests (research row R23). |
| New tests in `tests/contract` | Keeps the change in a compliant folder and avoids reserved modules. | Editing `test_list_status.py` or `test_auth.py` needs the owner release for the reserved test files. |

## Dependencies and Sequencing

1. Issue #4748 owns the local repair of `auth.py` (issue comment IC_kwDOQltU8c8AAAABk_UEwg). If that repair lands first, rebase this branch onto `main` before T009.
2. This pull request ships the endpoint change and the token check together. Decision D-5 explains the order.
3. Tests T005 and T006 run first and fail before T007 to T009.

## Risks and Mitigations

- **Reserved `auth.py`**: T001 checks the release and the unchanged blob before the first edit.
- **Rebase conflict in `_fetch_self`**: Sequence after issue #4748 when its repair lands.
- **Residual environment-token call**: The SDK validates an environment token during construction when both `MIST_HOST` and `MIST_APITOKEN` are set. The check discards that identity. A follow-up issue owns the isolation.
- **Test count below the gate**: T002 records the baseline. The change adds 13 tests.
- **Security wording in a shared record**: The record names the code path at source level. It gives no operating steps. Review the security checklist before the record is committed.

## Rollback Steps

1. Revert the squash commit of the pull request on `main`.
2. Run the Ops platform gate. It must pass after the revert.
3. Confirm that sign-in returns to the prior behavior: empty privileges and HTTP 401.

Caution: a revert restores the defect. Valid operators then see "Invalid API token" at sign-in again. No data, configuration, or schema change needs reversal.
