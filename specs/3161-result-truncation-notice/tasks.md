# Tasks: Result Truncation Notice

**Input**: [spec.md](spec.md) and [plan.md](plan.md).

**Source base**: `67a1ca625ab3526c68a8e54d1580dc1c92d3abc4`.

**Ownership**: Only `web_portal/static/js/operation_results.js` and new files in the granted feature namespaces may change.

Keep tasks unchecked until each acceptance condition passes. Do not write shared SpecKit state.

## Tasks

- [x] T001 Create the bounded native portal helper at `tests/support/result_truncation_notice/native_portal.py`.
- [x] T002 Create the native clipping and short-control regression at `tests/e2e/result_truncation_notice/test_native_clipping_notice.py`.
- [x] T003 Run the new regression against the unchanged renderer and record the expected notice failure in private evidence.
- [x] T004 Add geometry-based clipping detection, notice controls, lifecycle cancellation, and layout observation in `web_portal/static/js/operation_results.js`.
- [x] T005 Verify row details, output link, filtering, sorting, pagination, resizing, stale callback cancellation, sort warning, and short-result behavior in the new end-to-end regression.
- [x] T006 Add focused DOM accessibility and update-state regressions under `tests/unit/web_portal/result_truncation_notice/`.
- [x] T007 Add the release note at `changelog.d/issue-3161-result-truncation-notice.md`.
- [x] T008 Run affected tests, JavaScript syntax, Python compile, Ruff, Black, the configured mypy scope, and the required quality preflight and ratchets.
- [x] T009 Verify protected file and policy hashes, private receipt hashes, worktree cleanliness, and resource cleanup.
- [x] T010 Create one local Conventional Commit with the required co-author trailer and record the offline pull request checklist and limits in the private handoff.

## Stop boundary

Do not push, open a pull request, start Actions, merge, close the issue, change repository settings, or release another owner.
