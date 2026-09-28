# Development tooling migration

MistHelper carried its own development tooling for a long time. That tooling
served the engineers who build MistHelper. A customer never runs it.

Issue #3404 moves the tooling into a separate repository and stops shipping it
inside the MistHelper wheel and the MistHelper container image.

The new repository is `jmorrison-juniper/misthelper-devtools`.

## What the tooling holds

| Tree | Holds |
| - | - |
| `tools/` | Phase 2 deleted this tree. The `misthelper-devtools` package now supplies the repository linters, the analyzers, the compliance checkers, and the symbol difference tool. |
| `scripts/` | The maintenance commands, the bootstrap helpers, and the report generators. |
| `tests/` | The MistHelper test suite. |
| `specs/` | The SpecKit records. |

## Phase 1: stop shipping the tooling

Phase 1 is complete. It changed what the build produces. It deleted no file
from this repository, so every local command still works.

| Change | File |
| - | - |
| The wheel no longer packages `tools/`. | `pyproject.toml` |
| The wheel no longer exposes the `test-quality-analyzer` and the `ste-linter` commands. | `pyproject.toml` |
| The container image no longer copies `scripts/`. | `Dockerfile` and `Containerfile` |
| The build context excludes `tools/` and `scripts/`. | `.dockerignore` |
| A guard keeps the tooling out of both artifacts. | `tests/guardrails/test_shipped_artifacts.py` |

Phase 1 also moved one file. `scripts/build_zen_city_metadata.py` held the
hand-curated Zscaler city map, and `src/utils/zscaler_catalogue.py` read that
map at run time. The map is product code, so it moved to
`src/utils/zen_city_metadata.py`. The maintenance command stays in `scripts/`
and it imports the new module. `src/utils/zscaler_probe.py` was promoted the
same way in an earlier change.

`pyproject.toml` still holds the optional dependency group named `ste-linter`.
That group installs helper libraries for local checks. It is not a console
script entry in the wheel.

Warning: a product module must never import from `scripts/` or from `tools/`.
The container no longer ships either tree, so such an import breaks the image
at start time. The guard test reports that class of defect.

Caution: `Containerfile` and `Dockerfile` must stay byte-identical. Podman reads
`Containerfile` first, so an edit to `Dockerfile` alone leaves the local build
on the old recipe. Edit `Containerfile`, then run
`Copy-Item Containerfile Dockerfile -Force`.
`tests/unit/container/test_build_files_match.py` enforces the rule.

## Phase 2: delete the local copy

Phase 2 is complete. The devtools repository defines an installable Hatch wheel
and MistHelper pins its exact public Git commit in `requirements-dev.txt`, so CI
does not need a package-index credential and a later devtools commit cannot
change a build unexpectedly.

The migration changed the development environment only. Product imports and
runtime commands remain in MistHelper; CI, pre-commit, and development scripts
use the installed devtools package.

1. Make `misthelper-devtools` installable from a pinned commit — complete.
2. Add `misthelper-devtools` to the MistHelper development requirements — complete.
3. Point CI workflow steps at the installed package instead of local tool paths — complete.
4. Point `.pre-commit-config.yaml` at the installed commands — complete.
5. Update the subprocess-timeout tests to use the installed tool package — complete.
6. Delete `tools/` from this repository after verifying its consumers — complete.
7. Move the Juniper skill factory source, scripts, and tests to
   `misthelper-devtools`. Repository searches found no product imports, and
   the development-tooling repository contains the factory — complete.
8. Move the `[tool.ste_linter]` settings out of `pyproject.toml` — complete;
   `.ste-linter.toml` retains the same table and the workflows name it explicitly.

Validation after the move: the focused integration and guard suite passes
(136 tests), Ruff passes for the changed Python files, the citation linter
checks 249 citations with no unresolved references, and a rebuilt wheel has no
`tools/` or `src/juniper_skills/` entries.

## Phase 3: call the shared workflows

The devtools repository also publishes reusable GitHub Actions workflows. They
started from the MistHelper workflows. Issue #3450 moved these MistHelper
workflows and jobs to the shared copies.

| MistHelper workflow | Shared workflow |
| - | - |
| `copilot-auto-assign.yml` | `reusable-copilot-assign.yml` |
| `copilot-label-checkbox.yml` | `reusable-copilot-assign.yml` |
| `close-linked-issues.yml` | `reusable-close-linked-issues.yml` |
| `container-build.yml`, job `build-and-push` | `reusable-container-image.yml` |
| `release.yml`, job `build-container` | `reusable-container-image.yml` |

The `radon` job in `ci.yml` also runs a devtools command. It pipes the report of
`radon cc -j` into `complexity-gate --max 10` instead of an inline script
(issue #3456).

Each caller pins the full commit of a devtools release and names the release in
a comment. Dependabot reads that comment and proposes a new pin after a devtools
release. It does not update the `requirements-dev.txt` pin, so change that pin
by hand to the same release.

The Copilot assignment needs the `COPILOT_ASSIGN_TOKEN` repository secret.
GitHub assigns the Copilot cloud agent only for a user token. Without the
secret, the shared workflow writes one comment on the issue that tells how to
set it up, and it adds no `in-progress` label.

Phase 3 kept two sets of jobs local: the jobs of `auto-merge.yml` and the
`create_failure_issues` and `close_resolved_issues` jobs of `ci.yml`. Phase 6
moved both sets to the shared workflows.

## Phase 4: keep the test quality baseline here

The `test-quality-analyzer` command reads the baseline file inside the installed
package when a run gives no `--baseline` option. MistHelper could not repair or
prune that copy, so issues #3421 and #3422 moved the record of accepted findings
into this repository.

| Change | File |
| - | - |
| The baseline started as a byte-identical copy of the devtools file at the pinned release. A `--write-baseline` run then removed 335 entries that matched no current finding. It added no entry. | `.github/test-quality-baseline.json` |
| Each analyzer run in the ratchet job gives `--baseline` with that file. A change to the file makes the job check the whole suite. | `.github/workflows/ci.yml` |
| Git ignores the report folder of the analyzer. | `.gitignore` |
| A guard runs the ratchet script with a fake `subprocess` module and asks git which report paths it ignores. | `tests/guardrails/test_quality_ratchet_files.py` |

`.pre-commit-config.yaml` runs no ratchet hook, so it did not change.
`documentation/quality-gates.md` tells how to prune or rewrite the baseline.

Of the 335 removed entries, 7 named two test files that moved to the devtools
repository. The other 328 named findings that later changes repaired. The gate
now reports a finding that comes back at one of those places.

Devtools release v0.4.0 removed the copy of `baseline.json` from the package.
Without the `--baseline` option, the command now reads
`.github/test-quality-baseline.json` in the current repository.

## Phase 5: keep the product benchmarks and the analyzer settings here

Four modules in the devtools package imported MistHelper product code, so they
could not run in the devtools repository. Issue #3466 moved them back to this
repository. It also gave MistHelper its own copy of the test quality analyzer
settings.

| Change | File |
| - | - |
| The memory harness of the performance package. `tests/test_performance_memory.py` imports it. | `scripts/benchmarks/performance_memory.py` |
| The overhead benchmark of the performance package. | `scripts/benchmarks/bench_performance_overhead.py` |
| The overhead benchmark of the end-to-end hooks. | `scripts/benchmarks/bench_e2e_hook_overhead.py` |
| The command that resets the end-to-end store. | `scripts/e2e_store_reset.py` |
| The analyzer settings started as a copy of the devtools `config.toml` at release v0.3.0. Only the header comment is different. | `.github/test-quality-config.toml` |
| Each analyzer run in the ratchet job gives `--config` with that file. A change to the file makes the job check the whole suite. | `.github/workflows/ci.yml` |
| The whole-repository analyzer command gives the same settings file. | `scripts/run_repository_analyzers.py` |
| The ratchet guard checks each `--config` option and the tables of the settings file. | `tests/guardrails/test_quality_ratchet_files.py` |

The container image does not copy `scripts/`, so the product never ships these
modules. Devtools release v0.4.0 removed its copy of the four modules.

## Phase 6: adopt devtools release v0.4.0

Issue #3487 moved MistHelper to devtools release v0.4.0. That release installs
the tools as one `misthelper_devtools` package, reads the test quality baseline
from the repository, and adds shared workflows for the jobs that Phase 3 kept
local.

| Change | File |
| - | - |
| The development requirements pin the v0.4.0 commit. Each workflow caller pins the same commit. | `requirements-dev.txt` and `.github/workflows/` |
| Each import and each `python -m` command names `misthelper_devtools` instead of `tools`. The citation and SpecKit jobs run the `check-citations` and `speckit-task-audit` commands. | `.github/workflows/ci.yml`, `scripts/`, and `tests/` |
| The auto-merge workflow calls `reusable-auto-merge.yml` with the orphaned-push report. Its close job calls `reusable-close-linked-issues.yml` every six hours, so a missed close event waits six hours at most. | `.github/workflows/auto-merge.yml` |
| One `quality_gate_issues` job calls `reusable-quality-gate-issues.yml`. Its `needs` list is the list of gates that get an issue. `ci.yml` sets `scope: all`. The portable template kept the default scope until Phase 7 deleted it. | `.github/workflows/ci.yml` and `.github/quality-gates-portable.yml` |
| The weekly report calls `reusable-stranded-branch-report.yml`. The `stranded-branch-report` command replaces the local script and its test. | `.github/workflows/stranded-branch-report.yml` |
| The writing guide check calls `reusable-ste-lint.yml` with the same guide, settings file, and score. | `.github/workflows/ste-lint.yml` |
| The tests of the tools moved to the devtools repository, so MistHelper deleted its copies. The golden analyzer test stays, and it reads the settings file of this repository. | `tests/tools/` and `tests/unit/` |
| A new test grades the writing guide of this repository. | `tests/unit/test_ste_writing_guide.py` |
| The guardrail tests check each caller, its pinned commit, its inputs, and its permissions. | `tests/guardrails/test_auto_merge_issue_close.py`, `tests/guardrails/test_quality_gate_close_scope.py`, and `tests/guardrails/test_codeql_register_gate.py` |
| The baseline drops the entries of the deleted test files. The performance catalog drops the rows of the deleted files. | `.github/test-quality-baseline.json` and `specs/2448-misthelper-performance-monitoring/artifacts/` |

The shared auto-merge job does not merge a pull request that edits a file in
`.github/workflows/`, because GitHub refuses to let the workflow token write a
workflow file. The job writes a comment on the pull request instead. Merge such
a pull request by hand after its checks pass.

## Phase 7: adopt devtools release v0.5.2

Issue #3515 moved MistHelper to devtools release v0.5.2. Release v0.5.0
supplies the CodeQL job, the Mermaid parser, and the local check scripts that
Phase 6 kept, so MistHelper deleted its copies. Release v0.5.1 repairs the
shared link check for a link that starts with `/`. Release v0.5.2 repairs the
dispatch job of the shared auto-merge workflow.

| Change | File |
| - | - |
| The development requirements pin the v0.5.2 commit. Each workflow caller and the Mermaid action pin the same commit. | `requirements-dev.txt` and `.github/workflows/` |
| The CodeQL workflow calls `reusable-codeql.yml`. The file name did not change, so each code scanning alert keeps its key. | `.github/workflows/codeql.yml` |
| The register job runs `codeql-verdict-register check`. The Bandit job runs `bandit-exclude-check` with two product source samples. The drift job runs `exclusion-drift`. | `.github/workflows/ci.yml` |
| The diagram job runs `diagram-refs`. An allowlist file holds the MistHelper module names that the diagrams use. | `.github/workflows/ci.yml` and `.github/diagram-refs-allowlist.txt` |
| The Mermaid job calls the `mermaid-lint` action. The action installs its own parser. | `.github/workflows/ci.yml` and `scripts/mermaid/` |
| The test quality ratchet gives `--changed-from` and `--full-gate-path` in place of an inline script. | `.github/workflows/ci.yml` |
| The `pytest-chunks` command replaces the local shard script. The `worktree-cleanup merged` and `worktree-cleanup stale-admin` commands replace the two cleanup scripts. | `scripts/` and `.github/copilot-instructions.md` |
| The Markdown link guard uses the `MarkdownLinkChecker` class of the devtools package. The guard and the new pre-commit hook skip `documentation/wiki/`. | `tests/guardrails/test_markdown_links.py` |
| The pre-commit file runs the `ste-linter` and `markdown-link-check` hooks of the devtools repository. Each other hook release matches the version that `requirements-dev.txt` pins. | `.pre-commit-config.yaml` |
| The portable template of the gate jobs is deleted. A new repository calls `reusable-python-quality-gates.yml` instead. | `.github/quality-gates-portable.yml` |
| The tests of the deleted scripts moved to the devtools repository. The guard tests check each new command, pin, and input. | `tests/` |
| The baseline drops the entries of the deleted test files. The performance catalog drops the rows of the deleted files. | `.github/test-quality-baseline.json` and `specs/2448-misthelper-performance-monitoring/artifacts/` |

A wiki page links to a bare page name, such as `Menu-API-Endpoints`. Only the
published wiki resolves that name, so each link check skips the wiki tree.

Some generated API pages and specs link to the upstream API reference with a
link that starts with `/`, such as `/#operations/listInsightMetrics`. GitHub
starts that link at the repository root, and so does the shared link check.
Release v0.5.0 reported each of the 17 links as a missing file, so this phase
waited for release v0.5.1.

After a merge, the dispatch job of the shared auto-merge workflow starts each
main workflow that shows no run on the tip of `main`. Release v0.5.1 read the
newest run from the run list of GitHub, and that list can answer from old data.
The job then started a second run of `ci.yml`, `codeql.yml`, or
`container-build.yml` on a tip that a run already covered. Release v0.5.2 looks
for a run on the tip commit itself, so this phase moved to release v0.5.2
before the merge.
