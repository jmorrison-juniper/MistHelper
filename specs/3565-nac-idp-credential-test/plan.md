# Implementation Plan: NAC IDP Credential Test

**Branch**: `feat/3565-nac-idp-credential-test` | **Date**: 2026-09-29 | **Spec**: `specs/3565-nac-idp-credential-test/spec.md`

**Input**: Feature specification from `specs/3565-nac-idp-credential-test/spec.md`

## Summary

Add menu 285 through deferred wiring to validate one Mist Access Assurance identity provider credential. The owned package lists NAC identity providers from organization settings, prompts for a provider, username, hidden password, and confirmation, calls `validateOrgIdpCredential`, prints the verdict, and exports one password-free result row.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Standard library `dataclasses`, `getpass`, `json`, `logging`, and `time`; existing `mistapi>=0.64.0,<0.65`; existing `SourceDependencyResolver`; existing `DataExporter`.

**Storage**: `DataExporter.write_with_format_selection` writes `NacIdpCredentialTest.csv` under `data/` and can write the configured database backend.

**Testing**: `pytest` unit tests under `tests/unit/troubleshooting/nac_idp_credential_test/` with no network access.

**Target Platform**: MistHelper CLI and SSH container on Windows-compatible Python paths.

**Project Type**: Single Python CLI package under `src/troubleshooting/nac_idp_credential_test/`.

**Performance Goals**: Complete one provider list read and one validation call in the normal Mist API latency window. No polling is in scope.

**Constraints**: Do not log or export passwords. Ask `y` or `N` before sending the credential. Do not edit forbidden wiring files. Use `wiring.md` for integration values.

**Scale/Scope**: One interactive credential validation per run. Pagination for organization SSO uses the SDK page helper if the fallback SSO list is used.

## Constitution Check

- **Five-Item Rule**: Pass. The new package uses five module files or fewer, and each method stays small.
- **Class-Based Architecture**: Pass. Client, model, prompt, and operation logic live in classes.
- **Safety-First**: Pass. Text prompts use the existing safe input path. The password prompt uses hidden input.
- **Full Deployment Pipeline**: Deferred after local gates. This branch completes local gates, branch push, draft pull request creation, and CI handoff. The integration and release pipeline completes README, menu registration, CI, squash merge, main build, image verification, deployment, and health checks.
- **Observability & Logging**: Pass. The client logs before and after each API call with `%s` formatting and no secrets.
- **Output Backends**: Pass. The result uses `DataExporter.write_with_format_selection`.
- **Inline Comments**: Pass. Each executable line in the owned package includes an inline `WHY` comment.
- **Action Logging**: Pass. Prompts, API calls, data transforms, validation results, and exports log before and after actions without secrets.

## Project Structure

### Documentation (this feature)

```text
specs/3565-nac-idp-credential-test/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── client-contract.md
├── tasks.md
└── wiring.md
```

### Source Code (repository root)

```text
src/troubleshooting/nac_idp_credential_test/
├── __init__.py
├── client.py
├── model.py
├── operation.py
└── prompts.py

tests/unit/troubleshooting/nac_idp_credential_test/
├── __init__.py
├── test_nac_idp_credential_test_client.py
├── test_nac_idp_credential_test_model.py
└── test_nac_idp_credential_test_operation.py
```

**Structure Decision**: Use one nested troubleshooting package and one mirrored unit test directory. Menu registration stays deferred to `wiring.md`.

## Complexity Tracking

No constitution violation is planned.
