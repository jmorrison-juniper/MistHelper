# Local validation record

## Result

The controlled native schedule proves a descriptor-lifetime defect on clean main.
The local repair prevents descriptor reuse while receive remains active.
This result does not establish the exact schedule of every prior full-suite failure.

The baseline is `03e609b828d949cc8d983571209d95bd708a7956`.
The support worktree and PR #4503 remain unchanged.
No publication, merge, or deployment is authorized.
Umbrella issue #1794 remains incomplete.

## Failure and repair

CPython copies the descriptor before its timed native read waits for input.
Local close can release that descriptor while the native read still holds its number.
An unrelated idle socket can receive the number.
The native read then waits on the unrelated socket.
The existing stopped-state assertion fails with `LIVE`.

One shared `SocketRuntime` now owns receive and close for each connection.
Close sets the event and aborts before acquiring the receive lock.
Physical close waits until the active receive exits.
A later receive checks the event under the same lock.
The repair changes no timeout, state assertion, public session state, or failure reason.
It adds no reader join, production scheduling hook, or native test dependency.

## Before and after evidence

| Evidence | Before repair | After repair |
| - | - | - |
| Native descriptor-reuse schedule | `reused=True old_closed=True`, `LIVE`, one failure | `reused=False old_closed=False`, one pass |
| Portable ownership schedule | Three failures | Three passes |
| Expanded portable lifecycle checks | Not used as before-repair proof | 12 passes |
| Existing live transport tests | Earlier baseline run passed | 307 passes |
| Complete affected unit and contract trees | Not used as before-repair proof | 493 passes |
| Complete unit suite | Prior runs had inconsistent outcomes | 29924 passed, 25 skipped, 5 warnings |

The expanded checks cover closure without receive, repeated close, concurrent close, and abort failure.
They also require receive exceptions and worker exit without deadlock.
An abort failure remains visible to the caller.
The repair does not force descriptor release after an abort failure.
The controlled native diagnostic remains outside the repository.

Complete logs remain in the investigation session files:
`native-fd-before.log`, `native-fd-after-final.log`, `ownership-before.log`, and `ownership-after.log`.
The native diagnostic uses `test_native_fd_reuse.py` and `poll_schedule.dylib` from that directory.

## Local checks

All commands use the isolated environment.

| Command | Result |
| - | - |
| `.venv/bin/python -m pytest tests/unit/websocket_streams/live/transport/runtime/lifetime --no-cov -q` | 12 passed in 0.65 seconds |
| `.venv/bin/python -m pytest tests/unit/websocket_streams tests/contract/websocket_streams --no-cov -q` | 493 passed in 26.55 seconds |
| `.venv/bin/python -m pytest tests/unit --no-cov -q --tb=long` | 29924 passed, 25 skipped, 5 warnings in 745.98 seconds |
| `.venv/bin/python -m pytest tests/contract/websocket_streams -q --no-cov` | 12 passed in 0.23 seconds |
| `.venv/bin/python -m ruff check .` | All checks passed |
| `.venv/bin/python -m black --check .` | 2502 files unchanged |
| `.venv/bin/python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | No issues in 864 source files |
| `.venv/bin/python -m compileall -q src/mist/realtime/websocket_streams/live/transport` | Passed without output |
| `.venv/bin/bandit -c pyproject.toml -r src/mist/realtime/websocket_streams/live/transport -q` | Passed without findings |
| `.venv/bin/radon cc src/mist/realtime/websocket_streams/live/transport -j \| .venv/bin/complexity-gate --max 10` | All functions within the threshold |
| `.venv/bin/python -m pylint src/mist/realtime/websocket_streams/live/transport --fail-under=9.5` | 9.79 out of 10 |
| `.venv/bin/python -m vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | Passed without findings |
| `.venv/bin/python -m pydocstyle src/ wsgi.py web_portal` | Passed without findings |
| `.venv/bin/interrogate src/mist/realtime/websocket_streams/live/transport --fail-under 90` | 100 percent |

The structure and changelog guard selection passed 34 tests and skipped one CI-only diff check.
The selection includes the process-folder, changelog-fragment, transport-constitution, and WebSocket feature-structure guards.

Symbol comparison preserved every production declaration.
It reported two added imports, `threading` and `websocket`, in `socket_runtime.py`.
It reported the removed, unused `Any` import in `frame_reader.py`.
Those two comparisons return status 1 for intentional import changes.
The two connection modules report no changed module-level name.

The initial STE check read eight feature Markdown files.
Every file scored at least 87.
The initial directory argument was invalid. The corrected command named every file explicitly.

The final validation record scored 95.
The updated task record scored 98.
The attempted integration-test directory does not exist. The existing contract selection passed 12 tests.
The test-directory mypy command selected no files because repository configuration excludes tests.
The documented production type selection passed instead.

The advisory task audit examined 862 feature records, 385 task files, and 10571 task markers.
It returned status 1 for historical unchecked tasks, malformed markers, and missing delivery paths.
It reported no finding for this feature.
The CI job treats this report as advisory.
No historical record was changed.

## Requirement coverage

| Requirements | Tasks | Result |
| - | - | - |
| FR-001, FR-002 | T002, T003 | Active reads retain descriptors. Closed owners refuse later reads. |
| FR-003 | T002, T004, T006 | Runtime, shell, and stream follow the same ownership schedule. |
| FR-004 | T005, T006 | Existing transport outcomes pass unchanged. |
| FR-005 | T001, T002 | The native and portable schedules failed before implementation. |
| SC-001, SC-002, SC-003 | T006 | Existing shell, screen, and write-failure tests pass unchanged. |

The read-only specification analysis found eight requirements and eight tasks.
Coverage is 100 percent. No task is unmapped.
No ambiguity, duplication, or uncovered requirement was found.
Publication and deployment remain excluded by the explicit user instruction.

## Scope and committed-test check

One complete unit run passed with the repaired production code and all 12 lifecycle checks.
The run used no native interposer or socket-method replacement.
Its complete output, including warnings, is `full-unit-after.log`.
The original native reproduction remains separate diagnostic evidence.

The first committed-test quality comparison checked three files and reported four new HTTP failure-mode findings.
The lifetime fixture unnecessarily imported an HTTP API fake through a runner helper.
The fixture now constructs connection settings directly. It still exercises the same runtime and connection methods.
This removes an unrelated HTTP client from a socket-lifetime test without changing assertions or the quality baseline.
The final affected selection passes 493 tests after this fixture-only change.
Production code remains identical to the full-suite-tested repair.

After the full run, `main` advanced to `0c84e9f536204d17ec2e40fa98d101b329240957`.
That commit changes only `mist-ops-platform/tests/unit/api/test_auth.py`.
It changes no root unit test, transport source, or shared test configuration.
The local branch rebased onto that commit.
The affected tests and structure checks passed after the rebase.
The committed-test quality procedure must run again after the fixture commit.
Its preflight and comparison results belong in the session validation logs.
The check must report zero new findings before any future publication.
This investigation does not authorize publication.

Dependency audit, container checks, and generated menu checks do not apply to this transport-only change.
