# Wiring manifest

## Menu entries
| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 274 | Export the PSK hygiene report | src.reports.psk_hygiene.operation | PskHygieneReport.run | safe |  | False | False |

## OperationRegistry comment
One `# WHY:` paragraph for the registry entry:

`# WHY: Menu 274 is safe because it only reads organization PSKs, WLANs, and WLAN templates. It writes PskHygiene.csv through the normal export path, and it never writes passphrase or old_passphrase values. The report states that site-level WLANs are outside scope.`

## Primary key strategies
```python
"psk_hygiene_report": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["name", "ssid", "role", "vlan", "expire_time"],
    "indexes": ["ssid", "role", "wlan_match", "findings"],
},
```

## copilot-instructions category table
Add menu `274` to the `safe` row. The operation is read-only and not destructive.

## Import line for MistHelper.py
`from src.reports.psk_hygiene.operation import PskHygieneReport  # Menu 274 (issue #3555) -- PSK hygiene report.`

## Deferred integration pull request edits
- `MistHelper.py` menu 274 registration is deferred to the integration pull request.
- `src/utils/operation_registry.py` menu 274 entry is deferred to the integration pull request.
- `README.md` menu table and operation count edits are deferred to the integration pull request.
- Generated menu reference edits are deferred to the integration pull request.
- `src/refactors/endpoint_primary_key_strategies.py` edits are deferred to the integration pull request.

## Local validation evidence
- `python -m py_compile` passed for all new PSK hygiene source and test Python files.
- `python -m ruff check src\reports\psk_hygiene tests\unit\reports\psk_hygiene` passed.
- `python -m black --check src\reports\psk_hygiene tests\unit\reports\psk_hygiene` passed.
- `python -m mypy src\reports\psk_hygiene --config-file pyproject.toml` passed.
- `python -m pydocstyle src\reports\psk_hygiene` passed.
- `python -m pytest tests\unit\reports\psk_hygiene -q --timeout=120` passed with 25 tests.
- Menu wiring stays deferred to the integration pull request.
