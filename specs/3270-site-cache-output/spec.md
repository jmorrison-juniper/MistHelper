# Feature Specification: Site cache output ordering

## User Scenarios and Tests

### User Story 1 - See the requested export first (P1)

A NOC engineer runs a site-scoped operation that refreshes the site selector cache and writes a result file. The result panel previews the operation result, not `SiteList.csv`.

**Acceptance Criteria**

1. Given menu 69 writes `SiteWlans_AlamoSanAntonio.csv` and refreshes `SiteList.csv`, when the run completes, then the preview selects `SiteWlans_AlamoSanAntonio.csv` first.
2. Given menu 1 exports the site list, when the run completes, then the result panel still reports `SiteList.csv`.
3. Given a site-scoped operation refreshes only `SiteList.csv` and logs a no-data reason, when the run completes, then the panel shows the reason and no table preview.

## Requirements

- **FR-001**: The portal must treat `SiteList.csv` as a prompt cache for site-scoped operations.
- **FR-002**: The portal must keep `SiteList.csv` as a real result for the site list export operation.
- **FR-003**: The portal must preview an operation result before a prompt cache when both files changed.
- **FR-004**: The portal must not let a prompt cache hide a no-data result.
- **FR-005**: The guard test must measure the site-parameter row count.

## Success Criteria

- **SC-001**: Menu 69 previews the WLAN export file before the site cache file.
- **SC-002**: Menu 1 continues to preview `SiteList.csv`.
- **SC-003**: A guard test fails if cache files sort before operation files.
- **SC-004**: The measured cache-risk row count is recorded in test output.

## Assumptions

- The site selector can refresh `SiteList.csv` before the operation writes its result.
- A changed prompt cache can be useful evidence, but it must not be the first preview for another operation.
