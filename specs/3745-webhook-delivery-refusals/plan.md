# Implementation Plan: Webhook delivery refusals

**Branch**: `jmorrison-juniper-webhook-delivery-refusals` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3745-webhook-delivery-refusals/spec.md`

## Summary

Validate native response pages inside `OrgWebhookDeliveriesExporter` before normal empty-result or persistence paths.
Use the real SDK next-page operation after each accepted page.
Apply the same decision to directly coupled webhook discovery.
Retain the existing persistence method, selection values, output metadata, and standalone database warning.

## Technical Context

**Language/Version**: Python 3.13 or newer. The owned environment uses Python 3.13.13.

**Primary Dependencies**: Existing mistapi 0.64.0, Requests, pytest, and pinned misthelper-devtools 0.6.0.

**Storage**: Existing CSV and database selection. Native tests use only temporary CSV files.

**Testing**: New unit and native integration cases, unchanged related tests, and current repository gates.

**Target Platform**: macOS verification, with existing Windows and Linux path behavior unchanged.

**Project Type**: Menu-driven Python application.

**Performance Goals**: Read each successful SDK page once. Add no retry or live request.

**Constraints**: Only the exact granted paths may change. Do not accept missing status as HTTP `200`.

**Scale/Scope**: One existing exporter, two new test modules, this feature directory, and one release fragment.

The [public fixture release](https://github.com/jmorrison-juniper/MistHelper/issues/3745#issuecomment-5965269231)
also permits two success-fixture corrections in `tests/unit/export/test_org_webhook_deliveries_exporter.py`.
Only the discovery and delivery success fixtures receive concrete successful response fields.
All original assertions, case identifiers, order, aliases, and failure contracts remain.

## Constitution Check

The explicit local-only grant overrides deployment and shared-state hooks for this preparation.
PowerShell is absent. The current templates provide the feature-only specification, plan, and tasks.
No shared `.specify` state, Git hook, branch creation script, or automatic commit runs.

The existing exporter owns four methods. A nested response class keeps response validation in the same semantic owner.
New response methods retain the five-parameter, five-block, and 25-line limits.
A passive refusal exception contains no I/O or parsing behavior.
The existing selection and persistence identities remain available without a compatibility alias.

The granted test filenames enter existing noncompliant test directories.
This explicit reservation does not authorize a directory restructure.
Future structural repair needs its own issue and reservation.
The existing selection and delivery methods have 18 and 24 lines.
The implementation must retain bounded methods without changing outside callers.

## Project Structure

### Documentation (this feature)

```text
specs/3745-webhook-delivery-refusals/
├── spec.md
├── plan.md
├── tasks.md
├── design/
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   └── response-contract.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/export/org_webhook_deliveries_exporter.py
tests/unit/export/test_org_webhook_response_refusals.py
tests/unit/export/test_org_webhook_deliveries_exporter.py
tests/integration/export/test_org_webhook_native_refusals.py
changelog.d/issue-3745-webhook-delivery-refusals.md
```

**Structure Decision**: Keep the product repair inside the reserved class. Separate feature design documents to retain five directory children.

## Phase 0: Research

[Research](design/research.md) records the actual SDK status, body, and pagination contract.
Four unchanged-source native cases establish separate delivery and discovery evidence.
The complete unchanged-base analyzer report preserves current findings and related-source identities.

## Phase 1: Design

[The response contract](design/response-contract.md) defines acceptance, refusal, and pagination.
[The data model](design/data-model.md) contains no persistent state or schema change.
[The quickstart](design/quickstart.md) defines the local validation commands.

Search existing response integrity helpers before adding a body check.
Reuse `ResponseIntegrityChecker` for the SDK's retained malformed-body signal.
Add explicit blank-body, status, array-shape, and page-link decisions in the exporter.
Do not import the unpublished reader from issue #3699.

Collect accepted rows in memory. Write only after every page passes.
Use `mistapi.get_next` directly so each returned page receives the same validation.
Do not call unchecked `get_all` across later pages.
Use a passive refusal exception for safe known validation reasons.
Report unexpected reader failures by exception type without exposing untrusted exception text.

## Phase 2: Verification

Use actual SDK operations, actual `APIResponse`, controlled Requests transport, actual persistence, and actual CSV output.
Count forbidden external boundaries and close all native sessions and responses.
Keep operator setup and temporary output separate.
Prove new failure guards against the unchanged source or a bounded actual-source mutation.

Run the smallest affected selectors before related exporter and SDK contract scopes.
Measure exporter statement and branch coverage precisely.
Run current compile, Ruff, Black, CI mypy scope, security, complexity, and docstring gates.
Run the six-input and three-guide preflight before unchanged full and clean committed-scope quality ratchets.
Run explicit `--include-mist-api` analysis on the actual new native module.
Compare original test membership, order, assertions, hashes, and current inferred source applicability.
Report an induced outside-file obligation before any outside edit.

The licensed STE dictionary is absent unless an owned check proves otherwise.
Heuristic STE coverage must not claim complete vocabulary coverage.
The normal macOS bootstrap failed in copied-interpreter `ensurepip` with `SIGABRT`.
The supported UV recovery changes only the owned ignored environment.
An audit resolver failure must remain a failure. A separate runtime alternative must state its exact scope.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing test directory child counts exceed five. | The user grants two exact new filenames. | Moving existing tests would exceed the reservation. |
| Native transport evidence needs test-specific lifecycle support. | Native sessions, Responses, and real output need direct measurement. | A fake paginator or writer would not prove the response defect. |

No wrapper, facade, compatibility alias, suppression, baseline update, dependency change, or shared-state edit is permitted.
