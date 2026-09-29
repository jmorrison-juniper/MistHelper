# Implementation Plan: Client Device Fingerprint Census

**Branch**: `feat/3569-client-fingerprint-census` | **Date**: 2026-09-29 | **Spec**: `specs/3569-client-fingerprint-census/spec.md`

## Summary

Add menu `289` as a deferred wiring entry for a site-scoped client fingerprint census. The new package prompts for one site and one OpenAPI distinct field, calls the Mist fingerprint count endpoint, prints the top 20 rows, and writes `ClientFingerprintCensus.csv` through the shared exporter.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, existing `SourceDependencyResolver`, existing `DataExporter`  
**Storage**: CSV and configured export backends through `DataExporter.write_with_format_selection`  
**Testing**: `pytest`, `ruff`, `black`, `mypy`, `pydocstyle`, `vulture`, `interrogate`  
**Target Platform**: Windows and containerized MistHelper runtime  
**Project Type**: MistHelper menu operation package  
**Performance Goals**: One Mist count call per run. Console output limited to 20 rows.  
**Constraints**: Edit only owned files. Put shared-file changes in `wiring.md`. No network calls in tests.  
**Scope**: One menu operation, one new package, one new unit-test directory, one release-note fragment.

## Constitution Check

- **Safety**: The operation is read-only and uses the `interactive_safe` category because it prompts for a site and a field.
- **Observability**: The client, model, and operation log before and after meaningful actions.
- **Structure**: The feature uses a client module, a model module, and an operation module.
- **Fleet contract**: Shared-file registration stays in `wiring.md`.
- **Simplified Technical English**: User-facing text uses short, direct sentences.

## Project Structure

```text
specs/3569-client-fingerprint-census/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  wiring.md
  contracts/client-fingerprint-census.md
src/reports/client_fingerprint_census/
  __init__.py
  client.py
  model.py
  operation.py
tests/unit/reports/client_fingerprint_census/
  __init__.py
  test_client_fingerprint_census_client.py
  test_client_fingerprint_census_model.py
  test_client_fingerprint_census_operation.py
changelog.d/issue-3569-client-fingerprint-census.md
```

## Phase 0 Research

Research covers OpenAPI shape, SDK function availability, existing count-export patterns, and NAC/AIOps context. See `research.md`.

## Phase 1 Design

The data model holds normalized census rows and display rows. The contract describes the menu handler and the deferred wiring. See `data-model.md` and `contracts/client-fingerprint-census.md`.

## Phase 2 Implementation

1. Create pure model helpers for enum values, row normalization, sorting, and top-row selection.
2. Create a client class that wraps the SDK site-scoped function and returns normalized response dictionaries.
3. Create `ClientFingerprintCensus.run()` for prompts, API call, console table, and export.
4. Create unit tests for the model, client, operation, empty response, and OpenAPI enum.
5. Create `wiring.md` and the release-note fragment.

## Risk Log

| Risk | Decision |
| - | - |
| The assignment names `mfg`, but the count OpenAPI enum omits it. | Use the OpenAPI enum and record the mismatch in research. |
| The OpenAPI operation ID says `countOrgClientFingerprints`, but the installed SDK exposes `countSiteClientFingerprints`. | Use the SDK site alias because the path is site-scoped. |
| Shared menu files are not editable in the fleet branch. | Defer each shared-file change to `wiring.md`. |
