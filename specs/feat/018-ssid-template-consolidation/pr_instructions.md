PR Instructions — SSID Template Consolidation (Feature 018)

This file documents local branch and PR preparation steps for the current feature work.

Suggested local commands (run from repo root):

```bash
# create feature branch from main
git fetch origin
git checkout -b feat/018-adapter-tests

# add changes and commit
git add -A
git commit -m "feat(018): add adapter tests, integration conftest, and PR notes"

# push branch (requires remote access / credentials)
git push -u origin feat/018-adapter-tests
```

PR body template (paste into GitHub PR):

- **What**: Adds `MistApiAdapter` tests (retry/backoff), integration `conftest.py` with mocked `mistapi`, wires Menu 159, and marks T014 complete.
- **Why**: Improves reliability by testing transient API failures and provides an integration fixture for future tests.
- **Testing**: Unit tests executed locally via `python -m unittest tests.unit.test_api_adapter_retries tests.unit.test_api_adapter tests.unit.test_cache tests.unit.test_manager_phase1 tests.unit.test_analysis -v` (all passing).

Please add labels: `feature`, `in-progress`, `tests`.
