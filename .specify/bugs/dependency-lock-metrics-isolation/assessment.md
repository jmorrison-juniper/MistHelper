# Bug Assessment: Dependency Lock and Metrics Gateway Isolation

- **Slug**: dependency-lock-metrics-isolation
- **Created**: 2026-11-06
- **Source**: https://github.com/jmorrison-juniper/MistHelper/issues/4584
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

Issue #4584 reports that the dependency lock guard rejected pytest 9.1.1 after the declared
version changed to 9.2.0. It also reports that a metrics gateway test retained `MistHelper.org_id`
from an earlier test.

The issue URL uses host `github.com`. The URL policy allowed this host.

## Symptom

The lock guard failed because `uv.lock` named pytest 9.1.1 instead of the required 9.2.0.
The missing-organization test could use organization state left by an earlier test.

## Reproduction

1. Run `tests/guardrails/test_dependency_lock_file.py`.
2. Run `tests/unit/test_metrics_gateway_org_selection.py` after another test sets `MistHelper.org_id`.
3. Check the lock for the declared pytest version.

## Suspected Code Paths

- `tests/guardrails/test_dependency_lock_file.py:68` checks that the lock satisfies each declared requirement.
- `uv.lock:3098` records pytest version 9.2.0 on current main.
- `tests/unit/test_metrics_gateway_org_selection.py:27` clears `MistHelper.org_id` before the missing-organization test.

## Root Cause Hypothesis

The dependency update changed the pytest requirement without updating the lock file.
The metrics gateway test depended on shared class state without resetting it.
Confidence is high because PR #4576 updated the lock and added the state reset.

## Proposed Remediation

**Preferred**: No further source change is needed. PR #4576 merged as
`8cc4652d2b88cec6978f3522ac0feaa52f796b7c`, and its commit is an ancestor of current main.
The pull request also repaired pytest 9.2 monkeypatch teardown tests.

**Files likely to change**:

- No files need a new source change.
- `uv.lock` and the three affected test modules changed in PR #4576.

**Tests to add or update**:

- The current lock guard and affected unit tests pass in the focused run.

## Risks & Considerations

- An open pull request also changes `uv.lock`. No new change was made because the reported defect is resolved.
- The focused run used Python 3.14.7. This worktree did not have Python 3.13 available.
- The first test attempt used the system interpreter, which did not have pytest. The locked development environment then enabled the focused run.

## Open Questions

- None for the reported failures.
