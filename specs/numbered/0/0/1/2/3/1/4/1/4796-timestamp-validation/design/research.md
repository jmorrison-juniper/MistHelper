# Research: Timestamp validation

## Decision

Compare the parsed UTC value with the original timestamp label in the same fixed format.

## Rationale

PowerShell 7.7 and .NET parse `20261013-240000` as `20261014-000000`.
The comparison rejects this normalization and keeps existing date validation.

## Alternative

A separate hour range check would fix the reported value but would not detect other normalization.
