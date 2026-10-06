# Implementation Plan: Endpoint Payload Preservation

**Branch**: `endpoint-payload-preservation` | **Date**: 2026-10-06  
**Issue**: [#3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699)  
**Spec**: [spec.md](spec.md)

## Summary

Preserve proven non-empty top-level response objects in the endpoint-family
exporter without changing the Mist SDK dependency, output backends, or key
strategy. The repair must keep list and `results` pagination behavior, expose
discarded payloads through loud logging, and compare received records with
written records during validation.

The red proof comes first. Tests must first fail on both documented SLE trend
objects because `mistapi.get_all` currently returns zero records for an object
without `results`. Implementation then adds the smallest response-shape branch
that preserves only proven object payloads and leaves unknown objects unchanged.

This plan does not implement code. It does not modify
`endpoint_primary_key_strategies.py`.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, pytest, requests response
fixtures, and the existing exporter utilities.

**Storage**: Existing CSV, SQLite, ArangoDB, and Redis output backends.
No schema or storage migration is required.

**Testing**: Targeted pytest tests under `tests/unit/export/` and the existing
endpoint-family, SDK compatibility, key, output, and guardrail selectors.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Python CLI export application with shared output services.

**Performance Goals**: Preserve current request, pagination, normalization, and
write costs. Add no unbounded retry or concurrency.

**Constraints**: Use existing `mistapi` methods and response decoding. Do not
use direct HTTP calls when the SDK method exists. Do not change dependencies,
schemas, primary-key strategies, menu registration, or output contracts.

**Scale/Scope**: Menus 263 through 268 expose 132 endpoint-family operations.
The measured scope contains 97 specification-proven object-payload losses.
The two SLE trend operations require literal object-shape proof.

## Constitution Check

*GATE: Pass before research and re-check after design.*

| Gate | Before research | After design |
| --- | --- | --- |
| Managed structure | Uses the existing numeric eight-level route and one feature directory. | Adds only feature-owned planning records. |
| Five-Item Rule | Existing `specs/` and source hierarchy debt is recorded below. | No new production hierarchy or module is planned. |
| Class architecture | Reuses `EndpointFamilyExporter` and existing test classes. | No wrapper, alias, adapter, or compatibility shim is planned. |
| Safety and secrets | Uses local mocked transport and no production credential. | Tests require secret redaction and safe failure evidence. |
| Mist transport | Uses the two existing SLE SDK methods and SDK response decoding. | Contract tests prove endpoint parity, authentication use, and pagination preservation. |
| Observability | Existing logging boundary remains authoritative. | Discarded non-empty payloads receive an explicit loud log with operation and shape evidence. |
| Output integrity | Uses the existing normalization and output path. | Received-versus-written counts must be equal before validation reports completion. |
| Dependency and schema | Keeps the current SDK range and stores. | No dependency, key strategy, or schema file is changed. |
| Validation | Reads the current CI commands and focused selectors. | Quickstart lists targeted tests and applicable gates. |

**Gate result**: Pass. The plan records the only allowed implementation
manifest and excludes `endpoint_primary_key_strategies.py` from edits.

### Existing structural debt and separate remediation

The repository has overfull root, `specs/`, source, and test directories.
This feature uses the required managed route and existing semantic modules.
Separate governance work must archive old specification records and partition
legacy exporter and test modules without changing this repair.

The feature directory also contains more than five required planning records.
That is a process-record exception required by Spec Kit and the user request.
Do not add `tasks.md` in this planning run.

## Parent Implementation Manifest

Retain the parent plan manifest exactly as the implementation boundary:

```text
src/operations/exporting/export/endpoint_family_exporter.py
src/foundation/support/refactors/endpoint_primary_key_strategies.py
src/foundation/support/utils/operation_registry.py
MistHelper.py
tests/unit/export/test_endpoint_family_exporter.py
tests/unit/test_pk_strategies.py
```

`src/foundation/support/refactors/endpoint_primary_key_strategies.py` is
explicitly read-only for this issue. No implementation or test change may
modify that file. The remaining manifest paths are the only permitted code
and test surfaces. Do not add a new production module or test helper.

## Design

### Response-shape decision

The exporter must distinguish these shapes:

1. A top-level list remains a list of received records.
2. A `results` envelope remains subject to existing SDK pagination.
3. A proven non-empty top-level object becomes one received record.
4. An empty list, empty `results`, or empty object remains empty.
5. An unknown non-empty object is not accepted from assumption alone.
6. An unavailable, malformed, or unsuccessful response keeps current safe
   non-raising behavior and error logging.

The proven object allowlist must contain the documented summary trend shape
with `start`, `end`, `sle`, and `classifiers`, and the classifier trend shape
with `start`, `end`, `metric`, and `classifier`. Recorded response evidence
from issue #3699 supplements the repository OpenAPI specification.

### Validation and logging decision

The response boundary must retain enough evidence to report whether the SDK
returned zero records because the response was truly empty or because a valid
object lacked `results`. A non-empty discarded payload must produce a loud
warning or error-level log with the operation, response status, shape class,
and discarded record count. It must not log secrets or full credentials.

The validation path must compare received records with written records. A
mismatch is an incomplete export, not a successful empty result. Tests must
assert both counts and the mismatch evidence.

## Red-Proof-First Implementation Order

1. Add targeted failing tests for the two literal documented SLE trend object
   shapes through the real SDK response decoder and exporter path.
2. Add failing tests for empty list, empty `results`, empty object, unknown
   object, unsuccessful response, malformed response, and discarded-payload
   logging.
3. Add failing tests for received-versus-written count mismatches.
4. Add failing tests that retain list and `results` pagination order, request
   arguments, labels, filenames, and `api_function_name`.
5. Add failing tests for both trend operations when deprecated SDK attributes
   are absent. Restore those attributes after every test.
6. Implement the smallest response-shape change in
   `endpoint_family_exporter.py`. Keep `_normalize`, flattening, escaping,
   output selection, and existing error handling compatible.
7. Run targeted tests and repair only failures caused by this issue.
8. Run unchanged regression selectors and applicable repository gates.

Do not begin implementation by changing production code. The first test run
must prove the current defect with a red result.

## Targeted Tests

The implementation phase must update only
`tests/unit/export/test_endpoint_family_exporter.py` within the parent
manifest's test surface. It must cover:

- Summary trend object preservation with exact literal fields.
- Classifier trend object preservation with exact literal fields.
- One received and one written record for each documented object.
- Top-level list preservation, including a valid following page.
- `results` envelope preservation, including a valid following page.
- Empty list, empty `results`, and empty object zero-record behavior.
- Unknown non-empty object rejection without assumption-based support.
- Loud logging for every discarded non-empty payload.
- Received-versus-written mismatch detection.
- Error status, malformed response, and non-raising behavior.
- Exact operation identity, endpoint URL, identifiers, labels, filename, and
  `api_function_name`.
- Deprecated SDK attribute absence for both retained trend operations.
- Secret redaction and successful authentication evidence.

`tests/unit/test_pk_strategies.py` remains a read-only regression selector.
It must not be edited, and `endpoint_primary_key_strategies.py` must not be
edited.

## Phase 0 Research Result

Issue #3699 records that SDK 0.64.0 decodes both trend objects correctly, but
`mistapi.get_all` returns an empty list because neither object has `results`.
The existing `_normalize` method can already represent each object as one row.
The loss occurs before normalization.

The repository test module already proves generic list and `results` dispatch,
empty-result behavior, cancellation, and exact writer arguments. Those tests
must be extended with documented object fixtures and count evidence.

The repository OpenAPI document and the two endpoint response documents are the
authority for proven shapes. No direct HTTP transport or dependency update is
needed.

See [research.md](research.md) for decisions and evidence.

## Phase 1 Design Result

- [data-model.md](data-model.md) defines payload, received record, written
  record, evidence, and validation entities.
- [contracts/endpoint-payload-preservation.md](contracts/endpoint-payload-preservation.md)
  defines the response-shape and logging contract.
- [quickstart.md](quickstart.md) defines targeted validation and applicable
  repository gates.

No agent-context update, source implementation, task list, dependency change,
schema migration, container action, or live Mist Cloud request is part of this
planning run.

## Complexity Tracking

| Violation | Why needed | Separate remediation |
| --- | --- | --- |
| Existing overfull source and test modules | The parent manifest reserves existing semantic owners. | Partition exporter and test families in separate refactoring work. |
| Required multi-file Spec Kit feature directory | The planning workflow requires separate research, model, contract, and validation records. | Reconcile the shared template with the five-item rule separately. |
