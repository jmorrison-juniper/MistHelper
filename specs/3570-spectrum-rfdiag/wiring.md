# Wiring Manifest: Spectrum RF Diagnostics

**Feature**: `specs/3570-spectrum-rfdiag/spec.md`
**Status**: Deferred until after the RF diagnostics package and unit tests are ready.

## Purpose

This manifest records integration work that must happen after the core RF diagnostic package and unit tests are ready. It keeps planning and package implementation bounded.

## Deferred Integration Items

- Add menu 290 entry for the RF diagnostics operation in `MistHelper.py`.
- Add the operation registry entry for the RF diagnostics operation in `operation_registry.py`.
- Add the endpoint primary-key strategy entry in `endpoint_primary_key_strategies.py`.
- Review and update endpoint catalog coverage for these Mist paths:
  - `POST /api/v1/sites/{site_id}/analyze_spectrum`
  - `GET /api/v1/sites/{site_id}/analyze_spectrum`
  - `POST /api/v1/sites/{site_id}/rfdiags`
  - `GET /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}`
  - `POST /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/stop`
  - `GET /api/v1/sites/{site_id}/rfdiags/{rfdiag_id}/download`
  - `GET /api/v1/sites/{site_id}/rfdiags`
- Add a changelog fragment for issue 3570.
- Update README or operation count only when menu integration is enabled.
- Update the generated menu reference only when menu integration is enabled.
- Update copilot-instructions category mappings only when menu integration is enabled.

These items are deferred to the integration pull request: `MistHelper.py`
registration, `operation_registry.py` registration,
`endpoint_primary_key_strategies.py` registration, README, generated menu
reference, and copilot-instructions category updates.

## Guardrails

- Core behavior stays in `src/troubleshooting/rf_diagnostics`.
- Unit coverage stays in `tests/unit/troubleshooting/rf_diagnostics`.
- Integration edits must be planned before implementation starts.
- Request body tests must prove OpenAPI shape before wiring is enabled.
- Do not edit `MistHelper.py`, `operation_registry.py`, README, changelog, or endpoint primary-key strategy files during this planning step.
