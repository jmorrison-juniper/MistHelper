# Feature Specification: No-output completion reasons

## User Scenarios and Tests

### User Story 1 - Read an honest result for no-data operations (P1)

A NOC engineer runs menus 77, 78, or 82 from the Operations portal. If the handler returns no operation data, the result panel states a no-data reason and does not preview a prompt cache.

**Acceptance Criteria**

1. Given menu 77 returns anomaly rows, when the run completes, then the portal shows `SiteAnomalyEvents_<site>.csv`.
2. Given menu 78 returns no device anomaly rows and refreshes `SiteInventory.csv`, when the run completes, then the portal shows the no-data reason instead of the device inventory cache.
3. Given menu 82 returns switch metrics, when the run completes, then the portal shows `SiteSwitchesMetrics.csv`.

## Requirements

- **FR-001**: The portal must classify `SiteInventory.csv` as a prompt cache for device-selecting operations.
- **FR-002**: The portal must keep `SiteInventory.csv` as a real result for menu 60.
- **FR-003**: The portal must show a no-data reason when a prompt cache is the only changed file.
- **FR-004**: The guard test must fail if menu 78 previews `SiteInventory.csv` as its operation result.

## Success Criteria

- **SC-001**: Menu 78 no longer previews device inventory cache rows when no device anomaly data exists.
- **SC-002**: Menu 60 still previews `SiteInventory.csv`.
- **SC-003**: Menus 77 and 82 continue to show operation-specific outputs.

## Assumptions

- The device selector can refresh `SiteInventory.csv` during a run.
- The anomaly handler can correctly log a zero-record reason.
