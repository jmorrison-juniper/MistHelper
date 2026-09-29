# Wiring Manifest: Spectrum RF Diagnostics

**Feature**: `specs/3570-spectrum-rfdiag/spec.md`
**Status**: Deferred to planning and implementation

## Purpose

This manifest records integration work that must happen after the core RF diagnostic package and unit tests are ready. It keeps the specify step bounded.

## Deferred Integration Items

- Menu 290 entry for the RF diagnostics operation.
- Operation registry entry for the RF diagnostics operation.
- Endpoint catalog review for spectrum analysis and RF diagnostic recording endpoints.
- Changelog fragment for the operator-facing feature.

## Guardrails

- Core behavior stays in `src/troubleshooting/rf_diagnostics`.
- Unit coverage stays in `tests/unit/troubleshooting/rf_diagnostics`.
- Integration edits must be planned before implementation starts.
- Request body tests must prove OpenAPI shape before wiring is enabled.
