# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 275 | Audit site variable coverage | `src.reports.site_variable_audit.operation` | `SiteVariableAudit.run` | `safe` |  | `False` | `False` |

## OperationRegistry comment

`# WHY: Menu 275 only reads organization templates, WLANs, device profiles, sites, and site variables, then writes CSV reports. It is safe for --test because it prompts for nothing and does not change Mist configuration.`

## Primary key strategies

```python
"siteVariableAudit": {
    "type": "natural_pk",
    "primary_key": ["site_id", "template_id", "variable_name", "field_path"],
    "indexes": ["site_name", "template_type", "template_name", "variable_name"],
},
"siteVariableSummary": {
    "type": "natural_pk",
    "primary_key": ["site_id"],
    "indexes": ["site_name", "missing_count", "unused_variable_count"],
},
```

## copilot-instructions category table

Add Menu 275 to the `safe` row. Increase the `safe` count by one. Do not add Menu 275 to any destructive, interactive, websocket, resource-intensive, or continuous-loop row.

## Import line for MistHelper.py

```python
from src.reports.site_variable_audit.operation import SiteVariableAudit  # Menu 275 (issue #3556) -- audit missing and unused site variables.
```

## Deferred integration status

- `MistHelper.py` is deferred to the integration pull request.
- `src/utils/operation_registry.py` is deferred to the integration pull request.
- `src/refactors/endpoint_primary_key_strategies.py` is deferred to the integration pull request.
- `README.md` is deferred to the integration pull request.
- `documentation/menu_reference.md` is deferred to the integration pull request.
- `documentation/wiki/` generated files are deferred to the integration pull request.
- `MistHelper.py --test` proof for Menu 275 is deferred until the integration pull request wires Menu 275.

## Source package files

- `src/reports/site_variable_audit/__init__.py`
- `src/reports/site_variable_audit/client.py`
- `src/reports/site_variable_audit/model.py`
- `src/reports/site_variable_audit/operation.py`

## Test files

- `tests/unit/reports/site_variable_audit/__init__.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_client_test.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_contract_test.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_fixtures_test.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_model_test.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_operation_test.py`
- `tests/unit/reports/site_variable_audit/site_variable_audit_summary_test.py`

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
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m vulture src\reports\site_variable_audit --min-confidence 70
C:\Users\jmorrison\mh-fleet\3556-site-variable-audit\.venv\Scripts\python.exe -m interrogate -v src\reports\site_variable_audit
```
