# Implementation Plan: Radon Job Mando Pin Conflict

## Summary

The radon job failed at its install step on PR #4888. Dependabot raised mando to 0.8.2, and radon 6.0.1 rejects that release. This change keeps mando at 0.7.1. It adds an ignore rule for mando 0.8.0 and later. It adds four guard tests to an existing guard file and one changelog fragment. It edits no lock or requirements file.

## Technical Context

- **Language**: Python 3.15 or newer (R-50).
- **Pinned packages that the guard uses**: packaging 26.3 (R-48) and PyYAML 6.0.4 (R-49).
- **Lock state**: `uv.lock` holds mando 0.7.1 and radon 6.0.1 (R-16, R-17).
- **CI**: GitHub Actions. The radon job runs the install step (R-02) and then the complexity command (R-03).
- **Testing**: pytest on `tests/guardrails/test_dependency_lock_file.py`.
- **Storage**: None. The change edits one YAML file, one test module, and adds one Markdown fragment.
- **Fixed constraint**: The complexity rule and its command stay unchanged (FR-009).

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule (Structural Discipline) | Pass | The change adds no direct child to `tests/guardrails`, which holds 79 children (R-23, grandfathered). The fragment is one unique record in `changelog.d/`, which holds 335 children (R-55). Principle I allows that record. |
| II. Class-Based Architecture (No Wrappers) | Pass | The new logic sits in two classes, `RadonMandoRule` and `DependabotMandoRule`. The test functions follow the existing module pattern. No wrapper function exists. |
| III. Safety-First (NON-NEGOTIABLE) | Pass | The change adds no keyboard input, no destructive operation, and no secret. |
| IV. Full Deployment Pipeline (NON-NEGOTIABLE) | Pass with a stated limit | T-LOCAL-GATES runs each applicable local gate. The two `pytest-chunks` runs stay in CI because they take a long time. T-REMOTE-CI verifies them. |
| V. Observability & Logging | Pass | Each new file read logs an info line before the read and a debug line after it. |
| VI. Inline Comments (NON-NEGOTIABLE) | Pass | Each new Python line carries an inline comment. The YAML rule carries block comments that give the reason, as the existing npm rule does (R-19). |
| VII. Action Logging (NON-NEGOTIABLE) | Pass | The new file reads follow the same before and after logging pattern. |
| Technology and Compatibility | Pass | The guard uses only pinned packages (R-48, R-49). No runtime requirement changes (FR-010, R-15). |
| Documentation | Pass | README.md and the operation tables stay unchanged, because no operation or operator behavior changes. The radon row in `documentation/quality-gates.md` stays correct (R-40). The reason for the ignore rule lives in the YAML comment, one location only. |
| Release Notes | Pass with D-6 | The change adds one fragment. The constitution overrides the internal-only exemption of the changelog README (R-29, R-34). |
| SpecKit Escalation | Pass | The change touches three files, so escalation applies (R-30). This record is the specification. |
| Multi-Agent Git Workflow | Pass | The branch name follows the constitution pattern (R-31). Required labels apply (R-32). The PR body holds `Closes #4898` (R-36). The auto-merge label waits for green checks (R-33). |

## Architecture

The Quality Gates workflow in `.github/workflows/ci.yml` runs the radon job. The install step runs `pip install -r requirements-dev.txt` (R-02). The install step stops when two pins conflict (R-06, R-07). Dependabot reads `.github/dependabot.yml` before it opens a pull request. The ignore rule in that file blocks mando 0.8.0 and later (FR-001). The guard file reads the pins and the ignore rule on each test run.

## File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `.github/dependabot.yml` | Modify | Insert an `ignore` block in the pip update entry, after line 11. The block names `mando` and the range `>=0.8.0`. |
| `tests/guardrails/test_dependency_lock_file.py` | Modify | Add two module constants, two helper classes, and four test functions. Add one sentence to the module docstring about the radon pin and the ignore rule. |
| `changelog.d/issue-4898-radon-mando-conflict.md` | Add | One `###` heading and one `**Fixed**` bullet that names issue 4898. |
| `specs/numbered/0/0/1/2/4/0/4/3/4898-radon-mando-conflict/` | Add | This record, copied from the draft folder. |
| GitHub issue #4898 | Label | Add `in-progress` before the branch exists (T003). |
| GitHub PR #4888 | Close | Close without a merge after the fix PR merges (T-MERGE). |

Unchanged files: `requirements-dev.txt` (R-09, R-10), `requirements.txt` (R-15), `pyproject.toml` (R-14), `uv.lock` (R-16, R-17), `.github/workflows/ci.yml` (R-01 to R-03), `documentation/quality-gates.md` (R-40), and `README.md`.

## Guard Test Contract

The module uses these new names. The implementer keeps the names unless a test fails for another reason.

- `RADON_PINNED_VERSION`: `Version("6.0.1")`. The radon version whose metadata the rule describes.
- `RADON_MANDO_RANGE`: `SpecifierSet("<0.8,>=0.6")`. The mando range from radon 6.0.1 metadata (R-51, R-52).
- `RadonMandoRule.read_pins(path)`: Returns the exact pins of one requirements file. Logs an info line before the read and a debug line after it.
- `RadonMandoRule.defects(pins)`: Returns one message for radon not at 6.0.1, and one message for mando outside `RADON_MANDO_RANGE`.
- `DependabotMandoRule.blocks(path, version)`: Returns true when a pip ignore rule for `mando` covers the version. Parses the file with PyYAML. Logs before and after the read.
- `test_pinned_mando_satisfies_the_radon_requirement()`: Reads `requirements-dev.txt` and asserts that `defects` returns an empty list (FR-002).
- `test_radon_rule_reports_a_mando_release_that_radon_rejects()`: Passes radon 6.0.1 and mando 0.8.2 and asserts one message that names `<0.8,>=0.6` (FR-002).
- `test_dependabot_ignores_the_mando_release_that_radon_rejects()`: Asserts that `blocks` returns true for 0.8.2 and false for 0.7.2 (FR-001, FR-003).
- `test_dependabot_without_the_mando_rule_allows_the_rejected_release(tmp_path)`: Writes a pip entry with no ignore rule and asserts that `blocks` returns false for 0.8.2 (FR-003).

The module docstring gets one new sentence. It names the radon pin and the Dependabot rule as the second subject of the module.

## Ignore Rule Text

The rule goes in the pip entry of `.github/dependabot.yml`. The comment style matches the npm entry (R-19).

```yaml
    ignore:
      # radon 6.0.1 requires mando below 0.8. Pull request #4888 raised mando to 0.8.2,
      # and pip stopped on a resolution conflict in the radon job (issue #4898).
      # Keep this rule until a radon release accepts mando 0.8.
      - dependency-name: "mando"
        versions: [">=0.8.0"]
```

## Dependencies

No package is added. The guard reuses packaging (R-48) and PyYAML (R-49), which `requirements-dev.txt` already pins.

## Contracts

Omitted. This change exposes no interface contract. The ignore rule follows the Dependabot configuration schema (R-53, R-54).

## Data Model

Not applicable. See `design/data-model.md`.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| Dependabot reads the range in a different way | A rejected mando release still opens | The github/docs source and the dependabot-core parser document the `versions` key (R-53, R-54). SC-004 checks the next weekly run. |
| radon releases a version that accepts mando 0.8 | The ignore rule blocks a valid update | The radon pin test fails. A maintainer updates the constants and removes the rule. |
| Closing PR #4888 removes the mando bump | The bump record is lost | The close note cites the main pin (R-09, R-16). The close is reversible. |
| The guard test runs after the install step | A conflict stops the test before it runs | T-LOCAL-GATES runs the test locally. The ignore rule stops the proposal before a pull request exists. |
| A security advisory affects mando below 0.8 only | Dependabot may not propose the fix | A maintainer reviews the advisory by hand (spec edge cases). |
| A YAML typo in the ignore rule | Dependabot ignores the file | The guard test parses the YAML with PyYAML (T006). |

Warning: a force-push to `dependabot/pip/mando-0.8.2` destroys the commits of PR #4888. Do not push to that branch.

## Rollback Steps

1. Revert the squash commit of the fix PR on main. The revert restores the previous Dependabot behavior and the previous guard file.
2. If PR #4888 must return, reopen it. Its head commit `e86098cdc2b189d217805b3b4060ef609cbc37af` stays on GitHub.
3. Run `python -m pytest tests/guardrails/test_dependency_lock_file.py` on the reverted tree. The command confirms the restored state.

Caution: a revert reopens the path for mando 0.8 proposals. Keep the ignore rule until radon accepts mando 0.8.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `tests/guardrails` holds 79 direct children (existing, R-23) | The guard file already lives in that folder. The change adds no child. | A new file in the folder adds a direct child to a noncompliant parent. |
| `changelog.d` holds 335 direct children (existing, R-55) | The constitution requires one unique fragment for each change (R-29). | Skipping the fragment breaks the constitution MUST rule (R-29). |

Remediation action, tracked separately: file a new issue that records the folder debt in `tests/guardrails` and `changelog.d`. The orchestrator files it.
