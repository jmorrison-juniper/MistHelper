# Operator Rollout Checklist: CI Quality Gates Remediation

Purpose: safe rollout steps (dry-run and smoke tests) for the remediation changes to Quality Gates workflow. No ETA specified; follow organizational change windows.

Preparation

- [ ] Ensure maintainer access to the repository and CI settings
- [ ] Identify an owner for the change and a rollback owner
- [ ] Create a short-lived feature branch for the changes (e.g., ci/quality-gates-pins)

Dry-run (on branch)

1. Local verification
   - [ ] Reproduce CI locally (see specs/ci-quality-gates-triage/spec.md "Reproduce locally") and collect logs
   - [ ] Verify pinned tool versions install successfully in a fresh Python 3.13 venv
   - [ ] Run python checks locally: ruff, mypy, pytest unit tests, bandit

2. Push branch and run CI
   - [ ] Push branch ci/quality-gates-pins to remote
   - [ ] Trigger CI run and wait for completion
   - [ ] Collect logs for install steps and ensure tool versions are printed
   - [ ] Confirm at least one successful run; if failures occur, capture logs and escalate

Smoke tests (post-merge)

- [ ] Merge PR to main (with approvals) during low-impact window
- [ ] Monitor CI Health:
  - Watch next 3 merges or scheduled runs; expect at least 3 consecutive green Quality Gates runs
  - Confirm no new test regressions attributed to pinned tool versions

Rollout validations

- [ ] Confirm that pip install time is reduced (if cache added)
- [ ] Confirm that retries reduced transient install failures
- [ ] Confirm that pip-audit behavior is acceptable (no unexpected CVE failures); if CVE is discovered, follow security team process

Rollback plan

- [ ] If CI regression persists after remediation, revert the workflow change (rollback PR) and open a follow-up issue to investigate deeper causes
- [ ] If a pinned tool causes functional test regressions, open a follow-up for incremental version bumping and running canary upgrades

Post-deploy monitoring

- [ ] Monitor CI for 72 hours (or next N PRs) and record any failures in the issue tracker
- [ ] If stable, schedule Phase B improvements (cache, consolidate installs, canary job)

Notes

- Keep the patch minimal. Do not change project tests or source code in this patch unless absolutely necessary for stability.
- Document any agreed version bumps or long-term upgrade plan in the issue.
