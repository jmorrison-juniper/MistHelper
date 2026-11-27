# Workflow contracts: Merge queue rollout and acceptance

This contract lists the trigger and concurrency shapes that the guard tests pin. A change to one of these shapes needs a test change and an owner review.

## Events

| Workflow | Event | Shape on `main` | Source |
| - | - | - | - |
| `.github/workflows/ci.yml` | `merge_group` | `types: [checks_requested]` | R-01 |
| `.github/workflows/ci.yml` | `pull_request` | No branch filter and no paths filter | R-05 |
| `.github/workflows/ci.yml` | `push` | `branches: [main]` | R-04 |
| `.github/workflows/codeql.yml` | `merge_group` | `types: [checks_requested]` | R-10 |
| `.github/workflows/codeql.yml` | `push` | `branches: [main]` | R-13 |
| `.github/workflows/ste-lint.yml` | `merge_group` | Absent by design (D-3) | R-14 |

## Concurrency

| Workflow | Group expression | Cancel expression | Result for each event |
| - | - | - | - |
| `ci.yml` | `quality-gates-${{ github.event.pull_request.number || github.ref }}` (R-02) | `${{ github.event_name == 'pull_request' }}` (R-03) | A pull request run cancels an older pull request run. A `merge_group` run has its own group, because its `github.ref` is unique. A `push` run on `main` is never canceled. |
| `codeql.yml` | `codeql-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}` (R-11) | `${{ github.event_name == 'pull_request' }}` (R-12) | The same result as `ci.yml`. |

## Required contexts

| Source | Names | Rows |
| - | - | - |
| `ci.yml` job names | `Ruff (lint)`, `Black (format check)`, `mypy (strict)`, `pytest (coverage gate)`, `Bandit (security)`, `pip-audit (CVE scan)`, `Pylint (score gate)`, `Radon (complexity)`, `Vulture (dead code)`, `pydocstyle (docstring style)`, `Interrogate (docstring coverage)`, `Diagram reference lint`, `E2E smoke tests`, `pytest (ops platform)` | R-09 and R-31 |
| Application context | `CodeQL` | R-52 (checked live only, U-3) |

The protection list holds 15 contexts in total (R-52). The 14 CI names and the `CodeQL` context make up the list.

## Checkout

Each `actions/checkout` step in `ci.yml` uses the default ref, which is the event commit. The explicit quality checkout uses `${{ github.event.pull_request.head.sha || github.sha }}` (R-06). The shared CodeQL checkout uses the default ref (R-21).

## Documentation contract

The procedure heading `## Merge queue preparation and activation` in `documentation/quality-gates.md` is the anchor that `.github/copilot-instructions.md` line 499 links to (R-23, R-29). The heading text does not change.

The workflow table rows for `ci.yml` and `codeql.yml` in `.github/copilot-instructions.md` name merge queue candidates after T004 (R-27, R-28).

## Contract decisions

- A missing `merge_group` trigger fails `test_merge_group_contract` (R-30).
- A renamed required job fails `test_required_check_names` (R-31).
- A cancel expression that can cancel a queue run fails `test_merge_group_contract` through the `cancel` mutation (R-30).
- A shared concurrency group fails `test_merge_group_contract` through the `group` mutation (R-30).
- A workflow table row without merge queue text fails the new method in T003.

## Activation

No contract changes a repository setting. A passing contract does not prove that the owner-enabled queue accepted a candidate. The owner evidence in `quickstart.md` section 4 proves that.
