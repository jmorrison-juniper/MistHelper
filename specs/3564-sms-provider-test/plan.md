# Implementation Plan: Test the guest portal SMS provider

**Branch**: `feat/3564-sms-provider-test` | **Date**: 2026-09-29 | **Spec**: `specs/3564-sms-provider-test/spec.md`
**Input**: Feature specification from `specs/3564-sms-provider-test/spec.md`

## Summary

Add a new interactive menu operation for menu 284. The operation tests the guest portal SMS provider credentials for `Twilio`, `SMSGlobal`, or `Telstra`. It prompts for credentials with hidden input, asks for confirmation before sending, calls the matching Mist utility endpoint, and writes a credential-free result row to `SmsProviderTest.csv`.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, existing `SourceDependencyResolver`, existing `InputUtils`, and standard-library `getpass`  
**Storage**: `data/SmsProviderTest.csv` through `DataExporter.write_with_format_selection`  
**Testing**: Targeted pytest unit tests under `tests/unit/troubleshooting/sms_provider_test/`  
**Target Platform**: Windows development and Linux container runtime  
**Project Type**: Single-project Python CLI application  
**Performance Goals**: One API request per confirmed run  
**Constraints**: Hidden credential input, no secret persistence, no direct edits to menu wiring files  
**Scale/Scope**: One package, one test directory, one spec directory, one release-note fragment

## Constitution Check

### Pre-Research Gate

| Gate | Status | Notes |
| - | - | - |
| Five-Item Rule | PASS | The package has small modules for model, client, input, and operation. |
| Class-Based / No Wrapper | PASS | `SmsProviderTest` is the menu handler class, and helper classes hold focused behavior. |
| Safety-First Input Handling | PASS | Public prompts use `InputUtils.safe_input`; secret prompts use hidden input. |
| Logging / Observability | PASS | Client and operation code log actions and results without credential values. |
| Secret Safety | PASS | Credential fields stay in request bodies only and never enter export rows. |

### Post-Design Re-check

| Gate | Status | Notes |
| - | - | - |
| Five-Item Rule | PASS | The design keeps each class focused and testable. |
| Class-Based / No Wrapper | PASS | No standalone pass-through wrapper is planned. |
| Safety-First Input Handling | PASS | The confirmation prompt stops before any API request unless the answer is `y`. |
| Logging / Observability | PASS | The result summary logs status and provider only. |
| Secret Safety | PASS | Tests include log and row redaction checks. |

## Project Structure

### Documentation for this feature

```text
specs/3564-sms-provider-test/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── wiring.md
├── contracts/
│   └── sms-provider-test-contract.md
└── tasks.md
```

### Source code for this feature

```text
src/troubleshooting/sms_provider_test/
├── __init__.py
├── client.py
├── inputs.py
├── model.py
└── operation.py

tests/unit/troubleshooting/sms_provider_test/
├── __init__.py
├── test_sms_provider_test_client.py
├── test_sms_provider_test_model.py
└── test_sms_provider_test_operation.py
```

## Complexity Tracking

No constitution violations are present.

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| None | N/A | N/A |
