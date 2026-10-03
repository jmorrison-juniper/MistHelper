# Implementation Plan: Packet Length Validation

**Branch**: `jmorrison-juniper-packet-length-validation` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Issue**: #3337

**Input**: `specs/3337-packet-length-validation/spec.md` and the user's final implementation manifest.

## Summary

Limit both existing packet-length prompts to 64 through 1536 bytes, inclusive.
Change exactly six production literals.
Preserve the input helpers, integer conversion, defaults, messages, and failure behavior apart from the displayed maximum.

Restore `tests/unit/test_packet_capture.py` exactly to source base `9148155c95e1f502abb0a09fd69f5a928b3bf22f`.
Add two parameterized offline test functions at the end of existing `tests/unit/capture/test_multi_ap_scan_workflow.py`.
Their names are `test_packet_length_prompt_limits` and `test_packet_length_prompt_defaults`.
Use the real shared prompt and the real collection sequence for wireless.
Substitute only `builtins.input`.
Preserve the existing tests apart from necessary imports and the module docstring.
Do not add a class, fixture, helper, wrapper, module, or production construct.

This documentation-alignment phase updates existing issue-owned documents only.
The parent owns source, tests, release notes, final validation, and delivery.
Implementation is in progress.
The parent supplied verified final local results for T001 through T029.
The documented local audit alternative does not replace the failed normal requirements audit.
Cross-artifact analysis is complete.
T030 is complete in local implementation commit `e74a996777d9fffb163c1be904f497132cbb7081`.
T031 through T038 remain blocked.

## Technical Context

**Language/Version**: Python 3.13.13 in the existing isolated `.venv`.

**Primary Dependencies**: Existing `InputUtils`, `mistapi>=0.64.0,<0.65`, pytest, coverage, and repository quality tools.
The correction needs no dependency change.

**Storage**: None for prompt validation.
Put gate reports under `data/issue-3337/`.
No database or capture artifact changes apply.

**Testing**: Two parameterized pytest functions with `unittest.mock.patch`, `capsys`, and `caplog`.
The tests substitute only `builtins.input`.

**Target Platform**: Local macOS validation with the existing Python environment.
Preserve the existing Windows and Linux behavior.

**Project Type**: Existing interactive Python CLI.

**Performance Goals**: Preserve the existing constant-time conversion and range checks.
The production code adds no loop or network operation.

**Constraints**: Six literal changes only.
Preserve minimum 64, shared default 128, wireless default 1300, and valid shared caller defaults.
Preserve `InputUtils.safe_input`, integer conversion, EOF handling, and cancellation handling.
Do not contact Mist cloud.

**Scale/Scope**: Two existing production files, two functions in one existing test file, issue-owned documents, and one release-note fragment.
No technical clarification remains.

## Constitution Check

The review uses `.specify/memory/constitution.md`, version 1.5.0.

| Principle | Pre-design decision | Post-design decision |
| --- | --- | --- |
| I. Five-Item Rule | Permit surgical edits to existing children. Record existing debt below. | Pass. The test file contains five functions. The feature root and design directory each contain five children. |
| II. Class-Based Architecture | Reuse the existing classes. Add no production abstraction. | Pass. The design adds no production class, wrapper, or refactor. |
| III. Safety-First | Retain real `safe_input`, early rejection, EOF defaults, and cancellation. | Pass. The contract and test matrix preserve these behaviors. |
| IV. Deployment Pipeline | The parent owns implementation gates and delivery. Documentation alignment grants no delivery permission. | Locally verified and committed. Coordinator-authorized remote delivery remains incomplete. |
| V. Observability | Preserve existing messages, output channels, and logging. Add no service or external action. | Pass. The contract changes only the maximum in existing messages. |
| VI. Inline Comments | Preserve production comments. Require explanatory comments on future changed test lines. | Pass by design. Implementation must retain the required comments. |
| VII. Action Logging | Preserve existing action logging. The correction adds no production action. | Pass by design. Existing input logs and diagnostic channels remain unchanged. |

The pre-design review permits this bounded design.
The post-design review found no new structural violation or unresolved technical decision.
The design must not add a structural violation.
This phase prohibits README changes, instruction updates, and delivery actions.
This plan does not amend the constitution or weaken a gate.

### Issue-Specific Instruction Precedence

The current request excludes README changes and production deployment.
The release fragment and terminal contract document the changed behavior.
Protected merge and offline exact-main tests remain required.
The request does not authorize production health checks or Mist cloud contact.

The authoritative Git workflow requires Conventional Commits.
Its commit rule controls this issue instead of the older version-stamped constitution example.
The release coordinator owns release version headings.
These scope and commit decisions do not change repository governance files.

## Project Structure

### Documentation

```text
specs/3337-packet-length-validation/
|-- spec.md
|-- .spec-context.json
|-- plan.md
|-- tasks.md
`-- design/
    |-- research.md
    |-- data-model.md
    |-- quickstart.md
    |-- checklists/
    |   `-- requirements.md
    `-- contracts/
        `-- prompt-limits.md
```

The issue directory contains five direct children.
The `design/` directory contains five direct children.
The requirements checklist resides under `design/checklists/` to preserve both limits.

### Approved Final Manifest

1. `src/operations/execution/capture/_packet_capture_prompts.py`.
2. `src/foundation/support/refactors/serial_cc/start_site_client_capture_wireless.py`.
3. `tests/unit/capture/test_multi_ap_scan_workflow.py`, limited to two appended parameterized test functions, necessary imports, and the module docstring.
4. Issue-owned documents under `specs/3337-packet-length-validation/`.
5. `changelog.d/issue-3337-packet-length-validation.md`.

The final manifest supersedes both earlier test locations.
`tests/unit/test_packet_capture.py` must match the source base exactly.
`tests/unit/serial_cc/test_start_site_client_capture_wireless.py` remains a read-only regression target.
Do not create `tests/unit/capture/test_packet_capture_prompt_limits.py`.
No other test file belongs to the edit manifest.
Supplied live open-pull-request checks show no ownership overlap.
The parent notified the coordinator and refined the ownership comment.

## Phase 0: Research

Use the supplied implementation evidence and the final test manifest.
Use the completed sender review and the supplied upstream release evidence.
The design needs no new technology, dependency, integration, or research agent.
Do not repeat source or test review during documentation alignment.
The decisions appear in [design/research.md](design/research.md).

## Phase 1: Design and Validation

The existing data flow needs no new model or persistence.
Document it in [design/data-model.md](design/data-model.md).
Document terminal behavior in [design/contracts/prompt-limits.md](design/contracts/prompt-limits.md).
Use [design/quickstart.md](design/quickstart.md) for future offline validation.

### Exact Production Changes

| Existing owner | Literal to change | Required value |
| --- | --- | --- |
| `PacketCapturePrompts.prompt_max_packet_length` | Prompt maximum | `1536` |
| Same method | Inclusive upper guard | `1536` |
| Same method | Range-error maximum | `1536` |
| Wireless `_MAX_PKT_LEN_SPEC` | `prompt` maximum | `1536` |
| Same specification | `high` | `1536` |
| Same specification | `range_lines` maximum | `1536` |

Replace the corresponding `2048` literals only.
Do not edit `_prompt_bounded_int`, `_collect_bounded_ints`, `InputUtils`, or capture senders.
Do not change fixed lengths of 1300 or 1500.
When the shared prompt returns `None`, the organization path stops before payload creation.
Issue #3338 owns the independent bundled OpenAPI refresh.

### Test Design

Append only `test_packet_length_prompt_limits` and `test_packet_length_prompt_defaults` to the approved existing test file.
Parameterize each function with `prompt_path` values `shared` and `wireless`.
Group raw input, expected length, and exact diagnostic in the limits-case parameter.
Call `PacketCapturePrompts.prompt_max_packet_length` directly.
Call `SiteWirelessClientCaptureService._collect_bounded_ints(InputUtils)` for wireless cases.
Use valid earlier inputs to isolate packet-length rejection.

| Final function | Required cases |
| --- | --- |
| `test_packet_length_prompt_limits` | All 1473 integers from 64 through 1536. All 512 integers from 1537 through 2048. Also cover 63, 0, -1, 2049, 9999, `text`, `64.0`, `1e3`, `KeyboardInterrupt`, and padded 64 and 1536. |
| `test_packet_length_prompt_defaults` | Blank, spaces-only, and tabs-only input. Shared defaults 128 and caller default 1300. Wireless default 1300. Packet-length EOF and complete wireless blank or EOF sequences. |

Supplied evidence records three definitions and zero quality findings before the additions.
Two appended functions keep the file at five definitions without a new directory child.
Keep each new function within five parameters, five logical blocks, and 25 lines.
Do not add a helper or module-level test-data declaration.
Use accurate annotations, including `pytest.CaptureFixture[str]`, `pytest.LogCaptureFixture`, and `-> None` where applicable.
The supplied final focused matrix executed 4010 items, with 2005 for each path.
Each path executed 1473 supported integers, 513 required rejected integers, and 19 additional cases.
The final test file contains five functions.
The limits function has 23 lines and four parameters.
The defaults function has 21 lines and three parameters.

Assert returned integers, exact prompt arguments, and actual errors.
Use `capsys` for shared printed errors.
Use `caplog` for wireless warnings and input-safety notices.
An input substitute does not print a prompt, so inspect its recorded prompt argument.
Do not use only a call assertion as behavior evidence.

Assert the complete wireless result, not only its final element.
Valid earlier settings must remain unchanged.
Invalid length must return `None`, not a partial tuple.
Blank input across the wireless sequence must return `(60, 1024, 1300)`.
EOF across that sequence must return the same tuple.
Packet-length EOF after inputs `120` and `7` must return `(120, 7, 1300)`.
Do not mock the validation results.
Do not replace the collection sequence, start a capture, or require credentials.

### Future Implementation Order

1. Restore the large test file to the source base and add the two final functions.
2. Run both final function nodes against unchanged production source.
3. Confirm failures on the former maximum or its messages, not on imports or missing tools.
4. Apply the six literal changes.
5. Run the same tests and the adjacent capture tests.

Record collected, executed, passed, failed, and skipped test counts.
Report accepted and rejected input counts for each real path.
Report executed statements against total statements in the changed guard regions.
Require at least 80% coverage in each changed guard region.

Use the existing coverage API to measure the focused run and export `data/issue-3337/coverage.json`.
The AST region check must fail for zero statements or coverage below 80% in any of the three regions.
Do not apply pytest-cov's whole-module 90% threshold to this focused function run.
Do not set `--cov-fail-under=0` or change configuration.
The repository's global coverage threshold remains unchanged and required in CI.

Compile both prompt files, the final test file, and `MistHelper.py`.
Run Ruff for the repository.
Run Black for the repository.
Run mypy with the exact CI `MYPY_PATHS`, repository-configured Bandit, and pip-audit.
Use the configured test-quality ratchet with its current baseline.
Do not edit a baseline, add a suppression, or weaken a check.
The parent owns the `Fixed` release-note fragment that references #3337.

The rejected large-file manifest passed 4010 focused cases and 4369 adjacent cases.
Its shared guard measured 11/11 statements.
Its wireless bounded validator measured 12/12, and its collector measured 8/8.
Each region measured 100%.
The configured ratchet reported 23 new line-sensitive `weak_zero_assertions` findings after existing assertions moved.
The large file still contained exactly 24 findings, with zero semantic new findings.
Baseline changes, suppressions, and unrelated test repairs remain prohibited.
Those earlier results did not satisfy final-manifest verification.
The parent restored the large test file exactly and supplied verified final results.
The final red run executed 4010 cases with 4010 failures and zero errors or skips against base-identical source.
Shared input 1537 returned `1537`, and wireless input 1537 returned `(120, 7, 1537)`.
Both results prove the old acceptance error.
The final green run passed 4010 cases with zero failures, errors, or skips.
Final adjacent tests passed 4373 cases with zero failures or skips.
Final coverage confirmed shared 11/11, wireless bounded 12/12, and collector 8/8 statements, each at 100%.
The final ratchet checked 944 files and 728 existing findings.
It reported zero new findings, 42 configured skips, and zero parse errors.
The compile check passed four files.
The full Black check passed 1882 files without changes.
Repository-scope Ruff and configured mypy passed, with mypy checking 608 source files.
Configured Bandit reported zero findings across 206617 lines in `data/issue-3337/bandit.json`.
The normal requirements audit failed during macOS ensurepip with SIGABRT before scanning.
The local audit alternative found no known vulnerabilities in audited installed packages.
The Git-pinned `misthelper-devtools` version `0.5.2` remained explicitly unaudited because PyPI does not contain it.
The normal requirements audit remains a delivery check.
These results come from supplied verified evidence, not gate execution by the documentation owner.

## Complexity Tracking

Source and test counts describe the recorded base `9148155c95e1f502abb0a09fd69f5a928b3bf22f`.
The documentation count describes the corrected feature-owned layout.
Directory counts use tracked direct children.
Module counts use direct functions, classes, and assignments.

| Existing violation | Count | Bounded decision | Separate incremental repair |
| --- | --- | --- | --- |
| `src/operations/execution/capture/` | 13 children | Edit one existing file. Add no child. | Move coherent capture groups into compliant packages in separate work. |
| `src/foundation/support/refactors/serial_cc/` | 9 children | Edit one existing file. Add no child. | Separate coherent capture groups under compliant packages. |
| Shared prompt module and class | 9 module declarations, 38 methods | Change three existing literals. Add no declaration or method. | Split existing prompt groups by responsibility in separate work. |
| Wireless module and service | 44 module declarations, 18 methods | Change three existing literals. Add no declaration or method. | Move existing specifications and workflow groups in separate work. |
| `_MAX_PKT_LEN_SPEC` | 7 existing fields | Preserve its shape. Change only the maximum and messages. | Review specification structure during the separate module repair. |
| `tests/unit/` | 148 children | Preserve all direct children. Restore the large test file exactly to the base. | Group existing tests into compliant packages in separate work. |
| `tests/unit/capture/` | 8 files | Edit one existing file. Add no directory child. | Reorganize the existing files through separate approved work. |

The final test file increases from three definitions to five.
It adds no structural violation.
The feature root and design directory each contain five children.
These new directories comply with the structural limit.

The source ancestors also exceed five children.
Their tracked counts are `src/` 42, `src/foundation/support/refactors/` 33, and `tests/` 38.
This change adds no child to those ancestors.
The app already supplied this issue directory under `specs/`.
Documentation alignment adds no sibling issue directory.

The constitution grandfathers these structural violations.
They do not permit new violations.
Do not perform the separate repairs in #3337.

## Workflow and Delivery Boundaries

The required PowerShell setup attempt failed because `pwsh` is unavailable.
Read the existing plan template and resolve the issue paths locally instead.
The setup helper can persist shared feature selection.
Do not run a replacement that writes `.specify/feature.json`.

Agent-context synchronization is outside the approved file manifest.
Do not update instructions for agents or install tooling to enable that step.
Registered completion hooks must remain issue-scoped.
A missing hook implementation is a bounded workflow blocker, not permission to change shared configuration.

The setup and context-script attempts both returned exit code 127 because `pwsh` is unavailable.
Neither script executed.
The registered `speckit.companion.after-plan` invocation also returned exit code 127.
This worktree has no installed implementation for that command.
The companion implementation command remains unavailable.
Skip unavailable PowerShell and companion commands without repeating the failed attempts.
Skip optional Git commit hooks.
Update only the feature's `.spec-context.json` directly.
Keep `currentStep=implement` and implementation in progress.
Record verified local validation with the documented audit alternative.
Record local implementation commit `e74a996777d9fffb163c1be904f497132cbb7081` and keep remote delivery blocked.
Do not record implementation completion before final evidence exists.

The coordinator assigned position 9 to this issue.
Coordinator `6d71fd26-57c2-48c0-abc8-607af98f75d0` must supply the full verified stable `main` SHA before any push or pull request.
The recorded source revision does not authorize delivery.

Future delivery requires a Conventional Commit and the Copilot trailer.
Preserve `.github/PULL_REQUEST_TEMPLATE.md` and include `Closes #3337`.
After coordinator approval, rebase the existing branch and repeat the required local gates.

Require every repository check, including CodeQL and the title check.
Require the branch to remain up to date.
Use a protected squash merge.
Perform offline local testing of the exact resulting `main` revision.
Do not switch a local checkout or access a shared `main` checkout.

No source review, test execution, gate, commit, push, pull request, rebase, merge, container run, or remote action occurs during documentation alignment.
