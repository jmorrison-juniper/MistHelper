# Troubleshooting core module isolation

## Goal

Keep the troubleshooting domain within the five-child hierarchy limit.

## Requirements

- Move `interactive_test_runner.py`, `marvis_troubleshoot_utils.py`, and
  `troubleshoot_utils.py` into `troubleshooting/core/`.
- Keep the troubleshooting root at five visible structural children.
- Keep all moved module-level symbols and runtime behavior unchanged.
- Update active imports, dependency mappings, tests, fixtures, and generated documentation.
- Do not keep compatibility modules at the old paths.
- Keep historical specifications and generated evidence unchanged.

## Verification

- Run the source hierarchy and public symbol preservation guards.
- Run `symbol-diff --base origin/main` on every changed Python file.
- Run the focused troubleshooting tests, compile, Ruff, Black, and mypy.
