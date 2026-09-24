# Research: Clear Stale Operation Results

## Decision: Split clear and reveal actions

Rationale: `resetExecutionPanel()` currently clears stale content and reveals `#executionPanel`. Selection needs the clear behavior without the reveal behavior.

Alternatives considered: Calling `resetExecutionPanel()` from `selectOperation()` was rejected because it shows an empty panel for command-line-only selections.

## Decision: Keep the repair in static JavaScript

Rationale: The stale panel is a browser state defect. The server already returns correct parameter data for command-line rows.

Alternatives considered: A route change was rejected because no route owns the stale DOM state.

## Decision: Add a Playwright regression test

Rationale: The defect is visible only after browser state changes. A browser test proves that the old table and file list disappear.

Alternatives considered: A text search test was rejected because it cannot prove visible DOM state.
