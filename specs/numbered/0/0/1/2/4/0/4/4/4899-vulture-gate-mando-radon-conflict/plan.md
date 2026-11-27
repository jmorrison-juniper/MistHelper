# Implementation Plan: Vulture Gate Mando Radon Conflict

**Branch**: `fix/4899-vulture-gate-mando-radon-conflict` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/4/0/4/4/4899-vulture-gate-mando-radon-conflict/spec.md`

**Input**: Numeric record route `specs/numbered/0/0/1/2/4/0/4/4`. The eight base-5 segments of 4899 are 0, 0, 1, 2, 4, 0, 4, 4.

## Summary

The `Vulture (dead code)` check fails at its pip install step. Pull request #4888 pins `mando==0.8.2`. The pinned `radon==6.0.1` requires `mando<0.8`. The fix keeps every pin. It adds one Dependabot ignore rule, two guard cases, one guide note, and one release-note fragment.

## Technical Context

**Language/Version**: Python 3.15 or newer for the guard module. The repository requires that version (`.github/copilot-instructions.md`, "Language and environment").

**Primary Dependencies**: pip, Dependabot (pip and github-actions ecosystems), PyYAML, and pytest. The guard module already imports `yaml` (`tests/guardrails/test_pr_title_workflow.py`, line 15). No new dependency.

**Storage**: Not applicable. The change writes no data.

**Testing**: pytest guard modules under `tests/guardrails`, plus remote checks of the Quality Gates run.

**Target Platform**: Windows 11 local checkout and the GitHub Actions Ubuntu runner for the Vulture job.

**Project Type**: CI configuration change, one guard test extension, one guide note, and one fragment.

**Performance Goals**: Not applicable. No runtime path changes.

**Constraints**: Keep every pin and gate. Add no direct child to `tests/guardrails`. The Dependabot rule must parse in Dependabot.

**Scale/Scope**: Four repository files. Three change and one is new.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | `tests/guardrails` already holds 79 direct children. The change adds no child there. The fragment is one unique record under `changelog.d/`. The route leaf holds one record. |
| II. Class-Based Architecture | Pass | The two cases join the existing class `TestDependabotPolicy`. No wrapper function is added. |
| III. Safety-First | Pass | No keyboard input, no destructive operation, and no secret appears in the change. |
| IV. Full Deployment Pipeline | Pass with exception | Steps 1 to 9 apply. Steps 10 to 12 do not apply. `.github/workflows/container-build.yml` runs on listed product paths only (lines 5 to 19), and none changes. |
| V. Observability and Logging | Pass | The change adds no runtime log. The guard fixture already logs its read action. |
| VI. Inline Comments | Pass | Each new Python line carries an inline comment. The YAML comment states the cause and the removal condition. |
| VII. Action Logging | Pass | The new cases call the existing assertion path. They add no action. |
| Python 3.15 only | Pass | No Python version changes. |
| mistapi for Mist REST | Pass | Not applicable. The change calls no Mist endpoint. |
| Podman and test containers | Pass | Not applicable. No container starts. |
| File paths with pathlib | Pass | The guard keeps `REPOSITORY_ROOT / ".github" / "dependabot.yml"`. |
| Data directory and operational store | Pass | Not applicable. The change writes no product output. |
| Syntax validation before commit | Pass | T-LOCAL-GATES runs `python -m py_compile MistHelper.py`. |
| Security findings | Pass | No security tool reports a finding for this change. Bandit runs on the changed test module. |
| README and release notes | Pass | No operation count changes. One fragment is added. |
| Pull request title | Pass | The title uses the `fix(ci):` form. |
| Labels | Pass | The issue keeps `bug` and `ci`. The `in-progress` label is added before the branch is made. |
| Specification escalation | Pass | The change touches three or more files. `AGENTS.md`, section "Specifications", requires a specification. |

Mist Cloud transport requirements: not applicable. This change names no Mist REST method and no WebSocket path.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/0/4/4/4899-vulture-gate-mando-radon-conflict/
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

No `contracts/` folder exists. No menu, command-line, output, or API contract applies to this change.

### Repository files that change

```text
.github/dependabot.yml                       modify
tests/guardrails/test_pr_title_workflow.py   modify
documentation/quality-gates.md               modify
changelog.d/issue-4899-mando-radon-pin.md    add
```

The record folder holds the eight specification files. Add it in a separate commit on the same branch.

## File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `.github/dependabot.yml` | Modify | Add the `ignore` block below the pip stream `commit-message` key (lines 3 to 11 on `main`). |
| `tests/guardrails/test_pr_title_workflow.py` | Modify | Add the same rule to the pip stream of `POLICY_SNAPSHOTS["dependabot"]` (lines 23 to 30). Add two cases to `test_unrelated_changes_fail` (lines 302 to 320). |
| `documentation/quality-gates.md` | Modify | Add one paragraph after the job table and before the warning at line 74. |
| `changelog.d/issue-4899-mando-radon-pin.md` | Add | Add one heading and one `Fixed` bullet. |
| `requirements-dev.txt`, `requirements.txt`, `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml` | None | Pins and gates stay unchanged. |

Exact text for `.github/dependabot.yml`, placed after line 11:

```yaml
    ignore:
      # radon 6.0.1 requires mando below 0.8. Pull request #4888 raised mando to 0.8.2,
      # and the pip install step of the Vulture job failed on that conflict (issue #4899).
      # This rule stops Dependabot from proposing mando 0.8 or later. Remove it when radon
      # accepts mando 0.8, and move the mando pin in requirements-dev.txt in the same change.
      - dependency-name: "mando"
        versions: [">= 0.8"]
```

Exact lines for `POLICY_SNAPSHOTS["dependabot"]`, placed after the `commit-message` key of the pip stream:

```python
                "ignore": [{"dependency-name": "mando", "versions": [">= 0.8"]}],  # Keep the rule that radon 6.0.1 needs.
```

Exact cases for `test_unrelated_changes_fail`, placed before the closing bracket of the list:

```python
            (("updates", 0, "ignore"), []),  # Removing the mando rule must fail the guard.
            (("updates", 0, "ignore", 0, "versions"), [">= 0.9"]),  # Moving the lower bound must fail the guard.
```

Exact paragraph for `documentation/quality-gates.md`, placed after the job table:

```text
The `vulture` job installs `requirements-dev.txt` before it runs the scan. A pin conflict stops that install step, so vulture does not run. Issue #4899 records a conflict between `mando==0.8.2` and `radon==6.0.1`. Dependabot ignores `mando` 0.8 and later, because radon 6.0.1 requires `mando` below 0.8. Remove that rule when radon accepts `mando` 0.8.
```

Exact fragment for `changelog.d/issue-4899-mando-radon-pin.md`:

```markdown
### Dependabot keeps mando below 0.8

- **Fixed**: Dependabot no longer proposes `mando` 0.8. That update conflicts with `radon` 6.0.1 and fails the Vulture job install step. Issue #4899.
```

## Architecture

```text
Dependabot weekly run -> .github/dependabot.yml ignore rule -> no mando 0.8 pull request
requirements-dev.txt (mando 0.7.1, radon 6.0.1) -> pip install step -> Vulture job scan
tests/guardrails/test_pr_title_workflow.py reads dependabot.yml -> fails on rule drift
```

## Dependencies

This change adds no package and repins none. The guard uses PyYAML, which it already imports.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| Dependabot rejects the `versions` syntax | Dependabot stops every pip update | Use the documented pattern (research RC-45). Run the guard (TEST-001). Check the next Dependabot run (SC-004). Revert if needed. |
| A later `mando` security fix does not reach the pins | Delayed update | The rule names its removal condition in two files. Radon uses `mando` for its command-line interface only, which the PyPI page states. |
| A person edits the rule away | The failure returns on the next Dependabot run | The guard fails on the removal (TEST-002). |
| The snapshot and the file drift apart | Guard fails | Both change in the same commit (T002). |
| Closing pull request #4888 loses its thread | Context moves | Caution: the thread stays on GitHub. A reviewer can reopen the pull request. |
| Another job fails on the fix pull request | Gate stays red | Read the new log and file a separate issue before any fix (TEST-007). |

## Rollback Steps

1. Revert the fix commit on `main` through a revert pull request.
2. Confirm that the revert restores the previous `dependabot.yml` and test file.
3. Reopen pull request #4888 only when a person needs its history for review.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `tests/guardrails` holds 79 direct children (grandfathered debt, research RC-37) | The policy guard already lives in that folder | A new guard file adds a direct child to a noncompliant parent, which Principle I forbids. The separate remediation is tracked outside this change. |
