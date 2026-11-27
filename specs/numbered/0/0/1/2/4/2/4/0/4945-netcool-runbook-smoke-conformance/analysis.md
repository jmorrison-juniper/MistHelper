# Specification Analysis Report: Netcool Runbook Smoke Package Conformance

**Scope**: Consistency review across `spec.md`, `plan.md`, and `tasks.md`, checked against the remote tree of `main` (blob SHAs in `design/research.md`). This report also records the defects in the existing package.

## Findings

| ID | Category | Severity | Location | Finding | Resolution |
| - | - | - | - | - | - |
| A-01 | Scope | High | Issue body, item 1. Function limits. | The issue names 14 functions. The statement limit of five per block explains exactly these 14 functions. A physical line count with docstrings included would flag 43 functions. | Decision D-1 and D-2 use code lines without docstrings and the statement limit. The 14 functions match the issue. |
| A-02 | Ambiguity | Medium | `constitution.md` line 38, five-item rule, module level. | The rule does not say whether the module logger counts as a top-level name. With the logger counted, eight modules break the limit. Without it, none do. | Decision D-3 counts the logger. The target layout passes both readings. |
| A-03 | Gap | High | Repository tooling. | No structure scanner exists for `scripts/`. `tests/guardrails/test_nested_package_structure.py` scans `src` only (line 16 `SOURCE_ROOT = "src"`). | Decision D-9 extends that file (T006). |
| A-04 | Gap | High | `ci.yml` lines 93, 99, 101, 104, 107. `pyproject.toml` lines 206, 324, 506. | Seven gates skip the package. Three exclusions remove it from Ruff, mypy, and Bandit. | Decision D-12 adds the package path and count steps (T027 to T029). |
| A-05 | Inconsistency | Medium | Issue body, acceptance criteria. | The issue states 227 existing tests. A static count of `def test_` in the five test modules gives 194. Twelve `parametrize` decorators exist. The collected count is not measured. | Decision D-15 uses the collected count before and after the change. The count appears in T003. |
| A-06 | Unverified | Medium | Issue body, problem item 2. | The issue reports 12 of 20 test comments and 5 of 25 package comments as weak. The sample was not reproduced. | T035 repeats the audit with a fixed seed (decision D-24). |
| A-07 | Gap | Medium | `ci.yml` line 311, `--cov=${{ env.SRC_PATH }}`. | CI gates coverage of `src` only. The package has no coverage gate. | Decision D-14 measures the package locally and records the value in the pull request. |
| A-08 | Conflict | Medium | `changelog.d/README.md` line 58 and the constitution, Documentation section. | The README says no fragment for an internal-only change. The constitution says each change MUST add one fragment. | Decision D-16. The constitution outranks the README. |
| A-09 | Governance | Medium | Constitution, Governance, lines 548 to 550. Issue #4937 (closed). | A compliance table MUST separate grandfathered debt from new design. The package remains a direct child of `scripts/`. | The Complexity Tracking table in `plan.md` separates the two. Issue #4944 tracks the folder debt. |
| A-10 | Risk | High | `pyproject.toml` line 506, `[tool.bandit] exclude_dirs` names `scripts`. | An explicit Bandit path may still skip the package. | The Bandit step counts files and fails at zero (T028). TEST-08 injects a violation. |
| A-11 | Risk | Medium | `pyproject.toml` line 206, `[tool.ruff] extend-exclude` names `scripts`. | An explicit Ruff path may still skip the package. | The Ruff step counts files and fails at zero (T028). TEST-08 injects a violation. |
| A-12 | Constraint | Medium | `tests/unit/scripts/netcool_runbook_smoke/`, five children on `main`. | A sixth test module breaks the five-child rule. | Decision D-11 keeps the five modules and puts new tests into them. |
| A-13 | Constraint | Low | `Dockerfile` COPY lines 70 to 149 on `main`. | The image does not contain the repository `scripts/` folder. | Decision D-22 records that step 12 of Principle IV does not apply. |
| A-14 | Risk | Medium | `command.py` line 63 `PACKAGE_LOGGERS`, line 73 loop. | Module logger names change with the move. | TEST-10 proves that the prefix `scripts.netcool_runbook_smoke` covers each new logger. |
| A-15 | Dependency | Low | `ci.yml` line 702, `check-citations src tests`. | The citation gate reads `src` and `tests` only. | No action. The spec record under `specs/` stays outside the gate. |
| A-16 | Advisory | Low | `ci.yml` line 750, `speckit-task-audit \|\| true`. | The task audit is advisory. | `tasks.md` uses the checkbox format that the audit reads (`CHECKBOX_RE`). |
| A-17 | Defect, existing | Medium | `client.py` 428 to 469 and 471 to 508, `checks/scope.py` and `checks/searches.py` 14 functions. | The functions mix several rules in one block. Each block holds up to 12 statements. | Phase 4 splits them (T021 to T025). |
| A-18 | Defect, existing | Medium | `checks/scope.py` 184, 331, 380, and `checks/searches.py` 395. Classes at five methods. | Each full class blocks the helper that a split needs. | The plan adds nine helper classes (T021 to T025). |
| A-19 | Defect, existing | Low | Package comments. Issue item 2. | Some comments restate the code. The issue reports the rate. | FR-011 and FR-012 and T033 to T035. |
| A-20 | Defect, existing | Low | `test_netcool_smoke_checks.py` and related modules. | Import paths name the old modules. The change must update every import. | FR-009 and T017 to T019. |

No runtime defect was found in the read paths of the package. The defects are structural and documentary. Mist REST calls use `APISession.mist_get`, and no direct HTTP request exists.

## Coverage Summary

| Requirement | Tasks | Tests or gates |
| - | - | - |
| FR-001, function code lines | T006, T021 to T025, T026 | TEST-01 |
| FR-002, function parameters | T006, T026 | TEST-01 |
| FR-003, body blocks and statements | T006, T021 to T025, T026 | TEST-01 |
| FR-004, class methods | T006, T026 | TEST-04 |
| FR-005, module top-level names | T006, T026 | TEST-02 |
| FR-006, directory children | T006, T026 | TEST-03 |
| FR-007, fourteen named functions | T001, T021 to T025 | TEST-01, TEST-12 to TEST-16 |
| FR-008, sub-package layout and empty `__init__.py` | T009 to T015 | TEST-10 |
| FR-009, import paths | T009 to T019 | TEST-10, Old paths gate |
| FR-010, entry point | T016, T020, T037 | TEST-10, Safe sweep gate |
| FR-011, statement comments | T033 | TEST-05 |
| FR-012, sample audit | T035 | Sample procedure in `design/quickstart.md` |
| FR-013, action logging | T034 | TEST-05 |
| FR-014, seven gates name the package | T002, T004, T027, T028, T031 | TEST-06 |
| FR-015, count steps | T028, T029 | TEST-07 |
| FR-016, gate guard | T007 | TEST-06, TEST-07 |
| FR-017, injected violations | T008 | TEST-08, TEST-09 |
| FR-018, job count | T032 | TEST-06 |
| FR-019, mypy strict | T004, T030 | Types gate |
| FR-020, package coverage | T005, T-LOCAL-GATES | Coverage gate, package target |
| FR-021, tests unchanged | T003, T-LOCAL-GATES | Tests gate |
| FR-022, console and evidence | T003, T036 | Fixed fake-session test |
| FR-023, Mist calls and output paths | T016, T036 | TEST-17 |
| FR-024, changelog fragment | T038 | Tests gate for the changelog guard |
| FR-025, pull request body | T-PR | Pull request review |

Each user story maps to tasks. US1 maps to T006, T009 to T026. US2 maps to T007, T008, T027 to T032. US3 maps to T033 to T035. US4 maps to T003, T036 to T038.

## Constitution Alignment

- Principle I, five-item rule: Fails today and passes after the change. The Complexity Tracking table records the grandfathered debt (A-09).
- Principle II, class-based design: Passes. Each helper lives in a class (decision D-25).
- Principle III, safety first: Passes. No input path changes. Redaction stays in `EvidenceRedactor` and `LogSetup`.
- Principle IV, deployment pipeline: Passes with the recorded step 12 exception (A-13).
- Principle V, observability: Passes. ASCII output stays.
- Principle VI, inline comments: Fails today for some statements. T033 and TEST-05 repair the gap.
- Principle VII, action logging: Fails today for some touched actions. T034 repairs the gap.

## Unmapped Tasks

None. Each task maps to at least one requirement. `T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, and `T-MERGE` map to FR-020, FR-021, FR-025, SC-003, and SC-008.

## Metrics

- Functional requirements: 25 (FR-001 to FR-025).
- Success criteria: 8 (SC-001 to SC-008).
- Tasks: 42 (T001 to T038, and four final tasks).
- Tests planned: 17 (TEST-01 to TEST-17).
- Decisions: 26 (D-1 to D-26). No decision requires a human.
- Functions examined in the package: 189. Functions that break a limit: 14.
- Classes today: 45. Classes after the change: 54 (nine new helper classes).
- Python files today: 11 in the package. Python files after the change: 37, including `__init__.py` files.
- Remote checks: 103 rows (`design/research.md`). The same count appears in `STATUS.json` and `summary.md`.

## Unresolved Items

1. The mypy strict result for the package is not measured. T004 measures it.
2. The radon, Vulture, pydocstyle, and Interrogate results for the package are not measured. T004 measures them.
3. The collected test count and the package coverage before the change are not measured. T003 and T005 measure them.
4. Explicit Ruff and Bandit runs on the package are not measured. The count step decides the behavior.
5. The pinned versions of the gate tools in `requirements-dev.txt` are not read. The research file lists them as unverified.
6. The baseline of the test-quality analyzer for the five test modules is not read. The local gate reads it during T-LOCAL-GATES.
7. The comment sample baseline of the issue is not reproduced (A-06).
