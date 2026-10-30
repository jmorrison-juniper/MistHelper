# AP discovery validation

Use the worktree virtual environment. Mock all Mist requests.

```text
source .venv/bin/activate
python -m pytest -q tests/unit/device/test_ap_profile_migration_manager.py
python -m ruff check .
python -m black --check .
```

The discovery tests must reject failed pagination with absent, empty, and populated first-page data.
The migration test must observe zero plans, confirmations, backups, and device updates.
Successful empty and complete reads must retain their exact results.

Run the documented source type, complexity, security, symbol, and test-quality checks before publication.
Keep issue #2753 open. Do not enable automatic merge.
