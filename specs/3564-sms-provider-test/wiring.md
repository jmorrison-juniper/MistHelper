# Wiring manifest

## Menu entries
| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 284 | Test the guest portal SMS provider | src.troubleshooting.sms_provider_test.operation | SmsProviderTest.run | interactive |  | False | False |

## OperationRegistry comment
One `# WHY:` paragraph for menu 284: SMS code guest portals depend on external provider credentials. This interactive operation asks for hidden credentials, confirms before it sends a test message, calls one `/api/v1/utils/` provider test endpoint, and writes a credential-free result row for troubleshooting.

## Primary key strategies
```python
"testSmsProviderSetup": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["provider", "destination", "tested_at"],
    "indexes": ["provider", "destination", "verdict", "http_status", "tested_at"],
},
```

## copilot-instructions category table
Add menu `284` to the `interactive` row. The count increases by one, from `29` to `30`.

## Import line for MistHelper.py
`from src.troubleshooting.sms_provider_test.operation import SmsProviderTest  # Menu 284 (issue #3564) -- Test guest portal SMS provider setup.`
