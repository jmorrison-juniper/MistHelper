# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 285 | Validate a NAC identity provider credential | src.mist.intelligence.troubleshooting.nac_idp_credential_test.operation | NacIdpCredentialTest.run | interactive |  | False | False |

## OperationRegistry comment

One `# WHY:` paragraph: `# WHY: menu 285 validates one Access Assurance identity provider credential before a cutover. It is interactive because it asks for a provider, a username, a hidden password, and a final y/N confirmation before it sends the credential to Mist. The operation writes only the safe verdict and returned attributes, so the password never enters the export path.`

## Primary key strategies

```python
"nacIdpCredentialTest": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["tested_at", "idp_id", "username"],
    "indexes": ["idp_id", "idp_name", "username", "verdict", "tested_at"],
},
```

## copilot-instructions category table

Add menu `285` to the `interactive` category row. The count increases by one.

## Import line for MistHelper.py

`from src.mist.intelligence.troubleshooting.nac_idp_credential_test.operation import NacIdpCredentialTest  # Menu 285 (issue #3565) -- validate one NAC identity provider credential without exporting the password.`
