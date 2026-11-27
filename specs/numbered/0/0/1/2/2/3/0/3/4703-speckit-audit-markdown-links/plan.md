# Implementation Plan: SpecKit Task Audit Link and Legend Classification

**Branch**: `fix/4703-speckit-audit-markdown-links` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification at `specs/numbered/0/0/1/2/2/3/0/3/4703-speckit-audit-markdown-links/spec.md`. The route `0/0/1/2/2/3/0/3` is base five for issue 4703, as RC-45 shows.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The repair already reaches MistHelper through the pinned devtools commit. This change adds two regression tests, one documentation update, one release-note fragment, and this record. It changes no runtime code.

## Technical Context

- **Language/Version**: Python 3.15 or newer, as stated in `.github/copilot-instructions.md` (section Language and environment).
- **Primary Dependencies**: misthelper-devtools pinned at commit `2239e7bd` through `requirements-dev.txt` line 197 (RC-11). The pin supplies the `speckit-task-audit` command.
- **Storage**: Not applicable. The change writes no data.
- **Testing**: pytest. The regression tests live in `tests/guardrails/test_process_folder_structure.py`.
- **Target Platform**: Windows 11, macOS, and Linux. The tests use `tmp_path` and create no platform-specific path.
- **Project Type**: CI tooling and documentation.
- **Performance Goals**: Not applicable. The audit job took about 65 seconds in run 45774119357, job 139753527621.
- **Constraints**: The audit job is advisory. The printed strings form a contract, described in `design/contracts/speckit-audit-report.md`.
- **Scale/Scope**: 922 feature records, 442 task files, and 11681 task markers in run 45774119357.

## Constitution Check

Each rule of `.specify/memory/constitution.md` (version 1.9.0) and `.github/copilot-instructions.md` receives one result.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The record adds one child under the route leaf. The test change edits an existing file. `tests/guardrails` already holds 79 entries, so this change adds no file there (RC-48). |
| I. Managed roots | Pass | Route `0/0/1/2/2/3/0/3` uses digits 0 to 4 under `specs/numbered/` (RC-45). The route folder is absent on `main` (RC-46). |
| II. Class-based architecture | Pass | The tests are module-level functions in an existing test module. No production wrapper is added. |
| III. Safety-first | Pass | The change adds no input read, no destructive operation, and no credential. |
| IV. Full deployment pipeline | Pass with a note | Steps 1 to 9 run in T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Steps 10 to 12 do not run, because `container-build.yml` runs only for product file changes (RC-41). |
| V. Observability | Pass | The tests print nothing. The change adds no production log output. |
| VI. Inline comments | Pass | Each executable line in the new test functions carries an inline comment. |
| VII. Action logging | Pass with a reason | The tests write only to `tmp_path` and assert counts. The existing guard tests in that file write no log lines, so the new tests follow the same practice. |
| Technology constraints | Pass | The change adds no dependency. Paths use `pathlib`. |
| Mist API, containers, operational store, output backends | Not applicable | The change sends no Mist request, starts no container, and writes no product output. |
| Menu operations and the `--test` sweep | Not applicable | The change adds no menu operation and changes no menu code. |
| Security findings | Pass | The change adds no suppression comment. |
| Documentation and release note | Pass | The quality-gates documentation and one changelog fragment are updated. |
| SpecKit escalation | Pass | The change touches three files and adds a record. This record satisfies the rule. |
| Multi-agent git workflow | Pass | Issue 4703 carries `in-progress`. The branch name follows `fix/<issue>-<slug>`. The pull request title uses Conventional Commits. The pull request body uses `Closes #4703`. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/3/0/3/4703-speckit-audit-markdown-links/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      speckit-audit-report.md
    checklists/
      requirements.md
      evidence.md
```

**Structure Decision**: One record folder sits under the numbered route. Supporting artifacts sit under `design/`, because the root would otherwise exceed five children.

## Architecture

The audit runs inside the audit job. Each step depends on the step before it.

```text
.github/workflows/ci.yml, job speckit_task_audit
  1. Install requirements-dev.txt, which pins misthelper-devtools to 2239e7bd
  2. Run speckit-task-audit || true
     a. Find each feature record under specs/ in the managed roots
     b. TaskFileScanner reads each tasks.md line by line
        - CHECKBOX_RE matches a checked or an unchecked box
        - _is_malformed skips links, legends, reference definitions, and fences
     c. Print the summary, each malformed marker with its path and line, and open findings
```

The job fails only when step 1 fails. The `|| true` in step 2 hides the audit exit code.

## File-by-File Change Map

| Path | Action | Purpose | Requirement |
| - | - | - | - |
| `tests/guardrails/test_process_folder_structure.py` | Modify | Append two regression test functions after the last function, which ends at line 278 (RC-35). | FR-001, FR-002, FR-003 |
| `documentation/quality-gates.md` | Modify | Add one table row and one paragraph that describe `speckit_task_audit`. | FR-002 |
| `changelog.d/issue-4703-speckit-audit-markdown-links.md` | Add | One heading and one Fixed bullet. | FR-001, FR-002 |
| `specs/numbered/0/0/1/2/2/3/0/3/4703-speckit-audit-markdown-links/` | Add | This record, copied from the draft folder. | Process record |
| `requirements-dev.txt` | No change | The pin already names `2239e7bd` (RC-11). | FR-003 |
| `.github/workflows/ci.yml` | No change | The audit job keeps its masked step (decision D-2). | Non-goal |
| Upstream `misthelper-devtools` repository | No change | The repair merged as commit `da96d6e` (RC-26). | FR-001, FR-002 |

## Dependencies

- misthelper-devtools at commit `2239e7bd`. No change.
- pytest, ruff, black, and bandit run in the existing toolchain. No package is added.
- No lock file changes. `requirements-dev.txt` stays unchanged.

## Test Design

- **Negative test** `test_legend_and_link_lines_are_not_malformed_markers`: a fixture file holds the legend line and the link line. The test expects `(checked, unchecked, malformed) == (0, 0, 0)`.
- **Positive test** `test_real_malformed_marker_reports_its_line`: a fixture file holds the legend line, the link line, and `- [ab] T009 Broken box`. The test expects `malformed == 1` and `malformed_lines == (3,)`.
- The fixture text repeats the two sample lines from `specs/001-mist-ops-platform/tasks.md` line 363 (RC-18) and `specs/3300-selective-insight-definitions/tasks.md` line 707 (RC-19). Each test writes its own file under `tmp_path`. No test reads the repository specs.
- **Failure proof**: At the issue-time pin, the negative test fails. The rule at `e8e093d` line 297 matches both sample lines (RC-20). The `TaskCounts` class at `e8e093d` line 112 has no `malformed_lines` field (RC-21). This proof is static, and execution is listed as Unverified in `design/research.md`.
- **Optional execution check**: The implementer may confirm the failure with a temporary local install of `e8e093d`. The branch must keep the pin at `2239e7bd`.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| The pinned commit changes upstream | The regression tests may fail | Keep `2239e7bd` until a reviewed pin update. The negative test catches a reverted pin. |
| Upstream renames `malformed_lines` or `TaskCounts` | The positive test fails | Update the test with the pin in the same change. |
| The audit job masks the exit code | Open tasks stay hidden in the job status | Out of scope (decision D-2). The documentation update states the masking. |
| The `mando` conflict blocks the install step | The audit does not run | Separate issue (decision D-7). Pull request #4888 owns the `mando` update. |
| The changelog name breaks the policy test | CI fails | Use the issue name form from the README table row (decision D-4). |
| The spec status changes to a complete word | A complete record with open tasks fails the audit rule | Keep the status `Draft` (decision D-5). |

## Gate Map

Each applicable gate runs on the changed files. Each row cites its source.

| Gate | Command | Applies to | Source |
| - | - | - | - |
| Ruff | `python -m ruff check .` | Test file | `.github/copilot-instructions.md` Local gates |
| Black | `python -m black --check .` | Test file and Markdown files | `.github/copilot-instructions.md` Local gates |
| Guardrail test file | `python -m pytest tests/guardrails/test_process_folder_structure.py -q` | Test file and record route | RC-33, RC-35 |
| Changelog policy | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q` | Changelog fragment | RC-07, RC-42, RC-43 |
| Full guardrails | `python -m pytest tests/guardrails -q` | Test file | RC-10 |
| Citations | `check-citations src tests` | Test file | RC-09 |
| Bandit | `bandit -c pyproject.toml -r .` | Whole repository | RC-08 |
| Symbols | `symbol-diff --base origin/main tests/guardrails/test_process_folder_structure.py` | Test file | `.github/copilot-instructions.md` Local gates, Symbols row |
| Test quality | The procedure in `.github/copilot-instructions.md`, section Test quality ratchet | Test file | `.github/copilot-instructions.md` section Test quality ratchet |
| STE | `ste-linter --config .ste-linter.toml --min-score 80` with each changed Markdown file | Documentation, fragment, and record | `.github/copilot-instructions.md` Local gates, STE row |
| Audit command | `speckit-task-audit` from the repository root | Record and tests | RC-01 |
| Not applicable: mypy | No change under `src/`, `MistHelper.py`, `wsgi.py`, or the scripts listed in `MYPY_PATHS` | Not run | RC-04 |
| Not applicable: pydocstyle and interrogate | Tests lie outside `PYDOCSTYLE_PATHS` and `INTERROGATE_PATHS` | Not run | RC-05, RC-06 |
| Not applicable: radon, vulture, pylint, pip-audit | No source file and no dependency file changes | Not run | `.github/copilot-instructions.md` Local gates |

## Rollback Steps

1. Revert the feature pull request. The revert removes the two tests, the documentation update, the fragment, and the record.
2. Do not revert the pin to `e8e093d`. Caution: that pin reported 36 false malformed markers at commit 3964d21.

## Complexity Tracking

None. Every constitution rule passes, or it passes with a stated reason.
