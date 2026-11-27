# Security Requirements Quality Checklist: Exported cell values stay out of DEBUG logs

**Purpose**: Check that the security requirements are complete before implementation.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Exposure

- [x] Each DEBUG statement that carries a cell value, device value, site address, or table is listed in `design/research.md`.
- [x] The four changed exporter files form the full set of changed log statements. Explained: a sweep covered value-like names in the exporting package. Residual statements outside the set are listed in D-8 and D-9.
- [x] Each changed message follows the forbidden content rule (`design/contracts/log-messages.md`).

## Redaction and Errors

- [x] Each parse failure logs the error type only (FR-008).
- [x] Each warning or error that carries exception text is listed, and its residual risk is recorded (D-8).
- [x] No suppression comment hides a finding (FR-015).

## Test Evidence

- [x] Each absence test uses synthetic marker values (FR-010, D-17).
- [x] The CSV round-trip test shows that the cell values remain in the file (SC-002).
- [x] The red run shows that six absence tests fail before the fix (T006).

## Operator Impact

- [x] The loss of the summary tables is recorded as a risk (D-4).
- [x] Old `data/script.log` files keep values, and the record warns operators (D-14).
- [x] The `--debug` flag and the log file path stay unchanged (FR-013).
