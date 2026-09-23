# Feature Specification: Honest operation output files

## User Scenarios and Testing

### User Story 1 - Empty export shows a no-output reason (P1)

An operator runs menu 4 when the organization has no guest records. The Output Files list stays empty. The completion message states the no-output reason from the log.

Acceptance Criteria:

1. Given a run log names a CSV file that does not exist, when the run ends, then the run record removes that file name.
2. Given a run has no files and a no-data log line, when the run completes, then the completion message includes that no-data line.

### User Story 2 - Site cache does not preview before the result (P1)

An operator runs menu 69 and selects a site. The Output Files list shows the WLAN result before the site cache file.

Acceptance Criteria:

1. Given a non-menu-1 run lists `SiteList.csv` and another output file, when the run record is finalized, then `SiteList.csv` is not first.
2. Given menu 1 lists only `SiteList.csv`, when the run record is finalized, then `SiteList.csv` remains visible.

## Functional Requirements

- FR-001: The portal must list an output file only when that file exists under the run data directory when the run ends.
- FR-002: The portal must keep the no-output completion message when no listed file remains and the log holds a no-data line.
- FR-003: The portal must not preview the site selection cache before another result file for site-scoped operations.
- FR-004: The portal must keep `SiteList.csv` as the menu 1 result file.
- FR-005: The repair must not edit `web_portal/services/output_scan.py`.

## Out of Scope

- Change the output scanner rules.
- Change Mist API calls or menu operation behavior.
- Change the shared container deployment.

## Success Criteria

- SC-001: A unit guard fails on the old phantom-file behavior and passes after the repair.
- SC-002: A unit guard fails on the old site-cache ordering behavior and passes after the repair.
- SC-003: Browser verification for menus 4 and 69 shows no File not found preview caused by a portal-listed phantom.
