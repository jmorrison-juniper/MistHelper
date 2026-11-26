# Research: Preserve CSV Carriage Returns

## Decision

Keep carriage returns in the shared multiline helper. Escape them in the CSV writer on copied records.
Keep the existing line-feed conversion and pre-dispatch processing.

## Rationale

An audit found 69 helper calls in 53 source files. Many run before format selection, including
the SQLite writer. Escaping carriage returns there would put CSV presentation into non-CSV data.
Copying CSV records prevents the writer from changing its input.

## Alternatives

Changing the helper to emit `\r` directly would introduce escaped values into non-CSV paths.
Moving existing line-feed processing across every caller is a separate change.
