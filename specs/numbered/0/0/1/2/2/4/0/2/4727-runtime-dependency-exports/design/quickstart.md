# Dependency Export Validation

## Prerequisites

- Use Python 3.13 or newer.
- Use UV 0.13.7 or a newer approved UV release.
- Run the commands from the repository root.

## Refresh the Lock and Exports

1. Review the current compatible updates:

   ```text
   uv lock --upgrade --dry-run --upgrade-package 'openai==3.48.0'
   ```

2. If the preview matches the reviewed update set, update the lock:

   ```text
   uv lock --upgrade --upgrade-package 'openai==3.48.0'
   ```

3. Generate the runtime export:

   ```text
   uv export --locked --no-hashes --no-emit-project --output-file requirements.txt
   ```

4. Generate the development export:

   ```text
   uv export --locked --no-hashes --no-emit-project --extra dev --output-file requirements-dev.txt
   ```

## Validate the Result

Run the dependency parity, lock, and export checks:

```text
python -m pytest tests/guardrails/test_dependency_declaration_parity.py tests/guardrails/test_dependency_lock_file.py tests/guardrails/test_dependency_export.py
uv lock --check
pip-audit -r requirements.txt
pip-audit -r requirements-dev.txt
```

The tests must pass. The lock check must pass. The audit must report no known vulnerabilities in packages it can inspect.

Each audit evaluates markers for the current Python and platform. Report this limit. Name every dependency source that the audits cannot inspect. Do not claim that one host audit covers every platform.

Caution: Do not widen package constraints to accept an incompatible release. A wider constraint can permit an unsupported package combination.
