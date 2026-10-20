# Contract Validation

If `.venv` is absent, run `python3 scripts/bootstrap_worktree.py`.
Use `.venv/bin/python` on macOS or Linux.
Use `.venv\Scripts\python.exe` on Windows.

Run these commands from the repository root with the environment active.

```text
python -m pytest tests/unit/dataclasses/test_operation_outcome.py -q
python -m pytest tests/unit/dataclasses/test_operation_outcome.py --cov=src.foundation.models.operation_outcome --cov-branch --cov-report=term-missing --cov-fail-under=100
python -m pytest tests/unit/web_portal/test_portal_silent_completion.py -q
python -m ruff check src/foundation/models/operation_outcome.py tests/unit/dataclasses/test_operation_outcome.py
python -m black --check src/foundation/models/operation_outcome.py tests/unit/dataclasses/test_operation_outcome.py
python -m mypy src/foundation/models/operation_outcome.py tests/unit/dataclasses/test_operation_outcome.py --config-file pyproject.toml
python -m bandit -c pyproject.toml src/foundation/models/operation_outcome.py -q
```

Expect all tests and checks to pass. Require full statement and branch coverage
for the new model. The unchanged portal tests must still pass.

The model tests cover all four states, wording changes, invalid input,
immutability, and serialization. No command needs Mist credentials.

Run the committed-test quality procedure in `.github/copilot-instructions.md`
before push. Keep the intended PR base consistent across its commands.
