# UI Contract: Clear Stale Operation Results

## Selection contract

When `selectOperation(menuNumber, element)` runs, the page must clear stale execution output before it loads parameters for `menuNumber`.

The selection contract includes these visible outcomes:

- `#outputFileList` has no list item from the prior run.
- `#resultsPanel` is hidden.
- `#logViewer` and `#debugLogViewer` are empty.
- `#progressBar` reads `0%`.
- `#statusBadge` reads `Pending`.
- `#executionPanel` is not revealed if it was hidden before selection.

## Run-start contract

When `runSelectedOperation()` starts a run, the page must reveal `#executionPanel` and clear all prior output.
