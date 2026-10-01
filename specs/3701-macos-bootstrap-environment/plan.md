# Implementation Plan: macOS bootstrap environment

**Branch**: `jmorrison-juniper-macos-bootstrap-environment` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: `specs/3701-macos-bootstrap-environment/spec.md`

## Summary

Issue #3701 records an abort before dependency installation.
The `EnvBuilder` constructor defaults to interpreter copies.
The copied uv-managed macOS interpreter cannot resolve `@rpath/libpython3.13.dylib`.

Match the standard-library `python -m venv` policy.
Set `symlinks` to true on POSIX and false on Windows.
Keep the change inside `WorktreeBootstrapper.create_environment`.
Keep `with_pip=True` and `upgrade_deps=False`.
Do not add a provider, helper class, wrapper, loader patch, or library copy.

## Technical Context

**Language/Version**: Python 3.13 or newer. Native evidence uses uv-managed CPython 3.13.13 on macOS arm64.

**Primary Dependencies**: The existing standard-library `venv`, pytest, and configured quality tools.

**Storage**: Owned temporary environments and private session evidence. No database change applies.

**Testing**: Real native environment creation with offline ensurepip. Direct platform decisions and existing offline bootstrap contracts.

**Target Platform**: Windows, Linux, and macOS. A simulated platform decision is not native Windows evidence.

**Project Type**: Existing setup command.

**Performance Goals**: No new provider discovery, network request, or package upgrade during environment creation.

**Constraints**: Keep installer, source, TLS, browser, health, credential, and dependency behavior unchanged.

**Scale/Scope**: One creation policy, one dedicated test module, one development setup section, and one issue-owned release fragment.

## Constitution Check

The repair retains the existing semantic class and introduces no source member.
The creation method remains within the function limits.
Tests use nested groups with at most five children.
The source module, `scripts/`, and its existing class exceed structural limits.
This repair does not expand that source debt.
Separate maintenance can restructure those existing elements.

Use existing action logs and explicit errors.
Add no suppression, exclusion, baseline change, credential change, or dependency change.
README and shared governance remain read-only.

The parent controls publication and the protected merge.
This local preparation does not authorize a push, a pull request, a workflow, a merge, or deployment.
The observed starting revision is not a verified-base grant.

## Project Structure

### Documentation (this feature)

```text
specs/3701-macos-bootstrap-environment/
  spec.md
  plan.md
  tasks.md
  checklists/requirements.md
  .spec-context.json
```

### Source Code (repository root)

```text
scripts/bootstrap_worktree.py
tests/unit/scripts/environment_creation/test_worktree_environment_creation.py
tests/unit/bootstrap/test_pip_index_probe.py
documentation/development-setup.md
changelog.d/issue-3701-macos-bootstrap-environment.md
```

**Structure Decision**: Keep the existing creation method. Isolate the new creation tests in a dedicated nested directory.

## Phase 0: Research

The local standard-library source confirms two distinct defaults.
`EnvBuilder` defaults to `symlinks=False`.
`venv.main` defaults to links when `os.name != "nt"`.
The existing interpreter property uses `sys.platform == "win32"` for the Windows path.
Use the same platform boundary for the explicit creation choice.

The original issue contains the complete sanitized trace.
Reproduce its real failure in a distinct owned environment before source changes.
Do not infer the failure from mocked builder arguments.

## Phase 1: Design and Contracts

### Creation and recovery

Pass the platform-specific `symlinks` value to the existing builder.
Keep the current recreation and reuse order.
Document `python scripts/bootstrap_worktree.py --recreate` for an earlier partial environment.
Explain that recreation removes packages in this worktree's `.venv`.
Do not claim that an existing copied interpreter repairs itself.

### Test design

Run direct builder decisions for `win32`, `linux`, and `darwin`.
Assert exact flags and interpreter paths.
Use temporary directories for reuse, removal failures, and propagation failures.
Create real environments with the native supported interpreter.
Run isolated interpreter probes with pip and the required standard modules.
Assert the environment prefix, base prefix, and version.
Prove that a deliberately invalid interpreter record fails the same check.
Count native environments separately from simulated platform decisions.

Run existing index, installation, browser, credential, and compose-provider contracts.
These contracts start no browser, installer, cloud client, or container.
Use the owned worktree environment for all dependency-backed checks.

The parent released the coupled `test_environment_options` assertion in `tests/unit/bootstrap/test_pip_index_probe.py`.
Add the platform-specific expected `symlinks` flag to its complete argument comparison.
Keep every installation assertion unchanged.
The live issue claim records this expanded path before the edit.

### Validation

Run the original native red check before implementation.
Run the dedicated failing policy tests before implementation.
Run the repaired native checks and focused adjacent selectors.
Measure changed executable regions, not the unrelated complete script.
Compile the entrypoint and changed Python files.
Run configured Ruff, Black, mypy, Bandit, test quality, and required-input preflight commands.
Keep every gate input unchanged.

Record a missing licensed STE dictionary as `dictionary_unavailable` and partial heuristic coverage.
If the normal pip-audit environment fails, do not call that a CVE result.
Use complete uv-generated runtime hashes with strict audit controls when needed.
Report the exact audited package count and the Git-only devtools limitation.

### SpecKit execution limits

Use the current specification, plan, task, and custom-agent instructions.
The mandatory Git hook attempt returned `127`: `env: pwsh: No such file or directory`.
The app-managed branch remains the feature branch.
The feature-only templates provide the fallback workflow.
Do not write `.specify/feature.json` or shared agent guidance.
Record unavailable companion commands honestly in the issue-owned context.
Decline optional early commit hooks because the parent requires one validated local commit.

## Phase 2: Local Handoff

Inspect the original pull request template and preserve all 23 checklist items in the unposted body.
Record each exact validation command and result.
Leave unperformed native Windows, container, live API, and publication checks incomplete.
Commit only the owned manifest with a Conventional Commits message and the Copilot App coauthor trailer.
Report the full commit SHA and clean worktree.
Wait for the position 34 full verified-main SHA grant.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| Existing oversized source class and directories | The defect resides in the current creation method. | A broad restructure would change unrelated bootstrap behavior. |

No new source structural exception applies.

## Local Validation Record

The final selected run passes all 181 tests on macOS arm64 with CPython 3.13.13.
No selected test skips.
The repeated native proof starts its interpreter and imports pip plus six required standard modules.
The creation method covers all 11 executable lines and all four branches.
The complete script reports 99.76 percent combined coverage against the unchanged 90 percent threshold.

The full test quality gate discovers 998 files and parses 950.
Its 48 exclusions come from the unchanged configuration.
It checks 725 findings and reports zero new findings and zero parse errors.
The unchanged input preflight validates six inputs and three guides.

The compile, Ruff, Black, configured types, and Bandit checks pass.
The source boundary check finds only one changed source member.
Both existing Python files retain all module-level names.
The coupled legacy method remains within 25 lines.

The writing check reads nine paths with scores from 93 through 100.
Its coverage remains `dictionary_unavailable/partial`.
No full vocabulary claim applies.

The normal pip-audit command still aborts in its separate temporary environment before a CVE audit.
The complete hashed native runtime alternative audits 105 packages.
It skips none and reports zero known vulnerabilities.
The Git-only development requirement remains outside that audit.
Issue #3612 remains outside this repair.

Both exact native reproduction directories are removed.
The working environment remains available.
No native Windows execution, container, browser download, live API, or publication occurs.
Private session evidence records the later local commit and required committed-scope check.
