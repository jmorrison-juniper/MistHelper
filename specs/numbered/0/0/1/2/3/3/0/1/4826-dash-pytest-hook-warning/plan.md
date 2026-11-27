# Implementation Plan: Dash pytest plugin marker warning

**Branch**: `chore/4826-dash-pytest-hook-warning` (planned) | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric record route `specs/numbered/0/0/1/2/3/3/0/1/`, record folder `4826-dash-pytest-hook-warning`.

## Summary

The warning comes from the installed Dash pytest plugin, version 4.5.1. Upstream changed the old-style marker on its `dev` branch. No Dash release contains that change yet. This interim change keeps the plugin and the warning visible. It adds a policy check that rejects suppression. It adds a known-warning section to the development setup guide. The Dash pins change later, after an upstream release.

## Technical Context

**Language/Version**: Python 3.15.2 for the local environment, from the bootstrap command (remote check RC-15). The policy check uses the standard library `tomllib` parser.

**Primary Dependencies**: `dash==4.5.1` (RC-09, RC-10) and `pytest==9.2.0` (RC-08, RC-11). The interim change adds no dependency.

**Storage**: Not applicable. The change writes no data file.

**Testing**: pytest in the repository test tree. The policy tests use `pytest.mark.parametrize` and `tmp_path`.

**Target Platform**: Windows 11 local development in a venv (RC-42). The quickstart also gives the Linux and macOS commands.

**Project Type**: Python command-line tool with a test tree.

**Performance Goals**: Not applicable. The policy check reads two small files.

**Constraints**: No suppression. No manifest change before an upstream release. No new direct child under a noncompliant parent (RC-17, RC-37, RC-38).

**Scale/Scope**: Two changed files and one new record folder in the interim change. One upgrade change later.

## Constitution Check

Gate result: pass. One structural debt item is recorded in Complexity Tracking.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass with debt | The policy check edits an existing module and adds no direct child (RC-36). The contract folder already holds 17 children (RC-37). Task T011 tracks the remediation. |
| II. Class-based architecture | Pass | The policy check is a class with three methods. No wrapper function delegates to a method. |
| III. Safety-first | Pass | The policy check reads one TOML file and one Markdown file. It reads no keyboard input and sends no network request. |
| IV. Full pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the pipeline. |
| V. Observability and ASCII | Pass | Log text and documentation text use ASCII only. Logs name file paths and never print a secret. |
| VI. Inline comments | Pass | Each new executable line carries an inline comment that gives its purpose. |
| VII. Action logging | Pass | The policy check logs info before the file read and debug after the parse. |
| Python version | Pass | Python 3.15.2 from the bootstrap command (RC-15). |
| mistapi | Not applicable | The change sends no Mist REST request and changes no WebSocket transport. |
| UV | Pass | The upgrade change regenerates `uv.lock` with the UV tooling (T009). |
| Podman | Not applicable | The change starts no container. |
| File paths | Pass | The policy check uses `pathlib.Path` for every path. |
| Data directory | Not applicable | The change writes no product output. |
| Container security and Zscaler | Not applicable | The change builds and pushes no container. |
| Database keys | Not applicable | The change writes no database row. |
| Security findings | Pass | The change adds no suppression. The policy check rejects suppression of the warning (RC-18). |
| Documentation | Pass | `documentation/development-setup.md` changes. No README change, because no user-facing behavior changes. |
| Release notes | Pass | No changelog fragment. The change is internal only (RC-24). |
| Complexity-driven escalation | Pass | This record exists because the change touches three or more paths (RC-19). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/3/0/1/4826-dash-pytest-hook-warning/
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

The `design/contracts/` folder is omitted. The change alters no menu, CLI, output column, or API shape.

### Source Code (repository root)

```text
tests/contract/test_pytest_coverage_gate.py    modify: add DashPytestPluginPolicy and TestDashPytestPluginPolicy
documentation/development-setup.md             modify: add the known-warning section before "Where the code lives"
```

**Structure Decision**: The policy check goes in the existing contract module. The guardrails folder (RC-38) and the contract folder (RC-37) already hold more than five children. A new file or package in either folder breaks the five-item rule. A narrow edit of an existing module adds no child.

## File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `tests/contract/test_pytest_coverage_gate.py` | modify | Add `import tomllib`, two path constants, class `DashPytestPluginPolicy`, and class `TestDashPytestPluginPolicy`. |
| `documentation/development-setup.md` | modify | Insert the section `## Known warning from the Dash pytest plugin` before `## Where the code lives`. |
| `specs/numbered/0/0/1/2/3/3/0/1/4826-dash-pytest-hook-warning/` | add | Add this record. |
| `pyproject.toml` | none | The policy check reads this file. The change does not edit it. |
| `requirements.txt`, `requirements-dev.txt`, `uv.lock` | none in the interim change | Change only in task T009, after an upstream release. |

## Policy Check Design

**Class `DashPytestPluginPolicy`** holds three methods.

- `load_ini_options(pyproject_path)` reads the TOML file with `tomllib`. It returns the table `tool.pytest.ini_options`. It raises `KeyError` when the table is missing.
- `find_violations(ini_options)` returns one message for each `no:dash` option in `addopts`. It returns one message for each `filterwarnings` entry that ignores a forbidden category.
- `missing_doc_terms(document_text)` returns each required term that the document lacks.

**Forbidden categories**: `Warning`, `PytestWarning`, `DeprecationWarning`, `PytestDeprecationWarning`, and `PytestRemovedIn10Warning`. Each name may carry the prefix `pytest.`. Each name is the warning class itself or a base class of it (RC-46).

**Required document terms**: `PytestRemovedIn10Warning`, `#4826`, `4.5.1`, and `-W error::pytest.PytestRemovedIn10Warning`.

**Failure behavior**: A missing table raises `KeyError`. The policy check does not return an empty result for a missing table, because an empty result hides the defect.

## Implementation Outline

1. Verify the current state with tasks T001, T002, and T003.
2. Add the policy check and the policy tests with task T004.
3. Add the known-warning section with task T005.
4. Copy the record with task T006. Confirm the manifest state with task T007.
5. Run the local gates with task T-LOCAL-GATES.
6. Open the pull request with task T-PR. Watch the checks with task T-REMOTE-CI. Merge after authorization with task T-MERGE.
7. Watch upstream releases with task T008. Upgrade with task T009 after a release that contains the fix.

## Dependencies

- An upstream Dash release that contains the decorator fix. No such release exists on 2026-11-26 (RC-48, RC-53).
- A handover from the manifest owner before task T009.
- Open pull request #4888 must merge, or the upgrade change must rebase after it (RC-63).
- Local gate tools named in `.github/copilot-instructions.md`: ruff, black, the test quality analyzer, the STE linter, radon, the complexity gate, and symbol-diff (RC-16).
- PowerShell 7 for `tests/guardrails/test_spec_route_contract.py`. The workstation has `C:\Program Files\PowerShell\7\pwsh.exe`.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| No Dash release contains the fix for a long time | The warning stays visible in each run | Keep the exact pytest pin. Run task T008 at each dependency review. Keep the issue open. |
| An engineer adds `-p no:dash` | Test results change, as PR #4831 showed | Policy test 2 fails. The guide gives a Caution statement. |
| An engineer adds a warning filter | The defect hides from the warnings summary | Policy test 3 fails for each forbidden category. |
| pytest 10 becomes the target | Plugin load can fail | The exact pins `pytest==9.2.0` block an accidental change (RC-08, RC-11). |
| The `dash[testing]` extra gets installed | More hook specifications and options load | The warning gate runs again in the upgrade change. |
| Another plugin emits PytestRemovedIn10Warning | The warning gate fails for another cause | The engineer reads the module named in the warning. |
| A later change splits the contract module | The policy check moves | Task T011 moves the check to a compliant package. |
| Open pull request #4888 edits `requirements-dev.txt` | A merge conflict in the upgrade change | Task T009 waits for #4888 or rebases after it. |

## Rollback Steps

1. Interim change, before merge: close the pull request and delete its branch. Keep the record in the draft folder.
2. Interim change, after merge: open a new pull request that reverts the squash commit. The revert changes no data.
3. Upgrade change: revert the pin commit and the lock file commit. Set `requirements.txt` line 45 and `requirements-dev.txt` line 76 back to `dash==4.5.1`.
4. Branch removal: if `fix/4826-dash-pytest-hooks` is deleted, restore it from the PR ref `refs/pull/4831/head`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| The policy check sits in `tests/contract/test_pytest_coverage_gate.py`, a module that reads the CI workflow (RC-36). | The module already belongs to the contract tests for pytest gates, and the edit adds no child. | A new file in `tests/guardrails/` or `tests/contract/` adds a direct child to a noncompliant parent (RC-37, RC-38). Task T011 tracks the move. |
