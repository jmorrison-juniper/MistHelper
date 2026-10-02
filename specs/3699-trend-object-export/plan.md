# Implementation Plan: Export documented trend objects

**Branch**: `jmorrison-juniper-documented-trend-object-export`

**Date**: 2026-10-02

**Spec**: [Feature specification](spec.md)

**Input**: `specs/3699-trend-object-export/spec.md`

## Summary

Repair the response boundary before the existing persistence path.
Both documented trend objects must retain one record.
Decide the real HTTP status before inspecting the payload.
Preserve the current operation tables, arguments, labels, filename construction, output helpers, and database metadata.

The completed owner publicly released both exact shared paths.
This owner's claim records that handoff before source edits.
The parent also approved the two reader files, checked native pages, and existing empty-array formatting.
The parent later approved explicit SLE-caller policy and a required typed response contract.
The parent grants local refresh only on accepted main `7a4435bdf8ceff7e1dd527e4d2fd854e79542f37`.
Publication remains blocked at position 44.

## Technical Context

**Language/Version**: Own Python `3.13.13` environment.

**Primary Dependencies**: Installed `mistapi 0.64.0`, Requests, pytest, and the pinned existing development tools.
Both manifests remain unchanged.

**Storage**: Existing `DataExporter.write_with_format_selection`.
Selected-output tests use only CSV and SQLite files under an owned temporary `data/` directory.
No production database router or container may initialize.

**Testing**: Actual SDK endpoint functions, actual `APIResponse`, controlled HTTP transport, and real normalization and output helpers.
Use independent literal expected records and byte comparisons.
Do not replace the endpoint, the response decoder, the flattener, or the selected writer with a successful stand-in.

**Target Platform**: macOS preparation, with unchanged Windows and Linux path behavior.

**Project Type**: Existing Python command-line operation and multi-backend exporter.

**Performance Goals**: No additional request for a non-paginated document.
Successful pagination must retain the same SDK links, call counts, and record order.

**Constraints**: Local commit only, exact reservations, visible failures, unchanged policy, and no secret disclosure.

**Scale/Scope**: Two documented operations within the existing 132-row family.
No menu count, category, schema, key, SDK constraint, generator, or reference change.

## Constitution Check

Reference: [Constitution](../../.specify/memory/constitution.md).

| Principle | Bounded treatment |
| --- | --- |
| Five-item discipline | Keep new packages at five children or fewer. Do not add another exporter method. Record existing parent debt. |
| Class-based design | A semantic response reader owns response acceptance and collection. It is not a facade, wrapper, or passive result with network methods. |
| Safety | Refuse unsuccessful or unusable responses before output. Keep real typed responses and safe exception context. |
| Export and keys | Retain the real `DataExporter`, flattening, escaping, and existing strategies. |
| Observability | Report the operation, status or exception type, checked-response count, and retained-record count. Do not print bodies or credentials. |
| Quality | Use the exact current CI scopes and unchanged test-quality policy. Prove guards fail. |
| Deployment | The explicit user restriction prohibits publication and deployment. Do not claim full deployment or constitution certification. |
| Documentation | Use only this private feature directory and one authorized release fragment. Shared guides remain unchanged. |

The constitution requests a complete deployment pipeline and a different commit format.
The current user authorization prohibits that pipeline and requires a Conventional Commit.
Record this conflict honestly without editing governance.
PowerShell is absent.
Do not run shared branch, feature-state, context-update, or automatic commit hooks.
Use the active templates directly in the explicit feature directory.
This is a bounded template-equivalent procedure, not a claim that those hooks executed.

### Existing structural debt

`src/export/`, `tests/unit/export/`, and `specs/` exceed five direct children.
`EndpointFamilyExporter` has 15 methods.
The existing family module contains large metadata tables.
The existing unit module contains many tests and fixtures.
Do not reorganize these unrelated children.
The proposed nested reader and test packages isolate this feature.
They still need the explicit placement grant because their existing parents are noncompliant.

Separate remediation should partition one exporter or test family at a time under its own issue and reservation.
This repair must not create that architectural program.

## Project Structure

### Documentation (this feature)

```text
specs/3699-trend-object-export/
  spec.md
  plan.md
  research.md
  tasks.md
```

The response contract and data model remain in this plan and the specification.
No shared `.specify` state or new guide is required.
Keep the complete offline PR template and generated evidence in the session artifact directory.

### Source Code (repository root)

| Path | Permission and responsibility |
| --- | --- |
| `src/export/endpoint_family_exporter.py` | Released. The real caller uses the semantic reader. |
| `tests/unit/export/test_endpoint_family_exporter.py` | Released. Coupled responses use native status, with genuine empty inputs. |
| `src/export/endpoint_family_response/__init__.py` | Approved minimal package documentation. No facade or re-export. |
| `src/export/endpoint_family_response/reader.py` | Approved owner of status, body integrity, collection, and normalization. |
| `tests/unit/export/trend_object_export/conftest.py` | Planned owned local transport and context fixtures. |
| `tests/unit/export/trend_object_export/documents.py` | Approved passive literal documents and independent expected records. |
| `tests/unit/export/trend_object_export/native_transport.py` | Approved controlled native transport and passive observations. |
| `tests/unit/export/trend_object_export/test_native_objects.py` | Planned native document and shape cases. |
| `tests/unit/export/trend_object_export/test_refusals.py` | Planned native status, wire, transport, and page refusals. |
| `tests/contract/export/trend_object_export/test_response_contract.py` | Planned metadata and negative guard proofs. |
| `tests/integration/export/trend_object_export/test_selected_output.py` | Planned actual CSV and SQLite output verification. |
| `changelog.d/issue-3699-trend-object-export.md` | Planned single release fragment with `Added` and `Fixed` scope. |

**Structure Decision**: Move response responsibility rather than adding a wrapper.
Move the existing normalization body into its approved semantic owner.
Update the real persistence caller and remove the obsolete exporter method.
Keep the normalization rules unchanged.
Do not retain a pass-through compatibility method.

## Response Contract and Data Model

The reader accepts a real SDK response and the active SDK session.
The operation identifier selects the documented object contract.
The SLE caller, not the generic reader, selects object permission.
The required typed contract carries the operation label and the explicit permission through each real caller.
Other callers pass an empty object policy.
Both trend operations permit a nonempty dictionary without `results` and without a next link.
Other existing collection behavior remains unchanged unless the parent approves a concrete coupled repair.

Status validation occurs first.
Only an actual integer in the successful HTTP range can proceed.
An absent, Boolean, string, mock, or unavailable status must not become `200`.
Refusal diagnostics contain no payload or URL value.

Reuse `ResponseIntegrityChecker` for a nonempty body that failed to parse.
An empty HTTP `200` wire body is a failure.
A real HTTP `204` remains an empty successful result.
Valid JSON empty containers remain empty results.
Keep SDK-supported list and `results` shape behavior.
An unsupported object next link must fail before output.

The native SDK currently collects a list error body's keys on a later-page refusal.
A checked traversal can use real `mistapi.get_next`, validate each page, and retain successful page order.
The parent approved that exact checked traversal before implementation.
Do not add header-total interpretation.
Do not replace SDK next-link construction.

The existing flattener drops empty arrays and expands nonempty classifier arrays.
The parent accepted that convention before implementation.
Do not add output fields, schema defaults, or primary-key context.
If the actual selected backend fails on a canonical object, report the exact gap before expanding scope.

## Validation Sequence

1. Establish live ownership, exact source release, and the updated public claim.
2. Record both native object failures before changing source.
3. Run both exact objects through the actual exporter and selected output.
4. Test realistic nested arrays and legitimate successful `error` fields.
5. Test list, `results`, empty, tuple, scalar, and actual native next-link controls.
6. Test first-page statuses, missing status, malformed JSON, empty wire, and transport failures.
7. Prove zero unintended callbacks, unchanged prior bytes, and zero `requests.Session.request` calls.
8. Prove both object and status guards detect an intentionally removed decision.
9. Run the complete affected existing suites from the predecessor.
10. Measure changed operational statements and branches.
11. Run configured compile, Ruff, Black, types, Bandit, complexity, docstrings, links, and quality checks.
12. Read all six quality inputs and check all three guides before each analyzer phase.
13. Compare the full candidate findings with the immutable full-base findings.
14. Explicitly analyze excluded native SDK tests with `--include-mist-api`.
15. Preserve the complete 23-item PR template offline, with exact commands, results, and capability limits.
16. Commit only reserved paths, then prove the clean committed comparison.
17. Remove exact owned temporary resources and send the local full-SHA evidence to the parent.

No push, PR, workflow start, merge, automatic merge, production resource, or delivery-completion step occurs.

## Complexity Tracking

| Constraint | Why the bounded treatment is necessary | Rejected alternative |
| --- | --- | --- |
| Existing exporter has 15 methods | Move the real response responsibility into an authorized semantic owner. | Add unrelated exporter methods or an empty facade. |
| SDK pagination loses top-level objects | Select the documented object before paginated collection. | Copy another session's draft or change the SDK. |
| Native status may be unavailable | Reject with measured operation context. | Default to `200` for old doubles. |
| Later-page list refusal exports partial data | Obtain a concrete scope grant before stronger checked traversal. | Quietly broaden this issue or pretend the existing behavior is safe. |
| Shared state hooks write outside the reservation | Use explicit paths and active templates with honest hook limits. | Modify `.specify` state or run a shared branch script. |

## Local Design and Analysis Result

All 13 functional requirements have tasks and direct evidence.
The three user stories cover records, refusals, and preservation.
The source barrier and both reported behavior decisions are resolved.
No product ambiguity or unowned source migration remains.

The exporter has 14 methods after the complete normalization migration.
The reader has five methods.
Every new method has at most five parameters and 25 lines.
The existing noncompliant parent directories remain recorded debt.
The parent explicitly approved the bounded nested package placements.

The analysis uses the specification, plan, tasks, active templates, and unchanged constitution.
It does not execute the unavailable PowerShell procedure or write shared state.
The deployment and governance conflicts remain explicit.
No unqualified constitution, deployment, publication, or actual-main certification is claimed.

## Accepted Local Refresh and Generated References

The shared reader's initial operation-name lookup created false static edges in other families.
The exact in-memory difference disproved the initial source-line explanation.
The parent approved a real responsibility correction, not a generator exception.
The SLE caller now owns the two explicit names.
The generic reader contains no endpoint-name lookup or hidden permission default.
All 132 actual SDK operations execute in the policy matrix.
Only the two intended operations receive object permission.

The completed #3300 owner publicly releases exactly four generated pages.
This owner records that release before generation.
The safe pages and every other output remain read-only.
Before generation, all 18 expected outputs were compared in memory.
Only two released interactive-safe copies required a change.
Both existing generators run twice.
All 18 outputs and 1,477,279 bytes are identical after the second run.
All 16 other outputs remain unchanged.
The read-only guard accepts all 16 API pages for 293 menus.
Accepted menus 53/74/75/76 retain counts 5/4/4/5.
Menu 54 retains all 28 definitions.
Menus 264-268 retain their original endpoint sets and counts.

The original 776 preparation remains preserved as evidence.
The exact unfinished local tree remains at stash `9d96feb696df742bcda242ee4b439060168b873d`.
All 16 feature-file hashes matched after the own local refresh and exact stash restore.
Only the parent can grant future publication.
