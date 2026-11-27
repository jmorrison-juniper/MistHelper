# Implementation Plan: Unattended token skip for menu 247

**Branch**: `fix/4744-unattended-token-skip` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/4/3/4/4744-unattended-token-skip/`. The route follows the base-5 rule in `.specify/scripts/powershell/spec-route.ps1` (remote row RC-45 in `design/research.md`).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Menu 247 asks for an email change token. An unattended run never supplies that token. The input provider returns an empty answer, so the handler returns normally, and the runner writes a pass event. This plan makes the input provider stop the option at an operator-only prompt. The runner then writes a skip event with the registry skip reason. The skip counts apart from passes and failures. No Mist call, registry row, or exporter line changes.

## Technical Context

- **Language/Version**: Python 3.15 or newer, as the repository toolchain states (remote row RC-46).
- **Primary Dependencies**: `mistapi` pinned at `>=0.64.0,<0.65`. The installed version is 0.64.1 (remote rows RC-51 and RC-52). Standard `logging` and pytest. No new dependency.
- **Storage**: Existing telemetry JSON lines under `data/`. No new file type.
- **Testing**: pytest with mocks. No live Mist call. No browser.
- **Target Platform**: The same as the existing runner. The change adds no platform-specific code.
- **Project Type**: CLI tool with an interactive test runner.
- **Performance Goals**: No change. Each option still waits one second in the loop (RC-07).
- **Constraints**: ASCII log lines. No token value in logs or records. No Mist call in tests. Changes stay in the runner package, its test module, one documentation row, and one fragment.
- **Scale/Scope**: Two source files (one new), one test module, one documentation row, and one fragment. Five new tests. Six call sites change.

## Constitution Check

Gate result: pass, with two justified violations recorded in Complexity Tracking.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule, hierarchy | Fail, justified | The new module goes into `src/foundation/support/menu_testing/`, which holds two children now and three after the change (RC-53). The runner test module already exceeds five top-level names, and five test functions join it. See Complexity Tracking row 1. |
| I. Five-Item Rule, functions | Fail, justified | `_run_single_option` has 73 lines and more than five logical blocks. That violation is grandfathered. The change adds one except clause. See row 2. The new branch in `answer` and the new module functions stay within 25 lines and five blocks. |
| I. Five-Item Rule, class members | Pass | `InteractiveTestRunner` keeps its members. The change edits existing methods only. No attribute or method is added (RC-57 and RC-59 show the ten fields and 32 methods). |
| II. Class-based architecture | Pass | The new names are classes with static methods. No standalone wrapper function is added. |
| III. Safety-first input | Pass | The input seam keeps its EOF and interrupt paths. The change adds no destructive operation. The token is never written to a log line or a record. |
| IV. Full deployment pipeline | Pass, planned | T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in order. Pipeline steps 10 to 12 (main build, revision check, deployment) run after merge under orchestrator control. This record does not deploy. |
| V. Observability and logging | Pass with reason | Log lines are ASCII and use `%s` templates. The skip is a structured telemetry event. The new module uses the standard `logging` module, as its sibling runner and exporter do. Open item U-3 asks the owner to confirm this reading. |
| VI. Inline comments | Pass, planned | Each new or changed executable line gets an inline comment. Test code follows the same rule. |
| VII. Action logging | Pass, planned | An info line precedes the operator-only check and the skip record. A debug line follows the skip record. |
| Technology: mistapi only | Pass | The change adds no Mist call. FR-007 forbids the unattended call. |
| Technology: Podman | Not applicable | The regression runs on the host. No container starts. |
| Technology: file paths | Pass | The change adds no path. Telemetry keeps the existing `data/` path. |
| Technology: output backends | Pass | No export path changes. The exporter write stays the same. |
| Database keys | Not applicable | No endpoint, primary key, or export changes. |
| Development workflow: new menus | Not applicable | No menu is added. Menu 247 keeps its category. |
| Development workflow: skip list | Pass | The `--test` set and the `--testinteractive` set stay the same. |
| Documentation: README | Pass | `README.md` holds no `--testinteractive` text (RC-38). The row in `documentation/cli-reference.md` changes (FR-016). |
| Documentation: release notes | Pass | One fragment at `changelog.d/issue-4744-unattended-token-skip.md` (RC-39 and RC-41). |
| Documentation: generated pages | Pass | No generated page is edited. The drift job checks the generated output in T-LOCAL-GATES. |
| Specifications | Pass | Three or more files and two or more classes change. This spec record exists. |
| Multi-agent git | Pass, planned | Branch `fix/4744-unattended-token-skip` starts from main. Labels: `bug`, `tests`, and `in-progress` at claim time. The open pull request search found no overlap with the changed files. |
| Governance | Not applicable | The constitution does not change. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/4/3/4/4744-unattended-token-skip/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      unattended-input-provider.md
      skip-event.md
      verify-self-email-api.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

| Action | Repository path | Change |
| - | - | - |
| Add | `src/foundation/support/menu_testing/operator_prompt.py` | Define `OperatorPromptRequired`, `OperatorPromptPolicy` (with `CONTEXTS`, `SKIP_CATEGORY`, `TEST_MODE`, and `is_operator_only`), and `OperatorPromptSkipRecorder` (with `record`). |
| Modify | `src/foundation/support/menu_testing/interactive_test_runner.py` | Import the three new names. Stop operator-only prompts in `UnattendedInteractiveInputProvider.answer`. Catch the stop in `_run_single_option` and return None. Return three tally values from `_run_option_loop`. Add runtime skips in `_run_and_finalize`. Keep every existing top-level name and class member. |
| Modify | `tests/unit/marvis/mist/intelligence/troubleshooting/core/test_interactive_test_runner.py` | Unpack three values at lines 418, 512, 582, 752, 780, and 813. Add five test functions and one helper. |
| Modify | `documentation/cli-reference.md` | Update row 60 for the operator-only skip (RC-36). |
| Add | `changelog.d/issue-4744-unattended-token-skip.md` | One heading and one Fixed bullet that names issue 4744. |
| Unchanged | `src/operations/exporting/export/self_account_exporter.py` | The token prompt context and the SDK call stay the same (RC-13 to RC-15). |
| Unchanged | `src/foundation/support/utils/operation_registry.py` | The category and the skip reason of menu 247 stay the same (RC-16). |
| Unchanged | `MistHelper.py` | The menu entry and the runner builder stay the same (RC-17 and RC-18). |
| Unchanged | `src/foundation/support/utils/input_utils.py` | The input seam stays the same (RC-20 and RC-21). |
| Unchanged | `src/mist/intelligence/analytics/telemetry_emitter.py` | The emitter signature stays the same (RC-22). |
| Unchanged | `tests/unit/export/test_self_account_exporter.py` | The exporter tests stay the same (RC-28). |
| Unchanged, runs more tests | `tests/unit/config/standalone/foundation/runtime/startup/test_standalone_interactive_test_runner.py` | The star import includes the new tests (RC-27). No test is copied. |
| Unchanged, verified | `tests/unit/marvis/actions/test_selection.py` and `tests/unit/marvis/actions/test_operation.py` | Both use the provider, and both stay valid (RC-29 and RC-30). |
| Generated, not edited | `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md`, and `documentation/menu-api/*.md` | The drift job covers them (RC-34 and RC-35). |

## Architecture

The provider raises when an operator-only prompt has no answer. The runner catches the stop and asks the recorder to write one skip event. The loop counts that skip apart from passes and failures.

```text
--testinteractive (runner)
  _run_single_option(option)
    _invoke_with_input_provider: input seam := provider.answer
      handler -> _prompt_token -> input seam (provider.answer)
        context in OperatorPromptPolicy.CONTEXTS and no default?
          yes: raise OperatorPromptRequired
               -> OperatorPromptSkipRecorder.record (skip event)
               -> return None
          no: existing answer rules (unchanged)
    finally: input seam restored
  _run_option_loop: None counts as skip, True as pass, False as fail
  _run_and_finalize: skip total = registry skips + runtime skips
```

Design rules:

- `OperatorPromptPolicy.CONTEXTS` is the only list of operator-only contexts.
- The provider checks the list before the rule table. A default answer wins.
- The caller passes the skip reason. The recorder does not own the reason text.
- The recorder writes exactly one skip event for each stopped option.

## Dependencies

None new. The pinned SDK already defines `verifySelfEmail` (RC-51). The requirements files do not change.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| The exporter changes the token prompt context. The provider then treats the prompt as optional. | The regression uses the real exporter handler. The regression fails when the context leaves the list. |
| A future handler wraps an operator-only prompt in a broad exception handler. The skip is lost. | Caution: the new module docstring states the rule. The regression proves the current path. Review each new operator-only context. |
| The complexity gate reports a block above 10 in `menu_testing`. | Run the gate in T-LOCAL-GATES. If it fails, move the outcome decision into `OperatorPromptSkipRecorder`, and keep one call in the except clause. Record the result in the pull request. |
| The regression stub does not resolve `InputUtils` as the runner expects. | Set the stub attribute to the same class that the runner receives. Verify the first test run. |
| The star import in the standalone module runs the new tests a second time. | Accept the duplicate run. Do not copy the tests. |
| The symbol gate reports a changed module-level name. | The runner keeps every name. The new names live in a new module. Record any report in the pull request. |
| The telemetry summary reports status pass for a skip-only run. | Out of scope. `analysis.md` item A-3 records the defect and a follow-up. |
| The new loop tests add about one second for each option. | Accept the delay. The new tests add about five seconds in total. |

## Rollback Steps

1. Revert the squash commit through a new pull request. Do not force-push `main`.
2. Confirm that the revert removes the changelog fragment with the code.
3. Confirm that no data migration exists. Telemetry files written during the change keep the extra skip events.
4. Restore the two-value loop tally only through the revert. Do not revert one file alone.

## Complexity Tracking

| Row | Violation (grandfathered) | Touched by this change | Why needed | Simpler alternative rejected because |
| - | - | - | - | - |
| 1 | The runner test module holds more than five top-level test functions. | Five test functions and one helper. | The regression needs the runner fixtures and helpers that live in that module. | A new file in `tests/unit/marvis/mist/intelligence/troubleshooting/core/` makes six children (RC-54). A new file elsewhere separates the tests from their subject. |
| 2 | `_run_single_option` has 73 lines and more than five logical blocks. | One except clause that calls the recorder and returns None. | The skip is an outcome of this method. | A separate refactor first is outside this scope. A second channel for the skip adds state and a new member. |
| 3 | `InteractiveTestRunner` holds 42 direct members (32 methods and 10 fields). | None. The change edits existing methods only. | Avoids a new direct child in a noncompliant class. | A new attribute or method adds a direct child to a noncompliant parent. |
| 4 | `interactive_test_runner.py` declares more than five top-level names. | None. The new names live in `operator_prompt.py`. | Avoids a new top-level name in a noncompliant module. | A new class in the runner module adds a direct child to a noncompliant module. |

Remediation actions (separate from this change, to be tracked by the orchestrator):

- R-1: Split the runner test module into subject modules.
- R-2: Split `_run_single_option` into outcome helpers.
- R-3: Decide the telemetry summary status rule for runs that exercise zero operations (analysis item A-3).
