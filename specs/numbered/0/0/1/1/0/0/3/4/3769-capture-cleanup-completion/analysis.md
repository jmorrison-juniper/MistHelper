# Capture cleanup verification

## Outcome

The deterministic barrier confirmed the cleanup-order race on current main.
The repair delays terminal notification until cleanup ends.
Cleanup exceptions produce one explicit failed result.
Capture identity checks and the existing utility test module remain unchanged.

## Specification analysis

The review found no blocking ambiguity, duplication, or inconsistency.
All seven requirements and four measurable outcomes map to the nine tasks.

| Requirement | Tasks | Evidence |
| - | - | - |
| FR-001, SC-001, SC-002 | T002, T003, T004 | Site and organization cleanup barriers |
| FR-002 | T004 | Foreign capture identifiers receive no deletion |
| FR-003, SC-003 | T005, T006 | GET and DELETE exceptions produce one failed result |
| FR-004 | T003, T006 | Execution error and six trigger failure cases |
| FR-005 | T002 | Two unchanged-source assertion failures |
| FR-006, SC-004 | T001, T008 | Existing utility test module and capture timing remain unchanged |
| FR-007 | T002, T008 | Controlled loopback service only |
| Delivery evidence | T007, T009 | Release-note fragment and explicit file manifest |

No new schema, endpoint, credential, environment variable, or transport is necessary.
The existing app-managed branch replaces the branch-creation hook.
PowerShell is unavailable, so the managed path follows the inspected base-5 route algorithm directly.
The shared feature pointer remains unchanged.
Optional commit hooks were deferred until verification. Disabled companion hooks did not run.

## Deterministic proof

Base commit: `9991d30a187e5d215462eefac60a09a57e5f99e5`.
Base tree: `8d28a4e9d24a27fed77528ec0975d6a5a88ad237`.

```text
.venv/bin/python -m pytest -q tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py -k terminal_waits_for_matching_cleanup
```

Before the repair: `2 failed, 5 deselected in 0.92s`.
Both cases observed `STOPPED` while the cleanup barrier remained blocked.
The barrier prevents the matching deletion from occurring before the assertion.
Every test releases the barrier and joins its worker, including assertion failure paths.
No repeated run supplies the proof.

## Local gates

| Command | Result |
| - | - |
| `python3 scripts/bootstrap_worktree.py` | Passed. Created the missing Python 3.13.13 environment. |
| `.venv/bin/python -m ruff check .` | `All checks passed!` |
| `.venv/bin/python -m black --check .` | `2483 files would be left unchanged.` |
| `.venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Success in 860 source files. Existing annotation notes remain. |
| `.venv/bin/python -m py_compile src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py` | Passed without output. |
| `.venv/bin/python -m bandit -c pyproject.toml src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py -q` | Passed without findings. |
| `.venv/bin/python -m radon cc src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py -j \| .venv/bin/complexity-gate --max 10` | All functions within the threshold. |
| `.venv/bin/symbol-diff --base origin/main src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py` | Zero lost or added names. |
| `.venv/bin/python -m pylint src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py --fail-under=9.5` | Passed at 9.90/10. Existing R0903 class warning remains. |
| `.venv/bin/python -m vulture src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py --min-confidence 70` | Passed without findings. |
| `.venv/bin/python -m pydocstyle src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py` | Passed without findings. |
| `.venv/bin/python -m interrogate src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py --fail-under 90` | Passed with 100% documentation coverage. |

Final focused tests:

```text
.venv/bin/python -m pytest -q tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py tests/unit/websocket_streams/live/runners/utility/test_ws_utility_runner.py --cov=src.mist.realtime.websocket_streams.live.runners.utility.runner.execution --cov-report=term-missing --cov-fail-under=80
```

Result before the final literal-body refinement: `38 passed in 13.92s`, with 99.01% coverage of the changed source module.
The refined new module also passed all 15 cases.
The broader final run below includes that refinement.

```text
.venv/bin/python -m pytest -q tests/unit/websocket_streams/live/runners/utility tests/unit/websocket_streams/live/transport tests/guardrails/test_process_folder_structure.py tests/guardrails/test_changelog_fragment_policy.py tests/guardrails/test_websocket_transport_constitution.py --cov=src.mist.realtime.websocket_streams.live.runners.utility.runner.execution --cov-report=term-missing --cov-fail-under=80
```

Result: `184 passed, 1 skipped in 19.35s`.
Changed-module coverage: 99.01%.
The skipped changelog guard requires a pull request event.
This measurement is not repository-wide test coverage.

## Test-quality ratchet

The first committed comparison found six missing failure-mode cases in the new module.
The next comparison found two body cases that the analyzer could not recognize in the initial parameter form.
Actual HTTP, connection, timeout, malformed-body, and empty-byte-body tests resolve all six findings.
The baseline and analyzer settings remain unchanged.

```text
git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"
git rev-parse --verify "origin/main^{commit}"
.venv/bin/python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
.venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

The preflight read and validated all four required inputs. One test passed.
The changed-file check examined one test module and found zero new findings.
The full check examined 1,199 files and 632 existing findings.
Both checks reported `gate: 0 new findings vs baseline`.

## Documentation gates

The Markdown link check examined nine feature-owned documents and found zero broken links.
The STE check passed all feature-owned documents at the required threshold of 80.
The final evidence document scored 95. The task document scored 97.

```text
.venv/bin/markdown-link-check specs/numbered/0/0/1/1/0/0/3/4/3769-capture-cleanup-completion changelog.d/issue-3769-capture-cleanup-completion.md
.venv/bin/speckit-task-audit --root .
```

The informational repository-wide task audit returned exit code 1.
It examined 845 feature records, 368 task files, and 10,394 task markers.
It reported 36 malformed markers and 140 missing delivery paths in unchanged records.
It reported no finding for this feature.
The CI workflow also treats this audit as informational.
All nine tasks in this feature are complete.

## Dependency audit

```text
.venv/bin/python -m pip_audit -r requirements.txt
```

The original command failed when its temporary interpreter aborted during `ensurepip` with signal 6.
The dependency manifest did not cause that interpreter failure.
The alternate command avoids the failed interpreter path:

```text
uv pip compile requirements.txt --output-file /tmp/misthelper-3769-audit-requirements.txt --quiet
.venv/bin/python -m pip_audit --disable-pip --no-deps -r /tmp/misthelper-3769-audit-requirements.txt
```

Result: `No known vulnerabilities found`.
No dependency manifest changed.

## File manifest

- `src/mist/realtime/websocket_streams/live/runners/utility/runner/execution.py`
- `tests/unit/websocket_streams/live/transport/clients/test_capture_cleanup_completion_3769.py`
- `changelog.d/issue-3769-capture-cleanup-completion.md`
- `specs/numbered/0/0/1/1/0/0/3/4/3769-capture-cleanup-completion/spec.md`
- `specs/numbered/0/0/1/1/0/0/3/4/3769-capture-cleanup-completion/plan.md`
- `specs/numbered/0/0/1/1/0/0/3/4/3769-capture-cleanup-completion/tasks.md`
- `specs/numbered/0/0/1/1/0/0/3/4/3769-capture-cleanup-completion/analysis.md`
- `specs/numbered/0/0/1/1/0/0/3/4/3769-capture-cleanup-completion/design/research.md`
- `specs/numbered/0/0/1/1/0/0/3/4/3769-capture-cleanup-completion/design/data-model.md`
- `specs/numbered/0/0/1/1/0/0/3/4/3769-capture-cleanup-completion/design/quickstart.md`
- `specs/numbered/0/0/1/1/0/0/3/4/3769-capture-cleanup-completion/design/checklists/requirements.md`

The source diff removes six noncomment lines, including one docstring and one `finally` header.
No module-level name changes.
The existing utility tests, `capture.py`, and `monitoring.py` remain unchanged.

## Limits

No production cloud request, menu sweep, container build, or deployment ran.
No web UI, frontend, dependency manifest, or generated menu reference changed.
The full repository test suite did not run.
Issue artifacts were unavailable because their list endpoint returned HTTP 404.
The PR template remains intact, with unused deployment and UI items explicitly identified as not applicable.
Publication targets `main`. Merge and auto-merge remain prohibited.
