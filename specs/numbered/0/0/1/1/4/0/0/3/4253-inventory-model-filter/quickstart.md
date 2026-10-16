# Offline validation

Run `python3 scripts/bootstrap_worktree.py` in the isolated worktree.
Use `.venv/bin/python -m pytest` for all tests.

Run `tests/unit/firmware_policy`, `tests/integration/firmware_policy`, and `tests/e2e/web_portal/test_firmware_policy.py`.
Verify default filtering, explicit all-model choices, empty responses, errors, and unchanged confirmation behavior.
All Mist responses must use the existing SDK session double.
Do not run menu 305 against a real organization.
