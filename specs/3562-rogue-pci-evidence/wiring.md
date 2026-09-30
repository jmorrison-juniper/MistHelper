# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 282 | Export the rogue and PCI evidence pack | src.reports.rogue_pci_evidence.operation | RoguePciEvidencePack.run | safe |  | False | False |

## OperationRegistry comment

One `# WHY:` paragraph for menu 282 must state that the operation is safe because it reads Mist rogue, WLAN, and site setting evidence, then writes local evidence files only. It must state that PCI DSS 4.0 requires evidence of rogue and unknown wireless access point detection, and that this operation packages detection rows, site detection settings, and a short evidence summary for review.

## Data sources

Menu 282 reads `listOrgWlans`, `listOrgSites`, `getSiteSetting`, `searchOrgEvents` with `type="rogue-ap-detected"`, and `listSiteRogueAPs`. It uses `listSiteRogueAPs.ap_mac` as the available approved organization AP BSSID source for this package-only branch. No separate AP BSSID inventory endpoint is in this branch scope.

## Pacing

The site settings pass calls the shared rate limiter before each `getSiteSetting` read. The request cost is one settings read for each site returned by `listOrgSites`.

## Outputs

The operation writes `RogueEvidence.csv`, `RogueSiteSettings.csv`, and `RogueEvidenceSummary.md` under the repository data path. CSV output uses `DataExporter.write_with_format_selection()`. The Markdown summary uses `FilePathUtils.get_csv_path()`.

## Tests

The unit test suite under `tests/unit/reports/rogue_pci_evidence/` covers classification, site setting rows, summary counts, file writes, no-prompt operation behavior, and 4xx and 5xx client failures. The SDK compatibility and output scan guards also run before push.

## Deferred wiring

This branch is a package-only precursor. The operation is not integration-complete until the integration pull request registers menu 282, registers primary key strategies, updates README documentation, and regenerates menu references.

## Primary key strategies

```python
"rogue_pci_evidence_pack": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "unique_fields": ["org_id", "site_id", "bssid", "ssid", "first_seen", "last_seen", "channel", "band", "rssi", "client_count"],
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

## README menu documentation

Update the README operation count and menu table during the integration pull request. This branch does not edit README because the fleet contract reserves shared documentation for integration.

## Import line for MistHelper.py

`from src.reports.rogue_pci_evidence.operation import RoguePciEvidencePack  # Menu 282 (issue #3562) -- export rogue and PCI evidence files.`
