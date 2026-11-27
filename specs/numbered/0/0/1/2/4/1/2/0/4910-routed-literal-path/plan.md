# Implementation Plan: Restore -LiteralPath in the setup scripts

**Branch**: `fix/4910-routed-literal-path` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/4/1/2/0/4910-routed-literal-path/spec.md`

**Input**: Numeric specification at `specs/numbered/0/0/1/2/4/1/2/0/4910-routed-literal-path/spec.md`. The route `0/0/1/2/4/1/2/0` follows the base-5 rule in `tests/guardrails/test_spec_route_contract.py` (RC-63).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

Keep five children or fewer at every new directory level. The feature root holds five children: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.

## Summary

Restore the `-LiteralPath` hardening on each optional-document probe of `check-prerequisites.ps1` and `setup-tasks.ps1`. Restore it on the spec-file and template probes of `create-new-feature.ps1`. Keep the `design/` paths. Add a line-scan guard to `test_routed_core_port.py`. Add two behavior tests for bracket folders to `test_spec_route_contract.py`. Add one changelog fragment.

## Technical Context

**Language/Version**: PowerShell scripts under `.specify/scripts/powershell/`, and Python test modules under `tests/guardrails/`.

**Primary Dependencies**: No new dependency. The behavior tests start `pwsh` through `subprocess`, as the existing tests in the same file do (RC-65).

**Storage**: Not applicable: the change stores no data.

**Testing**: `pytest` in `tests/guardrails/test_routed_core_port.py` (RC-24) and `tests/guardrails/test_spec_route_contract.py` (RC-27).

**Target Platform**: PowerShell 7 locally and on the CI runner. The CI pytest shard runs on `ubuntu-latest` (RC-90).

**Project Type**: Tooling change to the Spec Kit scripts and their guard tests.

**Performance Goals**: Not applicable: the guard reads four text files, and the behavior tests start one process each.

**Constraints**: Log lines use ASCII only (RC-92). The guard reads each script as UTF-8 with LF line endings. Test names use full words.

**Scale/Scope**: Four scripts, two test modules, one changelog fragment, and one spec record.

## Constitution Check

Each rule of `.specify/memory/constitution.md` has one result and one reason.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule, directories (RC-74) | Pass | The record sits on the managed route `specs/numbered/`. The change adds no direct child to `tests/guardrails` (RC-38, 81 children, grandfathered). |
| I. Five-Item Rule, feature root | Pass | The feature root holds five children: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`. |
| I. Five-Item Rule, top-level names (RC-74) | Pass with recorded debt | `test_routed_core_port.py` holds 10 top-level names (RC-26). The change adds 4, so it holds 14. `test_spec_route_contract.py` holds 31 (RC-64). The change adds 2, so it holds 33. Remediation action: split both files by rule in a separate issue. |
| I. Five-Item Rule, function limits | Pass | Each new method and function has at most five parameters and at most five logical blocks. Each stays under 25 lines. |
| II. Class-Based Architecture (RC-75) | Pass | The line scan lives in one class with one method. The test functions follow the pytest style of their modules. |
| III. Safety-First (RC-91) | Pass | The change adds no input prompt, confirmation, or secret. The guard reads files only. |
| IV. Full Deployment Pipeline (RC-76) | Pass with noted steps | Steps 1 to 9 apply. Steps 10 and 11 run through the auto-merge dispatch of `container-build.yml` (RC-55). Step 12, deploy and health check, is an owner action, and `analysis.md` records it. |
| V. Observability and Logging (RC-92) | Pass | Each new log message uses ASCII text. The guard logs at info and debug levels. |
| VI. Inline Comments (RC-77) | Pass with requirement | Each changed line and each line of a touched block gets an inline comment (FR-012). |
| VII. Action Logging (RC-78) | Pass with requirement | Each touched action gets an info log before it and a debug log after it (FR-012). |
| Technology: mistapi (RC-95) | Not applicable | The change calls no Mist Cloud endpoint. |
| Technology: file paths (RC-95) | Pass | The tests use `pathlib.Path`. The scripts use `Join-Path` and `GetRelativePath`. |
| Technology: container runtime (RC-95) | Not applicable | The change starts no container and publishes no port. |
| Technology: data directory (RC-95) | Not applicable | The change writes no product output. The behavior tests use `tmp_path`. |
| Development Workflow: testing (RC-93) | Pass | The change adds no menu, so the `--test` sweep is not affected. |
| Development Workflow: release notes (RC-93, RC-98) | Pass | The change adds one fragment (FR-013). |
| Development Workflow: README (RC-93) | Not applicable | The change alters no operator-visible behavior of the tool. |
| Audience standard | Not applicable | The change alters no text that a network operations engineer reads. |
| Complexity-Driven SpecKit Escalation (RC-79) | Pass | The change touches more than three files, so the specification is required. |
| Multi-Agent Git Workflow (RC-94) | Pass | The issue exists and carries the `bug` and `tests` labels (RC-84). The branch `fix/4910-routed-literal-path` follows the type, issue, and slug rule (RC-70). The pull request targets `main`. |

## Architecture

The guard reads the four scoped scripts. It counts each probe line and each bare probe line. A probe line contains `Test-Path` or `Get-ChildItem`. A bare probe line contains `Test-Path` without `-LiteralPath`, or `Get-ChildItem -Path`.

```text
scoped script text -> LiteralProbeScanner.scan -> (examined lines, bare line numbers)
                                                 -> guard assertion with counts
```

The behavior tests run `check-prerequisites.ps1` and `setup-tasks.ps1` through `SpecCommandFixture` on a bracket folder. They read the `AVAILABLE_DOCS` list from the JSON output.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/2/0/4910-routed-literal-path/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      prerequisite-output.md
    checklists/
      requirements.md
      verification.md
```

### Source Code (repository root)

File-by-file change map. Each path is a repository path. Each row names one action.

| Path | Action | Change |
| - | - | - |
| `.specify/scripts/powershell/check-prerequisites.ps1` | Modify | Add `-LiteralPath` to the probes on lines 135, 136, 139, and 143. Change `Get-ChildItem -Path` on line 139 to `-LiteralPath`. Add comments and logs to the document block from line 133 to line 146. |
| `.specify/scripts/powershell/setup-tasks.ps1` | Modify | Add `-LiteralPath` to the probes on lines 56, 57, 58, and 61. Change `Get-ChildItem -Path` on line 58 to `-LiteralPath`. Add comments and logs to the document block from line 54 to line 62. |
| `.specify/scripts/powershell/create-new-feature.ps1` | Modify | Add `-LiteralPath` to the probes on lines 211 and 213. Add comments and logs to the block from line 211 to line 225. |
| `tests/guardrails/test_routed_core_port.py` | Modify | Add class `LiteralProbeScanner`, test `test_scoped_scripts_use_literal_probes`, test `test_unreadable_scoped_script_fails`, and test `test_literal_probe_scanner_flags_bare_forms`. Add `import logging`. |
| `tests/guardrails/test_spec_route_contract.py` | Modify | Add test `test_bracket_folder_lists_optional_documents` with two cases and test `test_bracket_folder_without_documents_lists_none` with two cases. |
| `changelog.d/issue-4910-routed-literal-path.md` | Add | One `###` heading and one `Fixed` bullet that names issue #4910. |

Line numbers refer to the current `main` content (RC-01 to RC-14). Each number moves after the first edit in its file.

No file is deleted. No manifest changes (D-9).

## Dependencies

- `pwsh` 7 for the behavior tests (RC-65).
- `pytest`, `ruff`, `black`, and the other tools of the local gates table. No new package is added.

## Design Decisions

The decisions with alternatives and risks are in `design/research.md`, section "Decisions". The plan uses these outcomes:

- The fix keeps the `design/` paths and restores `-LiteralPath` on each probe (D-1, D-2).
- The guard covers four scripts, not two (D-3).
- The guard lives in `test_routed_core_port.py` (D-4).
- The behavior test uses `[` and `]` in folder names (D-6).

## Logging and Comments in Touched Blocks

The probe lines keep their current behavior. Each block that the change touches gets the following additions.

- Each changed line and each adjacent line of the block gets an inline comment. The comment states the cause and the purpose.
- Before each probe block, the script writes an info line with `Write-Verbose`.
- After each probe block, the script writes a debug line with `Write-Debug`. The line holds the number of found documents only.
- Neither line writes to standard output, so the text and JSON output do not change (D-7).

The following sample shows a restored probe line. It keeps the routed `GetRelativePath` branch.

```powershell
if (Test-Path -LiteralPath $paths.RESEARCH) { $docs += [IO.Path]::GetRelativePath($paths.FEATURE_DIR, $paths.RESEARCH) }
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `test_routed_core_port.py` holds 14 top-level names after the change (10 before, RC-26) | The guard belongs to the routed-rule guards of issue #4873 (RC-24). | A new file in `tests/guardrails` adds a direct child to a folder that holds 81 tracked children (RC-38). |
| `test_spec_route_contract.py` holds 33 top-level names after the change (31 before, RC-64) | The bracket behavior tests use the `SpecCommandFixture` helper in that module (RC-27). | A new module duplicates the fixture and the `pwsh` skip logic. |

## Risks and Mitigations

- **The bracket test passes before the fix.** Run the two guard modules before the fix (task T003). Revise the test if it passes. A test that passes before the fix proves nothing.
- **A probe split over two lines escapes the line scan.** Caution: keep each probe on one line. The guard counts the examined lines, so an empty scan fails.
- **The editor writes LF line endings into `.ps1` files.** `.gitattributes` sets `*.ps1` to `eol=crlf` in the working tree (RC-53). Check the diff after each edit. Keep the diff limited to the change map.
- **Write-Verbose or Write-Debug prints in an operator run.** Both streams are silent by default. The source is the Microsoft preference-variable page in `design/research.md`, section Sources. Run each script once with default preferences and compare the output with the output before the change.
- **The change to `create-new-feature.ps1` affects the generator tests.** Run `test_spec_route_contract.py` in full (task T008).
- **Another open pull request edits the same files.** The check on 2026-11-26 found no overlap. Repeat the check before the pull request opens (task T-PR).
- **Issue #4873 part 2 reclassifies the restored lines.** Record the coordination in `analysis.md` and in the pull request body.
- **The remaining bare probes in `update-agent-context.ps1` and `common.ps1` stay in place.** Each needs a separate issue (see `analysis.md`).

## Rollback Steps

1. Before the merge, close the pull request, delete the branch `fix/4910-routed-literal-path`, and remove its worktree. No file on `main` changes.
2. After the squash merge, open a new issue and branch from `main`. Revert the squash commit in a new pull request. Do not force-push `main`.
3. After a revert, run `python -m pytest tests/guardrails/test_routed_core_port.py` on `main`. The guard file returns to its previous state.
