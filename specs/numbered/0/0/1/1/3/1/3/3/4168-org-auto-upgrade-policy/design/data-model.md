# Data Model: Organization Auto-Upgrade Policy

## Device policy

Store the device type, selected model-to-version map, and explicit enabled state.
AP policies also contain `version="custom"`, a day, and a time.
Switch and SRX policies preserve existing snapshot controls.
SSR policies preserve existing supported non-version controls.
Do not retain obsolete fallback versions or channels that conflict with the selected model map.

## Organization change

Store its identifier, display name, original settings snapshot, planned settings body, and site changes.
The write body contains selected firmware policies only.
Nested objects contain their preserved sibling members.
Never print full settings snapshots. Serialize them only into private verified backup files.

## Site change

Store its identifier, display name, original settings snapshot, and override-removal body.
Absent policies require no write.
Clear AP, switch, SSR, and SRX overrides. Preserve ESL and linecard controls.

## Execution result

Record examined organizations and sites, verified organization writes, verified site writes, unchanged sites, and failures.
Track unprocessed sites after cancellation or failure.
Dry-run counts are planned counts, not successful writes.

## Validation

- Identifiers must be valid UUID strings.
- Model and version values must be nonblank strings and match available versions.
- Settings reads must return dictionaries with successful status codes.
- Version and inventory lists must be well formed. Missing records must not become success defaults.
- AP days must use the schema enumeration. Times must be `any` or valid 24-hour `HH:MM` values.
- Policy enablement requires an explicit operator choice.

## State transitions

Read and validate -> collect selections -> preview -> confirm -> save organization -> verify organization -> clear sites -> verify sites -> report.
Insert the complete backup gate after confirmation and before saving any organization.
Cancellation before confirmation and dry run perform no writes.
A failure after a write reports partial completion and stops that organization's remaining work.
