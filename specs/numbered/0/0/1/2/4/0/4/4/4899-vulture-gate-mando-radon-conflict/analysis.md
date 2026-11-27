# Analysis: Vulture Gate Mando Radon Conflict

## Consistency Review

| Check | Finding | Action |
| - | - | - |
| Issue title against the log | The title names vulture as the failing rule. The log shows that the pip install step failed, and the vulture scan never ran (`design/research.md`, Reproduction). | Name the true step in `spec.md`, `design/research.md`, and the pull request body. Do not edit the issue. |
| Spec against plan | Each FR maps to a task and a test (`tasks.md`, Requirement Coverage). | None. |
| Plan against the constitution | Principles I, IV, and VI pass with noted exceptions (`plan.md`, Constitution Check). | Record existing debt in the Complexity Tracking table. |
| Fragment rule | The changelog README allows no fragment for an internal-only change (RC-25). The constitution requires one fragment for each change (RC-26). | Add the fragment. The constitution governs (RC-27). Raise the README conflict in a separate issue. |
| Test location | A new guard file adds a direct child to `tests/guardrails`, which holds 79 children (RC-37). | Extend the existing class `TestDependabotPolicy` (decision D-3). |
| Snapshot coupling | Adding the rule to `dependabot.yml` fails `test_complete_policy` unless the snapshot changes (RC-16, RC-18). | T001 and T002 change in the same commit. |
| Dependabot syntax | The documented range pattern supports the rule (RC-45). Runtime acceptance is not yet observed (U-1). | TEST-001 to TEST-003, and SC-004 after the merge. |
| Pins and lock | `uv.lock` pins `mando` 0.7.1 and lists it under `radon` (RC-11, RC-12). The pull request edit changed `requirements-dev.txt` only. | Keep the pins. Do not regenerate the lock. |
| Local environment | The local `.venv` holds `radon` 6.0.1 and `mando` 0.7.1 (RC-44). Main pins match (RC-01, RC-02). | None. |
| Commit prefix | Pip updates use the `chore` prefix (RC-32). The rule keeps that prefix. | None. |
| Container build | `container-build.yml` runs on listed product paths only (RC-36). No listed path changes. | Mark plan steps 10 to 12 not applicable. |
| Guide sentence | The complexity guard reads the sentence "No block above cyclomatic complexity 10" (RC-22). | Keep the sentence unchanged (T004). |
| Local tooling note | The local file `documentation/development-tooling-migration.md`, around line 99, says Dependabot does not update the devtools pin in `requirements-dev.txt`. Pull request #4888 shows Dependabot did update the `mando` pin. | Not a conflict. That note covers the devtools commit pin only. No change. |

## Defects in Existing Work

- Defect A: The issue title names vulture as the failing rule. The failing step is the pip install step. The title misstates the cause. This change does not edit the issue.
- Defect B: Pull request #4888 changes `requirements-dev.txt` without a matching change to `uv.lock` (RC-11, RC-12). The lock and the generated file disagree for that edit. Closing the pull request (T-MERGE) is the repair. A rebase keeps the same conflict.
- Observation C: The `quality_gate_issues` job titles each issue with a job ID. The title does not name the failing step. This record names the step.

## Unresolved Items

The unresolved items are U-1 to U-9 in `design/research.md`, section Unverified. U-1 and U-9 need a check after the merge. U-2 to U-5 need a check on the fix pull request. U-6 needs a check at each Dependabot run.

## Sibling Issues

The same run opened these quality-gate issues for pull request #4888. Each issue maps to a job that shows the same resolver line, except issue 4894.

| Issue | Job ID | Evidence in run 45064243269 |
| - | - | - |
| 4891 | ruff | `Ruff (lint)` shows the resolver line |
| 4892 | black | `Black (format check)` shows the resolver line |
| 4893 | mypy | `mypy (strict)` shows the resolver line |
| 4894 | pytest | `pytest (coverage gate)` fails after the dependency lock job. The four coverage shards show the resolver line. |
| 4895 | bandit | `Bandit (security)` shows the resolver line |
| 4896 | pip_audit | `pip-audit (CVE scan)` shows the resolver line |
| 4897 | pylint | `Pylint (score gate)` shows the resolver line |
| 4898 | radon | `Radon (complexity)` shows the resolver line |
| 4900 | pydocstyle | `pydocstyle (docstring style)` shows the resolver line |
| 4901 | interrogate | `Interrogate (docstring coverage)` shows the resolver line |
| 4902 | test_quality_gate | `Test quality ratchet (gate)` shows the resolver line |
| 4903 | dependency_lock | `Dependency lock and exports` shows the resolver line |
| 4904 | codeql_register_check | `CodeQL verdict register check` shows the resolver line |
| 4905 | upgrade_portal_journeys | `Upgrade portal journeys` shows the resolver line |

Close each sibling issue only after its gate passes on `main`. Issues 4906, 4907, and 4908 belong to other pull requests and are out of scope (U-8).
