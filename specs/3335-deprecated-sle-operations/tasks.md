# Tasks: Remove deprecated SLE operations

**Issue**: [#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335).

**Reservation**: [Exact 23-path reservation](https://github.com/jmorrison-juniper/MistHelper/issues/3335#issuecomment-5936510347).

**Input**: [Specification](spec.md), [plan](plan.md), [research](research.md), [data model](data-model.md), [validation guide](quickstart.md), [contract](contracts/endpoint-removal.md), and [checklist](checklists/requirements.md).

**Active template**: `/Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-fictional-barnacle/.specify/templates/tasks-template.md`.
No task-template override, preset, or extension template takes precedence.

**Feature directory**:

```text
/Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-fictional-barnacle/specs/3335-deprecated-sle-operations
```

**Repository root for every command**:

```text
/Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-fictional-barnacle
```

**Status**: The metadata removal and local gates pass.
The coordinator confirmed offered-entry acceptance and authorized the validated local metadata commit.
The separate documented-object defect does not authorize a response change in this branch.
The explicit position-16 publication grant now names `df6889a40464db9dd7281765b5a58b993e33a7ed`.
Fresh PR checks, protected exact-head squash, and actual-main proof remain pending.

**Current Local Refresh Base**: `1a06f1516223a20eef715d91a32255e6219331db`.
The coordinator permits local rebase, generation, validation, and offline preparation only.
Issue #3366 and pull request #3727 retain the sole publication window.
The original preparation remains preserved at `623a48c88feb4cf5716f3986587f4971a51ffb6a`.

**Granted Publication Base**: `df6889a40464db9dd7281765b5a58b993e33a7ed`.
This sole publication and delivery grant supersedes the earlier local-only boundary.
The previous local refresh remains preserved at `bd962ceaa467b513cd2bac924135265bda3f80c6`.
No other child holds publication authority for this position.

## Execution and ownership rules

- Use this explicit directory. Do not discover a feature through shared context.
- Prefix shell commands with `rtk` or `rtk proxy`.
- Use the prepared `.venv`: Python 3.13.13 and installed mistapi 0.64.0.
  Do not install packages, rerun bootstrap, or replace Chromium.
- Do not invoke extra agents beyond the required SpecKit workflow.
  Do not run persisting setup, context, branch, or commit hooks.
- Phase 2 blocks every production edit, including fixed-label edits.
  Author all required tests first. Capture real red evidence before deleting a registration.
- The next implementation stage owns T001 through T027.
  The parent owns T028 through T037 after that stage returns its local handoff.
- The parent is session `d36ec015-9c4f-4a76-987a-d64f58df8e87`.
  It owns final independent validation, analysis, and the local Conventional Commit.
- Here, the parent is the coding session that supervises the SpecKit agents.
  The publication coordinator is session `6d71fd26-57c2-48c0-abc8-607af98f75d0`.
  Only that coordinator can release publication.
- Keep evidence in this file or the parent result. Do not add an evidence manifest, baseline, or shared context file.
- Check a task only after verification. Add `(delivered: exact/path)` and measured evidence.
  Combine evidence updates serially, even when independent work runs in parallel.
- If a gate fails outside this scope, stop and report it.
  Do not change dependencies, baselines, suppressions, exclusions, or unrelated code to obtain a pass.

## Exact change boundary

Only these 23 paths can enter the feature change or its local staging command:

```text
MistHelper.py
web_portal/menu_registry.py
src/operations/exporting/export/endpoint_family_exporter.py
src/operations/exporting/export/endpoint_catalog.py
src/foundation/support/refactors/endpoint_primary_key_strategies.py
tests/guardrails/test_endpoint_catalog.py
tests/unit/export/test_endpoint_family_exporter.py
documentation/menu-highlights.md
documentation/menu_reference.md
documentation/wiki/Menu-Reference.md
documentation/menu-api/README.md
documentation/menu-api/interactive-safe.md
documentation/wiki/Menu-API-Endpoints.md
documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md
changelog.d/issue-3335-deprecated-sle-operations.md
specs/3335-deprecated-sle-operations/spec.md
specs/3335-deprecated-sle-operations/checklists/requirements.md
specs/3335-deprecated-sle-operations/plan.md
specs/3335-deprecated-sle-operations/research.md
specs/3335-deprecated-sle-operations/data-model.md
specs/3335-deprecated-sle-operations/quickstart.md
specs/3335-deprecated-sle-operations/contracts/endpoint-removal.md
specs/3335-deprecated-sle-operations/tasks.md
```

Gate inputs outside this list are read-only.
Temporary test files and the documented local audit lock are not feature changes.
Never stage them or write to a production store.

Do not change `README.md`, `CHANGELOG.md`, `.github/copilot-instructions.md`, or `operator-guide.md`.
Do not change any manifest, quality setting, historical record, upstream reference, or SDK discovery index.
Do not create `.specify/feature.json`, `.spec-context.json`, or another feature-state artifact.
Do not perform an SDK discovery sweep or issue #3334 fingerprint work.

## Required invariants

Remove only the exact identifiers `getSiteSleSummary` and `getSiteSleClassifierDetails`.
Delete their two rows, two catalog entries, and two supplemental PK entries.
Do not match prefixes or add aliases, wrappers, shims, fallbacks, or production types.

| Surface | Before | After |
| --- | ---: | ---: |
| `_SITE_SLE_OPS` | 17 | 15 |
| `ALL_STAGE_TWO_ENDPOINT_OPS` | 134 | 132 |
| `ENDPOINT_CATALOG` | 286 | 284 |
| All ten selectable family tables | 286 | 284 |
| Observed PK mapping size | 571 | 569 |
| Top-level menu identifiers | 293 | 293 |
| Portal description entries | 179 | 179 |

The PK total is measured evidence, not a new global count rule.
Guard counts must come from inspected inputs.
Keep every unrelated row, key, description, and safety value unchanged.
Keep neighboring counts and full memberships: `SITE_MAP=7`, `SITE_DETAIL=33`, `ORG_DETAIL=61`, `MSP_DETAIL=10`, `OTHER_DETAIL=6`.

Retain both real functions from `mistapi.api.v1.sites.sle`:

| Operation | Required tuple | Issue |
| --- | --- | ---: |
| `getSiteSleSummaryTrend` | `site_id`, `scope`, `scope_id`, `metric` | 1217 |
| `getSiteSleClassifierSummaryTrend` | `site_id`, `scope`, `scope_id`, `metric`, `classifier` | 1213 |

Both trend strategies retain `type="auto_increment_with_unique"`, `primary_key=["misthelper_internal_id"]`, and `unique_constraints=[]`.
Summary indexes remain `["site_id", "scope", "scope_id", "metric"]`.
Classifier indexes add only `"classifier"`.
Each description remains `Endpoint family export for ` followed by its exact trend identifier.
Keep the supplemental `setdefault` merge and all earlier strategies unchanged.
Keep `mistapi>=0.64.0,<0.65` unchanged in both dependency declarations.

The coordinator confirmed that #3335 retains offered replacement entries, not verified canonical object exports.
[Issue #3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699) owns the separate existing trend-object output defect.
Preserve `_run` and the shared response behavior.
Generic list and `results` cases prove invocation and processing preservation only.

No schema, data, table, index, key, or store migration exists.
Do not delete stored deprecated-operation records or invent trend deduplication.
Preserve existing errors, logging, required-answer handling, and issue #3305 refusal.
Do not expose a token, credential, or secret in evidence.

## Structural debt record

The plan records existing debt and separate remediation.
This task list carries that record forward without adding remediation tasks to issue #3335.

| Existing debt | Bounded treatment | Separate maintenance direction |
| --- | --- | --- |
| Root: 48 tracked children. `MistHelper.py`: 214 top-level definitions. | Change only the menu 263 title. | Move one cohesive legacy menu group under a separate reservation. |
| `specs/`: 747 local children. Feature directory: seven children before this task file. | Reuse the reserved directory. The required task file makes eight children. | Reconcile document layout and archival policy in separate governance work. |
| `src/operations/exporting/export/`: 48 children. Family/catalog modules: 11/9 definitions. Exporter: 15 methods. | Delete existing metadata only. Add no production method. | Partition one semantic metadata family separately. |
| `src/foundation/support/refactors/`: 33 children. PK mapping: 571 observed entries. | Delete two supplemental entries only. | Partition one strategy family separately with equivalence tests. |
| Test directories: 38/45 children. Reserved modules: 8/20 top-level definitions. | Reuse both modules. Keep guard decisions in existing `TestCatalogCoverage`. | Organize one test family separately without resetting the baseline. |
| `web_portal/`: seven children. Description map: 179 entries. | Change one existing label. | Partition descriptions by existing category separately. |
| Documentation/wiki/menu-api parents: 58/25/8 children. | Update only reserved existing pages. | Archive obsolete pages separately through existing gates. |
| `changelog.d/`: 43 children before the required fragment. | Add only the unique reserved release fragment. | Archive released fragments through the release coordinator. |

The reserved document layout, existing test placement, and unique fragment are bounded placement exceptions.
Do not restructure a hierarchy to resolve them here.
New test methods must be typed and bounded: at most five parameters, five logical blocks, and 25 lines.
Use rare meaningful comments. The current user request overrides older per-line comment and obvious-action logging demands.
Do not broaden production logging or alter existing error behavior.

## Shared test contract

Phase 2 supplies shared acceptance tests for US1 through US4.
Each story phase then verifies its own complete behavior.
This placement makes red evidence a true prerequisite, not a test added after production removal.

Both reserved test modules must exercise all six exact-name/source combinations:
two retired identifiers multiplied by selectable rows, catalog keys, and PK keys.
Each module must also exercise all six controlled negative injections.
The exporter module can import the private `TestCatalogCoverage` decision through a non-collectable alias.
Do not duplicate the decision or create a helper module, wrapper class, or test framework.
Use `deprecated` in both modules' matrix test names and `menu_263` in the fixed-label test names.
The exact selectors below must collect the required cases.

Use actual raw sources for live absence assertions.
For negative injections, copy the real sources and inject one correctly shaped registration.
Before removal, remove retired entries only from those isolated injection copies.
Never use a cleaned copy as live absence evidence or mutate global registrations.
After removal, that copy preparation changes no live member.

Every decision must report acceptance, the actual inspected count, and exact findings or the read failure.
Empty, missing, malformed, and unreadable input must reject.
Test failure before the first read and after a partial read.
Partial failures retain the successfully inspected count.
Zero records never establish successful absence.

For trend journeys, use real `AppContext`, `mistapi.APISession`, SDK methods, response decoding, and pagination.
Supply console input at `builtins.input`.
Mock only the session's local HTTP `get` transport and final output boundary.
Use an empty local environment file, a `.test` host, and fresh temporary `data/SiteList.csv`.
Set the existing `MainEntrypoint.context` to the local test context and restore it automatically.
Restore all local test state and temporarily deleted SDK attributes after each case.
Real `requests.Response` fixtures must include status, JSON body, URL, and prepared request headers.
Require no SDK error log on successful cases.

Do not replace `_mist_helper`, `_choose`, `_resolve`, `_collect_arguments`, `_normalize`, `_persist`, `_run`, or `mistapi.get_all`.
Keep selectors, required-answer handling, flattening, escaping, and dispatch real.
Assert literal expected output, not output computed by the production normalizer.
The existing broad fake helper is not real trend evidence.

---

## Phase 1: Setup — existing environment and exact scope

**Purpose**: Establish local inputs and immutable comparisons without new infrastructure.

- [X] T001 Confirm the completed inputs, checklist, explicit root, and 23-path reservation. Record the scope and structural exceptions in `specs/3335-deprecated-sle-operations/tasks.md`. Keep all other feature documents unchanged. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E001)
- [X] T002 Capture pre-edit source and menu invariants from `src/operations/exporting/export/endpoint_family_exporter.py`, `src/operations/exporting/export/endpoint_catalog.py`, `src/foundation/support/refactors/endpoint_primary_key_strategies.py`, `MistHelper.py`, and `web_portal/menu_registry.py`. Record retained-member digests, counts, and dependency-file integrity in `specs/3335-deprecated-sle-operations/tasks.md`. Use local source comparisons, not a new baseline file. Record the parent-supplied 508-test four-module pass as prior evidence only. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E002)

**Checkpoint**: Inputs and scope are known. No bootstrap, installation, branch change, or source edit is needed.

---

## Phase 2: Foundational — all acceptance tests and real red evidence

**Purpose**: Block production edits until genuine failure evidence and preservation controls exist.

- [X] T003 Add one private typed guard decision and one parameterized regression entry point to existing `TestCatalogCoverage` in `tests/guardrails/test_endpoint_catalog.py`. Cover six live exact-name absence cases, six correctly shaped injections, and fail-closed empty/missing/invalid/unreadable inputs. Report measured counts, including partial-read counts. Set the coupled catalog expectation to 284. (delivered: `tests/guardrails/test_endpoint_catalog.py`, `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E003, E008)
- [X] T004 [P] Reuse that decision directly in `tests/unit/export/test_endpoint_family_exporter.py`. Add its six live absence cases, six negative injections, and zero/partial-read rejection assertions. Update only SLE and stage-two expectations to 15 and 132. Assert both exact retained row/strategy definitions and all neighboring memberships without rewriting unrelated tests. (delivered: `tests/unit/export/test_endpoint_family_exporter.py`, `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E004, E008)
- [X] T005 [P] Add fixed-label and complete menu-identity assertions in existing `TestMenuText` in `tests/guardrails/test_endpoint_catalog.py`. Read `MistHelper.py`, `web_portal/menu_registry.py`, and `documentation/menu-highlights.md`. Require the exact 15-operation title, 293 menu identifiers, 179 descriptions, and unchanged numbers, handlers, categories, safety, and fast-mode flags. (delivered: `tests/guardrails/test_endpoint_catalog.py`, `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E005, E008)
- [X] T006 Add real local `trend` journey cases in `tests/unit/export/test_endpoint_family_exporter.py`. Exercise both SDK functions through the real chooser, prompts, SDK, pagination, normalization, and writer dispatch. Cover list/results payloads, a next page, default empty queries, and direct optional `start`/`end`/`duration` queries. Assert real function identity, exact URI and argument order, literal flattened/escaped rows, exact filename, and original `api_function_name`. (delivered: `tests/unit/export/test_endpoint_family_exporter.py`, `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E006, E008)
- [X] T007 Extend the real `trend` cases in `tests/unit/export/test_endpoint_family_exporter.py`. Temporarily delete both deprecated SDK attributes and restore them after each case. Repeat both full journeys and exact writer payloads. Cover empty results, dictionaries without `results`, blank/invalid/EOF/interrupted answers, and invalid site selection. Require no trend request or writer on cancellation. Keep both retained PK dictionaries exact. (delivered: `tests/unit/export/test_endpoint_family_exporter.py`, `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E007, E008)
- [X] T008 Run G-RED and the pre-edit G-TREND controls against `tests/guardrails/test_endpoint_catalog.py` and `tests/unit/export/test_endpoint_family_exporter.py`. Record six genuine live-source absence failures per module, coupled count/label failures, and passing real trend controls in `specs/3335-deprecated-sle-operations/tasks.md`. Failures must name present identifiers and measured counts. Stop on collection, import, fixture, transport, or unrelated failures. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E008)

**Red checkpoint**: The same absence assertions remain for green execution.
The initial live counts are 286 selectable rows, 286 catalog entries, and 571 PK keys.
A skipped case, empty source, guessed count, or SDK error is not red evidence.
Retained-trend controls should already pass. Do not manufacture a failure in working trend behavior.

---

## Phase 3: User Story 1 — select supported SLE operations (P1, local MVP)

**Goal**: Remove exactly the two unsupported selections and their metadata.

**Independent test**: G-REM passes actual-source absence, full family membership, catalog agreement, and retained-key assertions.

**Tests first**: T003, T004, and T008 provide the real red contract.

- [X] T009 [P] [US1] Delete only the `getSiteSleSummary` and `getSiteSleClassifierDetails` rows from `_SITE_SLE_OPS` in `src/operations/exporting/export/endpoint_family_exporter.py`. Preserve every retained field and relative order. Keep all exporter methods and aggregate construction unchanged. (delivered: `src/operations/exporting/export/endpoint_family_exporter.py`; evidence: E012)
- [X] T010 [P] [US1] Delete only those two exact `EndpointInfo` entries from `ENDPOINT_CATALOG` in `src/operations/exporting/export/endpoint_catalog.py`. Preserve every retained description, safety value, and unknown-operation fallback. (delivered: `src/operations/exporting/export/endpoint_catalog.py`; evidence: E012)
- [X] T011 [P] [US1] Delete only those two exact supplemental PK registrations in `src/foundation/support/refactors/endpoint_primary_key_strategies.py`. Preserve both trend dictionaries, all unrelated strategies, earlier definitions, and the `setdefault` merge. Do not alter stored data or schemas. (delivered: `src/foundation/support/refactors/endpoint_primary_key_strategies.py`; evidence: E012)
- [X] T012 [US1] Run G-REM for `tests/guardrails/test_endpoint_catalog.py::TestCatalogCoverage` and `tests/unit/export/test_endpoint_family_exporter.py`. Confirm 15/132/284, both retained trends, and unchanged neighboring memberships. Compare source differences with T002. Record measured 284/284/569 guard inputs in `specs/3335-deprecated-sle-operations/tasks.md`. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E012)

**Checkpoint**: The metadata increment is independently verified.
This checkpoint does not authorize publication or omit coupled label work.

---

## Phase 4: User Story 2 — retain offered SLE trends (P1)

**Goal**: Prove offered entries and unchanged SDK invocation, generic processing, keys, updates, and refusal behavior.

**Independent test**: Both real trend journeys pass with and without deprecated SDK attributes.
The existing contract, key, dispatch, temporary SQLite, and issue #3305 selectors also pass.

**Tests first**: T006 and T007 existed and ran before T009 through T011.
No production edit belongs to this story.

- [X] T013 [P] [US2] Run G-TREND in `tests/unit/export/test_endpoint_family_exporter.py` after removal. Require nonzero cases for both real installed trend functions, exact requests/output, repeated dispatch equality, missing-attribute simulation, pagination, empty behavior, and required-answer cancellation. Confirm unchanged `mistapi>=0.64.0,<0.65`. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E016)
- [X] T014 [P] [US2] Run G-KEYS without edits to `tests/contract/test_export_api_function_names.py`, `tests/unit/db/test_database_schema_utils.py`, or `tests/unit/export/test_data_exporter.py`. Verify existing operation routing, configured keys, SQL generation, output selection, and polyglot dispatch. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E016)
- [X] T015 [P] [US2] Run G-UPSERT without edits to `tests/integration/test_menu_12_sqlite_upsert.py` and `tests/integration/test_menu_13_sqlite_upsert.py`. Use only their temporary databases. Confirm existing inventory/statistics update behavior, not a new trend uniqueness promise. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E016)
- [X] T016 [P] [US2] Run G-REFUSAL without editing `tests/unit/export/test_export_notice_separator.py::test_a_refused_insight_request_names_the_http_status`. Preserve the issue #3305 status, prior output, and no-writer behavior. Require no false success/empty notice or secret output. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E016)

**Checkpoint**: Preservation evidence covers real SDK execution and unchanged existing persistence contracts.

---

## Phase 5: User Story 3 — read accurate menu information (P2)

**Goal**: Synchronize existing labels and reserved references without changing menu identity.

**Independent test**: All three fixed labels state 15 operations.
Portal tests remain unchanged. All six references are deterministic and API `--check` passes.

**Tests first**: T005 and T008 established stale-label failures before production edits.

- [X] T017 [P] [US3] Change only `(17 operations)` to `(15 operations)` in the menu 263 title in `MistHelper.py`. Preserve its identifier, handler, category, non-destructive flag, and fast-mode flag. (delivered: `MistHelper.py`; evidence: E020)
- [X] T018 [P] [US3] Change only the same menu 263 count in `web_portal/menu_registry.py`. Preserve all 179 entries and every unrelated description. (delivered: `web_portal/menu_registry.py`; evidence: E020)
- [X] T019 [P] [US3] Change only the same menu 263 count in `documentation/menu-highlights.md`. Preserve menu numbering, neighboring rows, and safety text. (delivered: `documentation/menu-highlights.md`; evidence: E020)
- [X] T020 [US3] Run G-LABELS against `tests/guardrails/test_endpoint_catalog.py::TestMenuText` and the unchanged `tests/unit/web_portal/test_portal_label_accuracy.py` and `tests/unit/web_portal/test_portal_required_answers.py`. Require exact label agreement, unchanged menu identity, chooser order, browser flags, required controls, and existing read floors. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E020)
- [X] T021 [US3] Renew G-OWNERSHIP immediately before generation. Recheck issue #3335 and its exact reservation against all 23 paths. Read every paginated open-PR file list and renamed path. Verify `changed_files` and stable PR sets/heads. Record complete zero-overlap evidence in `specs/3335-deprecated-sle-operations/tasks.md`. Stop on overlap, incomplete reads, or changed ownership. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E021)
- [X] T022 [P] [US3] After T021, run the first G-GENERATE command pair for `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md`, `documentation/menu-api/README.md`, `documentation/menu-api/interactive-safe.md`, `documentation/wiki/Menu-API-Endpoints.md`, and `documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md`. Snapshot their resulting bytes in memory. Stop on any additional generated change. (delivered: `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md`, `documentation/menu-api/README.md`, `documentation/menu-api/interactive-safe.md`, `documentation/wiki/Menu-API-Endpoints.md`, `documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md`; evidence: E023)
- [X] T023 [US3] Run the same G-GENERATE pair again. Compare all six reserved reference files with the first-run bytes. Require equal wiki copies, exact retired-name absence in active maps, retained trends, menu 263 count 15, and API `--check` success. Record six byte-equality results in `specs/3335-deprecated-sle-operations/tasks.md`. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E023)
- [X] T024 [P] [US3] Add only `changelog.d/issue-3335-deprecated-sle-operations.md` after T021. Name both exact removals and both retained trend operations. State unchanged SDK constraint and no migration. Do not edit the shared changelog or add another guide. (delivered: `changelog.d/issue-3335-deprecated-sle-operations.md`; evidence: E024)

**Checkpoint**: Operator information agrees with source.
T021 cannot use the authoring check below as replacement generation evidence.

---

## Phase 6: User Story 4 — detect a deprecated registration (P2)

**Goal**: Prove that active-source checks reject each prohibited registration and cannot pass without reading valid input.

**Independent test**: Each reserved test module passes its six live absence cases and rejects all six injected registrations.
Each decision reports its actual count. Every empty or unreadable required input rejects.

**Tests first**: T003 and T004 authored the decisions and complete negative matrix before production edits.

- [X] T025 [US4] Run the direct `deprecated` matrix in both `tests/guardrails/test_endpoint_catalog.py` and `tests/unit/export/test_endpoint_family_exporter.py`. Require exact findings for all six injections per module. Measure live 284/284/569 and one-entry injection 285/285/570. Verify empty, missing, malformed, first-read failure, and partial-read failure rejection without global mutation or skips. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E025)
- [X] T026 [US4] Run G-ALL for both reserved test modules and both unchanged portal modules. Preserve every unrelated family/key/safety assertion and existing test floor. Record collected, passed, failed, and skipped counts in `specs/3335-deprecated-sle-operations/tasks.md`. Compare genuine red failures with the same passing green assertions. Do not substitute the earlier 508-test baseline for this result. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E026)

**Checkpoint**: All four stories have local acceptance evidence.
No deprecated-name repository sweep, migration, or unrelated repair is needed.

---

## Phase 7: Polish — local handoff and parent-owned completion

**Purpose**: Complete local preparation with independent validation and one bounded local commit.

- [X] T027 Prepare the implementation handoff in `specs/3335-deprecated-sle-operations/tasks.md`. Include exact changed paths, before/after invariants, red/green cases, both six-injection matrices, measured read counts, real SDK absence results, generator equality, and unchanged dependency/store evidence. Run G-DIFF. Return to the parent without staging, committing, fetching, rebasing, or publishing. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; evidence: E027)
- [X] T028 Parent only: independently run full G-CODE using unchanged `pyproject.toml`, including Ruff, Black, and syntax validation of `MistHelper.py`. Record exact exits and scope in `specs/3335-deprecated-sle-operations/tasks.md`. Do not narrow checks or perform unrelated formatting. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; E028, full Ruff passes and Black accepts 2,000 files.)
- [X] T029 Parent only: run G-TYPES with the exact CI targets `src/`, `MistHelper.py`, `wsgi.py`, `scripts/mist_ideas_analyzer_pkg/__init__.py`, and `scripts/mist_ideas_distiller_v2_pkg/__init__.py`. Keep `pyproject.toml` unchanged. Record results in `specs/3335-deprecated-sle-operations/tasks.md`. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; E029, 663 source files and both changed test files pass.)
- [X] T030 Parent only: run G-SECURITY with unchanged `pyproject.toml` and both separator samples for `src/foundation/support/utils/zen_city_metadata.py`. Require the exclude check and configured full Bandit scan. Record results in `specs/3335-deprecated-sle-operations/tasks.md`. Add no filter, suppression, or exclusion. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; E030, 786 file entries and 213,921 lines pass with zero findings.)
- [X] T031 Parent only: run full local G-QUALITY with unchanged `.github/test-quality-config.toml` and `.github/test-quality-baseline.json`. Include uncommitted test edits, not only HEAD-relative changed files. Record measured scope and findings in `specs/3335-deprecated-sle-operations/tasks.md`. Do not write, prune, or bypass the baseline. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; E031, 992 files checked and zero new findings.)
- [X] T032 Parent only: run G-LINKS and unchanged `tests/guardrails/test_markdown_links.py`. Directly parse all eight feature Markdown files plus `changelog.d/issue-3335-deprecated-sle-operations.md` with the installed checker's existing file parser. Require nine readable inputs and valid local links/anchors. Record results in `specs/3335-deprecated-sle-operations/tasks.md`. Do not stage files to obtain coverage. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; E032, 4,196 tracked files and nine new files pass.)
- [X] T033 Parent only: run G-STE for all listed feature documents, reserved changed operator pages, and `changelog.d/issue-3335-deprecated-sle-operations.md`. Keep `.ste-linter.toml` unchanged and require minimum 80. Report optional dictionary limitations explicitly in `specs/3335-deprecated-sle-operations/tasks.md`. Do not create a dictionary or allowlist. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; E033, all 23 paths pass with explicit partial dictionary coverage.)
- [X] T034 Parent only: run G-AUDIT against unchanged `requirements.txt`. On a standard macOS resolver failure, retain that output and use only this worktree's documented hashed runtime lock. Require a complete zero-advisory audit without installs or ignored advisories. Keep the lock outside the feature change. Record the separate Git-only development-tool scope in `specs/3335-deprecated-sle-operations/tasks.md`. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; E034, all 105 resolved runtime packages pass the strict hashed audit.)
- [X] T035 Parent only: independently rerun G-ALL, G-TREND, G-KEYS, G-UPSERT, G-REFUSAL, and API `--check`. Verify the six reference comparisons and G-OWNERSHIP evidence. If regeneration is necessary, renew ownership before G-GENERATE. Recheck exact source/menu/key differences with T002 and G-DIFF. Record independent results in `specs/3335-deprecated-sle-operations/tasks.md`. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; E035, 1,206 cases pass and the coordinator excludes the separately recorded object-output defect.)
- [X] T036 Parent only: execute the required `speckit.analyze` workflow for all eight feature documents under `specs/3335-deprecated-sle-operations/` and the bounded diff. Check every FR, VC, story, dependency, test decision, and structural exception. Record the analysis and approved scope disposition in `specs/3335-deprecated-sle-operations/tasks.md`. Do not widen the change or claim unqualified governance certification. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; E036 records all findings and the coordinator's metadata-only decision.)
- [X] T037 Parent only: after T028 through T036 complete, prepare the exact G-LOCAL-COMMIT handoff for the 23 listed paths. Verify the index contains no unrelated path. Record the ready local commit boundary in `specs/3335-deprecated-sle-operations/tasks.md`. Do not insert the commit's own hash into its content. Stop before publication. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; E037, the exact 23-path index is verified and the authorized local commit protocol is ready.)

**Local completion**: T001 through T037 can complete without publication.
A local commit does not release the queue or authorize a remote operation.
After T037 preparation, execute the authorized G-LOCAL-COMMIT protocol.
Verify its actual hash and clean status.
Report that evidence to the coordinator outside the commit itself.

---

## Exact validation commands

These commands describe future implementation and parent validation.
Do not execute them during task generation.
Run from the explicit repository root above.
Retain results in memory or task evidence, not through shell output redirection.

### G-RED — before every production edit

```bash
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py::TestCatalogCoverage -k deprecated -q
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_endpoint_family_exporter.py -k deprecated -q
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_endpoint_family_exporter.py::test_group_counts_match_discovery tests/guardrails/test_endpoint_catalog.py::TestCatalogCoverage::test_the_catalog_holds_every_family_operation -q
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py::TestMenuText -k menu_263 -q
```

Require six live-source absence failures in each module.
Additional injected/error controls are not substitutes for those failures.
Count and fixed-label cases must fail for their known current values.
G-TREND must pass as a preservation control before production edits.

### G-REM, G-TREND, G-LABELS, and G-ALL

```bash
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py::TestCatalogCoverage tests/unit/export/test_endpoint_family_exporter.py -q
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_endpoint_family_exporter.py -k trend -q
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py::TestMenuText -k menu_263 -q
rtk proxy .venv/bin/python -m pytest tests/unit/web_portal/test_portal_label_accuracy.py tests/unit/web_portal/test_portal_required_answers.py -q
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py tests/unit/export/test_endpoint_family_exporter.py tests/unit/web_portal/test_portal_label_accuracy.py tests/unit/web_portal/test_portal_required_answers.py -q
```

The first command is G-REM. The second is G-TREND.
The third and fourth together are G-LABELS. The fifth is G-ALL.
Retained request paths are:

```text
/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/summary-trend
/api/v1/sites/{site_id}/sle/{scope}/{scope_id}/metric/{metric}/classifier/{classifier}/summary-trend
```

The exporter supplies required positional values only.
The filename remains `{operation}_{argument_labels_with_spaces_replaced_by_underscores}.csv`.
Site labels use the selected site name. Remaining labels use the existing `{parameter}_{answer}` form.

### G-KEYS, G-UPSERT, and G-REFUSAL — unchanged selectors

```bash
rtk proxy .venv/bin/python -m pytest \
  tests/contract/test_export_api_function_names.py::test_source_export_calls_name_the_api_function \
  tests/unit/db/test_database_schema_utils.py::TestGetEndpointStrategy \
  tests/unit/db/test_database_schema_utils.py::TestBuildNaturalPkSql \
  tests/unit/db/test_database_schema_utils.py::TestBuildCompositePkSql \
  tests/unit/db/test_database_schema_utils.py::TestBuildAutoincrementSql \
  tests/unit/db/test_database_schema_utils.py::TestBuildCreateTableSql \
  tests/unit/export/test_data_exporter.py::TestWriteWithFormatSelection \
  tests/unit/export/test_data_exporter.py::TestRouteToPolyglot -q
rtk proxy .venv/bin/python -m pytest \
  tests/integration/test_menu_12_sqlite_upsert.py::TestSQLiteUpsertIdempotency \
  tests/integration/test_menu_13_sqlite_upsert.py::TestSQLiteUpsertIdempotency -q
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_export_notice_separator.py::test_a_refused_insight_request_names_the_http_status -q
```

Do not edit these tests or their production owners.
No existing SQLite selector can use `data/mist_data.db` or another persistent store.

### G-OWNERSHIP — live exact-file proof before generation

Use read-only `rtk proxy gh api` requests:

1. Read `user`, `repos/jmorrison-juniper/MistHelper/issues/3335`, and `repos/jmorrison-juniper/MistHelper/issues/comments/5936510347`.
2. Confirm the open claim, assignee, `in-progress` label, parent session, and all 23 exact reserved paths.
   Require exact equality between the parsed reservation path set and the specification's 23-path set.
3. Paginate `repos/jmorrison-juniper/MistHelper/pulls?state=open&per_page=100`.
4. For every PR, read `pulls/{number}` and every page of `pulls/{number}/files?per_page=100`.
5. Require unique file entries and equality with the detail response's `changed_files`.
   Compare both `filename` and `previous_filename` against every reserved path.
6. Read the open PR set and heads again. Recheck the issue claim and exact reservation.
   Require unchanged sets, heads, and ownership throughout the check.
7. Stop on an overlap, incomplete pagination, unreadable response, or changed snapshot.

The authoring check at `2026-10-01T17:48:32Z` confirmed 23 paths, 12 stable open PRs, and 103 complete file entries.
It found zero overlaps, including renamed paths.
The checked PRs were #3621, #3624, #3625, #3626, #3627, #3628, #3629, #3630, #3632, #3633, #3670, and #3687.
This evidence authorizes neither future generation nor publication without the required renewed check.

### G-GENERATE — two runs, six files, no discovery refresh

```bash
rtk proxy .venv/bin/python scripts/generate_menu_wiki.py
rtk proxy .venv/bin/python -m scripts.menu_api_map
```

Keep all six first-run outputs in memory.
Run the identical pair again and require all six byte comparisons to match.
Require the two wiki copies to match each other.
Then run:

```bash
rtk proxy .venv/bin/python -m scripts.menu_api_map --check
```

Do not use `--refresh-sdk-index`.
Compare status and exact changed paths before and after each pair.
If generation changes or removes any other path, stop and report it.
Do not include that path or automatically restore another worker's changes.

### G-CODE, G-TYPES, G-SECURITY, and G-QUALITY

```bash
rtk proxy .venv/bin/ruff check .
rtk proxy .venv/bin/black --check --diff .
rtk proxy .venv/bin/python -m py_compile MistHelper.py
rtk proxy .venv/bin/mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
rtk proxy .venv/bin/bandit-exclude-check --include-sample ./src/foundation/support/utils/zen_city_metadata.py --include-sample '.\src\foundation\support\utils\zen_city_metadata.py'
rtk proxy .venv/bin/bandit -c pyproject.toml -r .
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Use full Ruff and Black scope and the exact five CI mypy targets.
Use configured Bandit without severity filters or new skip rules.
Use the full local test-quality scope to include uncommitted tests.
Do not use a changed-from comparison as proof for those edits.

### G-LINKS — tracked gate plus direct untracked-file coverage

```bash
rtk proxy .venv/bin/markdown-link-check --exclude 'documentation/wiki/**'
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_markdown_links.py -q
```

The installed parser is `misthelper_devtools.markdown_link_check.MarkdownLinkChecker`.
Read each required file with strict UTF-8 handling.
Call the module's `_strip_code` function, then the checker's `_failures_in_file(path, body)` method.
Require zero returned failures for all nine readable inputs:

- The eight feature files in the exact scope list.
- `changelog.d/issue-3335-deprecated-sle-operations.md`.

This includes the five design files required by quickstart and the new task file.
A tracked-only scan that reads none of these untracked files is insufficient.
Do not patch the checker, silently skip read errors, or stage files just to expose them.

### G-STE — unchanged configuration, minimum 80

```bash
rtk proxy .venv/bin/ste-linter --config .ste-linter.toml --min-score 80 \
  specs/3335-deprecated-sle-operations/spec.md \
  specs/3335-deprecated-sle-operations/checklists/requirements.md \
  specs/3335-deprecated-sle-operations/plan.md \
  specs/3335-deprecated-sle-operations/research.md \
  specs/3335-deprecated-sle-operations/data-model.md \
  specs/3335-deprecated-sle-operations/quickstart.md \
  specs/3335-deprecated-sle-operations/contracts/endpoint-removal.md \
  specs/3335-deprecated-sle-operations/tasks.md \
  documentation/menu-highlights.md \
  documentation/menu_reference.md \
  documentation/wiki/Menu-Reference.md \
  documentation/menu-api/README.md \
  documentation/menu-api/interactive-safe.md \
  documentation/wiki/Menu-API-Endpoints.md \
  documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md \
  changelog.d/issue-3335-deprecated-sle-operations.md
```

Report partial coverage if the optional word dictionary is unavailable.
Do not lower the score, change configuration, or generate dictionary data.

### G-AUDIT — this worktree's runtime inputs only

```bash
rtk proxy .venv/bin/python -m pip_audit -r requirements.txt
```

Only if the standard macOS resolver fails, retain the failure and use the documented strict alternative.
During later validation, create `data/issue-3335/` only for local audit output if needed.
Keep the lock outside the feature change and staged index.
If that boundary cannot be maintained, stop. Do not change an ignore file.

```bash
rtk proxy env UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 uv pip compile requirements.txt --python .venv/bin/python --generate-hashes --output-file data/issue-3335/runtime-audit-lock.txt
rtk proxy .venv/bin/python -m pip_audit --no-deps --disable-pip --require-hashes -r data/issue-3335/runtime-audit-lock.txt
```

Require a complete audit with zero advisories.
Do not install dependencies, reuse another worktree's lock, or use `--ignore-vuln`.
The Git-only `misthelper-devtools` development pin is not part of this runtime audit:

```text
git+https://github.com/jmorrison-juniper/misthelper-devtools.git@b140350ebc40e61b57a3a65731c0df520f143661
```

State that dependency-scope limitation separately.
Do not claim runtime auditing covers that development tool.

### G-DIFF — exact local feature boundary

```bash
rtk proxy git --no-pager diff --check
rtk proxy git --no-pager diff --stat
rtk proxy git --no-pager diff --name-only
rtk proxy git status --short --untracked-files=all
```

Read every changed hunk and every feature-owned untracked file.
Require only the 23 reserved paths in the feature change.
Compare retained rows, keys, menu identity, and dependency contents against the recorded pre-edit evidence.
Never treat a directory-only status line as a complete file inventory.

### G-LOCAL-COMMIT — parent only, after independent validation and analysis

This is a future parent-owned local operation, not an authoring hook.
Require the local gate evidence and approved analysis disposition for T028 through T036 first.
Unperformed governance, deployment, and publication steps do not count as passed.
Stop if the current index contains unrelated work. Do not automatically reset or unstage it.
Stage only these exact paths:

```bash
rtk proxy git -C /Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-fictional-barnacle add -- \
  MistHelper.py \
  web_portal/menu_registry.py \
  src/operations/exporting/export/endpoint_family_exporter.py \
  src/operations/exporting/export/endpoint_catalog.py \
  src/foundation/support/refactors/endpoint_primary_key_strategies.py \
  tests/guardrails/test_endpoint_catalog.py \
  tests/unit/export/test_endpoint_family_exporter.py \
  documentation/menu-highlights.md \
  documentation/menu_reference.md \
  documentation/wiki/Menu-Reference.md \
  documentation/menu-api/README.md \
  documentation/menu-api/interactive-safe.md \
  documentation/wiki/Menu-API-Endpoints.md \
  documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md \
  changelog.d/issue-3335-deprecated-sle-operations.md \
  specs/3335-deprecated-sle-operations/spec.md \
  specs/3335-deprecated-sle-operations/checklists/requirements.md \
  specs/3335-deprecated-sle-operations/plan.md \
  specs/3335-deprecated-sle-operations/research.md \
  specs/3335-deprecated-sle-operations/data-model.md \
  specs/3335-deprecated-sle-operations/quickstart.md \
  specs/3335-deprecated-sle-operations/contracts/endpoint-removal.md \
  specs/3335-deprecated-sle-operations/tasks.md
rtk proxy git -C /Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-fictional-barnacle --no-pager diff --cached --check
rtk proxy git -C /Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-fictional-barnacle --no-pager diff --cached --name-only
```

Require the staged set to contain all actual feature changes and no path outside the reservation.
Then create the one local commit:

```bash
rtk proxy git -C /Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-fictional-barnacle commit -m "chore(export): remove deprecated SLE operations" -m "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"
rtk proxy git -C /Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-fictional-barnacle --no-pager log -1 --format=full
rtk proxy git -C /Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-fictional-barnacle status --short --untracked-files=all
```

Verify the commit subject, trailer, hash, and bounded content.
Return the hash in the parent result. Do not amend a commit only to insert its own hash into this file.
No fetch, rebase, branch rename, push, PR, protected merge, build, deployment, or exact-main proof belongs to this handoff.

---

## Dependencies and execution order

Every dependency below is a real prerequisite, not an implied numerical order.
Tasks within one listed group can run independently after their prerequisites complete.

| Tasks | Prerequisites |
| --- | --- |
| T001 | None |
| T002 | T001 |
| T003 | T002 |
| T004, T005 | T003 |
| T006 | T004 |
| T007 | T006 |
| T008 | T004, T005, T007 |
| T009, T010, T011 | T008 |
| T012 | T009, T010, T011 |
| T013, T014, T015, T016 | T012 |
| T017, T018, T019 | T013, T014, T015, T016 |
| T020 | T017, T018, T019 |
| T021 | T020 |
| T022, T024 | T021 |
| T023 | T022 |
| T025 | T023, T024 |
| T026 | T025 |
| T027 | T026 |
| T028 through T034 | T027 |
| T035 | T028, T029, T030, T031, T032, T033, T034 |
| T036 | T035 |
| T037 | T036 |

Story completion order:

```text
Setup -> Shared tests and real red -> US1 -> US2 -> US3 -> US4
      -> Implementation handoff -> Parent gates -> Parent analysis -> Local commit
```

US4's shared guard implementation deliberately precedes US1 removal.
US2's real SDK tests deliberately precede every production edit.
The later story phases independently verify those prepared tests against the completed increment.
No model, service, endpoint, schema, or infrastructure creation phase is needed.

## Parallel execution examples

Parallel markers describe optional scheduling, not permission to invoke agents.
Keep evidence writes to this file serial.

| Story or prerequisite | Parallel example | Required completed prerequisite |
| --- | --- | --- |
| Shared tests | T004 edits the exporter tests while T005 adds label tests in the guard module. | T003 |
| US1 | T009 removes selectable rows while T010 removes catalog entries and T011 removes PK entries. | T008 |
| US2 | T013 through T016 run independent local pytest commands with isolated temporary files/databases. | T012 |
| US3 | T017, T018, and T019 edit three distinct fixed-label files. | T013 through T016 |
| US3 | T022 runs the first generator pair while T024 authors the distinct release fragment. | T021 |
| US4 | Run each module's matrix from T025 in a separate pytest process, then consolidate counts. | T023 and T024 |

Do not run the two generator passes concurrently.
Do not edit the same test module concurrently.
Do not run parent staging while a gate or evidence edit is active.

## Coverage and implementation strategy

| Story | Story-phase tasks | Shared test prerequisites | Requirement coverage |
| --- | ---: | --- | --- |
| US1 (P1) | 4: T009–T012 | T003, T004, T008 | FR-001, FR-005, FR-006; C1, C2 |
| US2 (P1) | 4: T013–T016 | T004, T006, T007, T008 | FR-002, FR-003, FR-004, FR-010, FR-011, FR-012; C3–C5 |
| US3 (P2) | 8: T017–T024 | T005, T008 | FR-007, FR-008, FR-009, FR-013; C2, C7 |
| US4 (P2) | 2: T025–T026 | T003, T004, T008 | VC-001, VC-002, VC-003, VC-004; C6 |
| Shared/local completion | 19 | Setup, red gate, parent gates and analysis | VC-005, VC-006; C7, C8 |

**Total**: 37 tasks. Fourteen task lines carry `[P]`.
The two test modules each contain the six required semantic absence cases and six negative injections.
That duplication of coverage uses one private guard decision, not new infrastructure.

**MVP first**: Complete shared tests and real red evidence, then US1 as the first local metadata checkpoint.
US1 alone is not a releasable feature.
Complete US2 preservation, US3 coupled labels/references, and US4 guard proof before the implementation handoff.
Then let the parent run independent gates, analysis, and the exact local commit.

**Incremental delivery**: Verify each story's independent criterion before the next completion checkpoint.
Do not deploy or publish a partial increment.

## Deferred publication — expressly blocked

Publication is a separate future phase and has no actionable checkbox in this preparation list.
The parent owns queue position 16 after issue #3366.
It must receive a later explicit publication release before push, PR creation, protected merge, or exact-main proof.
Any later synchronization, CI, merge, image verification, or deployment plan belongs to that separately authorized phase.

An initial main SHA, an observed main SHA, passing local gates, or a local commit is not publication permission.
Local preparation can finish while publication remains blocked.
Stop after the parent-owned local commit and handoff.

## Local implementation evidence

### E001 — explicit inputs and scope

Read all eight feature inputs at the explicit absolute feature directory.
The checklist contains 16 completed items and zero incomplete items.
The structural exceptions above remain bounded. No hierarchy cleanup is part of this change.

Initial commands:

```bash
rtk proxy git --no-pager status --short
rtk proxy git branch --show-current
rtk proxy git rev-parse HEAD
rtk proxy git rev-parse --git-dir
rtk proxy git check-ignore -v .venv/ .pytest_cache/ __pycache__/ data/issue-3335/runtime-audit-lock.txt
rtk proxy gh api user --jq .login
rtk proxy gh api repos/jmorrison-juniper/MistHelper/issues/3335 --jq '{state,assignees:[.assignees[].login],labels:[.labels[].name]}'
rtk proxy gh api repos/jmorrison-juniper/MistHelper/issues/comments/5936510347 --jq '{id,user:.user.login,body}'
```

All commands exited 0.
The branch is `jmorrison-juniper-deprecated-sle-operations`.
HEAD is `856e5065413d3026f9c0f6d5222d9d379ec79d8b`.
Initial status contains only the untracked explicit feature directory.
Authentication and the issue assignee are `jmorrison-juniper`.
Issue #3335 is open with `chore`, `src`, `tests`, and `in-progress` labels.
Comment `5936510347` names parent session `d36ec015-9c4f-4a76-987a-d64f58df8e87` and all 23 reserved paths.
No claim or cloud resource was changed.

The prerequisite check used `rtk proxy .venv/bin/python -c` with the explicit eight-file list.
It required every file to exist and printed absolute `FEATURE_DIR` and `AVAILABLE_DOCS` values.
It also counted all checklist items. Its exit was 0.
The normal PowerShell check calls the persisting resolver, so it was not run.
Existing `.gitignore` and `.dockerignore` were read without edits.
The ignore probe confirmed the virtual environment, caches, and local data are already ignored.
No setup, commit, or persisting context hook ran.
No environment installation or audit ran.
The parent's earlier 508-test four-module pass is prior evidence only.

### E002 — pre-edit registrations and preservation snapshots

Two `rtk proxy .venv/bin/python -` source probes captured the following values before production edits.
The first probe completed every registration and CLI measurement.
Its final portal lookup rejected an assumed annotated assignment with `StopIteration`.
The second probe read the actual plain assignment and completed the portal measurement with exit 0.
This source-probe correction changed no file and is not red test evidence.

| Source | Exact identifier | Present | Inspected |
| --- | --- | --- | ---: |
| Selectable rows | `getSiteSleSummary` | Yes | 286 |
| Selectable rows | `getSiteSleClassifierDetails` | Yes | 286 |
| Catalog keys | `getSiteSleSummary` | Yes | 286 |
| Catalog keys | `getSiteSleClassifierDetails` | Yes | 286 |
| PK keys | `getSiteSleSummary` | Yes | 571 |
| PK keys | `getSiteSleClassifierDetails` | Yes | 571 |

Snapshots serialize complete row fields with `dataclasses.asdict`.
They use sorted JSON keys, compact separators, UTF-8, and SHA-256.
The retained snapshots omit only the two exact retired identifiers.
This omission defines preservation evidence, not the live absence input.

| Family menu | Original count | Retained count | Retained SHA-256 |
| --- | ---: | ---: | --- |
| 259 | 29 | 29 | `a1b130efc7fc2605136e8ced260d7a5aeb79a98e0eb9e0daf360ab61e7a9761d` |
| 260 | 55 | 55 | `a73aa854cc3b1cb75e7f932dcdbe6d8cfeb0b4f49ced6df903752793b67742fd` |
| 261 | 58 | 58 | `715c962a3f854ee6255769a989febb210550d53b1eb9d0fe148d08a556c541bc` |
| 262 | 10 | 10 | `0844ab9840694c88c8f8a1e654dbbb7a7d19fd8fb18c21dd58aba057f2502d60` |
| 263 | 17 | 15 | `3973a4a0594e0c0a8cb307329a58bcf010da2155b37b4cf7571abe6c1fc514f4` |
| 264 | 7 | 7 | `a5777f2fa6075431cbd4fedd08b4c076a1c72f0c99efde3b551314bfd8b9d7d0` |
| 265 | 33 | 33 | `18f6a4cb356dbcec3409a0fcb065ab438d581ea9e2b62a10fc4b04e64029549c` |
| 266 | 61 | 61 | `dfd2267bb67cfa939cb8470d8b51501db556bac79a7a2d70a8bdb0f7aa9285db` |
| 267 | 10 | 10 | `5ffbc2173183f78936aa421091c6a5df75c293dab567e11a59c6503845051e58` |
| 268 | 6 | 6 | `e418a0eea52f1b8d2f1f3e7488ba3fb5715907efd504c338d80e22f6dd58d4d8` |

| Retained surface | SHA-256 |
| --- | --- |
| Stage-two rows | `86816d4480396f34fa26eae3ae872901307996f3201f322bb822fdc5bba4c151` |
| Catalog descriptions and safety | `69f612e081360381395cf025e87a7e63b0e85410234fab785206ae7a18e0ffd3` |
| Complete PK strategies | `022e1799a9520720edc97f435ae02c91b5b3223a0dd54886ed16bf9bd7cd7664` |
| All 293 CLI menu calls, with only the 263 title corrected | `c9b358fa936a54c620493813b8d291b50ae6bd29cbc124f3c40dc888d6901391` |
| All 179 portal descriptions, with only the 263 title corrected | `57aa44e8b4598b9bcaa9881c63fa36fe82b813d8de049ca334fa75d8770a71e6` |

The CLI snapshot contains the complete location-free AST for every `MenuEntry` call.
It includes each identifier, title, handler, category, destructive flag, and fast-mode flag.
The original CLI digest is `ed405bbec6879ee0d90b217273d8f64a1166cd9f17549ef87e539c653dca2124`.
The original portal digest is `783316501e9dd71bae69c9d2fea451bee7a5ecebff938eff7e8c640798bbf70c`.
The only permitted difference is the exact menu 263 title.

| Read-only file | Initial byte SHA-256 |
| --- | --- |
| `requirements.txt` | `848301049195163bb029b66e486efdea9ec2da71126a1c64219978613dee8d72` |
| `requirements-dev.txt` | `b05947fed098677f50a79e9d2bbaf8ae8933c221daca72a7816ec0c2fea61a29` |
| `pyproject.toml` | `c6761f814c02355f771b7241c03d168efe8fbf62c98783c78294bb327e4ffb5a` |
| `.specify/feature.json` | `ddfe10fb5bfd4eefd69bbe4e78d7d9a40d22c1f73809df07857c10083a8b0a15` |
| `.specify/extensions.yml` | `9b6bc0bc814acdbe824b2ea02db781abed4f439675349e876d4f03d58e3cf5d9` |

The PK snapshot contains 123 natural, 123 composite, six time-series, and 319 auto-increment strategies.
Both real SDK trend functions were read directly.
They call `mist_session.mist_get(uri=uri, query=query_params)`.
The actual input handlers return an empty string for blank, EOF, or interrupted required answers.
Invalid menu and site selections cancel. Nonempty SLE identifiers have no new validation rule.
No environment audit or dependency change was needed.

### E003 — shared guard controls before production edits

```bash
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py::TestCatalogCoverage -k 'deprecated and not live' -q
```

Exit 0: 42 passed, nine deselected, zero failed, zero skipped, in 0.24 seconds.
The semantic class retains its three existing tests and adds one private decision and one matrix entry point.
The matrix covers three raw source kinds, two exact identifiers, and eight scenarios.
Each live case keeps its actual source. Only isolated negative-control copies remove prior retired entries.
Six shaped injections reject. Their inspected counts are 285 selectable rows, 285 catalog keys, and 570 PK keys.
Empty, missing, wrong-shape, malformed-record, and first-read failures reject with count zero.
Partial-read failures reject with count one and the exact `OSError` message.
The checkout site lock trail stayed at zero lines.
The genuine live-source red run remains T008.

The seven completed feature inputs were also snapshotted without edits:

| Input | Byte SHA-256 |
| --- | --- |
| `spec.md` | `7174088362c8a445519215ed5998b85c72ad44f2f41024a01e9c5ccd518f8bed` |
| `checklists/requirements.md` | `3f6f83916d9b0b202edcade7f092e62f8e2a7093ddf34843cafea55520936a16` |
| `plan.md` | `accb161462763f53e2ce09fa098ff3c7919a5dbea98ff8623a9926b1d18d7ed8` |
| `research.md` | `d8e41ddd730064b2890bc4e960f2cacdae75b887252d669a689cbe90cb6cb2bb` |
| `data-model.md` | `65da1144ecf2d3c529df0f2dcf1350a27d7f3303dfec4a42b206102995448e6f` |
| `quickstart.md` | `ba76c639c10d6e914a32755d6f6415f0268f49978ff7f7ce7eaed265310bfaf2` |
| `contracts/endpoint-removal.md` | `69441e456730d0cc42b556ec85e91b1ed41e2c2870103ef4b18a02c6f5624404` |

### E004 and E005 — shared preservation and menu tests

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_endpoint_family_exporter.py -k '(deprecated and not live) or every_retained_family_row or retained_trend_rows' -q
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py::TestMenuText -k 'menu_263 and complete_identity' -q
```

The first command exited 0: 54 passed and 421 deselected in 0.27 seconds.
These are 42 guard controls, ten full retained-family comparisons, and two exact trend row/catalog/PK assertions.
The second command exited 0: two passed and six deselected in 0.27 seconds.
The final identity assertion also includes all CLI dictionary keys, not only the constructor calls.
Its normalized full-dictionary SHA-256 is `f532b6295e41646128f22c21689119066ecc80868ffee4427a2eb069a310aee2`.
The final pre-edit identity controls passed again in E008.

New test definitions were inspected with the configured formatter in memory.
Every new function and method has at most five parameters and 25 physical lines.
Manual formatting used `apply_patch` only.
All 18 existing exporter function definitions retain their original line anchors.
Their assertion bodies remain unchanged, except the directly coupled stage-two count.
New import bindings and tests follow the original 233 lines to preserve old quality fingerprints.
No baseline, exclusion, suppression, or quality setting changed.
These checks are not substitutes for the parent's full code and quality gates.

### E006 and E007 — real SDK controls before removal

The first fixture-development command was:

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_endpoint_family_exporter.py -k real_trend -q
```

It exited 1 with 24 failures and 475 deselected in 0.70 seconds.
This was a local fixture defect, not valid removal red evidence.
The SDK constructor rejects unlisted clouds, including `.test` hosts.
Also, `ConfigUtils` deliberately skips `AppContext` during pytest and uses its real local cache.
Production editing stayed blocked while those setup defects were corrected.

The fixture now constructs a real session with an empty local environment.
It sets only that session's host state to `api.issue3335.test`.
It seeds the real `AppContext` and the existing `ConfigUtils` setters.
It keeps the real `SourceDependencyResolver`, selectors, handlers, SDK functions, response decoding, and `get_all`.
The same command then exited 0: 24 passed and 475 deselected in 0.50 seconds.
The complete final selector passed in E008.

All HTTP responses carry status 200, JSON body, URL, content type, and a prepared request with valid headers.
Only the local session's HTTP `get`, console input, and final `DataExporter` writer use mocks.
Every unexpected transport request is intercepted locally.
The session contains zero API tokens. No live credential file or production host is used.
The SDK log assertion covers setup, call, and teardown without suppressing errors.
Sessions, context, selection state, environment values, SDK attributes, and log settings restore after each case.

The 118 new real-SDK cases comprise:

| Cases | Count |
| --- | ---: |
| Both full journeys, four payload/page shapes, SDK present or absent | 16 |
| Default and explicit optional queries, both functions and SDK states | 8 |
| Empty lists, empty `results`, and dictionaries without `results` | 12 |
| Blank, EOF, and interrupt at all actual required-answer positions | 66 |
| Invalid numeric and text menu/site choices | 16 |

Each full journey runs twice and asserts exact transport and writer call lists.
The expected summary rows are literal flattened and escaped values.
The summary filename is `getSiteSleSummaryTrend_Local_Site_scope_site_scope_id_scope-3335_metric_coverage.csv`.
The classifier filename is `getSiteSleClassifierSummaryTrend_Local_Site_scope_site_scope_id_scope-3335_metric_coverage_classifier_low-rssi.csv`.
Routing uses the original exact trend identifier.
Repeated calls do not imply a new trend uniqueness constraint.

The absent-SDK half contains 59 new cases.
Both actual retired attributes are deleted and checked absent before each case.
That half includes eight full-journey cases and 16 completed export journeys.
The retained function identities and literal dispatch results remain the same.
Required-answer failures permit only the existing site lookup when it has already completed.
They make no trend request or writer call.
Invalid nonempty SLE identifiers receive no invented cancellation rule.

### E008 — final real red checkpoint

All commands ran before the first production edit.
They use the exact G-RED and G-TREND selectors above.

| Command | Exit | Passed | Failed | Deselected | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Guard class `-k deprecated -q` | 1 | 42 | 6 | 3 | 1.08 |
| Exporter module `-k deprecated -q` | 1 | 42 | 6 | 545 | 0.95 |
| Both coupled count selectors | 1 | 0 | 2 | 0 | 0.95 |
| `TestMenuText -k menu_263 -q` | 1 | 2 | 3 | 3 | 1.06 |
| Exporter module `-k trend -q` | 0 | 126 | 0 | 467 | 1.07 |

Zero tests skipped. No collection, import, fixture, transport, or unrelated failure remains.
Each module's six live failures explicitly names the present identifier.
They report 286 selectable records, 286 catalog records, and 571 PK records.
All six shaped injections per module reject with exact findings and measured counts.
The coupled failures report SLE 17 instead of 15 and catalog 286 instead of 284.
The stage-two pre-edit count remains the measured 134 from E002.
Each of the three fixed labels reports 17 instead of 15.
Both complete menu identity controls pass.
The trend selector contains 118 new real-SDK cases, two exact metadata cases, and six existing row checks.
No successful new SDK case emits an SDK error log.
The same live assertions remain for the green run.
The checkout site lock trail remained at zero lines in every run.

### E012 — metadata-only green checkpoint

```bash
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py::TestCatalogCoverage tests/unit/export/test_endpoint_family_exporter.py -q
rtk proxy git --no-pager diff -- src/operations/exporting/export/endpoint_family_exporter.py src/operations/exporting/export/endpoint_catalog.py src/foundation/support/refactors/endpoint_primary_key_strategies.py
```

G-REM exited 0: 638 collected and passed, zero failed, zero skipped, in 1.88 seconds.
The source diff contains two row deletions, two catalog deletions, and two supplemental PK deletions.
The catalog's current descriptive count changed from 286 to 284.
There is no production class, method, resolver, prompt, persistence, or aggregate-construction change.
The existing `setdefault` merge remains unchanged.

A read-only `rtk proxy .venv/bin/python -` comparison exited 0.
It recomputed each complete live family digest and compared it with E002.
All ten comparisons matched, including order and every retained row field.
The complete retained stage-two, catalog, and PK digests also matched E002 exactly.
Both trend definitions and their full strategy dictionaries passed the existing exact new assertions.

| Measured surface | After removal |
| --- | ---: |
| Site SLE | 15 |
| Stage two | 132 |
| Catalog | 284 |
| All selectable rows | 284 |
| PK metadata | 569 |
| Site map / site detail / org detail / MSP detail / other detail | 7 / 33 / 61 / 10 / 6 |

The shared live decisions returned `(True, 284, ())`, `(True, 284, ())`, and `(True, 569, ())`.
The same six absence assertions per module that failed in E008 now pass.
Every unrelated description, safety value, key, and strategy remains equivalent to the pre-edit snapshot.
No store, table, index, or persisted row changed.
The checkout site lock trail remained at zero lines.

### E016 — unchanged SDK, routing, keys, upserts, and refusal gates

Ran the exact G-TREND, G-KEYS, G-UPSERT, and G-REFUSAL commands documented above.
All four commands exited 0.

| Gate | Collected | Passed | Failed | Skipped | Deselected | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| G-TREND | 587 | 126 | 0 | 0 | 461 | 0.91 |
| G-KEYS | 21 | 21 | 0 | 0 | 0 | 1.67 |
| G-UPSERT | 7 | 7 | 0 | 0 | 0 | 10.25 |
| G-REFUSAL | 54 | 54 | 0 | 0 | 0 | 0.91 |

G-TREND repeats the complete E006/E007 acceptance coverage after removal.
Both real functions still resolve and export with both retired SDK attributes absent.
All 59 new absent-SDK cases pass. Their exact requests and output remain unchanged.
No new SDK case emits an error log.

G-KEYS preserves the unchanged export contract, configured strategies, SQL, format selection, and polyglot dispatch.
G-UPSERT uses only the seven existing temporary SQLite cases.
They verify existing inventory and statistics updates, not new trend deduplication.
G-REFUSAL passes all 54 parameterized issue #3305 cases.
It preserves HTTP statuses, prior output, no-writer behavior, and the absence of false empty/success notices.
None of these read-only selector modules or their production owners changed.
The dependency declarations remain `mistapi>=0.64.0,<0.65`.
Their final byte-integrity comparison belongs to E027, not an environment audit.
The checkout site lock trail remained at zero lines in all four runs.

### E020 — fixed labels and unchanged portal gates

```bash
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py::TestMenuText -k menu_263 -q
rtk proxy .venv/bin/python -m pytest tests/unit/web_portal/test_portal_label_accuracy.py tests/unit/web_portal/test_portal_required_answers.py -q
rtk proxy git --no-pager diff -- MistHelper.py web_portal/menu_registry.py documentation/menu-highlights.md
rtk proxy git --no-pager diff --check
```

All commands exited 0.
The fixed-label and identity selector passed five cases, with three deselected, in 0.18 seconds.
The unchanged portal modules passed all 70 collected cases in 0.28 seconds.
Zero tests failed or skipped.
All three exact labels now state 15 operations.
The reviewed source diff changes one count string in each of the three reserved paths.
The complete normalized CLI dictionary and portal description digests still match.
All 293 menu identifiers, handlers, categories, safety flags, and fast-mode flags remain unchanged.
All 179 portal descriptions remain unchanged except the exact 263 count.
Chooser order, browser flags, required controls, and existing read floors pass without test edits.
The checkout site lock trail remains at zero lines.

### E021 — renewed live claim and complete PR file ownership

The check started at `2026-10-01T19:38:43.352932Z`.
It completed at `2026-10-01T19:39:21.354659Z`, immediately before the first wiki command.
It made 30 read-only `rtk proxy gh api` calls.
Paginated requests used `--paginate --slurp` and `per_page=100`.

Read `user`, issue #3335, and comment `5936510347` before and after the PR scan.
Authentication, assignee, labels, parent session, queue position, and exact reservation remained unchanged.
The parsed comment, completed specification, and task manifest contain the same 23 exact paths.
Every open PR received its detail request and every page of its exact file list.
Each list had unique entries and matched `changed_files`.
Both current and previous filenames were compared with all 23 paths.
The open set and every head were stable across the check.

| PR | Stable head SHA | File entries / `changed_files` | Previous filenames | Overlaps |
| --- | --- | ---: | ---: | ---: |
| 3621 | `c5455c87036e6ec5983ae62ea424db86b8120cd2` | 15 / 15 | 0 | 0 |
| 3624 | `2bedbfba77d5a2cb55ec9aede7c26f1357b66544` | 3 / 3 | 0 | 0 |
| 3625 | `9d26c878e0f5c685de78510e34b4add83f5dccf6` | 10 / 10 | 0 | 0 |
| 3626 | `b3d3b109c0b141b0092fb13863abedd79f289e46` | 7 / 7 | 0 | 0 |
| 3627 | `ba660e089c9b2b3cface04921bb3299542212392` | 6 / 6 | 0 | 0 |
| 3628 | `abe300bc065799f1b01bab568d6286e7e63201c8` | 3 / 3 | 0 | 0 |
| 3629 | `f4a116b69efa2ab39bec43291ab7c28b8d0a3297` | 8 / 8 | 0 | 0 |
| 3630 | `51d2caebbec44fd74fefd19549f726186012598b` | 8 / 8 | 0 | 0 |
| 3632 | `9069bb33cfb7c3b4dee1966811404e86d6d3d907` | 10 / 10 | 0 | 0 |
| 3633 | `ad36aa0e67a7643ffcb4683209c5227d1baad035` | 14 / 14 | 0 | 0 |
| 3670 | `48301558fdd2daef23e02fa12aa0b3da67bf94cf` | 1 / 1 | 0 | 0 |
| **Total** | **11 stable heads** | **85 / 85** | **0** | **0** |

The earlier authoring snapshot had 12 PRs and 103 entries.
The fresh generation snapshot, not that prior result, supplied permission for bounded local generation.
Nothing changed within the fresh check.
No issue, comment, label, claim, or PR was mutated.
This check grants no publication release.

### E023 — both generators twice and six byte comparisons

Ran this exact pair twice, serially, after E021:

```bash
rtk proxy .venv/bin/python scripts/generate_menu_wiki.py
rtk proxy .venv/bin/python -m scripts.menu_api_map
```

All four generator commands exited 0.
First-run output bytes stayed in memory through the second pair.
The scope check watched feature files, existing map outputs, and the immutable SDK index.
It also compared exact Git status paths before and after each command.

| Pass / command | Measured seconds | Changed paths | Other result |
| --- | ---: | ---: | --- |
| First wiki | 0.680 | 2 | Both reserved copies written |
| First API map | 6.112 | 4 | Zero removed, 12 unchanged, 293 menus |
| Second wiki | 0.275 | 0 | Both copies byte-identical |
| Second API map | 5.344 | 0 | Zero written or removed, 16 unchanged, 293 menus |

Generator-reported API times were 3.8 seconds and 3.4 seconds.
Measured command times include process and scope-check overhead.
Only the six reserved references changed. Zero unexpected paths changed or appeared.
No SDK refresh flag was used, and the SDK index bytes remained equal.

| Reference | Bytes | First/second byte equality | SHA-256 |
| --- | ---: | --- | --- |
| `documentation/menu_reference.md` | 48681 | True | `1e41d53f8281753396ab8f4fc3d253f00c171e2dd3761f7d20677e620f507a86` |
| `documentation/wiki/Menu-Reference.md` | 48681 | True | `1e41d53f8281753396ab8f4fc3d253f00c171e2dd3761f7d20677e620f507a86` |
| `documentation/menu-api/README.md` | 53486 | True | `883e90d26870f1a3d8bebf66b80dab5038fcd6c17184bc6d62e0f628ed23d9a2` |
| `documentation/menu-api/interactive-safe.md` | 237365 | True | `ca998b10ef143daa4295167f93aad39b7de485dea17717f8adcc64816626d5b3` |
| `documentation/wiki/Menu-API-Endpoints.md` | 59222 | True | `3a7e691374a86a741fb1efda0afdbf12e859321063d14caa9eb0d1efccabc0ef` |
| `documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md` | 272408 | True | `7402b6e44f5294ceb529f081df086c7db3847cd2b912a3255568e509212b2858` |

The two wiki copies also match each other.
All six titles state 15 operations.
Both exact retired identifiers are absent from all four active-map files.
Both retained trends appear in each detailed interactive-safe map.
The README indexes link to those detail sections but do not list operation identifiers.
An extra initial index assertion was corrected to this actual index/detail contract.
That read-only validation probe failed after all six byte comparisons had already passed.
It caused no additional generation, source edit, or unexpected path.
The corrected validation then exited 0 and matched all six recorded hashes and sizes.
The index lists 16 reachable API endpoints for menu 263, including its existing organization-site lookup.
That endpoint count is separate from the 15 selectable SLE operations.

```bash
rtk proxy .venv/bin/python -m scripts.menu_api_map --check
```

Exit 0: all 16 map pages match source for 293 menu options, in 3.5 generator-reported seconds.

### E024 — unique release fragment

Added only `changelog.d/issue-3335-deprecated-sle-operations.md` through `apply_patch`.
Its exact path did not exist before authoring.
It names both removed identifiers and both retained trend identifiers.
It states the unchanged SDK constraint and no schema or data migration.
It preserves stored records, keys, upserts, and SLE refusal.
No shared changelog, README, operator guide, or standalone guide changed.

### E025 — final measured guard matrices

```bash
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py::TestCatalogCoverage -k deprecated -q
rtk proxy .venv/bin/python -m pytest tests/unit/export/test_endpoint_family_exporter.py -k deprecated -q
```

Both commands exited 0 in 0.35 seconds each.
The catalog class passed 48 selected cases, with three deselected.
The exporter module passed 48 selected cases, with 539 deselected.
Zero failures or skips occurred.

Each module owns six live exact-name absence assertions, six injection cases, and 36 fail-closed input cases.
The six live assertions per module are the same assertions that failed in E008.
The exporter reuses the identical decision function object from `TestCatalogCoverage`.
No production registration is patched or replaced.

| Source | Live inspected | Each one-entry injection inspected | Injected findings |
| --- | ---: | ---: | --- |
| Selectable | 284 | 285 | Exactly the injected retired identifier |
| Catalog | 284 | 285 | Exactly the injected retired identifier |
| PK | 569 | 570 | Exactly the injected retired identifier |

For each source and module, both original-shaped retired registrations reject.
The shared result is `(False, inspected_count, (injected_identifier,))`.
Empty, missing, wrong-shape, malformed-record, and first-read failures reject at count zero.
Partial-read failures reject at count one with `OSError: registration read failed`.
No empty or unreadable input produces acceptance.

A separate `rtk proxy .venv/bin/python -` probe called the same function through both module bindings.
It confirmed six whole-source live decisions and 12 exact injected rejections.
The probe's final printed `live_cases=12` label counted identifier/source assertions, not its six whole-source calls.
The measured per-decision record counts and all 12 injection results were correct.
The pytest matrices above provide the actual 12 independent live identifier/source assertions.
The checkout site lock trail remained at zero lines.

### E026 — complete local acceptance, not the prior baseline

```bash
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py tests/unit/export/test_endpoint_family_exporter.py tests/unit/web_portal/test_portal_label_accuracy.py tests/unit/web_portal/test_portal_required_answers.py -q
```

Exit 0: 733 collected, 733 passed, zero failed, zero skipped, in 1.88 seconds.
This is the final local four-module run, not the parent's prior 508-test result.
The same 12 live red assertions now pass.
Both count assertions and all three fixed-label assertions now pass.
All existing family, key, safety, chooser, and required-answer assertions remain.
The six removed parameter rows follow only from the two deleted operations across three existing row tests.
No unrelated assertion body, floor, fixture seam, or test setting was weakened.
All 118 new real-SDK cases and both retained-strategy assertions pass.
The checkout site lock trail held zero lines before and after the full run.
Parent-owned independent quality gates and analysis remain unexecuted in this stage.

### E027 — bounded implementation handoff

T001 through T027 are complete. T028 through T037 remain open.
This statement covers only the requested local implementation stage.
It does not report complete feature validation or publication permission.

Final G-DIFF commands:

```bash
rtk proxy git --no-pager diff --check
rtk proxy git --no-pager diff --stat
rtk proxy git --no-pager diff --name-only
rtk proxy git status --short --untracked-files=all
rtk proxy git --no-pager diff --cached --name-only
rtk proxy git rev-parse HEAD
```

All commands exited 0.
Whitespace checks pass. The staged index is empty.
HEAD remains `856e5065413d3026f9c0f6d5222d9d379ec79d8b`.
The branch remains `jmorrison-juniper-deprecated-sle-operations`.
No staging, commit, fetch, rebase, branch change, push, PR, merge, container, build, deployment, or live-store mutation occurred.
No agent or dependency installation ran.

Reviewed every tracked changed hunk and all feature-owned untracked content.
The tracked diff contains 14 paths, with 681 insertions and 79 deletions.
The remaining nine paths are the unique fragment and eight current feature inputs.
Seven of those eight feature inputs were already present and remain byte-identical.
Only `tasks.md` changed during this implementation stage.
The final Git inventory contains exactly the reserved 23 paths and zero outside paths:

```text
MistHelper.py
web_portal/menu_registry.py
src/operations/exporting/export/endpoint_family_exporter.py
src/operations/exporting/export/endpoint_catalog.py
src/foundation/support/refactors/endpoint_primary_key_strategies.py
tests/guardrails/test_endpoint_catalog.py
tests/unit/export/test_endpoint_family_exporter.py
documentation/menu-highlights.md
documentation/menu_reference.md
documentation/wiki/Menu-Reference.md
documentation/menu-api/README.md
documentation/menu-api/interactive-safe.md
documentation/wiki/Menu-API-Endpoints.md
documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md
changelog.d/issue-3335-deprecated-sle-operations.md
specs/3335-deprecated-sle-operations/spec.md
specs/3335-deprecated-sle-operations/checklists/requirements.md
specs/3335-deprecated-sle-operations/plan.md
specs/3335-deprecated-sle-operations/research.md
specs/3335-deprecated-sle-operations/data-model.md
specs/3335-deprecated-sle-operations/quickstart.md
specs/3335-deprecated-sle-operations/contracts/endpoint-removal.md
specs/3335-deprecated-sle-operations/tasks.md
```

The final read-only integrity probe exited 0.
All five protected byte hashes from E002 and all seven completed-input hashes from E003 match.
The SDK constraint stays unchanged in both declarations.
The SDK discovery index, baselines, quality settings, suppressions, exclusions, ignores, instructions, and shared artifacts remain unchanged.
This is file-integrity evidence, not a dependency or environment audit.
The parent retains runtime auditing.

New-definition checks found eight additions in the guard module and 21 in the exporter module.
Their maximum lengths are 25 lines. Their maximum parameter counts are five and four.
Configured formatting matches in memory for both modules.
Every original exporter function keeps its line anchor and location-free AST body.
Only the directly coupled 134-to-132 assertion differs.
No historical test repair or baseline rewrite was needed.
The retained source/menu/key comparisons and real SDK evidence are E002 through E026.

| Handoff gate | Final local result |
| --- | --- |
| Real red | Six live failures per module, two count failures, three stale labels |
| G-REM | 638 passed |
| G-TREND | 126 passed, including 118 new real-SDK cases |
| Both deprecated matrices | 48 passed per module |
| G-KEYS | 21 passed |
| G-UPSERT | Seven temporary SQLite cases passed |
| G-REFUSAL | 54 unchanged issue #3305 cases passed |
| G-LABELS | Five fixed-label/identity cases and 70 unchanged portal cases passed |
| G-ALL | 733 passed, zero failed or skipped |
| Ownership | 11 stable open PRs, 85 complete files, zero overlap |
| Generators | Two exact pairs, six byte-equal outputs, zero unexpected paths |
| API `--check` | 16 pages match 293 menus |
| G-DIFF | Clean whitespace, exact 23 paths, empty index |

Post-execution hook configuration was read again without edits.
Commit and persisting context hooks remain unexecuted under the isolation boundary.
The full implementation workflow still has parent-owned gates and analysis open.
No `.spec-context.json`, feature-state file, hook journal, or shared configuration was created or changed.

The parent must independently complete T028 through T036 before T037.
Those tasks own full Ruff/Black/syntax, exact CI mypy, configured Bandit, full test-quality, links, STE, runtime audit, acceptance reruns, and `speckit.analyze`.
The parent then owns one local Conventional Commit with the exact required Copilot trailer.
No parent gate is marked complete here.
Publication remains blocked at queue position 16 after #3366.
Neither this handoff, the initial SHA, sibling completion, nor passing local gates releases publication.

## Independent coding-session evidence

The following evidence comes after the implementation-agent handoff.
The current coding session owns these results.
The publication coordinator owns any later scope decision or publication release.

### E028 — complete syntax, lint, and format scope

The first full Ruff run found nine findings in new test code.
Five findings concerned percent formatting in test diagnostics.
Four findings concerned local import order.
The coding session corrected only those new statements and imports.
The unchanged full gate then passed.

The direct test type check also found invalid dynamic-module annotations and missing type guards.
The coding session added proper type-only imports, explicit fixture types, and checked AST access.
One existing result assertion now checks the complete identifier count before it reads the values.
Its exact value assertion remains unchanged.
The new AST metadata reader rejects missing and malformed mappings through three direct failure cases.
No baseline, suppression, exclusion, or dependency changed.

The release fragment now uses the required heading and change-type bullets.
This corrects the fragment format without changing its scope.

```bash
rtk proxy .venv/bin/python -m py_compile MistHelper.py src/operations/exporting/export/endpoint_family_exporter.py src/operations/exporting/export/endpoint_catalog.py src/foundation/support/refactors/endpoint_primary_key_strategies.py web_portal/menu_registry.py tests/guardrails/test_endpoint_catalog.py tests/unit/export/test_endpoint_family_exporter.py
rtk proxy .venv/bin/ruff check .
rtk proxy .venv/bin/black --check --diff .
```

All final commands exited 0.
Black accepted all 2,000 files in its configured scope.
Ten new guard definitions and 21 new exporter test definitions meet the 25-line and five-parameter limits.
No unrelated formatting occurred.

### E029 — exact CI types and direct test types

```bash
rtk proxy .venv/bin/mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
rtk proxy .venv/bin/mypy tests/guardrails/test_endpoint_catalog.py tests/unit/export/test_endpoint_family_exporter.py --config-file pyproject.toml
```

Both final commands exited 0.
The exact CI command reports no issues in 663 source files.
The additional direct command reports no issues in both changed test files.
Existing informational notes remain.
No type suppression or mypy configuration changed.

### E030 — configured security scope

```bash
rtk proxy .venv/bin/bandit-exclude-check --include-sample ./src/foundation/support/utils/zen_city_metadata.py --include-sample '.\src\foundation\support\utils\zen_city_metadata.py'
rtk proxy .venv/bin/bandit -c pyproject.toml -r .
rtk proxy .venv/bin/bandit -c pyproject.toml -r . --quiet --format json --output data/issue-3335/bandit-final.json
```

All commands exited 0.
The separator guard checked both inclusion samples.
Bandit measured 213,921 lines across 786 file entries.
The report has zero findings and zero read errors.
The existing 64 specific suppressions remain unchanged.
The local JSON report does not enter the feature commit.

### E031 — unchanged complete quality ratchet

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --log-level WARNING
```

The final command exited 0.
The gate checked 992 files and 725 existing findings.
It reports zero new findings, zero parse errors, and 48 existing analyzer skips.
Those analyzer skips are not skipped pytest cases.
Both repository quality inputs remain byte-identical to the base.

### E032 — tracked and new Markdown links

```bash
rtk proxy .venv/bin/markdown-link-check --exclude 'documentation/wiki/**'
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_markdown_links.py -q --timeout=120
```

Both commands exited 0.
The checker read 4,196 tracked Markdown files and found zero broken links.
All three existing guardrail tests passed.
The existing strict file parser separately read all eight feature documents and the release fragment.
All nine new files had zero broken local links.
No file was staged to obtain that coverage.

### E033 — writing scores and known capability limit

The configured STE command read all 23 reserved paths at minimum score 80.
Every path passed.
The measured scores ranged from 84 through 99.
The optional `data/ste_dictionary.json` input was unavailable.
The tool explicitly reported partial coverage and `dictionary_unavailable`.
This result proves the score gate, not complete dictionary coverage.
No dictionary, allowlist, or threshold changed.

### E034 — complete runtime audit

```bash
rtk proxy .venv/bin/python -m pip_audit -r requirements.txt
```

The standard command stopped before auditing.
Its temporary macOS environment hit the known `ensurepip` `SIGABRT`.
The coding session then used the authorized strict alternative:

```bash
rtk proxy env UV_LINK_MODE=copy UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 uv pip compile requirements.txt --python .venv/bin/python --generate-hashes --output-file data/issue-3335/runtime-audit-lock.txt --quiet
rtk proxy .venv/bin/python -m pip_audit --no-deps --disable-pip --require-hashes --strict -r data/issue-3335/runtime-audit-lock.txt
```

Both commands exited 0.
The local lock contains all 105 resolved runtime packages.
The strict audit reports no known vulnerabilities.
No advisory was ignored.
No package or manifest changed during this audit.
The lock belongs to this worktree and does not enter the feature commit.
The Git-only `misthelper-devtools` development requirement remains outside this runtime audit.
This result does not claim an audit of that development requirement.

### E035 — independent preservation and acceptance evidence

The coding session ran the G-ALL, G-KEYS, G-UPSERT, and G-REFUSAL selectors in one pytest command.
It also included unchanged neighboring exporters, endpoint safety, and generator tests.
The final command collected and passed 1,206 cases.
It reported zero failures and zero skips.
The site lock audit trail remained empty.

The complete selector set was:

```bash
rtk proxy .venv/bin/python -m pytest tests/guardrails/test_endpoint_catalog.py tests/guardrails/test_endpoint_backlog_safety.py tests/unit/export/test_endpoint_family_exporter.py tests/unit/export/test_simple_endpoint_exporter.py tests/unit/export/test_count_exporter.py tests/unit/web_portal/test_portal_label_accuracy.py tests/unit/web_portal/test_portal_required_answers.py tests/contract/test_export_api_function_names.py::test_source_export_calls_name_the_api_function tests/unit/db/test_database_schema_utils.py::TestGetEndpointStrategy tests/unit/db/test_database_schema_utils.py::TestBuildNaturalPkSql tests/unit/db/test_database_schema_utils.py::TestBuildCompositePkSql tests/unit/db/test_database_schema_utils.py::TestBuildAutoincrementSql tests/unit/db/test_database_schema_utils.py::TestBuildCreateTableSql tests/unit/export/test_data_exporter.py::TestWriteWithFormatSelection tests/unit/export/test_data_exporter.py::TestRouteToPolyglot tests/integration/test_menu_12_sqlite_upsert.py::TestSQLiteUpsertIdempotency tests/integration/test_menu_13_sqlite_upsert.py::TestSQLiteUpsertIdempotency tests/unit/export/test_export_notice_separator.py::test_a_refused_insight_request_names_the_http_status tests/unit/scripts/test_menu_api_map.py -q --timeout=120
```

The coding session also reconstructed the exact retired rows from the base AST.
The same guard rejected both identifiers in all three reconstructed sources.
It accepted all three current sources.
No live registration changed during that proof.

| Source | Reconstructed red input | Current green input |
| --- | ---: | ---: |
| Selectable | 286 | 284 |
| Catalog | 286 | 284 |
| PK | 571 | 569 |

Five complete production AST comparisons permit only the two exact registrations, coupled labels, and catalog count changes.
All five comparisons passed.
Eleven protected files remain byte-identical, including manifests, SDK index, quality inputs, shared state, and shared documents.
The exporter methods and persistence behavior remain unchanged.

The coding session rendered both wiki pages in memory from all 293 menu entries.
Both current files match that fresh rendering.
All six reference hashes match the repeated-generation measurements in E023.
The API map check passes 16 pages for 293 menus.
No independent comparison wrote a file.

The initial T035 acceptance decision paused because the response check below identified a replacement-output gap.
The coordinator then confirmed metadata-only scope and excluded that separate defect.
T035 now proves offered entries and unchanged invocation behavior.
Passing synthetic list and `results` cases does not resolve the separate defect.

### Confirmed separate defect — documented trend objects lose their records

The two endpoint documents describe non-paginated object responses:

- `documentation/api/sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_summary-trend.md`
- `documentation/api/sites/GET_sites_site_id_sle_scope_scope_id_metric_metric_classifier_classifier_summary-trend.md`

The summary object contains `start`, `end`, `classifiers`, and `sle`.
The classifier object contains `start`, `end`, `metric`, and `classifier`.
Neither documented object contains `results`.

The coding session constructed two valid local responses with those shapes.
Real SDK 0.64.0 `APIResponse` decoded each response with status 200 and no next page.
Real `mistapi.get_all` then returned zero records for both objects.
The unchanged `_run` method always uses that helper.
Its call therefore supplies an empty list to `_persist`.
The existing `_normalize` method would retain the same object as one row if it received the raw object.

| Operation | Decoded object | Pagination records | Existing object normalization |
| --- | --- | ---: | ---: |
| `getSiteSleSummaryTrend` | Matches the documented shape | 0 | 1 |
| `getSiteSleClassifierSummaryTrend` | Matches the documented shape | 0 | 1 |

The proof checked both objects without a network call, credential, store change, or production edit.
The coding session reported the gap to the publication coordinator before any broader change.
The coordinator confirmed metadata-only scope and required a separate issue.
Seven live searches found no exact open duplicate.
The historical matches concerned endpoint discovery and initial feature delivery.
The coding session read `.github/ISSUE_TEMPLATE/bug-report.yml` and preserved all six form fields.
[Issue #3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699) now records both shapes and the real SDK proof.
It has `bug`, `src`, `export`, and `mistapi` labels and no assignee.
This coding session does not implement that issue.
No exporter behavior, dependency, or store changed.
Do not claim that the documented trend-object defect is repaired.

### E036 — required SpecKit analysis and approved disposition

The read-only `speckit.analyze` workflow read all eight feature documents, relevant source/tests, and installed SDK code.
It checked all 13 functional requirements, eight success criteria, six verification constraints, and 37 tasks.
Every requirement had a task association.
The analysis made no file, Git, dependency, ownership, store, or cloud change.

The initial analysis found two critical and two high findings:

| Finding | Initial result | Approved disposition |
| --- | --- | --- |
| I1, documented trend objects become empty | Critical existing output defect | The separate issue owns the repair. The coordinator excludes response changes from #3335. |
| I2, working exports conflict with unchanged behavior | High artifact conflict | User Story 2 and SC-003/SC-007 now require offered entries and unchanged resolution/invocation. |
| C1, generic positive fixtures do not prove canonical objects | High coverage distinction | The tests and documents now label this evidence as generic processing preservation, not canonical export success. |
| C2, unchanged constitution conflicts with exact-path and rare-comment instructions | Critical certification conflict | The plan records the conflict and removes its unqualified pass claim. No governance file changed. |

The original observations remain valid.
Recording the separate issue does not repair its behavior or establish positive canonical object coverage.
The specific coordinator decision controls this metadata-only local implementation.
The local commit is authorized after the measured code gates.
Full constitution and deployment certification remain conditional on separate approval and evidence.
Do not treat those unperformed certification steps as passed.
The coding session makes no constitution, shared-state, comment-sweep, deployment, or protection change.

The specification, plan, research, data model, contract, validation guide, checklist, release fragment, and task evidence reflect this decision.
The exporter methods remain unchanged.

### Conditional delivery boundary

| Stage | Required condition | Current state |
| --- | --- | --- |
| Local metadata commit | Exact 23-path boundary, local gates, recorded analysis disposition, and coordinator authorization | Authorized after final file checks. |
| Remote publication | Explicit position-16 verified-main grant after issue #3366 and queue predecessors | Not authorized. |
| Pull request and protected merge | Granted current base, repeated local proof, original 23-item template, latest quality/title/CodeQL checks, and protected exact-head squash | Not performed. |
| Exact merged-main local proof | Confirmed merged revision and repeated local evidence for that exact revision | Not performed. |

A passing gate, the initial base, an observed main revision, or a sibling message is not a publication grant.
Never use `--admin`, a protection override, or `--delete-branch`.
Report the actual local commit SHA and companion issue number to the coordinator.
Do not create another repair or implement the companion issue in this branch.

### E037 — authorized local commit preparation

The coordinator authorized the metadata-only local commit.
The coding session staged all 23 exact reserved paths.
The index matches that set exactly and passes the cached whitespace check.
No unstaged or untracked feature path remains outside that set.
The branch is `jmorrison-juniper-deprecated-sle-operations`.
The commit starts from the verified base `856e5065413d3026f9c0f6d5222d9d379ec79d8b`.

The final metadata-only rerun passed 1,206 focused tests without failures or skips.
Full Ruff passes. Full Black accepts 2,000 files.
Exact CI mypy passes 663 source files, and direct mypy passes both changed test files.
The full unchanged ratchet checks 992 files and reports zero new findings.
The API map guard validates 16 pages for 293 menu options.
The strict hashed runtime audit again reports zero advisories across 105 resolved packages.
All 23 final STE scores pass at 85 through 99, with the same explicit optional dictionary limitation.
All nine current feature and fragment documents have valid local links.
The exporter methods, dependency manifests, primary-key merge behavior, shared records, and protected inputs remain unchanged.

All local preparation checkboxes are complete.
The actual commit command follows this preparation.
Its full SHA and clean-status proof belong in the coordinator handoff after that command succeeds.
Do not amend the commit to insert its own SHA into this file.
The separate issue remains unassigned and unrepaired by this branch.
Publication, protected merge, deployment, and exact merged-main proof remain conditional and unperformed.

## Local refresh on the immutable authorized base

This section records the later local refresh, not a publication receipt.
The exact authorized base is `1a06f1516223a20eef715d91a32255e6219331db`.
The coordinator did not grant push, PR creation, workflow execution, automatic merge, protected merge, or delivery.
Issue #3366 and pull request #3727 retain the sole publication window.
The later grant must identify the actual verified issue #3366 merge SHA.
That grant requires a new rebase and fresh verification of the newer complete tree.

### Preservation and reclaimed ownership

The original clean preparation is preserved by this local tag:

```text
preservation/issue3335-local-623a48c88feb4cf5716f3986587f4971a51ffb6a
```

The tag resolves to `623a48c88feb4cf5716f3986587f4971a51ffb6a`.
The owned branch rebased cleanly onto the authorized immutable base.
No conflict, shared-checkout access, fetch, or publication occurred.
Its rebased preparation is `5b1c40ab64253e4c27fec15575da3a1afcea4ec9`.

The prerequisite issue #3709 is closed, and pull request #3713 is merged.
The original claim again reserves all 23 feature paths.
The exact four reclaimed paths are the two API-map indexes and two interactive-safe pages.
The prerequisite is not republished.
The unresolved companion issue #3699 remains open and unassigned.
This branch does not repair or close it.

The live check read one stable open pull request and all eight exact file entries.
The check included renamed paths and matched each list against its declared file count.
No reserved path overlapped.
The same complete check ran immediately before generation.

### Unchanged environment and exact source proof

`requirements.txt`, `requirements-dev.txt`, and `pyproject.toml` match the original preparation and the immutable base.
The own environment uses Python 3.13.13 and `mistapi` 0.64.0.
The configured development tools remain installed at their current pins.
No package install, manifest, dependency, suppression, exclusion, baseline, or governance change was needed.

Five complete production AST comparisons permit only the two exact metadata removals and coupled counts.
All five comparisons pass against the immutable base.
All 15 `EndpointFamilyExporter` method bodies remain unchanged, including `_run`.
Fifteen protected inputs remain byte-identical to that base.
Those inputs include manifests, workflow settings, quality baselines, SDK index, shared records, and governance files.
The complete branch difference contains exactly the original 23 reserved paths.
Every unowned API reference page is byte-identical to the immutable base.
This preserves the current report and fingerprint repairs.

The refreshed guard proof reconstructs the two exact obsolete rows from the immutable base.
The real guard rejects both names in all three reconstructed sources.
It accepts all three current sources without changing any live registration.

| Source | Immutable-base red count | Refreshed green count |
| --- | ---: | ---: |
| Selectable | 286 | 284 |
| Catalog | 286 | 284 |
| PK | 571 | 569 |

Both documented top-level object responses still decode at HTTP 200 with no next page.
The unchanged SDK collector returns zero rows, while the unchanged normalizer retains one raw-object row.
This verifies that the separate companion defect remains unresolved.
It does not establish working canonical object exports.

### Combined generator proof

Both documented generator commands ran twice:

```bash
rtk proxy .venv/bin/python scripts/generate_menu_wiki.py
rtk proxy .venv/bin/python -m scripts.menu_api_map
rtk proxy .venv/bin/python -m scripts.menu_api_map --check
```

The rebase already preserved the combined generated output.
Both generator passes wrote zero changed API-map pages and removed zero pages.
Both wiki outputs match.
All 18 generated outputs were byte-identical across both passes, with 1,551,817 total bytes.
No unowned output changed.
The API map check passes all 16 pages for 293 menus.

| Owned reference | Refreshed SHA-256 |
| --- | --- |
| `documentation/menu_reference.md` | `1e41d53f8281753396ab8f4fc3d253f00c171e2dd3761f7d20677e620f507a86` |
| `documentation/wiki/Menu-Reference.md` | `1e41d53f8281753396ab8f4fc3d253f00c171e2dd3761f7d20677e620f507a86` |
| `documentation/menu-api/README.md` | `ee825c0ec18bb432a8907b7b872d577f948f0a628c68a9adb6c3a87d8b5c0399` |
| `documentation/menu-api/interactive-safe.md` | `648282509d7cbd040f666a990f37fafb8d51ffd3a33ae0fa62d3c575441f230f` |
| `documentation/wiki/Menu-API-Endpoints.md` | `17d004917c13fc99b6ceffa07675f5b2445c13a83ff59d4203425d60d12158b8` |
| `documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md` | `e3b50bf36504c96825646e80a9f788b943649f65d2baae88e0a2c9c2300ad8b7` |

### Repeated local gates and explicit limits

The same 1,206 owned, neighboring, portal, key, upsert, refusal, and generator cases passed.
No pytest case failed or skipped.
The command used the complete E035 selector set with these additional arguments:

```text
--cov=src.operations.exporting.export.endpoint_family_exporter
--cov=src.operations.exporting.export.endpoint_catalog
--cov=src.foundation.support.refactors.endpoint_primary_key_strategies
--cov-report=term-missing
--cov-fail-under=80
```

The command set `COVERAGE_FILE=data/issue-3335/refresh-coverage`.
The three metadata modules measured 93.99 percent combined coverage.
The catalog and PK modules each measured 100 percent.
The exporter module measured 93 percent.
This scoped result does not measure full-repository coverage.

| Exact repeated gate | Result |
| --- | --- |
| `rtk proxy .venv/bin/python -m py_compile MistHelper.py src/operations/exporting/export/endpoint_family_exporter.py src/operations/exporting/export/endpoint_catalog.py src/foundation/support/refactors/endpoint_primary_key_strategies.py web_portal/menu_registry.py tests/guardrails/test_endpoint_catalog.py tests/unit/export/test_endpoint_family_exporter.py` | Pass. |
| `rtk proxy .venv/bin/ruff check .` | Pass. |
| `rtk proxy .venv/bin/black --check --diff .` | Pass, 2,016 files. |
| `rtk proxy .venv/bin/mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Pass, 665 source files. |
| `rtk proxy .venv/bin/mypy tests/guardrails/test_endpoint_catalog.py tests/unit/export/test_endpoint_family_exporter.py --config-file pyproject.toml` | Pass, both changed test files. |
| `rtk proxy .venv/bin/bandit-exclude-check --include-sample ./src/foundation/support/utils/zen_city_metadata.py --include-sample '.\src\foundation\support\utils\zen_city_metadata.py'` | Pass, both separator samples. |
| `rtk proxy .venv/bin/bandit -c pyproject.toml -r . --quiet --format json --output data/issue-3335/bandit-refresh.json` | Pass, 788 file entries and 214,955 lines, zero findings or read errors. |
| `rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --log-level WARNING` | Pass, 1,001 files and 725 old findings, zero new findings or parse errors. |
| `rtk proxy .venv/bin/diagram-refs --source-files MistHelper.py src/ --allowlist-file .github/diagram-refs-allowlist.txt` | Pass, 153 references across 15 diagram files. |
| `rtk proxy .venv/bin/check-citations src tests` | Pass, 251 citations and zero unresolved. |
| `rtk proxy .venv/bin/markdown-link-check --exclude 'documentation/wiki/**'` | Pass, 4,270 tracked files and zero broken links. |
| `rtk proxy .venv/bin/python -m pytest tests/guardrails/test_markdown_links.py -q --timeout=120` | Pass, three cases. |
| `rtk proxy .venv/bin/ste-linter --config .ste-linter.toml --min-score 80 --quiet <all 23 exact feature paths>` | All scores pass at 85 through 99. Dictionary coverage is partial. |

The test analyzer retains 48 configured skips.
They are not skipped pytest cases.
Bandit retains the existing 64 specific suppressions.
No baseline, rule, suppression, threshold, or allowlist changed.
The STE tool explicitly names `data/ste_dictionary.json` as unavailable.
Dictionary validation did not run and is not a pass.

The standard runtime audit again stopped during the known macOS `ensurepip` abort:

```bash
rtk proxy .venv/bin/python -m pip_audit -r requirements.txt
```

The authorized strict alternative passed:

```bash
rtk proxy env UV_LINK_MODE=copy UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 uv pip compile requirements.txt --python .venv/bin/python --generate-hashes --output-file data/issue-3335/refresh-runtime-audit-lock.txt --quiet
rtk proxy .venv/bin/python -m pip_audit --no-deps --disable-pip --require-hashes --strict -r data/issue-3335/refresh-runtime-audit-lock.txt
```

It checked all 105 resolved, fully hashed runtime packages and found zero advisories.
No advisory was ignored.
The Git-only development tool remains outside that runtime audit.
The local lock and coverage file do not enter the commit.

### Offline template and held publication

The coding session read the current `.github/PULL_REQUEST_TEMPLATE.md`.
The offline body preserves all headings, the issue-number comment, and all 23 original checklist items.
It records exact current commands, results, and limits in the session artifact area.
It is not a live pull request.
Full-repository coverage, live Mist execution, browser journeys, container execution, CI, title checks, and CodeQL remain unperformed.
No unmet or unperformed criterion is represented as passed.

The refreshed local commit records only the current feature evidence within the existing reservation.
It changes no production method, test behavior, generator, dependency, baseline, or governance file.
The original preparation remains preserved.
The final clean local SHA belongs in the coordinator handoff after the commit succeeds.
No push, pull request, workflow start, automatic merge, protected merge, deployment, or actual-main delivery is authorized.

## Granted position-16 publication and delivery

The coordinator explicitly grants publication and delivery on exact main `df6889a40464db9dd7281765b5a58b993e33a7ed`.
This section supersedes earlier waiting boundaries for this issue only.
It does not authorize issue #3699, another repair, source behavior, or production actions.
Only the parent coordinator can release the next issue.

### Delivery tasks and immutable boundaries

- [X] T038 Verify the live grant, preserve both preparations, rebase the owned tree, and repeat current local proofs in `specs/3335-deprecated-sle-operations/tasks.md`. (delivered: `specs/3335-deprecated-sle-operations/tasks.md`; the measured granted-base evidence below passes.)
- [ ] T039 Commit the exact reserved feature, run required-input preflight and both committed/current full ratchets, push once, and create the single-owner PR from the current 23-item template. Record exact results through the PR protocol comment and session receipt.
- [ ] T040 Require all fresh latest-head quality, title, applicable STE, CodeQL analysis, and separate required CodeQL records. Recheck all 15 strict contexts, exact granted base, and full head before protected squash. Record the premerge proof in the PR.
- [ ] T041 Prove the actual resulting main SHA, parent, complete tree, and local results. Preserve the checked source, clean up named temporary output, and post the persistent PR receipt. Report the full SHA/tree/receipt to the coordinator, then pause.

These delivery tasks are incomplete in this pre-publication snapshot.
Their later measured completion belongs in the persistent PR receipt.
Do not push a post-merge bookkeeping commit to tick a historical snapshot.
No old-base result, generic completion message, skipped check, or advisory alone establishes delivery.

### Current grant and preservation proof

Live main matches the exact grant and has parent `1a06f1516223a20eef715d91a32255e6219331db`.
Its complete tree is `4f2460f125cd0c69379fc85cbf1a5616d4e54079`.
The Maps actual-main receipt was read in full.
The live inventory has zero open PRs, zero exact PR file entries, and no automatic merge request.
The original public claim reserves all 23 paths and records the full grant.
The companion issue remains open and unassigned.

The original preservation tag remains unchanged.
The following additional local tag preserves the completed local-only refresh:

```text
preservation/issue3335-refresh-bd962ceaa467b513cd2bac924135265bda3f80c6
```

The owned branch rebased cleanly onto the exact granted base.
All dependency manifests remain unchanged, so no environment install was required.
Five complete production AST comparisons permit only the two exact metadata removals and coupled count corrections.
All 15 exporter method bodies remain unchanged, including `_run`.
Sixteen protected inputs remain byte-identical to the granted base, including the corrected Maps template.
Every unowned file and combined report/fingerprint repair remains intact.
The complete feature difference is still exactly the original 23 reserved paths.

### Current generators and guard decisions

The complete live ownership check repeated immediately before generation.
Both existing scripts then ran twice on the combined granted tree.
All 18 generated outputs and 1,551,817 bytes match across both passes.
Both wiki pages match each other.
No output outside the reservation changed.
The API map guard passes all 16 pages for 293 menus.
The six owned hashes match the preceding local-refresh table.

The fresh guard matrices pass all 96 selected cases without skips.
The direct granted-base reconstruction rejects both obsolete names in all three sources.
The current sources pass at 284, 284, and 569 measured records.
Each exact shaped injection rejects at 285, 285, or 570 measured records.
The granted-base red counts remain 286, 286, and 571.
No production registration was modified during a guard proof.

### Fresh local results on the granted tree

The complete 1,206-case focused regression command passes without failures or skips.
Its three metadata modules measure 93.99 percent combined coverage.
That result is scoped metadata coverage, not full-repository coverage.
The separate 736-case core command also passes without failures or skips.
Both commands are the exact preceding selector sets, with publication-specific output paths.
The current tests include all offered trend, absent-SDK-attribute, neighboring-family, key, temporary-upsert, and refusal cases.
They do not repair or certify canonical object exports for the companion issue.

| Fresh command on the granted tree | Result |
| --- | --- |
| `rtk proxy .venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | Pass, six input reads/validations and three guide checks. |
| `rtk proxy .venv/bin/python -m py_compile MistHelper.py src/operations/exporting/export/endpoint_family_exporter.py src/operations/exporting/export/endpoint_catalog.py src/foundation/support/refactors/endpoint_primary_key_strategies.py web_portal/menu_registry.py tests/guardrails/test_endpoint_catalog.py tests/unit/export/test_endpoint_family_exporter.py` | Pass. |
| `rtk proxy .venv/bin/ruff check .` | Pass. |
| `rtk proxy .venv/bin/black --check --diff .` | Pass, 2,018 files. |
| `rtk proxy .venv/bin/mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Pass, 665 source files. |
| `rtk proxy .venv/bin/mypy tests/guardrails/test_endpoint_catalog.py tests/unit/export/test_endpoint_family_exporter.py --config-file pyproject.toml` | Pass, both changed test files. |
| `rtk proxy .venv/bin/bandit-exclude-check --include-sample ./src/foundation/support/utils/zen_city_metadata.py --include-sample '.\src\foundation\support\utils\zen_city_metadata.py'` | Pass, both inclusion samples. |
| `rtk proxy .venv/bin/bandit -c pyproject.toml -r . --quiet --format json --output data/issue-3335/bandit-publication.json` | Pass, 788 file entries and 214,955 lines, zero findings/read errors. |
| `rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --log-level WARNING` | Pass, 1,003 discovered files and 725 old findings, zero new findings/parse errors. |
| `rtk proxy .venv/bin/pylint src/ --fail-under=9.5 --reports=n` | Pass, score 9.83/10. Existing diagnostic messages remain visible. |
| `rtk proxy .venv/bin/pydocstyle src/ wsgi.py web_portal` | Pass. |
| `rtk proxy .venv/bin/interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v` | Pass, 99.6 percent across 13,213 definitions. |
| `rtk proxy .venv/bin/vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | Pass, zero findings. |
| `rtk proxy .venv/bin/radon cc src/ MistHelper.py wsgi.py scripts/analyze_marvis_pcap.py scripts/probe_zscaler_endpoints.py tests/unit/utils/test_zscaler_catalogue.py -j` into `rtk proxy .venv/bin/complexity-gate --max 10` | Pass at the exact current CI scope. |
| `rtk proxy .venv/bin/diagram-refs --source-files MistHelper.py src/ --allowlist-file .github/diagram-refs-allowlist.txt` | Pass, 153 references across 15 diagram files. |
| `rtk proxy .venv/bin/check-citations src tests` | Pass, 251 citations and zero unresolved. |
| `rtk proxy .venv/bin/markdown-link-check --exclude 'documentation/wiki/**'` | Pass, 4,275 tracked files and zero broken links. |
| `rtk proxy .venv/bin/codeql-verdict-register check` | Pass, all 88 dismissed-alert records match. This is not a new CodeQL scan. |

The full test-quality input preflight must repeat before the post-commit analyzer commands.
The committed ratchet compares the fetched intended `origin/main` against `HEAD` with both explicit full-gate trigger paths.
The complete local ratchet must also pass before push.
Neither baseline nor settings changed.

The standard runtime audit again stopped before scanning because macOS `ensurepip` aborted.
The strict own-worktree hashed alternative passed all 105 current runtime packages without ignored advisories:

```bash
rtk proxy env UV_LINK_MODE=copy UV_NATIVE_TLS=1 UV_SYSTEM_CERTS=1 uv pip compile requirements.txt --python .venv/bin/python --generate-hashes --output-file data/issue-3335/publication-runtime-audit-lock.txt --quiet
rtk proxy .venv/bin/python -m pip_audit --no-deps --disable-pip --require-hashes --strict -r data/issue-3335/publication-runtime-audit-lock.txt
```

The Git-only development tool remains outside that runtime audit.
STE score validation retains the configured minimum and explicitly unavailable licensed dictionary.
Dictionary checks, local full-suite coverage, live Mist, browser-agent, container, firmware, and deployment results are not claimed.
Fresh PR quality/title/STE/CodeQL results and actual-main proof belong to the later receipts.

### Protected publication conditions

Main protection is strict and enforces administrators.
All 15 required contexts retain their exact names and application constraints.
The separate required CodeQL result must not be substituted by the workflow analysis job alone.
Every fresh applicable check must report success on the exact latest source or verified test-merge revision.
An unrelated main advance, conflicting PR owner, or incomplete required result stops the merge.
The final merge must use the full checked head match and squash through normal protection.
Never use administrator bypass, automatic merge, or branch deletion.
No manual workflow dispatch is authorized.

The actual resulting main must have the granted base as its parent.
Its complete tree must equal the checked source tree.
The actual-main local commands must execute on that exact resulting commit in this own worktree.
The final PR receipt records all full SHAs, trees, fresh results, exact commands, limits, cleanup, and the unresolved companion.
Only after that persistent receipt may this session report completion and pause.
