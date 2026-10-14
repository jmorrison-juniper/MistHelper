# Portal Contract: Cisco Config Converter

## Navigation and Page

- The converter appears as one navigation entry in the existing MistHelper web portal.
- The page contains input selection, gateway role and model selection, parsed input, conversion proposal, unsupported items, known gaps, export, and apply controls.
- Preview and export remain available without Mist credentials.
- Apply is unavailable until a valid organization and Mist session are available.
- Every new interactive control has a stable `data-testid`.

## Input

- Accept only the approved Cisco IOS configuration file type and verified existing portal size limit.
- Do not implement input-size checks until T004 records the current portal limit. If the current policy has no limit, stop and request an approved value.
- Reject empty files, invalid encodings, unsupported file types, and paths outside the configured input area.
- Treat a submitted file name as display text. Resolve file access under the configured input area.
- Do not place file content or credentials in logs or browser storage.

## Preview and Export

- Preview returns parsed items, proposed settings, unsupported items, and applicable known gaps.
- Unsupported items remain visible in the review and in the exported proposal.
- Preview and export do not make Mist API requests.
- Export contains proposed configuration data only. It does not contain credentials.

## Errors

- Invalid input returns a clear operator-facing error and makes no Mist API request.
- Conversion exceptions do not produce a partial proposal that appears complete.
- A failed or indeterminate apply result does not appear as a successful apply.
