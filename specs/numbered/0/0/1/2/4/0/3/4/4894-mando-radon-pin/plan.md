# Implementation Plan: Keep mando inside the radon requirement

**Branch**: `fix/4894-mando-radon-pin` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this folder

**Input**: Numeric record `specs/numbered/0/0/1/2/4/0/3/4/4894-mando-radon-pin/`. The eight route digits 0 0 1 2 4 0 3 4 equal 4894 in base 5. Each folder holds five children or fewer.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`.

## Summary

Keep mando at 0.7.1. Add a mando ignore entry to the pip update block of `.github/dependabot.yml`. Add two guard tests to the existing export guard file. Add one changelog fragment. Close pull request #4888 without a merge.

## Technical Context

- **Language/Version**: Python 3.15 or newer. `pyproject.toml` requires `>=3.15`.
- **Primary Dependencies**: pip resolver, uv export from the dev extra, Dependabot pip ecosystem, PyYAML 6.0.4 (requirements-dev.txt line 356).
- **Storage**: Not applicable. The change touches no data store.
- **Testing**: pytest 9.2.0 from the dev extra. Guard tests live in `tests/guardrails/`.
- **Target Platform**: GitHub Actions `ubuntu-latest` for the Quality Gates jobs. The local host runs Windows 11.
- **Project Type**: CI configuration, one guard test extension, one changelog fragment.
- **Performance Goals**: Not applicable. The change adds no runtime path.
- **Constraints**: `uv.lock` is the source of the requirements exports. The export guard fails on any export that differs from `uv export --locked`.
- **Scale/Scope**: One pin kept, one ignore entry, two test cases, one fragment, one closed pull request, two separate issues.

## Constitution Check

*Checked after research and before implementation.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule: managed roots and base-5 route | Pass | The record sits at the route for issue 4894 under `specs/numbered/`. The route digits match 4894. |
| I. Five-Item Rule: no new direct child in a noncompliant parent | Pass | `tests/guardrails` holds 77 files on main. The tests extend the existing `test_dependency_export.py`. No child is added. |
| I. Five-Item Rule: process folder debt | Pass with debt recorded | `changelog.d/` holds 335 files on main. The fragment is one unique process record. Issue B under FR-010 tracks the remediation. |
| I. Five-Item Rule: feature root | Pass | The feature root holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design`. That is five children. |
| II. Class-based architecture and full names | Pass | The new tests sit in a test class. No wrapper function is added. Names use full words. |
| III. Safety-first input handling | Pass | The change adds no input path. The test reads one local YAML file. |
| IV. Full deployment pipeline | Pass with notes | Local gates, rebase, push, pull request, CI, squash merge, and main build run in order. The deployment stays with the owner. |
| V. ASCII log output | Pass | The new code prints no non-ASCII text. |
| VI. Inline comments | Pass | Each executable line of the new Python code carries an inline comment. |
| VII. Action logging | Pass | The new test logs before and after the YAML read, with the module logger. |
| Technology: paths and runtime | Pass | The test builds paths with `Path(__file__)`. The change adds no Podman or mistapi use. |
| Security: fix over suppress | Pass | The change suppresses no finding. |
| Documentation: release-note fragment | Pass | The constitution governs the fragment rule. Decision D-5 records the conflict. |
| Git: branch, issue first, PR title | Pass | The branch is `fix/4894-mando-radon-pin`. Issue 4894 receives `in-progress`. The title uses `fix(ci):`. |
| SpecKit escalation | Pass | The change touches more than three files, so this record exists. |
| Fleet coordination | Pass | Only pull request #4888 touches requirements-dev.txt. No other open pull request touches the change paths. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/0/3/4/4894-mando-radon-pin/
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

### Change Map

| Path | Action | Purpose |
| - | - | - |
| `.github/dependabot.yml` | Modify | Add `ignore:` with `dependency-name: "mando"` to the pip update block, lines 3 to 11 on main. |
| `tests/guardrails/test_dependency_export.py` | Modify | Add class `TestDependabotPipIgnore` with two test methods. Import `yaml`. Extend the module docstring. |
| `changelog.d/issue-4894-mando-radon-pin.md` | Add | One `Fixed` bullet for issue #4894. |
| `specs/numbered/0/0/1/2/4/0/3/4/4894-mando-radon-pin/` | Add | This record. Copy the eight files from the draft folder. |

GitHub actions outside the repository:

- Pull request #4888: close without a merge, with a comment.
- Issue #4894: add the `in-progress` label.
- Two new issues: one for the fragment policy conflict and one for the changelog.d folder debt.

Unchanged paths, the scope guard for FR-007: `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml`, `.github/workflows/windows-timeout-budget.yml`, `.github/workflows/windows-audit-report.yml`, and `mist-ops-platform/`.

### Contracts

No contract applies. The change adds no menu, CLI, output, or API contract. The `design/contracts/` folder is omitted.

### Test Placement

A new file in `tests/guardrails/` adds a direct child to a folder with 77 files. The Five-Item Rule forbids that addition. The two tests extend `test_dependency_export.py` instead. That file already guards dependency exports, and AGENTS.md prefers existing test files.

## Design Decisions

Decisions D-1 to D-6 live in `design/research.md`. This plan applies them.

## Dependencies

- No package is added. PyYAML 6.0.4 is already pinned at requirements-dev.txt line 356.
- The change relies on Dependabot reading requirements-dev.txt. The Dependabot pull request for mando proves that reading.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| Caution: radon accepts mando 0.8 in a later release, and the ignore entry then blocks the upgrade. | The ignore comment names the removal condition. The owner removes the entry with the radon change. |
| Caution: the ignore entry blocks a mando 0.7.x update. | Check mando advisories by hand. The mando PyPI description says it wraps argparse for command-line interfaces. |
| Caution: a hand edit of requirements-dev.txt fails the export guard. | Use uv to change a pin. The guard names the stale file. |
| Caution: the guard tests depend on the repository layout. | The test resolves the root from `Path(__file__)`, the same way the export guard does. |
| Caution: the fix head fails a check that this record did not predict. | T-REMOTE-CI reads each named check. Unknown results stay open in analysis.md until CI reports them. |

## Rollback Steps

1. Before the merge, remove the branch `fix/4894-mando-radon-pin` and its worktree. Warning: removing a worktree deletes its uncommitted files. Save them first.
2. After the merge, open a new pull request from `main`. That pull request removes the ignore entry, the two test cases, and the fragment.
3. Reopen pull request #4888 when its branch `dependabot/pip/mando-0.8.2` still exists. Unverified: the branch state after a close. See research U-02.

## Verification Plan

- Tasks T001 to T007 and the four final tasks each name one verification command. See `tasks.md`.
- The quickstart commands reproduce the failure and run each local check. See `design/quickstart.md`.
- The CI checks in TC-009 to TC-011 decide the remote result. See `tasks.md`.
