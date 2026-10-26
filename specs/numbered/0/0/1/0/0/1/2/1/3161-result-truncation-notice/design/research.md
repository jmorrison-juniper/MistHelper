# Research: Result clipping notice

## Decision

Measure `scrollWidth` against `clientWidth` for actual rendered data cells.
Keep the sort-limit warning independent.

## Rationale

The stylesheet uses `white-space: nowrap`, hidden overflow, an ellipsis, and `max-width: 18ch`.
The current notice reads only `sort_truncated`.
Text length cannot prove clipping because glyph width and available space vary.

## Alternatives considered

- A character threshold gives false positives and misses narrow layouts.
- Removing the width limit changes the shared layout and exceeds the file grant.
- A second preview or new exporter duplicates existing complete-value access.

## Limits

The issue artifact list endpoint returned HTTP 404.
The historical sample, menu timing, and earlier browser snapshot remain unavailable.
The current verification uses controlled temporary CSV output and the native preview endpoint.
