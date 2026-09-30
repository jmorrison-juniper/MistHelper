# Wiring Manifest: Site Variable Audit

## Menu entries

- Add Menu 275 with title `Site Variable Audit`.
- Call `SiteVariableAudit.run()` with no positional argument.
- Mark the operation as read-only and safe.
- Defer the edit to the integration pull request.

## OperationRegistry comment

- Add Menu 275 to the safe category.
- Use this comment: `Site variable audit is read-only and writes CSV reports only.`
- Defer the edit to the integration pull request.

## Primary key strategies

- Add `siteVariableAudit` for `SiteVariableAudit.csv`.
- Use `natural_pk` with `["site_id", "template_id", "variable_name", "field_path"]`.
- Add `siteVariableSummary` for `SiteVariableSummary.csv`.
- Use `natural_pk` with `["site_id"]`.
- Defer the edit to the integration pull request.

## copilot-instructions category table

- Increase the safe operation count by one.
- Add Menu 275 to the safe menu number list.
- Do not add Menu 275 to the destructive, interactive, websocket, resource-intensive, or continuous-loop lists.
- Defer the edit to the integration pull request.

## Import line for MistHelper.py

```python
from src.reports.site_variable_audit.operation import SiteVariableAudit
```

## Source package files

- `src/reports/site_variable_audit/__init__.py`
- `src/reports/site_variable_audit/client.py`
- `src/reports/site_variable_audit/model.py`
- `src/reports/site_variable_audit/operation.py`

## Test files

- `tests/unit/reports/site_variable_audit/__init__.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_fixtures_test.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_contract_test.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_operation_test.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_client_test.py`

## Generated reference commands

```powershell
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map
```

## Validation commands

```powershell
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m py_compile src\reports\site_variable_audit\client.py src\reports\site_variable_audit\model.py src\reports\site_variable_audit\operation.py
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m ruff check src\reports\site_variable_audit tests\unit\reports\site_variable_audit
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m black --check src\reports\site_variable_audit tests\unit\reports\site_variable_audit
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m mypy src\reports\site_variable_audit --config-file pyproject.toml
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m pydocstyle src\reports\site_variable_audit
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m pytest tests\unit\reports\site_variable_audit -q --timeout=120
```

## Deferred integration status

- `MistHelper.py` is deferred.
- `src/utils/operation_registry.py` is deferred.
- `src/refactors/endpoint_primary_key_strategies.py` is deferred.
- `README.md` is deferred.
- `documentation/menu_reference.md` is deferred.
- `documentation/wiki/` generated files are deferred.
- `MistHelper.py --test` Menu 275 proof is deferred until the integration pull request wires Menu 275.

