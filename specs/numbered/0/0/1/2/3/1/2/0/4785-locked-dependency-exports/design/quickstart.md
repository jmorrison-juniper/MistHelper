# Quickstart: Locked Dependency Exports

## Prerequisites

- Use Python 3.15.2 and the repository development environment.
- Install UV 0.13.7 or a compatible version.

## Regenerate the Lock and Exports

```powershell
uv lock --upgrade-package markdown-it-py --upgrade-package openai --upgrade-package simplejson
uv export --locked --no-hashes --no-emit-project --output-file requirements.txt
uv export --locked --no-hashes --no-emit-project --extra dev --output-file requirements-dev.txt
```

Keep Gunicorn below version 27. Keep platform markers from the generated exports.

## Validate

```powershell
uv lock --check
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/test_dependency_export.py tests/guardrails/test_dependency_lock_file.py tests/guardrails/test_dependency_declaration_parity.py
pip-audit -r requirements.txt
```

The lock check and dependency guards must pass. The audit must report no known vulnerabilities.
