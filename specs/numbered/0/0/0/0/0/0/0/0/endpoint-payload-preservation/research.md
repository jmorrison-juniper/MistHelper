# Research: Endpoint Payload Preservation

## Decision 1: Preserve only proven object shapes

**Decision**: Accept a non-empty top-level object only when the repository
OpenAPI specification or issue #3699 response evidence proves its shape.

**Rationale**: A generic object fallback would turn malformed or undocumented
responses into false export success. The specification names the summary and
classifier trend objects as the proven cases.

**Alternatives considered**:

- Treat every non-empty dictionary as one record. Rejected because it hides
  malformed responses and violates evidence-only response handling.
- Change the SDK pagination helper. Rejected because the SDK dependency and
  shared pagination contract must remain unchanged.
- Add direct HTTP requests. Rejected because the existing Mist SDK methods are
  available and direct transport would bypass SDK authentication and decoding.

## Decision 2: Keep pagination at the SDK boundary

**Decision**: Continue to use `mistapi.get_all` for lists and `results`
envelopes. Inspect the decoded response before or alongside pagination only
for a proven non-paginated object.

**Rationale**: Existing list order, following-page behavior, request arguments,
labels, filenames, and endpoint metadata are compatibility requirements.

**Evidence**: The current exporter calls the selected SDK method and then
passes its response to `mistapi.get_all`. Existing tests cover list, results,
paged-list, and paged-results fixtures.

## Decision 3: Make discarded payloads visible

**Decision**: Emit loud ASCII logging when a non-empty payload is discarded.
Include the operation, status, shape class, and record count. Do not log
credentials or secret values.

**Rationale**: A discarded valid object and a true empty result must not look
identical to an operator.

## Decision 4: Validate received versus written records

**Decision**: Count records after response-shape handling and count records
accepted by the output boundary. Treat a mismatch as incomplete output.

**Rationale**: The exporter can otherwise report success after losing records
between SDK collection and persistence.

## Decision 5: Preserve the parent manifest

**Decision**: Use the exact six parent paths as the implementation manifest.
Mark `src/foundation/support/refactors/endpoint_primary_key_strategies.py`
read-only and do not edit it.

**Rationale**: The user requires the parent boundary and explicitly excludes
the key-strategy module from this repair.

## Evidence inventory

| Evidence | Finding |
| --- | --- |
| Issue #3699 | Both documented trend responses are top-level objects without `results`. |
| Installed `mistapi` 0.64.0 | `get_all` collects lists and `results` envelopes, then returns zero records for these objects. |
| `EndpointFamilyExporter._normalize` | A dictionary can already become one normalized row. |
| Existing exporter tests | Generic pagination and empty-result behavior already have focused fixtures. |
| OpenAPI and endpoint documents | The summary and classifier trend fields are documented. |
| CI workflow | Mypy scans `src/`, `MistHelper.py`, `wsgi.py`, and the listed script packages. |
