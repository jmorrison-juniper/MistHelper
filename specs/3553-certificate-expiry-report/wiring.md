# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 272 | Export the certificate expiry report | src.reports.certificate_expiry.operation | CertificateExpiryReport.run | safe |  | False | False |

## OperationRegistry comment

`# WHY:` Menu 272 gives operators one read-only certificate expiry report across device certificates, RadSec, NAC, SSO, PSK portal, and CA sources. Mist raises certificate alerts on a fixed expiry calendar, but the portal does not show one renewal worklist. The entry stays `safe` because it only reads Mist API data and writes `CertificateExpiry.csv`.

## Primary key strategies

```python
"certificate_expiry_report": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": [
        "org_id",
        "source_name",
        "scope",
        "owner_name",
        "serial",
        "not_after",
    ],
    "indexes": [
        "org_id",
        "source_name",
        "scope",
        "band",
        "not_after",
    ],
},
```

## copilot-instructions category table

Add menu `272` to the `safe` category row. The safe count increases by one.

## Import line for MistHelper.py

`from src.reports.certificate_expiry.operation import CertificateExpiryReport  # Menu 272 (issue #3553) -- export certificate expiry risk.`

## Deferred integration notes

- Do not edit `MistHelper.py` on this feature branch.
- Do not edit `src/utils/operation_registry.py` on this feature branch.
- Do not edit `src/refactors/endpoint_primary_key_strategies.py` on this feature branch.
- Do not edit `README.md` or generated menu references on this feature branch.
