# Quickstart: Timestamp validation

Install the repository test environment and put PowerShell on `PATH`.
Run `python -m pytest tests/guardrails/test_spec_route_contract.py`.
The invalid timestamp tests must fail before the repair and pass after it.
Valid boundary routes must match the independent expected values.
