# Feature Specification: Rogue PCI Evidence Pack

**Feature Branch**: `3562-rogue-pci-evidence`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "menu 282 rogue and PCI evidence pack. PCI DSS 4.0 requires detection of rogue and unknown wireless access points and evidence of that detection. Menu 30 exports rogue AP detections as raw rows. No operation classifies each detection as honeypot, rogue, or neighbor, reports which sites run with detection off, and lists the approved SSIDs and BSSIDs as one evidence pack. RogueEvidence.csv: one row per detection with site, classification (honeypot, rogue, neighbor), SSID, BSSID, channel, band, RSSI, first seen, last seen, client count, and the org SSID it impersonates when it is a honeypot. RogueSiteSettings.csv: one row per site with rogue detection enabled, honeypot detection enabled, neighbor RSSI threshold, approved SSID count, and approved BSSID count. RogueEvidenceSummary.md: a short evidence statement with the counts and the run time."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export PCI rogue evidence pack (Priority: P1)

A network operator runs menu 282 to make one evidence pack for PCI DSS 4.0 rogue wireless review. The pack gives classified detections, site settings, and a short summary that an assessor can read.

**Why this priority**: This is the main user value. It changes raw rogue AP rows into evidence that supports the PCI DSS control.

**Independent Test**: Run the operation in `--test` mode with no prompt. Confirm that the run writes `data/RogueEvidence.csv`, `data/RogueSiteSettings.csv`, and `data/RogueEvidenceSummary.md`.

**Acceptance Scenarios**:

1. **Given** an organization has rogue AP events, **When** the operator runs menu 282 in `--test` mode, **Then** the operation writes the three evidence files under `data/` without a prompt.
2. **Given** the run completes, **When** the operator opens `RogueEvidenceSummary.md`, **Then** the summary states the run time and the counts for detections, honeypots, rogues, neighbors, total sites, and sites with detection off.
3. **Given** the evidence files are written, **When** an assessor opens the files, **Then** each file uses plain column names and can stand alone as audit evidence.

---

### User Story 2 - Classify rogue detections (Priority: P2)

A network operator needs each rogue AP event to say whether it is a honeypot, a rogue, or a neighbor. The operator needs the org WLAN name that a honeypot copies.

**Why this priority**: PCI evidence must show that unknown AP detections were reviewed and sorted. The classification gives the review result.

**Independent Test**: Use fixture data with known org WLAN SSIDs and org AP BSSIDs. Confirm that a detection whose SSID equals an org WLAN SSID and whose BSSID is not an org AP BSSID is classified as `honeypot` and names the org SSID it impersonates.

**Acceptance Scenarios**:

1. **Given** a detection has an SSID that equals an org WLAN SSID and a BSSID that is not an org AP BSSID, **When** menu 282 classifies the detection, **Then** `RogueEvidence.csv` sets `classification` to `honeypot` and sets the impersonated org SSID.
2. **Given** a detection does not match a known org WLAN SSID and does not use an approved BSSID, **When** menu 282 classifies the detection, **Then** the result is `rogue` unless site neighbor rules classify it as `neighbor`.
3. **Given** a detection matches neighbor criteria for the site, **When** menu 282 classifies the detection, **Then** the result is `neighbor`.

---

### User Story 3 - Report site detection settings (Priority: P3)

A compliance owner needs to know which sites have rogue detection, honeypot detection, and neighbor thresholds enabled. They also need to know which sites have detection off.

**Why this priority**: PCI evidence is not complete if some sites do not detect rogues. The site settings report shows the gap.

**Independent Test**: Use fixture data with at least one site where `rogue.enabled` is false. Confirm that `RogueSiteSettings.csv` includes that site with detection off and that `RogueEvidenceSummary.md` counts it.

**Acceptance Scenarios**:

1. **Given** the organization has sites, **When** menu 282 runs the site settings pass, **Then** it reads one setting record per site with the shared pacer.
2. **Given** a site has `rogue.enabled` set to false, **When** menu 282 writes `RogueSiteSettings.csv`, **Then** the site appears in the file with detection off.
3. **Given** one or more sites have detection off, **When** menu 282 writes `RogueEvidenceSummary.md`, **Then** the summary gives the count of those sites.

---

### Edge Cases

- If no rogue detections exist, the operation still writes all three files and the summary shows zero detections.
- If a site setting record is missing or cannot be read, the site still appears in the settings report with an error state and the summary states the incomplete count.
- If a detection has a blank SSID or BSSID, the operation keeps the row and leaves only the missing field blank.
- If the same detection appears from more than one source, the output uses one row per detection record and does not merge records unless the source data already merges them.
- If approved BSSID data is empty for a site, honeypot and rogue classification still works from org WLAN SSIDs and the missing approved count is zero.
- If Mist returns rate-limit or transient errors, the shared pacer controls retries and prevents a prompt in `--test` mode.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST add menu 282 as a safe, read-only operation named for rogue and PCI evidence.
- **FR-002**: The system MUST defer detailed menu wiring to `specs/3562-rogue-pci-evidence/wiring.md`.
- **FR-003**: The operation MUST run in `--test` mode with no prompt and write all output files under `data/`.
- **FR-004**: The operation MUST create `RogueEvidence.csv` with one row per rogue detection.
- **FR-005**: `RogueEvidence.csv` MUST include site, classification, SSID, BSSID, channel, band, RSSI, first seen, last seen, client count, and impersonated org SSID.
- **FR-006**: The classification value MUST be one of `honeypot`, `rogue`, or `neighbor`.
- **FR-007**: A detection whose SSID equals an org WLAN SSID and whose BSSID is not an org AP BSSID MUST be classified as `honeypot`.
- **FR-008**: A honeypot row MUST state the org SSID that the detection impersonates.
- **FR-009**: The operation MUST use org WLAN data from `listOrgWlans` to identify approved org SSIDs.
- **FR-010**: The operation MUST use org site data from `listOrgSites` to include every site in the settings report.
- **FR-011**: The operation MUST read one site setting record per site with `getSiteSetting` and the shared pacer.
- **FR-012**: The specification cost for the site settings pass MUST be one `getSiteSetting` request for each site in the organization.
- **FR-013**: The operation MUST use rogue event data from `searchOrgRogueEvents` and rogue AP data from `listSiteRogueAPs` to build the evidence pack.
- **FR-014**: The operation MUST create `RogueSiteSettings.csv` with one row per site.
- **FR-015**: `RogueSiteSettings.csv` MUST include rogue detection enabled, honeypot detection enabled, neighbor RSSI threshold, approved SSID count, and approved BSSID count.
- **FR-016**: A site with `rogue.enabled` false MUST appear in `RogueSiteSettings.csv` with detection off.
- **FR-017**: `RogueEvidenceSummary.md` MUST count sites with detection off.
- **FR-018**: `RogueEvidenceSummary.md` MUST state that the Mist cloud sits outside the cardholder data environment and MUST name the source page used for that statement.
- **FR-019**: The source page name in the summary MUST be `Juniper Mist Cloud PCI DSS Shared Responsibility and Compliance` unless project evidence selects a newer page name during implementation.
- **FR-020**: The operation MUST use the repository output pattern for collected API data and MUST write evidence files through the approved export path.
- **FR-021**: The operation MUST not change Mist cloud configuration.
- **FR-022**: The operation MUST not collect, store, or print cardholder data.
- **FR-023**: The wiring manifest `specs/3562-rogue-pci-evidence/wiring.md` MUST exist and MUST include every contract section for menu number, safety class, data sources, pacing, outputs, tests, and deferred wiring.
- **FR-024**: The release note fragment `changelog.d/issue-3562-rogue-pci-evidence.md` MUST exist before implementation is complete.

### Key Entities

- **Rogue Detection**: A wireless access point detection reported by Mist. Key attributes are site, SSID, BSSID, channel, band, RSSI, first seen, last seen, and client count.
- **Classification**: The compliance label assigned to a detection. Valid values are `honeypot`, `rogue`, and `neighbor`.
- **Org WLAN SSID**: An approved wireless network name from the organization WLAN list. It is used to find honeypot impersonation.
- **Org AP BSSID**: An approved AP radio MAC address in the organization. It is used to prevent approved APs from being marked as honeypots.
- **Site Rogue Settings**: The site-level setting record for rogue detection, honeypot detection, and neighbor RSSI threshold.
- **Evidence Summary**: A short Markdown statement that gives run time, counts, and the PCI context statement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In `--test` mode, menu 282 completes with no prompt and writes all three named files under `data/` in one run.
- **SC-002**: In controlled test data, 100% of detections that match the honeypot rule are classified as `honeypot` and include the impersonated org SSID.
- **SC-003**: The settings report includes 100% of organization sites returned for the run.
- **SC-004**: The summary count for sites with detection off equals the number of rows in `RogueSiteSettings.csv` where rogue detection is off.
- **SC-005**: The site settings pass makes one settings read per site and records that request cost in the implementation evidence.
- **SC-006**: A reviewer can confirm the PCI evidence statement, run time, and all counts from `RogueEvidenceSummary.md` in less than 5 minutes.
- **SC-007**: The operation does not change Mist configuration during 100% of test and production runs.

## Assumptions

- Menu 282 is a safe category operation because it reads data and writes local evidence files only.
- Menu 30 remains available as the raw rogue AP export. Menu 282 adds classification and PCI evidence packaging.
- The approved SSID list comes from organization WLANs.
- The approved BSSID list comes from organization AP inventory or rogue AP source data that identifies org AP BSSIDs.
- The evidence pack is for PCI DSS 4.0 rogue and unknown wireless AP detection support. It is not a full PCI compliance report.
- Mist cloud inventory and event records do not contain cardholder data for this evidence pack.
- Menu wiring, exact handler names, test file names, and the release note are deferred to the implementation plan and to `specs/3562-rogue-pci-evidence/wiring.md`.
