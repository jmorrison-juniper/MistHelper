# Quickstart: Native Windows Timeout Acceptance

## Local Checks

Run the workflow contract test:

```text
python -m pytest tests/guardrails/e2e_timeout_budget/test_windows_timeout_budget_workflow.py
```

Run the full timeout-budget test module:

```text
python -m pytest -q tests/guardrails/e2e_timeout_budget/test_timeout_budget.py
```

These local checks do not prove native Windows acceptance.

## Native Acceptance

After coordinator approval, push a relevant change to a non-main branch. Confirm that the optional Windows job reports seven tests, zero skips, zero errors, and zero failures. Do not count a canceled or timed-out run as acceptance.
