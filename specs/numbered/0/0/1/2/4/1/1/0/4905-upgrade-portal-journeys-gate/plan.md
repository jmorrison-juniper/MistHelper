# Implementation Plan: Upgrade Portal Journeys Gate on PR 4888

**Branch**: `fix/4905-upgrade-portal-journeys-gate` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record `specs/numbered/0/0/1/2/4/1/1/0/4905-upgrade-portal-journeys-gate/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the record root. Research, data model, quickstart, contracts, and checklists stay under `design/`. The contract folder holds one file, and the checklist folder holds three files.

## Summary

The journeys gate failed because pip could not resolve `requirements-dev.txt`. PR 4888 raised mando to 0.8.2. Radon 6.0.1 requires mando below 0.8. The change blocks mando 0.8 and later in the pip update stream, extends the policy guard to protect that block, and adds one changelog fragment. Mando stays at 0.7.1. After the merge and the orchestrator authorization, PR 4888 closes.

## Technical Context

**Language/Version**: Python for the guard test. YAML for the Dependabot configuration.

**Primary Dependencies**: pytest for the guard test. `packaging` for the version specifier in the new behavior test. The package is pinned in `requirements-dev.txt` (R-89). Dependabot reads `.github/dependabot.yml`.

**Storage**: Repository files only. No database and no data file.

**Testing**: Guard tests in `tests/guardrails/`. Local gates from the local gates table of `.github/copilot-instructions.md`, with rows R-43 to R-47, R-77, R-78, R-80, R-81, and R-84. The CI gate runs in GitHub Actions (R-62). Local runs use Windows 11.

**Target Platform**: Windows 11 for local work. GitHub Actions for remote CI.

**Project Type**: Configuration change, guard test change, and changelog fragment in an existing repository, plus one record.

**Performance Goals**: Not applicable. The change touches no runtime path.

**Constraints**: The policy snapshot must equal the file after the change (R-15). The export guard must keep the requirement files equal to the lock output (R-31, R-32). Each file change must keep the directory child counts within the five-child rule.

**Scale/Scope**: Three repository files changed or added. One record folder added with 11 Markdown files. One external pull request closed. Fifteen gate issues closed by the same closure step.

## Constitution Check

*Gate: passes before research and after design. The table records each rule that applies to this change.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, record directories | Pass | The record root holds five children (spec, plan, tasks, analysis, design). `design/` holds five children. `design/contracts/` holds one file. `design/checklists/` holds three files. The route leaf holds one record. |
| I. Five-item rule, changelog folder | Pass with recorded debt | `changelog.d/` already holds more children than five (local listing, R-35 and R-36 cover the fragment rules). The constitution allows one unique process record in an established process folder. The fragment is that record. See Complexity Tracking. |
| I. Function limits | Pass | The new test method takes two parameters, `self` and `policy`. It has fewer than five logical blocks and fewer than 25 lines. |
| II. Class-based architecture | Pass | The new method belongs to the existing class `TestDependabotPolicy` (R-14). The change adds no wrapper function. |
| III. Safety first | Pass | The change reads no secret and writes no secret. The test reads only `.github/dependabot.yml`. |
| IV. Full deployment pipeline | Pass with planned steps | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in that order. The merge waits for remote CI and orchestrator authorization. |
| V. Observability | Pass | The rationale comment and the test messages use ASCII characters only. |
| VI. Inline comments | Pass with planned steps | Each new executable line in the test carries an inline comment, as the file does at its other lines. T-LOCAL-GATES checks the review of this rule. |
| VII. Action logging | Pass with planned steps | The new test writes one `info` line before its check and one `debug` line after it. The existing fixture uses the same pattern. |
| Mist Cloud transport | Not applicable | The change makes no Mist REST or WebSocket call. |
| Package manager | Pass | No requirement file changes. `requirements.txt` and `requirements-dev.txt` stay as they are (FR-003). |
| File paths | Pass | The test builds paths with `Path`, as the file does at its existing fixture. |
| Container runtime and test containers | Not applicable | No container starts. |
| Data directory and output backends | Not applicable | The change writes no product output. |
| Database keys | Not applicable | The change adds no data entity. |
| Security findings | Pass | The change adds no suppression comment. Bandit runs on the changed test file (R-82). |
| Documentation and release notes | Pass | The change adds one fragment under `changelog.d/` (R-38). The fragment names the issue and states the change. |
| Testing | Pass | The change adds three test cases and updates one snapshot (TST-001 to TST-004). |
| Spec Kit record route | Pass | The route follows the base-5 rule (R-51, R-52). The record uses the managed root `specs/numbered/` (R-53). |
| AGENTS: Issue first and branch name | Pass with planned steps | Issue 4905 exists (R-71). T-PR applies the `in-progress` label before it creates the branch `fix/4905-upgrade-portal-journeys-gate`. |
| AGENTS: One pull request holds one change | Pass | The record and the fix form one concern (D-6). |
| AGENTS: STE writing style | Pass with planned steps | The STE gate reads each Markdown file of the record and the fragment (R-50). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/1/0/4905-upgrade-portal-journeys-gate/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      dependabot-pip-ignore.md
    checklists/
      requirements.md
      ci-gate.md
      dependency-pin.md
```

### Source changes (repository root)

```text
.github/dependabot.yml                                   (modify)
tests/guardrails/test_pr_title_workflow.py               (modify)
changelog.d/issue-4905-upgrade-portal-journeys-gate.md   (add)
```

## Architecture

Three parts govern the pip update stream. The policy file `.github/dependabot.yml` tells the Dependabot service which releases to propose. The guard test `tests/guardrails/test_pr_title_workflow.py` reads the same file and compares it with the policy snapshot. The journeys gate in `.github/workflows/ci.yml` consumes the pins of `requirements-dev.txt`, which the lock export produces (R-03, R-20, R-24). This change edits the first two parts and reads the third. It leaves the requirement files and the lock as they are.

## File-by-File Change Map

| Path | Action | Change | Requirement |
| - | - | - | - |
| `.github/dependabot.yml` | Modify | Add an `ignore` list to the pip update stream (`updates[0]`). The list holds one entry for `mando` with `versions: [">=0.8"]`. The entry carries the rationale comment in `design/contracts/dependabot-pip-ignore.md`. | FR-004 |
| `tests/guardrails/test_pr_title_workflow.py` | Modify | Add the same entry to `POLICY_SNAPSHOTS["dependabot"]["updates"][0]`. Add two cases to the parameter list of `test_unrelated_changes_fail`. Add one method, `test_mando_ignore_blocks_the_failed_release`, to `TestDependabotPolicy`. Add one import, `SpecifierSet` from `packaging.specifiers`. | FR-004, FR-006 |
| `changelog.d/issue-4905-upgrade-portal-journeys-gate.md` | Add | One `###` heading and one `Changed` bullet that names issue 4905. | FR-007 |
| `specs/numbered/0/0/1/2/4/1/1/0/4905-upgrade-portal-journeys-gate/` | Add | This record. | FR-008 |
| `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `uv.lock` | No change | The pins stay at mando 0.7.1 and radon 6.0.1 (R-01, R-02, R-07, R-08). | FR-003 |
| `.github/workflows/ci.yml` | No change | The journeys gate stays unchanged (R-19 to R-23). | FR-001 |
| Pull request 4888 | Close after the merge, with authorization | Not a file. The closing comment names the surviving branch and its commit. | FR-010 |
| Gate issues 4891 to 4904 | Close with the same closure step | Not a file. Issue 4905 closes when the fix pull request merges. | FR-011 |

## Planned Test Method

The new method follows the style of the existing fixture. Each line carries an inline comment.

```python
    def test_mando_ignore_blocks_the_failed_release(self, policy: dict[str, Any]) -> None:
        """Prove that the pip ignore rule blocks mando 0.8.2 and keeps the current pin."""
        logging.info("action=%s phase=%s", "check_mando_ignore", "before")  # Trace before the policy read.
        pip_stream = policy["updates"][0]  # Select the pip update stream.
        rules = [rule for rule in pip_stream["ignore"] if rule["dependency-name"] == "mando"]  # Find the mando entry.
        assert len(rules) == 1, "The pip update stream must hold one mando ignore entry."  # Reject a missing or duplicate entry.
        allowed = SpecifierSet(rules[0]["versions"][0])  # Read the rejected range as a version specifier.
        assert "0.8.2" in allowed, "The ignore range must block mando 0.8.2."  # Block the release that failed the gate.
        assert "0.7.1" not in allowed, "The ignore range must keep the current mando pin."  # Keep the pin that radon accepts.
        logging.debug("action=%s phase=%s checked=%s", "check_mando_ignore", "after", 3)  # Report the checked rules.
```

## Dependencies

- No new package. The behavior test imports `packaging.specifiers`. The package is pinned in `requirements-dev.txt` (R-89).
- The Dependabot service reads `.github/dependabot.yml` on each scheduled run.
- The CI gate reads `tests/guardrails/test_pr_title_workflow.py` through the pytest shards of `ci.yml`.

## Risks and Mitigations

| ID | Risk | Level | Mitigation |
| - | - | - | - |
| RK-1 | Dependabot rejects the range form for pip. | Medium | Check the first pip update run after the merge (U-1). If the service rejects the range, a follow-up change corrects the entry, and the policy snapshot changes with it. |
| RK-2 | A future radon release accepts mando 0.8. The entry then blocks a valid release. | Low | The comment names the removal condition. Check the newest radon release on PyPI with quickstart section 8 when radon changes. |
| RK-3 | PR 4888 stays red until it closes. | High | The red state is expected. Closure needs the orchestrator authorization (U-2). |
| RK-4 | Closing PR 4888 conflicts with the literal text of R-42. | Medium | The record reads R-42 inside its section (D-4). The branch survives. `gh pr reopen 4888` reverses the closure. |
| RK-5 | Mando stays on the 0.7 line. | Low | Mando is a dev-only transitive pin (R-06, R-09). Unverified item U-5 covers the 0.8.2 release notes. |
| RK-6 | A gate that research did not run fails on the fix pull request. | Medium | T-LOCAL-GATES runs the applicable gates before the commit. T-REMOTE-CI reads the CI result after the push. |
| RK-7 | A later change moves a pin in `requirements-dev.txt` without a lock change. | Medium | The export guard fails (R-31, R-32). The dependency lock job runs the guard in CI (R-27). |
| RK-8 | The policy snapshot drifts from the file. | Low | TST-001 compares the whole file with the snapshot (R-15). |

## Rollback Steps

1. Revert the fix pull request with a squash revert on a new branch. The revert restores the earlier `.github/dependabot.yml` and policy snapshot, and it removes the fragment.
2. If PR 4888 closed, run `gh pr reopen 4888 -R jmorrison-juniper/MistHelper`. The branch `dependabot/pip/mando-0.8.2` stays at `e86098cdc2b189d217805b3b4060ef609cbc37af`.
3. Warning: deleting the branch `dependabot/pip/mando-0.8.2` removes the only branch reference to the bump commit. Do not delete it.

## Complexity Tracking

| Violation or debt | Why it stays | Simpler option rejected because |
| - | - | - |
| `changelog.d/` holds more children than five. Existing debt. | The folder predates this change. The constitution allows one unique process record in an established process folder. The fragment is that record. | A fragment in another folder bypasses the release aggregation that `changelog.d/README.md` describes. |
| The class `TestDependabotPolicy` holds five methods after the change. | Five methods stay within the five-child limit. | A second class for one check adds a structure with no new subject. |
| Remediation action for the `changelog.d/` debt, tracked separately by the orchestrator. | The release coordinator aggregates merged fragments into `CHANGELOG.md`, as `changelog.d/README.md` describes. Each aggregation removes fragments from the folder. | Deleting fragments by hand loses released records, as the fragment README warns. |
