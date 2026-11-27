# Analysis: Interactive login request timeout

**Record**: `specs/numbered/0/0/1/2/3/3/0/2/4827-interactive-login-timeout/`
**Scope**: Consistency across `spec.md`, `plan.md`, `tasks.md`, `design/contracts/login-request-timeout.md`, and `design/research.md`. Defects in existing work. Unresolved items.

## 1. Consistency matrix

Each requirement maps to at least one task and at least one test. The test column names existing tests with their remote row and new tests with their task.

| Requirement | Tasks | Test or check | Evidence |
| - | - | - | - |
| FR-001 Orchestrator does not import the removed module | T001 | Existing: `TestImportResolution` | RC-07, RC-08 |
| FR-002 Import test resolves every import without a stub | T002 | Existing: `test_every_imported_module_resolves` | RC-09, RC-10 |
| FR-003 Login transports get the timeout before the first login request | T005, T007, T008, T009 | New: `test_pipeline_bounds_transports_before_first_login`, `test_loopback_stall_raises_read_timeout_within_bound`, `test_orchestrator_receives_configured_request_timeout` | RC-13, RC-14, RC-50 |
| FR-004 Adapter fills a missing timeout and keeps a caller timeout | T004, T008 | New: `test_adapter_fills_missing_timeout`, `test_adapter_keeps_caller_timeout` | RC-61 |
| FR-005 Adapter never retries | T004, T008 | New: `test_adapter_never_retries` | RC-61, RC-62, RC-63 |
| FR-006 Every login transport, including the two-factor replay, carries the adapter | T004, T008 | New: `test_apply_wraps_each_transport_and_keeps_headers`, `test_loopback_stall_raises_read_timeout_within_bound` | RC-55, RC-56 |
| FR-007 Zero or negative timeout fails before a request and names the setting | T004, T008 | New: `test_non_positive_timeout_is_rejected`, `test_authenticate_reports_invalid_timeout_as_value_error` | RC-04 and contract section 5 |
| FR-008 Missing hook fails closed, and the SDK pin test detects drift | T004, T006, T008 | New: `test_missing_transport_hook_fails_closed`, `test_sdk_exposes_transport_hook_and_no_timeout_parameter`, `test_login_paths_call_the_transport_hook` | RC-54, RC-55, RC-56 |
| FR-009 New log lines contain no secret | T004, T008 | New: `test_pipeline_bounds_transports_before_first_login` checks the log text for the password | Contract section 5 (log lines) |
| FR-010 Token path behavior is unchanged | T003 | Existing: `tests/unit/refactors/test_initialize_mist_session.py` | RC-11, RC-12, RC-49 |
| FR-011 Documents describe the timeout and the corrected entry point | T010, T011 | STE gate on the three documents (`design/quickstart.md`, section 5) | RC-22, RC-25, RC-27 |
| FR-012 One changelog fragment with the required name | T012, T-PR | Existing: `tests/guardrails/test_changelog_fragment_policy.py` | RC-28, RC-29, RC-45 |
| FR-013 No new direct child in the interactive package | T-LOCAL-GATES | Existing: `tests/guardrails/test_src_domain_structure.py` | RC-44, RC-46 |
| SC-001 Stalled request fails within 5 seconds | T004, T008 | New: `test_loopback_stall_raises_read_timeout_within_bound` | Contract section 3 |
| SC-002 Every new and changed test passes | T-LOCAL-GATES | Tests gate in `design/quickstart.md` | Not run |
| SC-003 Pylint 9.5 or above and mypy clean for `src/` | T-LOCAL-GATES | Code quality and Types gates | Not run |
| SC-004 SDK pin test passes on 0.64.1 | T006 | New: `test_login_paths_call_the_transport_hook` and the sibling test | RC-54, RC-64 |
| SC-005 Remote checks pass before auto-merge | T-REMOTE-CI, T-MERGE | Remote CI | Not run |
| SC-006 Changelog guard passes | T012 | Existing changelog guard | RC-45 |

Count check: 13 requirements, 6 success criteria, 12 new test functions (9 in T004, 1 in T005, 2 in T006), and 16 tasks. The `non_positive` test has two parameter cases.

## 2. Cross-artifact consistency

The review checked each artifact against the others. It found the following issues and fixed each one in the artifact that held it.

- **X-1, research wording**: The risk line in D-2 named "tests 11 and 12", but `tasks.md` has no numbered tests. Fixed. The line now names task T006.
- **X-2, SDK endpoint parity**: The spec maps SDK endpoint parity to the header test. The task T004 acceptance now states that the prepared request URL does not change. Fixed.
- **X-3, contract message lines**: The contract cites line ranges inside `login_orchestrator.py` (RC-04) and `__api_session.py` (RC-54). The file-level blob rows cover those lines. Fixed by citing ranges, not function names alone.
- **X-4, route rule source**: The plan first cited `.specify/scripts/powershell/spec-route.ps1`, which this review did not verify on `main`. Fixed. The plan cites the rule in `.github/copilot-instructions.md` (RC-70).
- **X-5, MSP export claim**: The spec first claimed that the MSP inventory export also uses the interactive login. The review found no row for that claim. Fixed. The claim is removed.
- **X-6, fake session shape**: The spec, plan, and task T004 all name the same three fakes (lines 295, 309, and 325) and the same replacement shape. Consistent.
- **X-7, test count**: The research, tasks, and checklist describe 12 new tests. The count is consistent across them.

No placeholder remains in any artifact.

## 3. Defects in existing work

Each defect has evidence, an effect, and a disposition.

- **DEF-1, misleading CONTRIBUTING row**: The row for `configure_session_timeout` says "Applies the request timeout policy to the Mist session." The function at `MistHelper.py` line 3357 only logs and changes nothing (RC-17, RC-22). Effect: a maintainer expects a timeout from this entry point. Disposition: fixed by task T010.
- **DEF-2, interactive login has no request timeout**: The SDK sets no request timeout (RC-61), and `MistSessionConfigurator` applies its timeout to the token path only (RC-12, RC-13). Effect: a stalled login can wait without a limit. The documented intent is in `MistHelper.py` line 2518 (RC-16). Disposition: fixed by tasks T004 to T009.
- **DEF-3, import of a removed module**: The orchestrator imported `src.mist.access.auth.session_timeout`, which no tree holds (RC-07, RC-08). Effect: the timeout step failed without an error. Disposition: fixed on `main` by PR #4830 (RC-01). Guarded by the existing import-resolution test (RC-09, RC-10).
- **DEF-4, mistapi pin drift**: `.github/copilot-instructions.md` line 21 states `mistapi>=0.64.0,<0.65` (RC-70). `pyproject.toml` line 29 states `>=0.64.1,<0.65` (RC-32). `requirements.txt` line 129 pins `==0.64.1` (RC-33). `.specify/memory/constitution.md` line 279 states `0.59+` (RC-69). Effect: three documents disagree about the allowed SDK range. Disposition: unresolved item U-4.
- **DEF-5, environment template omits the request variables**: `deploy/.env.example` has no line for `API_REQUEST_TIMEOUT`, `API_REQUEST_MAX_RETRIES`, or `API_REQUEST_RETRY_DELAY` (RC-23). Effect: operators cannot find the variables in the template. Disposition: unresolved item U-1.
- **DEF-6, legacy no-op entry point**: `configure_session_timeout` in `MistHelper.py` (RC-17) is a no-op. Effect: the name suggests a behavior that does not exist. Disposition: unresolved item U-3.
- **DEF-7, duplicate adapter logic**: The token path builds a timeout adapter with admission and retry branches (RC-87). The new interactive adapter repeats the timeout part. Effect: two copies can drift. Disposition: unresolved item U-2.
- **DEF-8, fake sessions cannot model the SDK hook**: The three pipeline tests use `MagicMock(spec=object)` for the session (RC-53). Such a fake has no `_new_session`. Effect: once the orchestrator reads the hook, these tests fail for the wrong reason. Disposition: fixed by task T004, which names the hook in the fake.
- **DEF-9, token session timeout can be lost**: The token timeout sits on the transport that exists at configure time. A later password login replaces that transport (RC-55, RC-56). Effect: the token timeout is lost if such a login happens later. The token path does not start a password login in the code traced so far. Disposition: unresolved item U-5.

## 4. Unresolved items

- **U-1, environment template**: Add the variables `API_REQUEST_TIMEOUT`, `API_REQUEST_MAX_RETRIES`, and `API_REQUEST_RETRY_DELAY` to `deploy/.env.example` after line 29. Reason: open PR #4208 changes that file (RC-86). Owner: a follow-up pull request after PR #4208 merges.
- **U-2, duplicate adapters**: Move one shared timeout adapter builder into `MistSessionConfigurator`, and call it from the token path and the interactive path. Keep each retry policy separate. Reason: open PR #4208 changes the token configurator file (RC-85). Owner: a follow-up pull request after PR #4208 merges.
- **U-3, legacy entry point**: Remove `configure_session_timeout` from `MistHelper.py` and update the public name list in the same change. Reason: the public name list needs a snapshot update, which is out of scope here (RC-18). Owner: a separate issue.
- **U-4, pin drift**: Align the mistapi range in `.github/copilot-instructions.md` (RC-70) and in `.specify/memory/constitution.md` (RC-69) with `pyproject.toml` (RC-32). Reason: documentation outside this change. Owner: a separate documentation issue.
- **U-5, token timeout after a password login**: Trace each password login on a token session. Reason: the trace is outside this change (DEF-9). Owner: a separate issue.
- **U-6, symbol gate and the new import**: The `symbol-diff` gate may list the new `requests.adapters` import as an added name. Reason: the gate has not run. Action: record the added name in the pull request body during T-LOCAL-GATES.
- **U-7, pylint on the nested class**: The `send` override may draw a pylint message. Reason: the gate has not run. Action: check the score during T-LOCAL-GATES. If pylint reports a new message, repair the code and do not suppress the message.

## 5. Coordination with open work

Open pull requests checked by `gh pr list --state open --json number,headRefName,files` (research section 5):

- **PR #4208 (open)**: Changes `src/foundation/support/refactors/initialize_mist_session.py` (RC-85) and `deploy/.env.example` (RC-86). This change edits neither file. Follow-ups U-1 and U-2 wait until PR #4208 merges.
- **PR #4813 (open)**: Changes export and data files. This change shares no file with it.
- **PRs #4886 to #4890 (open)**: Change dependency manifests, a workflow, or the npm frontend. This change shares no file with them.

No open pull request changes `login_orchestrator.py`, the interactive initializer, the changed tests, `README.md`, `documentation/operator-guide.md`, `documentation/CONTRIBUTING-MistHelper.md`, or `changelog.d/`.

## 6. Gate readiness

These checks come from reading the code shapes. None of them ran.

- **Types**: The new code uses `Any` for SDK objects. The `send` override takes `**kwargs: Any` and returns `Any`. This form should satisfy the `requests` stubs in `types-requests`. The check is U-6 and U-7.
- **Lint and format**: Each new line carries an inline comment, as the constitution requires. The Lint and Format gates check line length and style. Both run in T-LOCAL-GATES.
- **Complexity**: Each new function has one to three logical blocks and at most 15 lines, including its signature and docstring.
- **Dead code**: Each new name has at least one caller: `_apply_request_timeout` (called by `_run_login_pipeline`), `_timed_transport_factory` (called by `_apply_request_timeout`), `_mount_timeout_adapters` (called by both), `_build_timeout_adapter` (called by `_mount_timeout_adapters`), and `RequestTimeoutAdapter` (returned by `_build_timeout_adapter`).
- **Docstrings**: Each new function and class carries a docstring.
- **Security**: The change adds no `assert`, no secret, and no suppression comment.
