# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 282 | Export the rogue and PCI evidence pack | src.reports.rogue_pci_evidence.operation | RoguePciEvidencePack.run | safe |  | False | False |

## OperationRegistry comment

One `# WHY:` paragraph for menu 282 must state that the operation is safe because it reads Mist rogue, WLAN, and site setting evidence, then writes local evidence files only. It must state that PCI DSS 4.0 requires evidence of rogue and unknown wireless access point detection, and that this operation packages detection rows, site detection settings, and a short evidence summary for review.

## Primary key strategies

```python
"rogue_pci_evidence_pack": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["org_id", "site_id", "bssid", "ssid", "last_seen"],
    "indexes": ["org_id", "site_id", "classification", "bssid", "ssid"],
},
"rogue_pci_site_settings": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["org_id", "site_id", "run_started_at"],
    "indexes": ["org_id", "site_id", "rogue_enabled"],
},
```

## copilot-instructions category table

Add menu `282` to the `safe` category row. The count increases by one after the integration pull request wires the menu.

## Import line for MistHelper.py

`from src.reports.rogue_pci_evidence.operation import RoguePciEvidencePack  # Menu 282 (issue #3562) -- export rogue and PCI evidence files.`

