# Result Truncation Notice

## Problem

The operations result table shortens long cell values with an ellipsis. The current warning only reports incomplete sorting. A reader can miss that a cell value is shortened.

## Goal

Show a visible notice when a rendered result cell clips its value. Give the reader an accessible control that opens the affected row details. Point the reader to the existing Output Files panel for the complete file.

## Non-goals

- Do not change the result summary text.
- Do not change the table styles, template, operation handler, exporter, or output file.
- Do not change sorting, filtering, pagination, row details, or downloads.
- Do not recreate or claim the unavailable historical 124.69-second run.
- Do not change the issue 3311 data preview.

## Requirements

1. Detect clipping from rendered cell geometry. Do not infer clipping from text length.
2. Show a clear notice when one or more visible table cells clip their values.
3. Preserve the existing sort-truncation warning and its state.
4. Add accessible controls for affected rows. Each control opens the existing full row detail.
5. Point to the existing Output Files panel and preserve the complete CSV download link.
6. Recheck clipping after result data changes and table layout changes.
7. Cancel stale scheduled checks and prevent duplicate event handlers.
8. Do not report a clipped value from another page or file.
9. Keep cell text, row details, output bytes, and download bytes unchanged.
10. Prove the actual registered safe menu 55 operation with controlled synthetic SDK responses and the real browser renderer.
11. Prove one short value has no clipping notice.

## Acceptance criteria

- A 246-character value in a 181-pixel result cell produces a visible notice.
- The notice identifies the affected row and opens that row's existing details.
- The notice links to the Output Files panel, which keeps the complete CSV link.
- The notice updates after paging, sorting, filtering, and resizing.
- No notice appears when the visible cells do not clip.
- The existing sort-truncation notice remains visible with its existing message.
- Native test output has the same 30 records and bytes as the accepted private qualification.
- The short native control keeps its complete value and shows no clipping notice.
- The original private evidence files remain unchanged.

## Scope

Production file:

- `web_portal/static/js/operation_results.js`

New test and feature files:

- `tests/support/result_truncation_notice/`
- `tests/e2e/result_truncation_notice/`
- `tests/unit/web_portal/result_truncation_notice/`
- `specs/3161-result-truncation-notice/`
- `changelog.d/issue-3161-result-truncation-notice.md`

All other tracked paths are read-only.
