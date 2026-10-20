# Analysis and validation: Protected merge queue validation

## Specification analysis

The analysis examined 10 functional requirements, five success criteria, and 13 tasks.
All 10 functional requirements have task coverage.
No critical inconsistency, unresolved ambiguity, duplicate requirement, or unmapped task was found.
SC-005 requires live owner-controlled activation evidence and remains incomplete.

| Requirement | Tasks | Evidence |
| - | - | - |
| FR-001, FR-002 | T004, T005 | Two workflow triggers and 14 stable CI context contracts |
| FR-003, FR-004 | T003, T006, T007 | Candidate checkout and event concurrency contracts |
| FR-005 | T003, T006, T010 | Existing event guards and aggregate tests |
| FR-006 | T004, T006, T010 | Synthetic rejection cases and measured counts |
| FR-007 | T001, T008, T010 | Settings excluded from the diff |
| FR-008, FR-009 | T008, T012, T013 | Separate preparation and activation instructions |
| FR-010 | T001, T005 | CI diff changes only its trigger section |

The design records existing guard-module and changelog structure debt.
It adds no top-level Python name or unrelated process record.
The optional commit hooks remain deferred until the coherent change is ready.
Disabled companion hooks did not run.
The app-managed branch replaces the branch-creation hook's normal action.

## Local results

Commands ran with the worktree environment active unless an explicit interpreter appears.

| Command | Result |
| - | - |
| `python3 scripts/bootstrap_worktree.py` | Passed. Restored missing worktree tools and Chromium. |
| `python -m pytest -q tests/guardrails/test_ci_gate_triggers.py -k 'merge_group_contract or event_concurrency_isolation'` before workflow repair | Expected failure. Three live cases exposed missing events and unrestricted CodeQL cancellation. |
| `python -m pytest -s -q tests/guardrails/test_ci_gate_triggers.py tests/guardrails/test_ci_runtime_budgets.py tests/guardrails/test_quality_gate_close_scope.py tests/guardrails/test_codeql_register_gate.py` | Passed. 100 tests. |
| `python -m pytest -q tests/guardrails/test_process_folder_structure.py tests/guardrails/test_spec_route_contract.py tests/guardrails/test_changelog_fragment_policy.py` | Passed. 68 tests and one skip. |
| `python -m pytest -q tests/guardrails` | Passed. 1,060 tests and three skips. |
| `python -m ruff check .` | Passed. `All checks passed!` |
| `python -m black --check --diff .` | Passed. 2,482 files unchanged. |
| `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Passed. No issues in 860 source files. Existing notes remain. |
| `python -m bandit -c pyproject.toml -r . -q` | Passed. Exit 0, no findings. Existing comment warnings remain. |
| `symbol-diff --base origin/main tests/guardrails/test_ci_gate_triggers.py` | Passed. No module-level name changed. |
| `actionlint -shellcheck= -pyflakes= .github/workflows/ci.yml .github/workflows/codeql.yml` | Passed with portable actionlint 1.7.12. Workflow syntax only. |
| `ste-linter --quiet --config .ste-linter.toml --min-score 80` with the ten preparation Markdown files | Passed. Scores ranged from 87 through 98. |
| `python -m pytest -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` | Passed. One test. The required post-commit preflight remains separate. |

The repeated Markdown link check examined all 11 indexed Markdown files and found zero broken links.
The required post-commit preflight passed with four input reads and four input validations.
The committed ratchet examined 1,198 files and 675 existing findings.
It reported `gate: 0 new findings vs baseline`, with zero parse errors.
The analyzer reported 49 skips. No baseline or analyzer configuration changed.
The symbol comparison reported no module-level name changed.
An exact comparison proved that `ci.yml` is unchanged outside the three inserted trigger lines.

Required committed commands:

```text
git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"
git rev-parse --verify "origin/main^{commit}"
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

The comparison base resolved to `efd178c3f76e580afc0b5511734498b61f3a0090`.
Every command succeeded.

The advisory `speckit-task-audit --root .` examined 842 feature records and 365 task files.
It reported existing unchecked tasks, malformed markers, and missing evidence elsewhere.
This feature had no malformed marker or missing delivered file.
Its remaining tasks require publication review and owner activation.
Do not interpret the repository-wide advisory output as a clean task audit.

Neither a local guard pass nor a successful preparation merge proves queue activation.

## Local environment repairs

The normal requirements audit initially aborted during temporary interpreter creation on macOS.
Changing `TMPDIR` alone did not repair it.
The process-local native library path works when Python starts the module directly.
The long-path console entry uses a shell that discards that variable.

Exact successful requirements audit:

```text
DYLD_LIBRARY_PATH=/Users/jmorrison/.local/share/uv/python/cpython-3.13.13-macos-aarch64-none/lib .venv/bin/python -m pip_audit -r requirements.txt
```

Result: `No known vulnerabilities found`, exit 0.
No package was excluded and no finding was suppressed.
The command audits the unchanged requirements file with its dependency resolution.
The normal console entry also passed after a supported local entry-path repair:

```text
python -m pip install --quiet --force-reinstall --no-deps pip-audit==2.10.1
export DYLD_LIBRARY_PATH=/Users/jmorrison/.local/share/uv/python/cpython-3.13.13-macos-aarch64-none/lib
pip-audit -r requirements.txt
```

The reinstall used the same environment through a shorter session-local symbolic link.
That path lets the generated console script start Python directly instead of a shell.
The pip-audit version stayed 2.10.1.
The exact documented audit reported `No known vulnerabilities found`, exit 0.
No auditor source or audit behavior changed.
Issue #4359 preserves the original local tooling defect and both supported repairs.

The installed-environment audit initially reported vulnerable bootstrap pip 26.0.1.
The supported environment-only repair was:

```text
uv pip install --python .venv/bin/python --upgrade pip
python -m pip_audit --local
```

Pip changed to 26.2.2 in the ignored environment.
The repeated installed-environment audit reported no known vulnerabilities, exit 0.
It explicitly could not audit the Git-only `misthelper-devtools` package.
That audit does not replace the successful requirements audit.
Issues #4360 and #4255 track the bootstrap installer defect.

## Scope and remaining evidence

The `ci.yml` diff adds only the released trigger section.
It leaves the #4306 historical-fetch repair unchanged.
PR #4208 retains ownership of its browser evidence section.
This branch neither imports nor removes that unmerged step.

No product code, dependency manifest, baseline, repository setting, or required status changed.
No container, Mist API, product sweep, frontend suite, or product coverage run was needed for this configuration-only change.
GitHub must still run the required checks and CodeQL on the preparation pull request.
Coordinator review is required before auto-merge or merge.
Queue activation requires separate owner approval.
Two live protected queued merges and resulting main checks remain unverified.
Issue #3071 must remain open.
