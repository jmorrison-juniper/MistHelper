# Console routing research

## Decision

Add a console-handler filter for records emitted by the existing direct-output helper.

## Rationale

The live SSH capture shows a plain menu row followed by its INFO log record.
The helper prints and logs each line. Bootstrap sends INFO records to the console by default.
SSH also omits the container's console threshold from its session file.
Filtering this one logger at the console handler preserves file records and unrelated diagnostics.

## Alternatives considered

- Carry the container logging thresholds into SSH. This does not prevent duplicates when INFO is intentional.
- Raise the default console threshold. This hides unrelated INFO diagnostics and does not cover debug mode.
- Remove helper logging. This loses the file copy.
- Remove helper printing. This hides menus when the console threshold is WARNING.

No unresolved design questions remain.
