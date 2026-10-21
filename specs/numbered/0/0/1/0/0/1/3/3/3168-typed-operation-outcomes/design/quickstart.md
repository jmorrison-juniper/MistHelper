# Contract Validation

If `.venv` is absent, run `python3 scripts/bootstrap_worktree.py`.
Use `.venv/bin/python` on macOS or Linux.
Use `.venv\Scripts\python.exe` on Windows.

Run these commands from the repository root with the environment active.

```text
python -m pytest tests/unit/dataclasses/test_operation_outcome.py -q
python -m pytest tests/unit/dataclasses/test_operation_outcome.py --cov=src.foundation.models.operation_outcome --cov-branch --cov-report=term-missing --cov-fail-under=100
python -m pytest tests/unit/reports/psk_hygiene/test_operation.py -q
python -m pytest tests/unit/export/test_data_exporter.py -k test_returns_false_on_invalid_inputs -q
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

The PSK hygiene tests cover completed, no-output, missing-input, and failed
export results. They also confirm that primary fetch and export exceptions
propagate. The exporter test confirms that empty input rows are rejected
before a writer or database route runs.

The alert digest tests cover completed, no-output, and failed results. They
also confirm that write exceptions propagate and that wording does not change
the state. Run `python -m pytest tests/unit/reports/alert_digest -q`.

Run the committed-test quality procedure in `.github/copilot-instructions.md`
before push. Keep the intended PR base consistent across its commands.

The posture checklist tests cover completed, failed, and missing-input results.
They also confirm that collection errors propagate. Run
`python -m pytest tests/unit/reports/org_security_posture -q`.
