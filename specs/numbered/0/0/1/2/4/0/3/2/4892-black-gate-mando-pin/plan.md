# Implementation Plan: Black Gate Failure From the Mando Pin

**Branch**: `fix/4892-black-gate-mando-pin` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification at `specs\numbered\0\0\1\2\4\0\3\2\4892-black-gate-mando-pin\spec.md`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design\`.

## Summary

The Black (format check) job fails at its pip install step. Pull request #4888 raises the mando pin to 0.8.2. Radon 6.0.1 requires mando below 0.8, so pip stops. This change keeps the mando pin at 0.7.1. It adds a Dependabot ignore rule for mando 0.8 and later. It adds two guard tests and one changelog fragment. It changes no lock file, no product code, and no workflow.

## Terms

| Term | Meaning |
| - | - |
| Black job | The job named `Black (format check)` in `.github\workflows\ci.yml`. |
| Black format check step | The step named `Black format check` in the Black job. It runs `black --check --diff .`. |
| Mando pin | The locked mando version. The value is 0.7.1. |
| Radon range | The mando range that radon 6.0.1 accepts. The value is `<0.8,>=0.6`. |
| Pip entry | The `package-ecosystem: "pip"` block in `.github\dependabot.yml`. |
| Ignore rule | An entry in the `ignore` list of the pip entry. It removes matching updates. |
| Pull request #4888 | The Dependabot pull request that raises mando to 0.8.2. |

## Technical Context

- **Language/Version**: Python 3.15. `pyproject.toml` line 23 requires `>=3.15` (R-82).
- **Primary Dependencies**: PyYAML 6.0.4 (`requirements-dev.txt` line 356, R-83) and packaging 26.3 (line 228, R-84).
- **Storage**: Not applicable. The change writes no data.
- **Testing**: pytest, in `tests\guardrails\test_dependency_lock_file.py`.
- **Target Platform**: GitHub Actions `ubuntu-latest` (`.github\workflows\ci.yml` line 142, R-81). Windows 11 runs the local gates.
- **Project Type**: CI configuration, one guard test, one changelog fragment, and one spec record.
- **Performance Goals**: Not applicable. The guard reads two small files.
- **Constraints**: Five children or fewer per new directory. STE for prose. Inline comments and action logging in test code.
- **Scale/Scope**: Four changed paths in the repository, plus the record folder.

## Constitution Check

*Gate: passes before research and after design. Source: `.specify\memory\constitution.md`, version 1.9.0.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, new specs directories | Pass | Each new directory holds one child or fewer. The route parents hold five or fewer after the change (research R-32, R-33). |
| I. Five-item rule, changelog folder debt | Pass with recorded debt | `changelog.d\` holds 335 direct children (R-30). One unique fragment is a permitted record. Remediation is recorded in analysis F-6. |
| I. Five-item rule, guardrails folder debt | Pass | `tests\guardrails\` holds 79 direct children (R-31). The change adds no direct child. It edits an existing child. |
| I. Module names, touched debt | Pass with recorded debt | `tests\guardrails\test_dependency_lock_file.py` holds 8 top-level names (R-86). The change adds 3, for 11 total. Remediation is recorded below. |
| I. Function limits | Pass | Each new function holds five parameters or fewer, five blocks or fewer, and 25 lines or fewer. |
| II. Class-based architecture | Pass | The new logic lives in a named class with static methods. No wrapper function is added. |
| III. Safety-first input | Pass | The test reads one fixed repository file. It takes no external input and handles no secret. |
| IV. Full deployment pipeline | Pass with stated exceptions | Steps 1 to 9 apply. Steps 10 to 12 do not run. `container-build.yml` runs only for product file changes (`.github\copilot-instructions.md` line 473, R-87). |
| V. ASCII logging | Pass | New log lines use ASCII only. |
| VI. Inline comments | Pass | Each new executable line carries an inline comment. YAML keys follow the npm precedent with a comment block above (`.github\dependabot.yml` line 45, R-21). |
| VII. Action logging | Pass | Each file read has an info line before it and a debug line after it. |
| Technology: Python 3.15 | Pass | `pyproject.toml` line 23 (R-82). |
| Technology: UV and requirements.txt | Pass | `uv.lock`, `requirements.txt`, and `requirements-dev.txt` stay unchanged (R-16, R-19). |
| Technology: file paths | Pass | The test uses `pathlib.Path`, as the module already does (R-85). |
| Technology: Mist API | Not applicable | The change calls no Mist endpoint. |
| Data directory | Pass | No output goes to `data\`. |
| Development workflow, testing | Pass | Each applicable local gate runs. See Gate Applicability. |
| Documentation, README | Not applicable | No operator-visible behavior changes. |
| Documentation, release notes | Pass | One fragment is added (decision D-7, R-26). |
| SpecKit escalation | Pass | The change touches four or more paths, so this record exists. |
| Multi-agent, issue first | Pass | Issue #4892 exists. Add `in-progress` before the branch. |
| Multi-agent, branch name | Pass | Branch `fix/4892-black-gate-mando-pin`. |
| Multi-agent, labels | Pass | The issue has `bug` and `ci` (R-96). Add `in-progress` (R-90). |
| Multi-agent, file overlap | Pass | Pull request #4888 changes `requirements-dev.txt` only (R-51). Check open pull requests again before the push. |
| Governance | Not applicable | The change amends no constitution rule. |

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\1\2\4\0\3\2\4892-black-gate-mando-pin\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    contracts\
      dependabot-mando-ignore.md
    checklists\
      requirements.md
      dependency-policy.md
```

## File Change Map

| Path | Action | Purpose | Requirements |
| - | - | - | - |
| `.github\dependabot.yml` | Modify | Add an `ignore` list with a mando rule to the pip entry (lines 3 to 11). | FR-003, FR-004 |
| `tests\guardrails\test_dependency_lock_file.py` | Modify | Add class `DependabotPolicy` and two test functions. | FR-003, FR-004, FR-005 |
| `changelog.d\issue-4892-black-gate-mando-pin.md` | Add | One fragment with one heading and one `Fixed` bullet. | FR-007 |
| `specs\numbered\0\0\1\2\4\0\3\2\4892-black-gate-mando-pin\` | Add | The ten Markdown files of this record. | FR-001, FR-008 |
| `requirements-dev.txt`, `requirements.txt`, `uv.lock` | No change | Keeps the mando pin at 0.7.1. | FR-002 |
| `.github\workflows\ci.yml`, `pyproject.toml`, `documentation\` | No change | No gate or document changes. | FR-002, FR-006 |

## Dependencies

- No new package. PyYAML and packaging are already pinned in `requirements-dev.txt`. `tomllib` is in the standard library.
- Read-only GitHub commands for evidence (`gh` GET requests only).
- The Dependabot runtime behavior for `versions` is unverified. Research U-1 records it.

## Gate Applicability

| Gate | Applies | Command | Expected result | Note |
| - | - | - | - | - |
| Compile | Yes | `python -m py_compile MistHelper.py` | No output | The constitution requires it before each commit (R-94, R-71). |
| Lint | Yes | `python -m ruff check .` | `All checks passed` | Covers the changed test file (R-70). |
| Format | Yes | `python -m black --check .` | No file needs a change | Covers the changed test file (R-63). |
| Types | No | `python -m mypy $MYPY_PATHS --config-file pyproject.toml` | `Success` | `MYPY_PATHS` lists product paths only (R-73, R-76). |
| Tests | Yes | `python -m pytest tests\guardrails\test_dependency_lock_file.py` | All tests pass | The changed test file (R-64). |
| Tests, changelog | Yes | `python -m pytest tests\guardrails\test_changelog_fragment_policy.py` | All tests pass | Covers the fragment. |
| Full tests | Yes | `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal` | One summary line per shard | The changed file sits in this shard (R-69). |
| Coverage | Indirect | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | 80 percent or above | `src` is unchanged. CI runs this in the coverage shards (R-72, R-89). Not run locally. |
| Test quality | Yes | `test-quality-analyzer --gate` with the command block in `.github\copilot-instructions.md` line 124 (R-68) | `gate: 0 new findings vs baseline` | Run after the local commit and before the push. |
| Complexity | No | `radon cc <package> -j` into `complexity-gate --max 10` | No block above 10 | `RADON_PATHS` lists one test file, not this module (R-74, R-77). |
| Security lint | Yes | `bandit -c pyproject.toml -r . -q` | No finding | The CI command (R-66, R-88). The tests folder is excluded by `pyproject.toml` line 503 (R-22). |
| Dependency audit | No | `pip-audit -r requirements.txt` | No known vulnerability | `requirements.txt` is unchanged. |
| Code quality | No | `pylint src/ --fail-under=9.5` | Score 9.5 or above | `src` is unchanged. |
| Dead code | No | `vulture $VULTURE_PATHS --min-confidence 70` | No finding | `VULTURE_PATHS` lists product paths only (R-78). |
| Docstrings | No | `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90` | No violation | Both paths list product paths only (R-79, R-80). |
| Menu reference | No | `python scripts/generate_menu_wiki.py` | No changed file | No menu changes. |
| Symbols | Yes | `symbol-diff --base origin/main tests\guardrails\test_dependency_lock_file.py` | No module-level name lost | Added names are listed in the pull request body (R-67). |
| STE | Yes | `ste-linter --config .ste-linter.toml --min-score 80` with the 11 new Markdown files | Each file scores 80 or above | Ten record files and the fragment (R-65). |
| Ops portal | No | npm commands in `ops-portal\` | Each exits 0 | No portal change. |
| Ops platform | No | pytest in `mist-ops-platform\` | At least 390 tests | No platform change. |

## Implementation Outline

1. Write the two guard tests in `tests\guardrails\test_dependency_lock_file.py`. Run them. The first test fails.
2. Add the mando ignore rule to `.github\dependabot.yml`. Run the tests. Both pass.
3. Add the changelog fragment. Run the changelog guard.
4. Copy the ten record files to the route folder. Run the STE gate.
5. Confirm that the pins and the workflow are unchanged.
6. Run the local gates in the table above, except the test quality gate.
7. Commit. Run the test quality gate on the commit. Push the branch. Open the pull request.
8. Watch the remote CI run.
9. After the orchestrator authorizes the merge, enable auto-merge and squash merge.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| Dependabot does not honor the range | The ignore has no effect, or GitHub reports a configuration error | Guard test in T001. Check the Dependabot page after merge (U-1). |
| Radon later accepts mando 0.8 | The ignore hides a valid update | The config comment and the guard constant name the removal condition. |
| Black finds a real format issue after pip succeeds | The Black job still fails | The local Format gate runs before the push. |
| Pull request #4888 stays red | The fourteen sibling issues stay open | Owner action, recorded in analysis U-5. |
| The test module grows | More debt in one module | Recorded in Complexity Tracking. Remediation is a separate issue. |

## Rollback Steps

1. Revert the squash commit on `main`. The pip entry returns to its previous form without the ignore rule.
2. Confirm that the pip entry has no `ignore` list.
3. Keep pull request #4888 open. The owner decides its next step.

Caution: a revert does not reopen any closed issue. It also does not change the state of pull request #4888.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `tests\guardrails\test_dependency_lock_file.py` holds 11 top-level names after the change, above the limit of five. | The lock and dependency declaration guard lives in this module. | A new module adds a direct child to `tests\guardrails\`, which holds 79 children (R-31). |
| `changelog.d\` holds 335 direct children. | Each change adds one unique record. | Not applicable. The change adds one record and removes none. |

Remediation action, separate from this change: group the tests of `test_dependency_lock_file.py` into classes, and split the fragment folder. Owner: maintainer. The owner opens a tracking issue.

## Contracts

One contract applies: `design\contracts\dependabot-mando-ignore.md`. It defines the pip entry shape and the guard behavior.
