# Plan: Result Truncation Notice

## Source base

Use accepted commit `67a1ca625ab3526c68a8e54d1580dc1c92d3abc4`. The assigned worktree already starts at this commit. Do not rebase.

## Design

Keep clipping detection inside `OperationResults`. Inspect rendered visible table cells after each render and after observed layout changes. Use `scrollWidth` and `clientWidth` to identify actual overflow. Use one observer and one pending animation-frame callback at most. Invalidate pending work when the selected file or rendered data changes.

Keep `renderTruncationNotice` as the owner of the existing sort warning and the new clipping warning. Build notice text and controls with DOM text nodes. Each affected-row control must call the existing `toggleRow` behavior. Link to the existing `#outputFiles` element. Do not edit the template or stylesheet.

## Verification design

The end-to-end regression starts the real portal on an allowed loopback port. It invokes the actual registered safe menu 55 handler through the portal UI. A controlled Mist SDK transport returns only invented, documented OSPF records. The real exporter writes the CSV. The real preview route and browser render that file.

Use a short one-record control and the 30-record, three-page synthetic result. Compare CSV records and hashes with the accepted private qualification. Capture the response with Playwright `expect_response` before the action. Read the completed body and parse it outside event callbacks. Keep browser recording disabled.

The long-result test must fail against the unchanged renderer because the clipped-cell notice is absent. It must pass after the renderer change. Then verify row details, accessible controls, output link, short control, filtering, sorting, pagination, and a layout resize. The test must not fake the renderer, output, or pagination.

## Ownership and safety

Only the product JS file and the feature-scoped new paths listed in `spec.md` may change. Preserve all existing tests and their assertions. Do not use real Mist credentials, external services, stores, containers, production ports, or live output directories.

## Artifacts

Keep the original qualification, failed attempt, diagnosis, and corrective snapshot private receipts unchanged. Record red and green evidence in a new private session artifact. Use one release-note fragment. Do not edit `CHANGELOG.md`.
