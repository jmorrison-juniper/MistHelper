# Wiring Manifest: Rogue PCI Evidence Pack

## Contract Status

This file is the menu wiring contract for issue #3562. Implementation MUST keep each section current.

## Menu Entry

- Menu number: 282
- Menu name: Rogue and PCI Evidence Pack
- Category: safe
- Behavior: read Mist data and write local evidence files only
- Prompt policy: no prompt in `--test` mode

## Deferred Wiring

Detailed menu wiring is deferred to this file. `spec.md` defines the user need and the acceptance rules. This file defines the connection points that implementation must satisfy.

## Data Sources

- `listOrgWlans`: read org WLAN SSIDs used as approved SSID names.
- `listOrgSites`: read all sites that must appear in the settings report.
- `getSiteSetting`: read one setting record per site.
- `searchOrgRogueEvents`: read org rogue event records used for evidence rows.
- `listSiteRogueAPs`: read site rogue AP records used for evidence rows and approved context.

## Pacing Contract

The site settings pass MUST read one `getSiteSetting` record per site. It MUST use the shared pacer. The stated request cost is one site setting request for each site returned by `listOrgSites`.

## Classification Contract

- If a detection SSID equals an org WLAN SSID and the detection BSSID is not an org AP BSSID, classify it as `honeypot`.
- If a detection meets site neighbor criteria, classify it as `neighbor`.
- Otherwise classify the detection as `rogue`.
- A honeypot row MUST name the org SSID that it impersonates.

## Output Contract

All evidence files MUST be under `data/`.

- `RogueEvidence.csv`: one row per detection with site, classification, SSID, BSSID, channel, band, RSSI, first seen, last seen, client count, and impersonated org SSID.
- `RogueSiteSettings.csv`: one row per site with rogue detection enabled, honeypot detection enabled, neighbor RSSI threshold, approved SSID count, and approved BSSID count.
- `RogueEvidenceSummary.md`: short evidence statement with counts, run time, and PCI context.

## Site Settings Contract

A site with `rogue.enabled` false MUST appear in `RogueSiteSettings.csv` with detection off. The summary MUST count those sites.

## PCI Evidence Statement Contract

`RogueEvidenceSummary.md` MUST state that the Mist cloud sits outside the cardholder data environment. It MUST name the source page: `Juniper Mist Cloud PCI DSS Shared Responsibility and Compliance`, unless implementation verifies a newer source page name.

## Test Contract

- The operation runs in `--test` with no prompt.
- The run writes the three evidence files under `data/`.
- The honeypot classification rule has a direct test.
- The detection-off site setting rule has a direct test.
- The summary count of detection-off sites has a direct test.

## Release Note Contract

The release note fragment `changelog.d/issue-3562-rogue-pci-evidence.md` MUST exist before implementation is complete. This specify step does not create it because the fleet contract allows edits only under `specs/3562-rogue-pci-evidence/**`.
