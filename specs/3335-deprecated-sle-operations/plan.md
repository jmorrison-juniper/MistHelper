# Implementation Plan: Remove deprecated SLE operations

**Branch**: `jmorrison-juniper-deprecated-sle-operations`

**Date**: 2026-10-01

**Issue**: [#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335)

**Spec**: [Completed specification](spec.md)

**Checklist**: [Completed requirements checklist](checklists/requirements.md)

**Input**: `specs/3335-deprecated-sle-operations/spec.md`

**Template**: [Active plan template](../../.specify/templates/plan-template.md)

**Status**: Metadata removal and local validation complete. The local commit is authorized. Publication remains blocked.

## Summary

Remove exactly `getSiteSleSummary` and `getSiteSleClassifierDetails` from three active registration sources.
Keep `getSiteSleSummaryTrend` and `getSiteSleClassifierSummaryTrend` on the existing exporter path.
Change the three fixed menu 263 labels from 17 to 15 operations.
Later, regenerate only the six reserved reference files and add the unique release fragment.

This is metadata removal, not a schema or data migration.
Do not change SDK resolution, prompts, normalization, export dispatch, key strategies, or persistence behavior.
Do not add production classes, wrappers, aliases, compatibility shims, or silent fallbacks.

The coordinator confirmed that #3335 covers offered replacement entries, not a shared response repair.
[Issue #3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699) records the separate documented trend-object defect.
Generic list and `results` fixtures prove unchanged SDK processing only.
They do not establish working exports of the documented trend objects.

This planning run writes only:

- `specs/3335-deprecated-sle-operations/plan.md`
- `specs/3335-deprecated-sle-operations/research.md`
- `specs/3335-deprecated-sle-operations/data-model.md`
- `specs/3335-deprecated-sle-operations/quickstart.md`
- `specs/3335-deprecated-sle-operations/contracts/endpoint-removal.md`

Resolve feature paths directly from the explicit directory.
Do not run the state-persisting PowerShell setup or agent-context scripts.
Do not create `tasks.md`, `.specify/feature.json`, or `.spec-context.json` in this run.

## Technical Context

**Language/Version**: Python 3.13 or newer. The prepared interpreter is Python 3.13.13.

**Primary Dependencies**: Installed `mistapi` 0.64.0, existing pytest and repository development tools.
Keep `mistapi>=0.64.0,<0.65` unchanged in both dependency declarations.
The parent completed environment setup. Do not reinstall packages or Chromium.

**Storage**: Existing `DataExporter` backends only.
Do not create, delete, migrate, rekey, truncate, or update persistent stores during planning.
Later database regressions use temporary test databases, not `data/mist_data.db` or external services.

**Testing**: pytest, real installed SDK functions, local HTTP transport mocks, and output-boundary mocks.
Change tests only in the two reserved test modules.
Run the existing portal, contract, key, upsert, and SLE-refusal selectors without edits.

**Target Platform**: Local macOS preparation, with existing Python portability for Windows and Linux.
No container or cloud operation is part of this design.

**Project Type**: Existing Python command-line application and web portal with endpoint-family exports.

**Performance Goals**: No new performance target.
Remove two metadata records from each active registration source.
Keep the existing execution and pagination costs for retained operations.

**Constraints**: Exact-name removal, real SDK evidence, fail-closed guards, unchanged dependencies and quality settings.
No historical-record cleanup, new guide, test-infrastructure expansion, or issue #3334 fingerprint work.

**Scale/Scope**:

| Set | Current | Required |
| --- | ---: | ---: |
| `_SITE_SLE_OPS` | 17 | 15 |
| `ALL_STAGE_TWO_ENDPOINT_OPS` | 134 | 132 |
| `ENDPOINT_CATALOG` | 286 | 284 |
| All selectable family rows | 286 | 284 |
| PK metadata, measured on this baseline | 571 | 569 |
| Top-level `MenuEntry` identifiers | 293 | 293 |
| Portal `MENU_DESCRIPTIONS` entries | 179 | 179 |

The PK total is measured evidence, not a new global ratchet.
Each guard must count its actual input.
All five neighboring family counts and memberships remain unchanged.

## Constitution Check

Reference: [Constitution](../../.specify/memory/constitution.md), version 1.5.0.
The explicit user limits control this isolated planning run and later publication boundaries.

| Gate | Before research | After design |
| --- | --- | --- |
| Structural discipline | Existing debt identified. Exact document layout requires the exception below. | Narrow metadata edits. No new production hierarchy or symbol. Test logic stays in the reserved modules. |
| Class-based architecture | Reuse `EndpointFamilyExporter`, `EndpointInfo`, and existing row classes. | Guard decisions belong to existing `TestCatalogCoverage`. No production wrapper or shim. |
| Safety-first input | Existing `InputUtils.safe_input` and selectors remain authoritative. | Tests supply console input, not replacement answer-handling methods. Cancellation remains unchanged. |
| Export boundary and keys | Preserve `DataExporter.write_with_format_selection` and all retained strategies. | Remove only two obsolete strategy registrations. No schema, migration, or new key. |
| Logging and comments | Preserve existing production logging. | The current user instruction requires rare meaningful comments and type safety. No obvious-action logs or per-line test comments. |
| Local quality gates | Read the actual workflow settings. | [Validation guide](quickstart.md) names the focused tests and exact required gates. No baseline or exclusion change. |
| Deployment and release | Metadata-only scope changes no exporter method. | The local commit is authorized after the required evidence. Publication, stores, containers, and cloud mutations remain blocked. |
| Documentation scope | Use the unique reserved feature directory. | No shared instruction, README, shared changelog, operator guide, or historical document edit. |

**Gate result**: Local metadata conformance is verified against the explicit user boundary.
Do not treat this result as an unqualified constitution certification.
The unchanged constitution does not express the current exact-path and rare-comment instructions.
The analysis records that policy conflict without changing the constitution or weakening a runtime gate.
Any full pipeline or governance certification remains conditional on its separate approval and evidence.

### Existing structural debt and separate remediation

Counts below came from tracked directory children and parsed source definitions.
The `specs/` count came from the current local directory inventory.
These are observations, not new suppression settings.

| Touched hierarchy | Existing debt | Bounded treatment | Separate incremental remediation |
| --- | --- | --- | --- |
| Repository root | 48 tracked direct children. `MistHelper.py` has 214 top-level definitions. | Change only the existing menu 263 title later. | Move one cohesive legacy menu group into a compliant nested package under a separate reservation. |
| `specs/` | 747 current direct children. | Reuse the already reserved feature directory. | Define a versioned archive layout for completed specifications in separate maintenance work. |
| Feature document root | The required completed layout has seven direct children, including `spec.md` and `checklists/`. | Keep the five exact user-requested paths. Do not create more artifacts. | Reconcile the shared Spec Kit document template with the five-child rule in separate governance work. |
| `src/export/` | 48 tracked children. The family module has 11 top-level definitions. The catalog module has nine. | Delete registrations within existing files. | Split one cohesive exporter family into a compliant nested package in a separate feature. |
| `EndpointFamilyExporter` | 15 methods. `_SITE_SLE_OPS` has 17 entries. The catalog has 286 entries. | Add no method. Remove only the two retired rows and catalog entries. | Separately partition metadata ownership by existing semantic family without changing runtime behavior. |
| `src/refactors/` and PK metadata | 33 tracked children. The merged PK dictionary has 571 entries. | Delete two supplemental entries. Preserve the existing `setdefault` behavior. | Separately move one strategy family into a compliant nested metadata package with equivalence tests. |
| Test placement | `tests/guardrails/` has 38 tracked children. `tests/unit/export/` has 45. The modules have eight and 20 top-level definitions. | Reuse both modules and existing test entry points where practical. No standalone helper wrappers or new infrastructure. | Separately organize one test family into a compliant package, without resetting the quality baseline. |
| `web_portal/` | Seven tracked children. `MENU_DESCRIPTIONS` has 179 entries. | Change only the existing label for 263. | Separately partition menu descriptions by existing categories without changing menu identity. |
| Documentation parents | `documentation/` has 58 tracked children, `wiki/` has 25, and `menu-api/` has eight. | Later update only existing reserved pages. | Separately archive obsolete documentation through the existing link and generator gates. |
| `changelog.d/` | 43 tracked children. The required unique fragment later adds one child. | This planning run creates no fragment. Its later exact path is an explicit release-policy placement exception. | Separately archive released fragments through the release coordinator. |

The exact feature-document and release-fragment paths are user requirements.
Moving them would break the reservation and create unauthorized shared work.
Required test additions also stay in the two explicit existing modules.
Use the existing semantic test class for private guard decisions.
Keep new methods typed, with at most five parameters, five logical blocks, and 25 lines.
Do not use an architectural cleanup to enlarge this issue.

## Project Structure

### Documentation for this feature

```text
specs/3335-deprecated-sle-operations/
  spec.md
  checklists/requirements.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/endpoint-removal.md
```

`spec.md` and the checklist are completed inputs.
The other five files are the only outputs of this planning run.
`tasks.md` belongs to a later phase and is not created here.

### Existing implementation surfaces

| Purpose | Reserved later paths |
| --- | --- |
| Selectable rows | `src/export/endpoint_family_exporter.py` |
| Catalog entries | `src/export/endpoint_catalog.py` |
| PK registrations | `src/refactors/endpoint_primary_key_strategies.py` |
| Fixed labels | `MistHelper.py`, `web_portal/menu_registry.py`, `documentation/menu-highlights.md` |
| Changed tests | `tests/guardrails/test_endpoint_catalog.py`, `tests/unit/export/test_endpoint_family_exporter.py` |
| Generated wiki references | `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md` |
| Generated operation maps | `documentation/menu-api/README.md`, `documentation/menu-api/interactive-safe.md`, `documentation/wiki/Menu-API-Endpoints.md`, `documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md` |
| Unique release fragment | `changelog.d/issue-3335-deprecated-sle-operations.md` |

**Structure decision**: Keep the existing semantic owners and edit only their metadata.
The full 23-path reservation remains in [the specification](spec.md) and the linked issue comment.
That reservation does not authorize implementation edits during this planning run.

## Phase 0: Research Result

[Research](research.md) resolves removal precision, SDK behavior, test boundaries, keys, generation, and gate selection.
No dependency discovery, replacement API, new production type, or store design is needed.
The installed SDK supplies both trend functions.
Its real pagination helper accepts list responses and dictionaries with `results`.
Do not change that behavior to manufacture export success for other response shapes.
The documented trend objects have no `results` field and currently produce zero collected records.
The separate issue owns that defect.

## Phase 1: Design Result

- [Data model](data-model.md) records existing registrations, keys, export records, and menu metadata.
- [Endpoint-removal contract](contracts/endpoint-removal.md) defines exact removal and retained behavior.
- [Validation guide](quickstart.md) gives later commands and expected evidence.

The post-design constitution check is complete.
No agent-context update or shared feature-state update is part of the design.

## Phase 2: Bounded Implementation Sequence

### 1. Establish real red evidence

In `TestCatalogCoverage`, add one private typed guard decision and one parameterized regression test.
The class currently has three methods. Those additions can keep it at five.
Inspect actual selectable row objects, the actual catalog, and the actual PK mapping.
For each source, assert absence of each exact retired identifier directly.
Run all six live-source cases before removing registrations.
They must fail because the identifiers are present, not because a fixture is empty or a count was guessed.

Keep these assertions after removal.
Separately inject each retired registration into a copy of each real source.
All six direct guard decisions must reject it and report the actual nonzero inspected count.
Empty, missing, invalid, and unreadable required input must reject, including partial-read failures.
Do not patch global registration tables, scan the entire repository for forbidden strings, or skip unreadable sources.

### 2. Remove only the registrations and correct the coupled labels

Delete the two `_EndpointFamilyOp` rows from `_SITE_SLE_OPS`.
Delete the two `EndpointInfo` entries from `ENDPOINT_CATALOG`.
Delete the two supplemental PK entries, without changing the surrounding merge.
Do not change `_resolve`, `_choose`, `_collect_arguments`, `_normalize`, `_persist`, or `_run`.

Change only `(17 operations)` to `(15 operations)` in the three fixed menu 263 labels.
Keep the top-level menu identifiers, handlers, categories, and safety flags.
Update only the coupled test expectations: SLE 15, stage two 132, and catalog 284.
Neighboring family expectations remain 7, 33, 61, 10, and 6.

### 3. Prove retained SDK invocation and unchanged generic processing

In the existing exporter test module, exercise both real SDK functions through the real exporter path.
Use an existing `AppContext`, a real `mistapi.APISession`, and temporary local site input.
Supply answers at the console input boundary.
Mock only the session's local HTTP transport and the final output boundary.

Keep SDK resolution, SDK endpoint methods, `mistapi.get_all`, required-answer collection, normalization, flattening, and escaping real.
Assert exact function identity, URI, arguments, normalized records, filename, and `api_function_name`.
Use literal expected records, not the production normalizer to compute the expected value.
Each real response fixture must include status, JSON body, URL, and prepared request headers.
Require no SDK error log on a successful journey.
Check empty results and blank, EOF, or interrupted required answers.

Repeat both trend journeys with both deprecated SDK attributes temporarily deleted.
Restore those two attributes automatically after each case.
This is an absence simulation within SDK 0.64.0, not a dependency upgrade.
Do not use the existing broad fake helper as proof of the real trend journeys.
These generic fixtures are not the documented object responses.
Do not claim that they prove the separate output defect is repaired.

Assert both retained strategy dictionaries exactly.
Repeated local trend runs must pass the same records and operation identifiers to the writer.
Do not add a new natural key, unique constraint, or trend deduplication mechanism.
Existing temporary-database upsert tests provide regression evidence for their existing key strategies.

### 4. Run the unchanged regressions

Run both portal label and required-answer modules unchanged.
Run the export-routing contract, configured key and SQL strategy selectors, and existing temporary SQLite upsert tests.
Run `test_a_refused_insight_request_names_the_http_status` unchanged for issue #3305.
The focused selector list is in [quickstart.md](quickstart.md).
Do not expand test infrastructure or repair hundreds of old ratchet findings.

### 5. Renew ownership, then generate within the reservation

Before later generation, read all currently open PRs and every paginated exact file list again.
Include renamed paths and verify each list's size against `changed_files`.
Recheck the issue claim and reservation.
Stop on overlap, incomplete reads, or a changed PR set or head during the check.

Run the wiki generator twice and compare both file contents in memory.
Run the API-map generator twice and compare all six reserved generated files.
Run the API-map `--check` mode.
Do not use `--refresh-sdk-index`.
If any generator changes a path outside the six reserved outputs, stop and report it.
Do not include the unexpected file or automatically restore another worker's changes.

Then add the unique release fragment.
Describe both exact removals and both retained trend operations.
Do not edit the shared changelog or add another guide.

### 6. Complete local gates and stop before publication

Run the exact commands and acceptance checks in [quickstart.md](quickstart.md).
They include full Ruff and Black, exact CI mypy paths, configured Bandit and its exclude check,
the unchanged test-quality configuration and baseline, deterministic generation, Markdown links, STE minimum 80, and runtime audit.

The strict macOS audit alternative uses this worktree's own hashed runtime lock.
It does not audit Git-only development tools, change dependencies, or ignore advisories.
Keep those development tools stated separately in the evidence.

The coordinator authorizes one validated local metadata commit.
Stage only the exact reserved paths after the local evidence and analysis disposition are recorded.
Do not fetch, rebase, push, open a PR, merge, build, deploy, or change a store before separate authorization.
Use Conventional Commits and the Copilot trailer:

```text
chore(export): remove deprecated SLE operations

Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>
```

The parent owns queue position 16 after issue #3366.
Only the parent can release publication.
A passing local gate or a later local commit is not that release.

## Live Reservation Evidence

The read-only check completed at `2026-10-01T17:33:21Z`.
Authentication was `jmorrison-juniper`.
Issue #3335 remained open, assigned to that user, with `chore`, `src`, `tests`, and `in-progress` labels.
The reservation matched all 23 exact paths in the specification.
Its session was `d36ec015-9c4f-4a76-987a-d64f58df8e87`.

All 12 open PR file lists were complete and stable, with 103 file entries and zero reserved-path overlaps.
The check covered the five design files and the six later generated files.
The PRs were #3621, #3624, #3625, #3626, #3627, #3628, #3629, #3630, #3632, #3633, #3670, and #3687.
Later implementation generation still requires a fresh check.

## Planning Validation Evidence

All five new design files were read directly with the existing Markdown file parser.
No local link or anchor failure was found.
Seventeen documented existing pytest selectors were checked against their actual files and symbols.
The mypy path string matches the current CI setting exactly.
All existing tracked files remain unchanged.
The completed spec and checklist were not edited.

The configured STE run passed the current minimum of 80 for all five files.
Its optional `data/ste_dictionary.json` input was unavailable.
The tool reported partial coverage and skipped dictionary checks.
Do not claim full dictionary coverage or generate a shared dictionary during this isolated phase.
Implementation tests, generators, code gates, and dependency audits were not run.

## Complexity Tracking

| Exception | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Required seven-child feature document layout | The user reserved five exact design paths beside completed inputs. | Moving documents would violate the explicit reservation and require shared template changes. |
| Required test placement in existing overfull modules | The user limits changed tests to two existing files and requires substantive regression cases. | A new test package or helper framework would expand the reservation and add unnecessary infrastructure. |
| Later unique fragment in overfull `changelog.d/` | The spec and release policy require the exact unique fragment. | Editing the shared changelog or moving the fragment is not authorized. |

These exceptions do not authorize broader code or hierarchy changes.
Each debt item has a separate remediation action above.
Planning ends with the five completed design files.
