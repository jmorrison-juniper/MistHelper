# Implementation Plan: Prefer uv for worktree setup

**Branch**: `jmorrison-juniper-unclaimed-issue-repairs`
**Date**: 2026-09-30
**Spec**: [spec.md](spec.md)
**Input**: `specs/3399-uv-bootstrap/spec.md`
**Issue**: #3399, already owned by parent session `6d71fd26-57c2-48c0-abc8-607af98f75d0`

## Summary

Select uv once per `WorktreeBootstrapper.install_requirements()` invocation through `shutil.which("uv")`.
Use its resolved path for every present requirement file.
Use pip installation only when discovery returns `None`.
Keep pip available for the existing configuration read.

Each uv command uses `pip install --python <venv interpreter> -r <file>`.
Each file receives a separate child environment.
Keep working pip source choices through explicit uv mapping.
Apply the existing public-index decision without changing saved configuration.
Raise on a failed installation.
Do not retry through another installer.

Reuse the existing classes and methods with the narrow implementation correction below.
Keep browser setup, environment creation, health-check behavior, and GitHub account behavior unchanged.
Add focused offline tests and related documentation during a later implementation task.
This task creates planning artifacts only.

## Technical Context

**Language/Version**: Python 3.13 or newer. The caller reports an existing uv-managed Python 3.13.13.

**Primary Dependencies**: Existing standard-library modules, optional installed uv, and the worktree interpreter's pip.
Existing pytest, pytest-cov, and coverage support the tests.
No dependency declaration changes apply.

**Storage**: Run-local source mappings, child environment dictionaries, and an ordered list of successful file names.
The existing `.venv` layout remains unchanged.
No database or new persistent runtime record applies.

**Testing**: Offline pytest tests with temporary files, controlled clocks, simulated executable discovery, and simulated subprocess results.
Replace all connection probes and external setup actions.
Do not import `MistHelper.py` through the repository-wide test configuration.

**Target Platform**: Windows, Linux, and macOS.
Windows retains `.venv/Scripts/python.exe`.
Other platforms retain `.venv/bin/python`.

**Project Type**: Existing command-line setup script.
Its external interface consists of commands, process environments, console reports, return values, and exit status.

**Performance Goals**: One uv discovery and one pip configuration subprocess per install invocation.
Each invocation performs at most one three-second connection probe.
Each present file receives one package-install subprocess.
No fixed speed improvement applies.

**Constraints**: Use offline analysis.
Do not use the active dependency bootstrap's environment.
Do not install packages, run runtime checks, change branches, create issues, commit, push, or edit shared `CHANGELOG.md`.
Keep all planning writes under `specs/3399-uv-bootstrap/`.

**Scale/Scope**: Two requirement files, two installer paths, one existing source module, and focused existing test modules.
No new installer framework, source package, lockfile, upgrade operation, or deployment applies.

All technical choices are resolved in [research.md](research.md).

## Constitution Check

The initial review passed before research.
The post-design review passed with the same boundaries.

| Gate | Design evidence | Initial | Post-design |
| --- | --- | --- | --- |
| Structure and class ownership | Edit existing members. Add no source module or top-level class. The implementation correction records one nested-class exception. | PASS | CORRECTED |
| Safety and compatibility | Use argument lists, isolated environments, one existing probe, and exceptions that stop later setup actions. | PASS | PASS |
| Language and dependencies | Target Python 3.13 or newer. Keep pip and existing pins. Add no dependency or automatic uv installation. | PASS | PASS |
| Comments, action logs, and reports | Require inline reasons, before-and-after action logs, ASCII, STE, and no secret values in new reports. | PASS | PASS |
| Tests and documentation | Require offline coverage, exact file ownership, related documentation, and a unique later release fragment. | PASS | PASS |

Principle IV applies after a code change.
This task changes no code or release fragment.
It does not authorize that deployment workflow.
API exports, database keys, interactive input, containers, and production network operations do not apply.

### Existing structural debt

`scripts/` and the source module exceed five direct children.
`WorktreeBootstrapper` has ten direct methods.
Do not add another method to that class.
The implementation correction permits one nested installation-policy class.
`PipIndexProbe` has five methods.
Reuse those methods without increasing their count.
Store the source snapshot within its existing constructor.

`tests/unit/bootstrap/` has seven children.
Do not add a file or package there.
The index test module has four classes and one constant.
`TestInstallEnvironment` has four methods.
Add its new nested test group as the fifth direct child.
Each new group must have no more than five direct children.

`TestFallbackIndex` has six methods.
Preserve that existing count.
The browser-certificate test module exceeds five direct definitions.
Edit one existing test without adding a definition.
The unchanged browser-download method exceeds the 25-line limit.
Do not edit that method for this feature.

**Separate remediation**: Parent-authorized maintenance can split existing oversized structures without changing their behavior.
Do not combine that maintenance with issue #3399.
Every changed or new method must satisfy the five-parameter, five-block, and 25-line limits.

## Project Structure

### Documentation for this feature

```text
specs/3399-uv-bootstrap/
  spec.md                              Existing specification. Do not edit.
  checklists/requirements.md           Existing checklist. Do not edit.
  .spec-context.json                   Existing issue context. Record plan completion here.
  plan.md                             This plan.
  research.md                         Offline decisions and evidence.
  data-model.md                       Run-local entities and state transitions.
  quickstart.md                       Deferred offline validation commands.
  contracts/
    bootstrap-installation.md         Command, environment, failure, and test contract.
```

Do not create `tasks.md` during this command.

### Exact paths for later implementation

| Kind | Planned path | Planned change |
| --- | --- | --- |
| Implementation | `scripts/bootstrap_worktree.py` | Select the installer, capture source settings, map child environments, and report failures and timing. |
| Tests | `tests/unit/bootstrap/test_pip_index_probe.py` | Add offline command, source, isolation, timing, failure, and complete setup scenarios within existing class structure. |
| Tests | `tests/unit/scripts/test_browser_download_certificates.py` | Make the existing pip-install test simulate absent uv. Keep its browser assertions unchanged. |
| Documentation | `documentation/development-setup.md` | Explain optional uv, pip absence fallback, child settings, local source overrides, failure behavior, and Python selection. |
| Documentation | `README.md` | Add one short reference to the development setup behavior. Do not change operation counts. |
| Release note | `changelog.d/issue-3399-uv-bootstrap.md` | Add one issue-owned fragment during implementation. Do not create it during planning. |

### Existing regression paths

Run these unchanged files with the two planned test files:

- `tests/unit/bootstrap/test_github_account_checker.py`
- `tests/unit/scripts/test_browser_driver_bootstrap.py`

### Protected paths

Do not change `scripts/bootstrap_worktree.ps1`, requirement files, `pyproject.toml`, or shared agent guidance.
Do not change `CHANGELOG.md`, browser methods, health-check methods, GitHub methods, or the current specification.

**Structure Decision**: Keep the existing script and test locations.
Use nested test groups only where their current parent permits another child.
Reuse argument-list and explicit-interpreter prior art, not the incompatible `PackageInstaller` discovery and failure policy.

## Phase 0: Research

The research resolved these questions:

1. Installer discovery and explicit interpreter targeting.
2. Effective pip sources and exclusive public fallback.
3. Child environment isolation and certificate trust.
4. Failure propagation, timing, and offline test isolation.
5. Existing class ownership and structural limits.

[research.md](research.md) records each decision, rationale, alternative, and evidence.
No unresolved clarification remains.

## Phase 1: Design and Contracts

### 1. Installer run ownership

Keep uv discovery in `install_requirements()`.
Keep the selected path local to that invocation.
Reset `self.index_override` before the new probe.
Create one new `PipIndexProbe` instance.
Pass its source snapshot and the selected installer to existing install helpers.
Do not store installer selection on the bootstrapper.

Process `REQUIREMENT_FILES` in its existing order.
Skip an absent file.
Append a file name only after successful installation.
Return the same `list[str]` result.

### 2. Configuration and environment mapping

Capture the four pip source settings during the existing configuration read.
Keep the probe's current primary-line selection.
Use effective installation precedence for uv source mapping.
Caller environment settings precede `install.*`, then `global.*`.

Each installation receives a new environment through `_install_environment()`.
Keep the existing zero-argument helper behavior for `_browser_environment()`.
Apply uv overrides only when the selected installer is uv.
Apply file-config suppression only to a pip installation with a public override.

Set `UV_LINK_MODE=copy`, `UV_NATIVE_TLS=1`, and `UV_SYSTEM_CERTS=1` for each uv installation.
Set child-only `UV_HTTP_RETRIES=1` and `UV_HTTP_TIMEOUT=15` to preserve bounded transport.
Suppress uv source configuration in that child with `UV_NO_CONFIG=1`.
Remove `UV_CONFIG_FILE` from that child.
Normalize all four uv source aliases before source mapping.

If the probe selects the public fallback, remove inherited extra indexes from the installation child.
Set the corresponding uv primary source explicitly.
For pip installation, use child `PIP_CONFIG_FILE=os.devnull` to suppress saved extra indexes.
Never write a configuration file.

### 3. Failure and observability

Use `subprocess.run(..., check=False, env=child_environment)` with visible installer output.
Do not add `shell=True` or captured installer output.
Report the installer before installation.
State the missing-uv reason when pip is selected.

Report each attempted file's duration to one decimal place, including nonzero results and launch errors.
Raise with installer, file, and return-code context when available.
The existing `main()` exception handler returns `1`.
No later requirement file or setup action starts after failure.

Report successful total duration, including a run with no files.
Keep the current total-duration boundary after discovery and the index probe.
Log source hosts or decisions, not credential-bearing source URLs.
Limit related edits in the probe to safe reports and source capture.
Do not change its connection decisions.

### 4. Offline tests

Use the [contract coverage matrix](contracts/bootstrap-installation.md#offline-test-contract).
Keep new tests in a nested group under `TestInstallEnvironment`.
Use four scenario groups and one shared fixture at that level.
Each group must satisfy the constitution limits.

The groups cover commands, indexes, isolation, and failures with reports.
Use temporary requirement files and `subprocess.CompletedProcess` records.
Simulate every subprocess and connection.
Record environment object identity as well as values.
Use controlled monotonic clock values.

Exercise the actual `main()` sequence against local substitutes.
Record environment creation, health checks, browser actions, reports, and account actions.
Prove both failure suppression and successful call order.
Test the existing account constant without real credentials or GitHub calls.

Make the existing browser-certificate pip test select pip through mocked uv absence.
Do not let host-installed uv determine its command assertion.
Exclude repository-wide `tests/conftest.py` during the focused run.
Disable automatic plugin discovery and load only the required coverage plugin.

Require at least 80% coverage of changed behavior.
Keep the stronger configured coverage-report threshold of 90%.
Do not lower either gate or edit exclusions.
Do not report a skipped coverage gate as a pass.

### 5. Validation and agent context

[quickstart.md](quickstart.md) contains runnable commands for the later implementation.
Do not run them while the separate bootstrap is active.
macOS Python 3.9.6 is not a supported validation interpreter.
Use the completed `.venv` with Python 3.13 or newer.

The required PowerShell setup invocation returned `127` because `pwsh` is unavailable.
This plan uses the repository's existing plan template directly.
The agent-context script also requires PowerShell and normally edits shared files.
Shared guidance remains outside the caller's permitted scope.
Record plan technology and completion in the issue-scoped `.spec-context.json` instead.
Report script or hook execution limits without claiming successful execution.

### Post-design gate result

The design keeps installer state local, preserves working sources, and makes the public override exclusive.
It keeps production browser and GitHub behavior unchanged.
All planned source edits retain existing class membership.
All required offline cases have explicit observations.
The post-design constitution review passes.

## Phase 2: Planning Handoff

This command ends with the design artifacts.
It does not generate tasks or implement the feature.

The later task order is:

1. Add failing offline tests for the contract.
2. Implement run-local selection and source capture in existing methods.
3. Implement child mapping, timing, and failure context.
4. Run focused tests after the parent confirms bootstrap completion.
5. Update the exact documentation paths and the issue-owned release fragment.

The parent retains issue ownership and branch control.
Any later commit, push, or deployment requires separate authorization.

## Complexity Tracking

The implementation correction below records the caller-authorized nested-class exception.
Existing structural debt and its separate remediation remain recorded above.
Unavailable planning commands are execution limits, not unresolved design choices.

## Implementation Correction: Changed-function limits

The caller authorized implementation and released the restored Python 3.13.13 environment.
The caller also authorized the narrowest correction when the no-helper design conflicts with class-size constraints.

Source precedence, alias normalization, configuration controls, action logs, and failure handling cannot fit in the original methods within 25 lines.
Long expressions would hide these decisions.
One nested `WorktreeBootstrapper.InstallationPolicy` class will own child-source policy and installer execution.
It will contain at most five methods.
`install_requirements()` will retain once-per-invocation discovery and run ownership.
`_install_environment()` will retain the fresh copy and unchanged browser defaults.
`InstallationPolicy.install()` owns command construction, execution, and per-attempt timing.
Remove the old `_install_file()` method and migrate its actual call site.
These methods will not become pass-through wrappers.

The new policy replaces the old direct method, so the bootstrapper's existing child count does not increase.
It adds no source module, top-level class, dependency, configuration file, or installer framework.
`PipIndexProbe` will retain its five existing methods.
Separate parent-authorized maintenance can reduce the existing child count later.
Every changed or new function still must satisfy the five-parameter, five-block, and 25-line limits.

Qualified type annotations name the existing nested fixture recorder.
No module-level test alias, class, helper function, file, or package is added.
The four scenario groups and shared fixture remain unchanged.

The README ownership reservation ended when the Maps repair merged and its child was archived.
Add one sentence beside its existing development setup reference.
Keep detailed bootstrap instructions on the setup page.
The source and failure red commands hide captured fake credentials while retaining failed-case names and counts.

## Planning Execution Record

| Operation | Result |
| --- | --- |
| PowerShell setup script | The invocation returned `127`. `pwsh` is unavailable. The existing template supplied the plan structure. |
| PowerShell agent-context script | The invocation returned `127`. Shared agent files remain unchanged. Issue context records the design stack. |
| Optional Git hooks | Both commit hooks were skipped because the caller forbids commits. |
| Mandatory companion hook | The command invocation returned `127`. Its declared state update was recorded locally in the existing issue context. |
| Static artifact review | Fourteen local links resolved. Twelve protected file hashes matched their planning-start values. |
| Runtime validation | No tests, dependency installs, browser downloads, or GitHub checks ran. |

The unavailable companion command did not execute successfully.
The local context update is not evidence of extension execution.
No unresolved design choice remains.
