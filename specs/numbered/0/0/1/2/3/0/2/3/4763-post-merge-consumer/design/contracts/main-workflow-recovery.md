# Contract: Main workflow recovery

This contract describes the shared recovery workflow as the consumer calls it. The values are read from the pinned commit `d63a120487cecf750184cb178387cdc25c0a7635`.

## Call from the consumer workflow

The consumer calls the shared workflow at the pinned commit (RC-01). It sets two inputs (RC-02).

| Input | Consumer value | Shared default | Meaning |
| - | - | - | - |
| main-workflows | `ci.yml codeql.yml container-build.yml ste-lint.yml` | empty | Main workflows that a merge starts |
| report-orphaned-push | `true` | `false` | Enables the orphan report |

The shared inputs also include `label` (default `auto-merge`), `merge-method` (default `squash`), and `default-branch` (default `main`). The input block sits at lines 48 to 75 (RC-23).

## Events and jobs

| Event | Enable job | Dispatch job |
| - | - | - |
| pull_request with action labeled, synchronize, opened, or reopened, and the label present | Runs (RC-26) | Runs only after a confirmed merge into the default branch (RC-28) |
| pull_request closed with merged true | Skipped (RC-26) | Runs (RC-29) |
| pull_request closed without merge | Skipped (RC-26) | Skipped (RC-29) |
| schedule | Skipped (RC-26) | Runs (RC-28, RC-65) |
| workflow_dispatch | Skipped (RC-26) | Runs (RC-28) |

A dispatch job for a non-closed event also needs a successful enable job (RC-28). A canceled run skips the dispatch job (RC-30).

## Outputs

- `enable-auto-merge` sets the output `merged` to `true` after a confirmed merge (RC-25, line 234).
- The output stays empty after a pending request (RC-26).

## Start rules

- The job reads the tip once at line 311 (RC-31).
- A lookup failure stops the job before any start (RC-31, lines 311 to 314).
- The job checks coverage five times, 20 seconds apart (RC-32).
- A run on the tip counts as coverage. A queued run counts too (RC-34, lines 335 and 336).
- A missed workflow starts with `gh workflow run <file> --ref main` (RC-34, line 365).
- A failed start exits 1 after the merge (RC-34, lines 385 to 389).

## Log lines

| Line | Source |
| - | - |
| `GitHub accepted the merge request.` | RC-25, line 194 |
| `Verified pull request N: merged.` | RC-25, line 235 |
| `Verified pull request N: enabled.` | RC-26, line 239 |
| `<file> already covers the tip.` | RC-34, line 339 |
| `<file> showed no run on the tip in 5 checks, so the workflow missed the tip.` | RC-34, line 363 |
| `Started <file> on main.` | RC-34, line 366 |
| `Each main workflow now covers the tip of main.` | RC-34, line 390 |

## Compatibility

A main workflow changes in two places at once. The consumer list and the guard test must change together (RC-02, RC-09). A pin change must also change the guard constant (RC-08, RC-71).
