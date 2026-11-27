# Implementation Plan: Lint repair for W0212 and W0201 findings

**Branch**: `chore/4133-lint-w0212-w0201` | **Date**: 2026-11-26 | **Spec**: specs/numbered/0/0/1/1/3/0/1/3/4133-lint-w0212-w0201/spec.md

**Input**: Numeric specification from `specs/numbered/0/0/1/1/3/0/1/3/4133-lint-w0212-w0201/spec.md`. The route comes from `.specify/scripts/powershell/spec-route.ps1`. The base-5 digits of 4133 are 1, 1, 3, 0, 1, 3. Padded to eight digits, they give the route `0\0\1\1\3\0\1\3`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. No interface contract applies, so `design/contracts/` is omitted.

## Summary

Two findings remain on `main`. Both are W0212 protected-access findings in `tests/unit/test_menu_entry_metadata.py`, at lines 84 and 93. The change replaces the two protected handler calls with calls through the public `MistHelper.dispatch_main_mode` function. The change adds one changelog fragment. No product code changes.

## Technical Context

**Language/Version**: Python 3.15 or newer, as `.github/copilot-instructions.md` requires.

**Primary Dependencies**: pytest, pylint 4.1.4 (pinned in `pyproject.toml` line 117), ruff, black, bandit, and the test-quality analyzer installed in `.venv\Scripts`. The change adds no dependency.

**Storage**: None. The test writes no product output.

**Testing**: pytest with the monkeypatch fixture. The test file collects 35 cases.

**Target Platform**: Windows 11, macOS, and Linux, and the Podman container.

**Project Type**: A test-only change with one changelog fragment.

**Performance Goals**: None. The test keeps its current runtime. It makes no network call and waits for nothing.

**Constraints**: No edit to `MistHelper.py`. No HTTP client name in the test module. No new top-level name in the test module.

**Scale/Scope**: One test file with two changed test functions. The parametrized cases do not change. One fragment.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Principle or rule | Gate | Result | Reason |
|---|---|---|---|
| I. Five-item rule | No directory exceeds five children. Each module keeps its top-level name count or lowers it. | Pass | The record adds one child under `specs\numbered\0\0\1\1\3\0`, which holds one child now. The route folder `specs\numbered\0\0\1\1\3` already exists with four children (RC-15). The test module already holds nine top-level names. That count is grandfathered debt. The change adds none. |
| II. Class-based architecture | Behavior lives in named classes. No delegating wrapper. | Pass | The test file uses pytest functions, as it does now. The change adds no wrapper and no helper function. |
| III. Safety first | Input is replaced. No secret is printed or stored. | Pass | `InputUtils.safe_input` is replaced by a scripted fake. The test reads no real input and no credential. |
| IV. Full deployment pipeline | Local gates, rebase, push, pull request, CI, squash merge. | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step. T-PR waits for orchestrator authorization (decision D-5). |
| V. Observability and logging | Log output stays ASCII. No secret reaches a log. | Pass | The change adds no log output. The messages that the test checks are ASCII. |
| VI. Inline comments | Each executable line carries an inline comment. | Pass | Each new line follows the `# WHY:` form that the file already uses. Task T002 audits the changed lines. |
| VII. Action logging | An `info` line before and a `debug` line after each product action. | Pass by scope | The rule covers product actions. The test adds no product action. The file has no logger. Complexity Tracking records the reviewer decision. |
| Mist Cloud transport | Every REST request uses a working mistapi method. | Not applicable | The change makes no REST request and no WebSocket request. |
| Test containers | Each test container joins the compose group. | Not applicable | The change starts no container. |
| File paths | Paths come from the path library. | Pass | The test builds no path. |
| Output backends and data directory | Product output goes to `data/` through the exporter. | Not applicable | The change writes no product output. |
| Security findings | Findings are fixed, not suppressed. | Pass | Decision D-3 rejects suppression. The diff adds no `disable`, `noqa`, or `type: ignore` comment. |
| Database keys, container security, and Zscaler | Schema, container, and registry rules. | Not applicable | The change alters no schema, container, or registry path. |

For repository structure and generated files:

- The commit subject and the pull request title use the Conventional Commits form. The subject is `test(lint): call the public menu dispatch in the menu metadata test`.
- The change adds only its own record under `specs\numbered\0\0\1\1\3\0\1\3\4133-lint-w0212-w0201` and one fragment under `changelog.d\`.
- The test module holds nine top-level names above the five-item limit. Remediation action: the orchestrator files a separate issue to split that module. The change does not start that split.

For a feature that uses Juniper Mist Cloud: Not applicable. The change makes no Mist call.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/3/0/1/3/4133-lint-w0212-w0201/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

### Source Code (repository root)

```text
tests/unit/test_menu_entry_metadata.py        (modify: one import, two calls, four patches)
changelog.d/issue-4133-lint-w0212-w0201.md    (add: one fragment)
```

No product file changes. `MistHelper.py`, `src/**`, `.github/**`, `pyproject.toml`, and the test-quality baseline stay unchanged.

**Structure Decision**: One test module and one fragment. The record uses the numeric route. Its layout copies the reference record of issue 4920, at the same depth.

## File-by-File Change Map

| Path | Action | Change |
|---|---|---|
| `tests/unit/test_menu_entry_metadata.py` | Modify | Add `import argparse`. Replace the call at line 84 with a call through `MistHelper.dispatch_main_mode`. Replace the call at line 93 the same way. Replace four collaborators with monkeypatch doubles. Keep every test name and every parameter list. |
| `changelog.d/issue-4133-lint-w0212-w0201.md` | Add | One `###` heading and one `Changed` bullet. The bullet names issue 4133. |
| `specs\numbered\0\0\1\1\3\0\1\3\4133-lint-w0212-w0201\` | Add | The record files in Project Structure. T-PR copies them from DRAFT_DIR. |

## Contracts

No interface contract applies. The menu row, the console text, and the exit codes stay unchanged. The two tests assert the existing behavior. Therefore `design/contracts/` is omitted.

## Dependencies

No new dependency. The test adds the standard-library module `argparse`. Tool versions stay at the pins in `pyproject.toml` (pylint 4.1.4 at line 117) and in `requirements-dev.txt`.

## Test Design Through the Public Path

Each of the two tests calls `MistHelper.dispatch_main_mode` with an `argparse.Namespace`. The namespace holds `test`, `testinteractive`, and `tui` as false, and `menu`, `org`, `site`, `device`, and `port` as empty. The dispatch falls through to the interactive loop (`MistHelper.py` lines 8232 to 8256, and lines 7966 to 8036).

The test replaces four collaborators with monkeypatch doubles:

- `ConfigUtils.get_cached_or_prompted_org_id` returns a fixed organization identifier. The loop reads it at line 7972.
- `EnvironmentUtils.is_running_in_container` returns false. The loop reads it at line 8000.
- `InputUtils.safe_input` returns the scripted selections and records each prompt. The loop reads it at line 8032.
- `MistHelper.echo` appends each message to a list. The refusal and notice assertions read that list.

Line 7972 also writes `MainEntrypoint.context.org_id`. The test sets that attribute through monkeypatch before the call, so pytest restores the original value.

Assertions:

- Invalid selection: the exit code is 1. The last message is the refusal. The prompt count is 1.
- Empty selection: the notice appears once. The prompt count is 2. The run ends without an exit.

## Risks and Mitigations

| Risk | Effect | Mitigation |
|---|---|---|
| The test-quality analyzer reports a new finding for the test file. | The gate fails. T-PR waits. | The analyzer checks only the names that the test calls through the module alias, and it reads those function bodies (research RC-35 and RC-36). The planned test calls only `dispatch_main_mode`. Its body names none of the four HTTP modules, and the test imports none of them. The gate runs in T-LOCAL-GATES. If it fails, stop. Do not edit the baseline. |
| `dispatch_main_mode` changes its fallback path or its signature. | The test fails. | The assertions check the exit code and the refusal text. A changed outcome fails the test. |
| Replaced values leak into later tests. | A later test fails. | Each replacement uses monkeypatch, which restores the value at teardown. |
| A host with container detection changes the path. | The test fails on that host. | The container check returns false in both tests. |
| The publication hold in the issue comments stays in force. | T-PR waits. | Decision D-5. The orchestrator records the authorization before T-PR starts. |
| Pylint 4.1.3 and 4.1.4 report different results. | The finding count differs. | The installed 4.1.4 source defines the rules (rows RC-33 and RC-34). T-LOCAL-GATES runs the pylint command again. |
| `main` moves before T-PR. | Line numbers shift. | The branch rebases on `origin/main`. The pylint command runs again after the rebase. |

Caution: a failed rebase stops T-PR. Resolve the conflict in the test file, and then run the local gates again.

## Rollback Steps

1. Before the merge, close the pull request, or delete the branch.
2. After the merge, revert the squash commit in a new pull request.
3. The revert removes the fragment and the record files with the commit.

Warning: never force-push `main`. A force push removes commits that other agents depend on, and the removal cannot be undone from this repository.

## Complexity Tracking

| Violation | Why it is needed | Simpler alternative rejected because |
|---|---|---|
| Principle VII is passed by scope. The test file has no logger. | The test performs no product action. | A logger adds one module-level name to a module that already exceeds the five-item limit. The added name gives no behavior check. |
| The test module holds nine top-level names. | The file exists in this form. This is grandfathered debt. | Splitting the module changes more than two calls. The split belongs in a separate issue. |
