# Implementation Plan: Certificate Expiry Report

**Branch**: `feat/3553-certificate-expiry-report` | **Date**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3553-certificate-expiry-report/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add menu 272 as a read-only organization certificate expiry report. The report will collect device
certificate expiry, organization certificate settings, NAC server certificates, SSO IdP
certificates, PSK portal IdP certificates, and CA certificates. It will normalize all sources into
one `CertificateExpiry.csv` file and one console band summary.

This fleet branch delivers the package, tests, release note, and wiring manifest. The integration
pull request must register menu 272 in `MistHelper.py`, `src/utils/operation_registry.py`,
`src/refactors/endpoint_primary_key_strategies.py`, `README.md`, and generated references before
the feature reaches release.

The package remains unregistered on this branch. `CertificateExpiryReport.run()` includes a runtime
guard that blocks export until the integration pull request adds the primary key strategy. No
production path can export rows without that strategy.

The implementation will use a class-based package at `src/reports/certificate_expiry/`. The package
will contain `client.py` for Mist API reads, `model.py` for dataclasses and pure normalization, and
`operation.py` for the static menu handler and export call. The operation will resolve the shared
session, organization, and exporter through `SourceDependencyResolver`, matching the pattern in
`src/security/rogue_dhcp/operation.py` and `src/marvis/actions/operation.py`.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, `cryptography`, and existing MistHelper
`DataExporter` and `SourceDependencyResolver` facilities. `requirements.txt` will receive an
explicit `cryptography` pin during implementation.

**Storage**: Multi-backend export through `DataExporter.write_with_format_selection()` with the
bare filename `CertificateExpiry.csv`. `DataExporter` resolves the effective path under `data/`.
The planned endpoint name is `certificate_expiry_report`.

**Testing**: `pytest` unit tests under `tests/unit/reports/certificate_expiry/`. Planned validation
also includes syntax, Ruff, Black, mypy, pydocstyle, Vulture, and interrogate checks for
`src/reports/certificate_expiry/` and `tests/unit/reports/certificate_expiry/`.

**Target Platform**: Windows local development and the existing Linux container runtime.

**Project Type**: Python CLI menu operation with CSV and configured database export.

**Performance Goals**: Complete one organization report with one bounded pass over each source.
Use paginated reads where the Mist endpoint declares pagination.

**Constraints**: The report is read-only. Its handler must run without prompts in unit tests, and
the integrated menu must run in `--test` without prompts after the integration pull request wires
menu 272. It must not log or export certificate bodies, private keys, or complete PEM text. It
must use `SourceDependencyResolver`, `DataExporter`, and platform-safe paths.

**Scale/Scope**: One organization, six certificate scopes, one CSV export, and one console summary.
The feature owns `src/reports/certificate_expiry/` and `tests/unit/reports/certificate_expiry/`
during implementation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence and planned control |
| - | - | - |
| Five-Item Rule | PASS | New code will use one nested package with no more than five direct module files. |
| Class-based architecture | PASS | `CertificateExpiryClient`, `CertificateExpiryRecord`, normalizer classes, and `CertificateExpiryReport` own the behavior. No wrapper functions are planned. |
| Safety-first input | PASS | The operation is read-only and must run without prompts in `--test`. No destructive flow exists. |
| Multi-backend export | PASS | `operation.py` will call `SourceDependencyResolver.DataExporter.write_with_format_selection()`. |
| Primary key strategy | PASS | `wiring.md` defines `certificate_expiry_report` before implementation. |
| Observability | PASS | Implementation must log before and after each Mist read, normalization pass, summary, and export. |
| Inline comments | PASS | Implementation must add same-line intent comments on all new executable code. |
| Secret handling | PASS | `model.py` will normalize metadata only and will never return PEM bodies or private keys. |
| Deployment pipeline | PLANNED | This step edits specification artifacts only. Code gates are planned for implementation. |

## Project Structure

### Documentation (this feature)

```text
specs/3553-certificate-expiry-report/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── cli.md           # Menu 272 and export contract
├── wiring.md            # Fleet contract for deferred wiring
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
src/
└── reports/
    └── certificate_expiry/
        ├── __init__.py
        ├── client.py       # Mist API reads only
        ├── model.py        # Dataclasses and pure normalization only
        └── operation.py    # Static run() handler, console summary, and export

tests/
└── unit/
    └── reports/
        └── certificate_expiry/
            ├── test_client.py
            ├── test_model.py
            └── test_operation.py
```

**Structure Decision**: Use one new package under `src/reports/` and one matching unit-test package.
The package separates external reads, pure normalization, and the static operation handler. This
keeps Mist API behavior mockable and keeps certificate parsing away from export code.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Not applicable. | Not applicable. |

## Phase 0 Research Summary

See [research.md](research.md).

Key decisions:

- Use `listOrgDevicesStats` with `type=all` for device `cert_expiry` epoch values.
- Use `getOrgSettings` for RadSec CA certificates, organization device certificates, and NAC
  server certificates.
- Use `listOrgCertificates` for organization CA certificate data. The assignment name
  `getOrgCertificates` maps to this verified OpenAPI and SDK operation.
- Use `listOrgSsos` and `listOrgPskPortals` for SAML IdP certificate fields.
- Treat `getOrgCrlFile` and `getOrgNacCrl` as metadata-only completeness sources because their
  schemas do not expose active certificate expiry rows. Successful reads create no CSV rows, and
  failed reads appear only in the failed-source summary.
- Use direct `cryptography` imports to parse PEM certificates. Pin the dependency in
  `requirements.txt` during implementation.

## Phase 1 Design Summary

See [data-model.md](data-model.md) and [contracts/cli.md](contracts/cli.md).

The design exposes one report contract:

1. Menu 272 runs the report without a prompt.
2. The report writes metadata-only rows to `data/CertificateExpiry.csv`.
3. The console summary reports all four bands.
4. The implementation omits certificate bodies and private keys from logs and output.

## Post-Design Constitution Check

| Gate | Status | Notes |
| - | - | - |
| Five-Item Rule | PASS | The planned package has four module files. |
| Class-based architecture | PASS | Each planned module owns classes, not wrapper functions. |
| Safety-first input | PASS | The operation is read-only and no prompt is required. |
| Multi-backend export | PASS | The operation contract requires `DataExporter.write_with_format_selection()`. |
| Primary key strategy | PASS | `wiring.md` defines the strategy for implementation. |
| Secret handling | PASS | `model.py` strips PEM bodies and private keys before export. |
| Testing | PLANNED | Unit tests will use synthetic fixtures and no network. |

## Planned Verification

These entries are planned for the implementation step, because this step edits only
`specs/3553-certificate-expiry-report/**`.

| Check | Planned command | Expected result |
| - | - | - |
| Unit tests | `python -m pytest tests\unit\reports\certificate_expiry` | All certificate report unit tests pass. |
| Syntax | `python -m py_compile MistHelper.py <each new .py file>` | No output. |
| Lint | `python -m ruff check src\reports\certificate_expiry tests\unit\reports\certificate_expiry` | All checks pass. |
| Format | `python -m black --check src\reports\certificate_expiry tests\unit\reports\certificate_expiry` | No file needs formatting. |
| Types | `python -m mypy src\reports\certificate_expiry --config-file pyproject.toml` | No type errors. |
| Docstrings | `python -m pydocstyle src\reports\certificate_expiry` | No docstring errors. |
| Dead code | `python -m vulture src\reports\certificate_expiry --min-confidence 70` | No findings. |
| Docstring coverage | `python -m interrogate -v src\reports\certificate_expiry` | At least 90 percent coverage. |
| Dependency security | `python -m pip_audit -r requirements.txt` | No vulnerabilities that block the pull request. |
