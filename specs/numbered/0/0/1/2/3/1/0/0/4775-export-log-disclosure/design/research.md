# Research: Export Log Disclosure

## Decision

Log aggregate row and field counts instead of exported values.
Remove inventory tables from logs and retain the output files.
Do not include the address in a parse-failure message.
These inventory changes are blocked by the issue #4762 file hold.

## Rationale

Diagnostic logs can have a wider audience than exported data.
Counts retain useful progress information without the data values.

## Alternatives

Masking selected fields leaves other exported values exposed.
Disabling DEBUG logging does not protect an operator who enables it later.
