# Implementation Plan: Operator Guide Operation Count

**Branch**: `docs/4915-operator-guide-count` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric record at `specs\numbered\0\0\1\2\4\1\3\0\4915-operator-guide-count`, derived from `spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. This record has no `design/contracts/` folder, because no interface contract applies to a text change and one guard test.

## Summary

The operator guide states `303 operations` and `numbered 1 to 304` (R-01). The menu reference states 308 actionable menu operations, numbered 1 to 309 (R-03). This change deletes the stale sentence. The guide keeps its existing link to the menu reference (R-02). A guard test fails when the guide states an operation count again. One release-note fragment records the fix.

## Technical Context

- **Language/Version**: Python 3.15 or newer (R-65). The guard test is Python code.
- **Primary Dependencies**: pytest, and the standard library modules `logging`, `re`, and `pathlib`. The change adds no dependency.
- **Storage**: Not applicable. The guard reads one Markdown file of 754 lines (R-01).
- **Testing**: pytest guard tests in `tests/guardrails`. The local gates table runs them (R-64), and continuous integration runs them (R-41).
- **Target Platform**: Windows 11 for the author. Paths built with `pathlib` run on Windows, macOS, and Linux (R-30).
- **Project Type**: Documentation change with one guard test and one release-note fragment.
- **Performance Goals**: Not applicable. The guard test reads one file once.
- **Constraints**: No runtime code change. Prose follows STE. Log output uses ASCII only (R-25). Each new Python line carries an inline comment (R-26).
- **Scale/Scope**: One operator guide, one test module, one fragment, and one record.

## Constitution Check

Each rule row gives its result and its reason. The R-number points to the remote verification table in `design/research.md`.

| Rule | Result | Reason |
| - | - | - |
| Principle I: each hierarchy level holds five children or fewer (R-15) | Pass | The guard test enters `tests/guardrails/test_destructive_menu_docs.py`, an existing module. The folder `tests/guardrails` already holds 79 direct children (R-81), so a new file there would add a child to a noncompliant parent. |
| Principle I: each route level holds five children or fewer (R-83, R-85) | Pass | `specs/numbered/0/0/1/2/4/1` holds one child before the change (R-83). The route adds child `3`, so that level holds two. `specs/numbered/0/0/1/2` holds five children (R-85) and gains none. |
| Principle I: new records sit under managed roots (R-24) | Pass | The record sits under `specs/numbered/`, a managed root. |
| Principle I: unique process records may be direct children of `changelog.d` (R-16) | Pass | The fragment is the only new direct child of `changelog.d`. It is the unique record for this change. |
| Principle I: record existing folder debt and a remediation action (R-16, R-81, R-82) | Pass | Debt: `changelog.d` holds 335 direct children (R-82), and `tests/guardrails` holds 79 (R-81). Remediation action: analysis item A-8. |
| Principle II: class-based architecture (R-21) | Pass | The guard logic lives in the class `OperatorGuideCountIndex`. The test function calls that class. |
| Principle III: safety first (R-22) | Pass | The change reads one Markdown file. It writes no product output and reads no secret. |
| Principle IV: pipeline steps 1 to 9 (R-20, R-23) | Pass | Step 1 maps to T-LOCAL-GATES. Steps 2 to 7 map to T-PR. Step 8 maps to T-REMOTE-CI. Step 9 maps to T-MERGE. |
| Principle IV: pipeline steps 10 to 12 (R-18, R-19, R-56, R-57, R-58) | Fail | No container build runs for this change. The build paths exclude the guide and the tests (R-56). The image excludes the documentation folder (R-57, R-58). Decision D-6 records the exception and its evidence. |
| Principle V: ASCII-only log output (R-25) | Pass | The guard messages and log lines use ASCII characters only. |
| Principle VI: inline comments on each new line (R-26) | Pass (planned) | Each executable line of the new Python code carries an inline comment on the same line. |
| Principle VII: action logging (R-27) | Pass (planned) | The guard logs an info line before it reads the guide and a debug line after the read. |
| Technology: mistapi is the sole Mist REST interface (R-28) | Not applicable | The change calls no Mist endpoint and no mistapi method. |
| Technology: Podman is the container runtime (R-29) | Not applicable | The change starts no container. |
| Technology: file paths use `os.path` or `pathlib` (R-30) | Pass | The guard builds every path with `pathlib.Path`. |
| Development workflow: one release-note fragment for each change (R-17) | Pass | The fragment `changelog.d/issue-4915-operator-guide-count.md` is the one fragment for this change. |
| Development workflow: new menu operations | Not applicable | The change adds no menu operation. |
| AGENTS.md: each Markdown file passes the STE gate (R-31) | Pass | T-LOCAL-GATES runs ste-linter at 80 on each changed Markdown file and on the changed Python file. |
| AGENTS.md: each change carries tests, and a test must fail first (R-32) | Pass | T002 adds the guard test. The test fails before T003 and passes after it. |
| AGENTS.md: one issue holds one subject (R-33) | Pass | The change covers one stale sentence. Other stale text stays out of scope (D-5). |
| AGENTS.md: claim the issue, name the branch, and use a worktree (R-34, R-35, R-36) | Pass | T001 adds the `in-progress` label, names the branch `docs/4915-operator-guide-count`, and creates a worktree. |
| AGENTS.md: stage by explicit path (R-37) | Pass | T-PR stages each changed path by name. |
| AGENTS.md: the pull request body closes the issue (R-38) | Pass | The pull request body contains `Closes #4915`. |

## Architecture

No new module is added. The guard test reads one file and checks one link target.

- Input: `documentation/operator-guide.md`.
- Logic: the class `OperatorGuideCountIndex` finds each count phrase in the text.
- Assertions: the test function `test_operator_guide_defers_the_count_to_the_menu_reference` asserts that no phrase exists and that the link exists.
- Generated page: `documentation/menu_reference.md` remains generated by `scripts/generate_menu_wiki.py` (R-07). The change does not touch it.

The count pattern matches a number that directly precedes the word `operations`, and the text `numbered 1 to` followed by a number. The pattern matches bold text. It does not match a number followed by other words.

## File-by-File Change Map

| Action | Path | Change |
| - | - | - |
| Modify | `documentation/operator-guide.md` | Delete line 13, which states `303 operations` and `numbered 1 to 304`. Keep lines 14 and 15, which hold the link to the menu reference. |
| Modify | `tests/guardrails/test_destructive_menu_docs.py` | Add a module constant for the guide path. Add the class `OperatorGuideCountIndex`. Add the test function. Add one paragraph to the module docstring that names the guide and the issue. |
| Add | `changelog.d/issue-4915-operator-guide-count.md` | One `###` heading and one Fixed bullet that names issue #4915. |
| Add | `specs/numbered/0/0/1/2/4/1/3/0/4915-operator-guide-count/` | This record: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/checklists/requirements.md`. |
| Unchanged | `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md`, `scripts/generate_menu_wiki.py` | The generator inputs and the generated pages stay the same (FR-004). |
| Unchanged | `MistHelper.py`, `src/`, `README.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md` | No runtime code or governed instruction changes. The stale instructions remain for a follow-up issue (A-4). |
| Unchanged | `CHANGELOG.md` | A feature branch never edits this file (R-17). The fragment carries the release note. |

## Dependencies

No new dependency is added. The local gates use the tools that the local gates table names (R-62, R-63, R-64, R-66, R-67, R-70). The pre-commit hooks use ruff, ste-linter, and markdown-link-check (R-49, R-50, R-51).

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
| - | - | - |
| The guard matches a sentence that counts the operations of one menu. | Low | The spec edge case rewords the sentence. The guard message names the matched phrase. |
| The guard misses a count written in words. | Low | Analysis item A-9 records the residual risk. The menu reference remains the source of the count. |
| The guide scores below 80 in STE after the edit. | Low | T-LOCAL-GATES runs ste-linter in both modes before the commit. |
| A Windows workstation reports guard failures unrelated to this change. | Medium | Issue #4917 is open and reports 23 failing guardrail tests on a Windows workstation (source: GitHub issue view in `design/research.md`). T-LOCAL-GATES compares any failure with that report. A new failure blocks the change. |
| Pre-commit does not check the record files, because the hook excludes `specs/` (R-49). | High | T-LOCAL-GATES runs ste-linter on each record file by name. |
| Another open pull request edits the guide at the same time. | Low | T001 checks open pull requests for an overlap before the branch exists. |
| The OneDrive folder locks files during a checkout. | Medium | T001 uses a worktree, as AGENTS.md requires (R-36). |
| Principle IV steps 10 to 12 do not run. | High | Decision D-6 records the exception. The orchestrator confirms it. Analysis item A-7 tracks the conflict. |

## Rollback Steps

1. If the merged change causes a failure, open a revert pull request for the squash commit.
2. If only the guard test fails on `main`, remove the new function and class in a new pull request. Keep the guide edit.
3. Do not force-push `main`. Caution: a revert restores the stale count until a corrected change merges.
