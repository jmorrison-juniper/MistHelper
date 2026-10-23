# Validation: Site read refusal

Activate the worktree environment before each command.
All tests use local mocks and start no firmware operation.

1. Run `python -m pytest tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py`.
2. Run `python -m pytest tests/contract/upgrade_portal/test_org_site_records_routes.py tests/contract/upgrade_portal/test_org_upgrade_routes.py`.
3. Run `python -m pytest tests/e2e/upgrade_portal/test_org_upgrade_flow.py -k cloud_read_refusal`.

The first command checks connection failures, timeouts, saved-state preservation, and recovery.
The second command checks successful saves and existing validation.
The third command checks the browser form after the refusal envelope.

Run the applicable lint, formatting, type, security, complexity, symbol, and documentation gates before the commit.
After the commit, run the documented test-quality preflight and comparison against `origin/main`.
