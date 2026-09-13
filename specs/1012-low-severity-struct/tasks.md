# Tasks: Clear the Last Two Low-Severity STRUCT Violations

**Spec**: `specs/1012-low-severity-struct/spec.md`
**Issue**: #1012

## Phase 1: Baseline

- [X] T001 Record the analyzer score, grade, and violation counts before the change.

## Phase 2: `_preflight_verify_credentials`

- [X] T002 Extract the problem-collection branches into `_collect_credential_problems`.
- [X] T003 Extract the failure reporting and exit into `_report_credential_failure`.
- [X] T004 Reduce the caller to preflight logging plus the two helper calls.

## Phase 3: `_establish_mist_session`

- [X] T005 Extract the systematic-test org check into `_preflight_systematic_test_org`.
- [X] T006 Extract the interactive login branch into `_init_interactive_session`.
- [X] T007 Extract the token branch into `_init_token_session`.

## Phase 4: Verification

- [X] T008 Confirm the analyzer reports 0 Low-severity violations for `MistHelper.py`.
- [X] T009 Confirm the compliance score rose above the baseline.
- [X] T010 Run ruff and black across the repository.
- [X] T011 Run mypy over the gate paths.
- [X] T012 Run radon over the gate paths and confirm no block above CC 10.
- [X] T013 Run the credential preflight and session unit tests.
- [X] T014 Confirm `python MistHelper.py --help` still succeeds.
