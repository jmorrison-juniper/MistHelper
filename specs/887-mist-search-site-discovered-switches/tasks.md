# Tasks: searchSiteDiscoveredSwitches

## Completed

- [x] Confirm the issue and read `spec.md`.
- [x] Confirm the installed SDK callable and signature.
- [x] Confirm menu 228 registration.
- [x] Confirm the shared exporter calls the endpoint and persists rows.
- [x] Confirm the composite primary-key strategy.
- [x] Confirm API and menu documentation.
- [x] Add a focused unit test for the endpoint binding and write.
- [x] Correct the changelog reference to issue #1395.
- [x] Run targeted and repository quality checks.

## Acceptance mapping

| Requirement | Implementation |
|---|---|
| FR-001 | Menu 228 calls `searchSiteDiscoveredSwitches`. |
| FR-002 | Site selection uses the shared `safe_input` flow. |
| FR-003 | The shared Mist session and pagination path apply. |
| FR-004 | The shared `DataExporter` path writes the rows. |
| FR-005 | The composite strategy is registered. |
| FR-006 | The exporter logs before and after the API call. |
| FR-007 | New test code follows inline comment rules. |
| FR-008 | README-derived menu docs and the changelog identify menu 228. |
