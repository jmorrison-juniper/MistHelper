# Quickstart: Merge queue workflow contracts

## Prerequisites

Use the worktree environment.
If pytest is absent, run `python3 scripts/bootstrap_worktree.py`.
Activate `.venv` with the command for your operating system.

## Local verification

```text
python -m pytest -s tests/guardrails/test_ci_gate_triggers.py tests/guardrails/test_ci_runtime_budgets.py tests/guardrails/test_quality_gate_close_scope.py tests/guardrails/test_codeql_register_gate.py
python -m ruff check .
python -m black --check --diff .
```

All tests must pass. The guard must print workflow and required-context counts.
Synthetic trigger, name, checkout, and cancellation mutations must fail their contract decisions.
Run the remaining applicable gates from the repository instructions before delivery.

The committed ratchet must report zero new findings.
See the canonical test-quality procedure in `.github/copilot-instructions.md`.

## Operational verification

The owner must separately approve queue activation.
Use the rollout procedure in `documentation/quality-gates.md`.
Record actual queue commit, checks, merge, and main results on #3071.
Do not mark operational acceptance complete from local checks.
