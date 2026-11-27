# Research: Raw shell history test failure (issue 3767)

## Summary

The reported failure is `test_shell_history_preserves_raw_control_and_split_utf8_bytes` at accepted main. The assertion expects `finished` and observes `failed`. No scanned CI log shows this test as FAILED. The leading hypothesis is a keepalive dead-peer close during the silent window that the test device creates. One controlled run must confirm that hypothesis. This authoring step did not run the test, because the brief forbids test runs.

## Decisions

| ID | Decision | Alternatives | Reason | Risk |
| - | - | - | - | - |
| D-1 | Write a diagnosis-only record. Change no source, test, fixture, timeout, or workflow in this record. | Fix now by changing the fixture. Raise the test timeout. Disable the test. | The issue states "Initial scope is read-only causal diagnosis", and it forbids timeout and fixture changes. | The flake can recur until the follow-up merges. |
| D-2 | Run the controlled reproduction once with DEBUG log events and no source change. | Add a diagnostic assertion. Add prints. Run the test many times. Attach a debugger. | The issue allows one controlled reproduction. Existing log events separate the branches (R-12, R-17, R-19). | One run can pass and show nothing. The record then states "not reproduced". |
| D-3 | Name H1, the dead-peer close, as the leading hypothesis. Keep H2 and H4 as confounders. | Name H2, the environment, as primary. Name H4, shared state, as primary. Name no hypothesis. | The dead-peer close needs only 0.1 seconds of silence (R-05, R-13). The device waits 0.2 seconds (R-04). A pong must arrive inside the window (R-23). | H1 may be wrong. T006 and T007 decide it. |
| D-4 | Use a fixture timing change as the follow-up remedy. Send the close frame without the 0.2-second delay. | Raise `read_timeout_seconds` in the test profile. Change the production keepalive default. Retry the test. | TCP keeps frame order, and the reader handles each data frame before the close frame (R-10, R-11, R-18). The change removes the silent window. The timeout change and the retry are forbidden by the issue. The production default is outside scope (R-21). | A reviewer can read the change as a weakening. The owner must authorize the change (T008). |
| D-5 | Use Python 3.15.2 for the controlled run. | Use Python 3.13, the issue environment. Use the latest 3.15 patch release. | `pyproject.toml` requires 3.15 (R-36). CI uses 3.15 (R-37). The copilot instructions name 3.15.2 for bootstrap. | The local failure may not repeat on 3.15.2. |
| D-6 | Keep `Closes #3767` in the pull request body, as the brief requires. | Use `Refs #3767` until the fix merges. | Section 4 of the brief sets the closing keyword. The orchestrator can change the body before merge. | The issue closes before the cause is confirmed. Caution: review the body before merge. |
| D-7 | Add the label `in-progress`. Keep `needs-investigation`. | Remove `needs-investigation`. | The issue comment of 2026-10-26 keeps the label because the cause is unknown. The copilot instructions require `in-progress` before a branch. | Label automation may react to the new label. |
| D-8 | Set the size to `S`. | Set `M` for the record and the fix. Set `L` for a wider scope. | The planned fix changes one fixture class in one file (T008). | The controlled run can widen the scope. The size changes then. |

No decision in this record is a human decision under section 6 of the brief. The owner authorization for T008 is a gate, not a decision category.

## Issue Facts and Linked Work

- Issue 3767 is open with the labels `bug`, `needs-investigation`, `tests`, and `runtime`. It was created on 2026-10-03 and last updated on 2026-10-26.
- The issue body names the failing test, the assertion, the accepted main commit `d4d1110352eeab3d9f9d483242232c12f6de4d2d`, and the candidate commit `12f10ece0901452bd71eb1baa563ee77de5687db`.
- The issue comments of 2026-10-26 state that one current-main run passed and that the diagnosis is incomplete. The comments state no code change.
- Linked pull requests: none. The search for "3767" returned pull request #96. Its body cites `github/codeql-action` pull request 3767, which lives in a different repository. PR #96 is therefore unrelated to this issue.
- Related issues, all closed: #3758 (test failure for shell logs, closed 2026-10-03), #3760 (type error in the fake cloud `on_connect` binding, closed 2026-10-19), and #3761 (complexity of the shell log assertion test, closed 2026-10-20).
- Legacy record: none. No folder under `specs/` starts with `3767-` on current main or accepted main (R-42, R-43). The route folder `specs/numbered/0/0/1/1/0/0/3/2/` does not exist on current main.
- Legacy handoff branch: `recovery/3767-handoff-20261004` returns HTTP 404 now (R-66). CI run 37172626352 named this branch at accepted main on 2026-10-04 (R-70). The content is unavailable, so the record reuses none of it.
- The route is correct. Base-5 digits of 3767 are `110032`. The eight-digit route is `00110032`, which matches `specs/numbered/0/0/1/1/0/0/3/2` (R-41).

## Commit Identities

| Identity | Value | Evidence |
| - | - | - |
| Accepted main | `d4d1110352eeab3d9f9d483242232c12f6de4d2d`, tree `fc9e37e7ba4d156f40b586211d9486274089c2ef`, dated 2026-10-03 | R-44 |
| Candidate | `12f10ece0901452bd71eb1baa563ee77de5687db`, tree `688ec81037a3fe18cab7b4885e6a7040983d0d5f`, parent `5dbe7af29c6a0c3a3d923684d49f05b9ce75b7c3` | R-45 and the compare call |
| Current main | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` | Git ref call on 2026-11-26 |
| Compare, accepted main to candidate | `ahead_by` 2, `behind_by` 0. Two files differ: `tests/unit/websocket_streams/live/transport/fake_mist_cloud/server.py` (+2 -2) and `tests/unit/websocket_streams/live/transport/test_fake_cloud_on_connect_3760.py` (+177 -0). | Compare call |

The candidate matches the issue. Only the two #3760 fixture paths differ from accepted main. The failing test file has the same blob at both commits (R-01 and R-47).

## Remote Verification Table

Each row names one checked claim. The table row count equals the `remote_checks` count in `3767-STATUS.json`. `main` means `refs/heads/main`. The local rows name installed packages. Lines come from a decoded GitHub file body, or from the tree or file listing where the row says so.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Failing test definition, accepted main | `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `0fc79d8b799f2ce0704580eb62ade41f9fb25869` | present | 454 |
| R-02 | Failing assertion `assert session.state in states` in `_wait_for_state` | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `0fc79d8b799f2ce0704580eb62ade41f9fb25869` | present | 108 |
| R-03 | Wait for the FINISHED state | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `0fc79d8b799f2ce0704580eb62ade41f9fb25869` | present | 464 |
| R-04 | Raw-output device sends the close after a 0.2-second timer | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `0fc79d8b799f2ce0704580eb62ade41f9fb25869` | present | 168 |
| R-05 | Test profile sets `read_timeout_seconds=0.05` | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `0fc79d8b799f2ce0704580eb62ade41f9fb25869` | present | 85 |
| R-06 | Failing test definition, current main | same | `main` | `e613e2a149ee85768d93a4cac85f187a18c5f2a9` | present | 538 |
| R-07 | Raw-output device close timer, current main | same | `main` | `e613e2a149ee85768d93a4cac85f187a18c5f2a9` | present | 190 |
| R-08 | Outcome DROPPED result when output was seen and no code arrived | retired `websocket_streams/live/runners/shell/lifecycle/outcomes.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `5f989e210774c8c91e5c2c47f4b64ca44e2a4acc` | present | 55 |
| R-09 | Outcome gate `elif not self.output_seen` | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `5f989e210774c8c91e5c2c47f4b64ca44e2a4acc` | present | 48 |
| R-10 | Reader catches `ConnectionClosed` and calls `finish` | retired `websocket_streams/live/runners/shell/lifecycle/reading.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `12d1be02da3e7bdb122f71e24ba2e07a10ee0f06` | present | 43 |
| R-11 | Reader appends each data frame to history | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `12d1be02da3e7bdb122f71e24ba2e07a10ee0f06` | present | 71 |
| R-12 | Reader logs `terminal_connection_closed` with `code`, `dropped`, and `status` | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `12d1be02da3e7bdb122f71e24ba2e07a10ee0f06` | present | 46 |
| R-13 | Keepalive closes a silent peer at two quiet intervals with `dropped=True` | retired `websocket_streams/live/transport/runtime/reader/keepalive.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `c134b4e2f6f6d6fc7154e101613c67bbb3b5223b` | present | 34 |
| R-14 | Keepalive sends a ping after one quiet interval | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `c134b4e2f6f6d6fc7154e101613c67bbb3b5223b` | present | 37 |
| R-15 | Keepalive resets the quiet timer when a frame arrives | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `c134b4e2f6f6d6fc7154e101613c67bbb3b5223b` | present | 45 |
| R-16 | Frame reader maps a socket error to `ConnectionClosed` with the dropped flag | retired `websocket_streams/live/transport/runtime/reader/frame_reader.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `01daf19d7589f8c5f94f40e628a9a42f794a2cba` | present | 56 |
| R-17 | Frame reader logs `frame_read_completed` with status `closed` before a socket error | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `01daf19d7589f8c5f94f40e628a9a42f794a2cba` | present | 55 |
| R-18 | Frame reader maps a close frame to `ConnectionClosed` with the code | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `01daf19d7589f8c5f94f40e628a9a42f794a2cba` | present | 68 |
| R-19 | Socket close logs `socket_close_started` | retired `websocket_streams/live/transport/runtime/reader/socket_runtime.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `ab5742a2022901ae0b5111e8ec546eb5cbbca144` | present | 84 |
| R-20 | An empty close payload yields code 1005 | retired `websocket_streams/live/transport/runtime/reader/contracts.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `77ee06fdbc3b4035720d2c02f9b976ff1d77c299` | present | 42 |
| R-21 | Production `read_timeout_seconds` default is 20.0 | retired `websocket_streams/live/transport/endpoint.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `428d631f38185ee4b92e12f196d826e78d85a501` | present | 23 |
| R-22 | `SessionState.FAILED` has the value `failed` | retired `websocket_streams/live/sessions/record/state.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `79707450503b008bdc316f19907a7a5ac9a8cb41` | present | 28 |
| R-23 | Fake cloud answers each ping with a pong when `answer_pings` is true | `tests/unit/websocket_streams/live/transport/fake_mist_cloud/server.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `a6d96bbbb1067eb719b1bc22161d59586e2a3511` | present | 307 |
| R-24 | Fake cloud on_connect form on accepted main is `hasattr(handler, "on_connect")` | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `a6d96bbbb1067eb719b1bc22161d59586e2a3511` | present | 199 |
| R-25 | Candidate changes the on_connect check to `handler is not None and hasattr(handler, "on_connect")` | same | `12f10ece0901452bd71eb1baa563ee77de5687db` | `5a88211eb6795994ffbe2f87daaa736a3f8be1a4` | present | 199 |
| R-26 | Fake cloud on current main uses `getattr(handler, "on_connect", None)` | same | `main` | `780931c7094724064467f4b0d71d883495bb1a01` | present | 206 |
| R-27 | Candidate adds the test file for the #3760 binding | `tests/unit/websocket_streams/live/transport/test_fake_cloud_on_connect_3760.py` | `12f10ece0901452bd71eb1baa563ee77de5687db` | `31bc475f926496fddfba6a20c721e153278f2948` | present | 1 |
| R-28 | The #3760 test file is absent on current main | same | `main` | none | absent | 0 |
| R-29 | `coverage.ini` is absent on current main | `coverage.ini` | `main` | none | absent | 0 |
| R-30 | `coverage.ini` is absent on accepted main | `coverage.ini` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | none | absent | 0 |
| R-31 | The accepted-main source path is absent on current main | retired `websocket_streams/live/runners/shell/lifecycle/outcomes.py` | `main` | none | absent | 0 |
| R-32 | Outcome mapping on current main, moved path | `src/mist/realtime/websocket_streams/live/runners/shell/lifecycle/outcomes.py` | `main` | `c8b251646a7f9450607137862e8b8f81ce840ba1` | present | 55 |
| R-33 | Keepalive dead-peer close on current main, moved path | `src/mist/realtime/websocket_streams/live/transport/runtime/reader/keepalive.py` | `main` | `17ff619f9abe5b6c9b123b731da8d9c597477967` | present | 34 |
| R-34 | Shell client local close on current main, moved path | `src/mist/realtime/websocket_streams/live/transport/shell_client.py` | `main` | `902fbe2db6ccb9a8c4224985d22615e665a9498d` | present | 107 |
| R-35 | Shell runner constructs `TerminalReading` on current main | `src/mist/realtime/websocket_streams/live/runners/shell/runners.py` | `main` | `6d886a0f3e6d7892f7ad8a9faf3f967a5940a02f` | present | 45 |
| R-36 | Project requires Python 3.15 or newer | `pyproject.toml` | `main` | `eca34c826ea44ba4f2faefc07d04c2c117e99751` | present | 23 |
| R-37 | CI default Python version is 3.15 | `.github/workflows/ci.yml` | `main` | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 77 |
| R-38 | CI shard `root-units` runs `tests/unit` | `.github/workflows/ci.yml` | `main` | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 262 |
| R-39 | CI shard `root-units` has a 20-minute limit | `.github/workflows/ci.yml` | `main` | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 265 |
| R-40 | CI pytest command uses `--cov-fail-under=0` and `--timeout=120` | `.github/workflows/ci.yml` | `main` | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 311 |
| R-41 | Spec route uses base 5 with eight digits | `.specify/scripts/powershell/spec-route.ps1` | `main` | `37293a255f9b5de20ccb2b3ef0ad15717bab2826` | present | 17 |
| R-42 | No `specs/` folder named `3767-*` exists on current main | `specs/**/3767-*` | `main` | none | absent | 0 |
| R-43 | No `specs/` folder named `3767-*` exists on accepted main | `specs/**/3767-*` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | none | absent | 0 |
| R-44 | Accepted main commit exists, with tree `fc9e37e7ba4d156f40b586211d9486274089c2ef` | `commit d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `fc9e37e7ba4d156f40b586211d9486274089c2ef` | present | 0 |
| R-45 | Candidate commit exists, with tree `688ec81037a3fe18cab7b4885e6a7040983d0d5f` | `commit 12f10ece0901452bd71eb1baa563ee77de5687db` | `12f10ece0901452bd71eb1baa563ee77de5687db` | `688ec81037a3fe18cab7b4885e6a7040983d0d5f` | present | 0 |
| R-46 | CI scan shows no FAILED line for the test in 59 scanned logs | `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py` | `ci.yml` failing runs, created 2026-10-03 to 2026-11-26 | not-applicable-log-scan | absent | 0 |
| R-47 | Accepted-main push run 37138384453 shows the test PASSED in job root-units | `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `0fc79d8b799f2ce0704580eb62ade41f9fb25869` | present | 0 |
| R-48 | Run 45767339705 fails only in `test_netcool_smoke_client.py`, and the test PASSED | `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py` | `01f64a2066c3b109daf4fb99449b2bd4b3f86604` | not-applicable-log-only | present | 0 |
| R-49 | Current main Quality Gates run 45774119357 (manual dispatch on main) passes job root-units | `pytest coverage shard (root-units)` job | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` | not-applicable-job-conclusion | present | 0 |
| R-50 | Installed mistapi WebSocket package file | `.venv\Lib\site-packages\mistapi\websockets\__init__.py` | installed mistapi 0.64.1 | `e269ee63278ef3b24269050c20eccfc83a3fb04f` | present | 1 |
| R-51 | Installed mistapi registers the `websockets` package | `.venv\Lib\site-packages\mistapi\__init__.py` | installed mistapi 0.64.1 | `f6fca30f4088d763e76f3072d02a3095d46852b9` | present | 28 |
| R-52 | Installed websocket-client defines `ping` | `.venv\Lib\site-packages\websocket\_core.py` | installed websocket-client 1.9.2 | `3aa97f08542118e1539479ecf989e0d4aef9b799` | present | 394 |
| R-53 | Contributor guide states Python 3.15 or newer | `documentation/development-setup.md` | `main` | `1733975a7e0a0962fe5367e165a21f5831f8c3e5` | present | 13 |
| R-54 | Instructions hold at most 20 words each | `AGENTS.md` | `main` | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 48 |
| R-55 | A test that fails in the full run and passes alone means shared state | `AGENTS.md` | `main` | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 138 |
| R-56 | Temporary owned WebSocket transport exception | `.specify/memory/constitution.md` | `main` | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 282 |
| R-57 | Writing gate grades each Markdown file | `documentation/quality-gates.md` | `main` | `6776d334cca5d9b43273473a06da367a65605c6d` | present | 277 |
| R-58 | Local gates table row for Tests | `.github/copilot-instructions.md` | `main` | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 61 |
| R-59 | Local gates table row for STE | `.github/copilot-instructions.md` | `main` | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 74 |
| R-60 | STE linter configuration file exists | `.ste-linter.toml` | `main` | `d9f28ef8faf4a4c36a4e967d5b978f96eb306253` | present | 1 |
| R-61 | Test quality configuration file exists | `.github/test-quality-config.toml` | `main` | `d0c88405e03f11e71b1fc8fe9238f14936991da7` | present | 1 |
| R-62 | Test quality baseline file exists | `.github/test-quality-baseline.json` | `main` | `512da22b0769e8343a4b5b734c507d6aa3969ac6` | present | 1 |
| R-63 | Reference record spec file exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | `main` | `83b950279e45704943ad6942d23c8fc99cced492` | present | 1 |
| R-64 | Reference record research file exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md` | `main` | `2e4aaa714e56fff7f96a2af9e686e9f5c06224a7` | present | 1 |
| R-65 | Bootstrap script exists | `scripts/bootstrap_worktree.py` | `main` | `e16515ffa789cca7d0bdd7e9789898588e5f1312` | present | 1 |
| R-66 | Legacy handoff branch `recovery/3767-handoff-20261004` is absent | `branch recovery/3767-handoff-20261004` | GitHub API | none | absent | 0 |
| R-67 | Shell frame reader read slice is 0.025 seconds with a 0.05-second read timeout | retired `websocket_streams/live/transport/shell_client.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `871cb346b63de90a85798b3050abfde3723de469` | present | 123 |
| R-68 | Reader generic exception branch logs an unexpected failure | retired `websocket_streams/live/runners/shell/lifecycle/reading.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `12d1be02da3e7bdb122f71e24ba2e07a10ee0f06` | present | 51 |
| R-69 | Keepalive raises the dead-peer `ConnectionClosed` with `dropped=True` | retired `websocket_streams/live/transport/runtime/reader/keepalive.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `c134b4e2f6f6d6fc7154e101613c67bbb3b5223b` | present | 36 |
| R-70 | CI run 37172626352 names branch `recovery/3767-handoff-20261004` at accepted main | `branch recovery/3767-handoff-20261004` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | not-applicable-run-listing | present | 0 |
| R-71 | Outcome STOPPED result when an operator stop is set | retired `websocket_streams/live/runners/shell/lifecycle/outcomes.py` | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `5f989e210774c8c91e5c2c47f4b64ca44e2a4acc` | present | 45 |
| R-72 | Outcome mode override result | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `5f989e210774c8c91e5c2c47f4b64ca44e2a4acc` | present | 47 |
| R-73 | Outcome WRITE_FAILED result when the close was local | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `5f989e210774c8c91e5c2c47f4b64ca44e2a4acc` | present | 50 |
| R-74 | Outcome FINISHED result when a close code exists | same | `d4d1110352eeab3d9f9d483242232c12f6de4d2d` | `5f989e210774c8c91e5c2c47f4b64ca44e2a4acc` | present | 52 |

Row R-48 uses the full head SHA of run 45767339705.

## CI Scan

The scan used these GET-only commands. It listed each failing `ci.yml` run in the window. It read the job list of each run. It downloaded `gh run view --log-failed` for each run whose root-units job failed or was canceled. It searched each log for the test node name.

| Measure | Count |
| - | - |
| Failing `ci.yml` runs in the window `created=2026-10-03..2026-11-26` | 316 |
| Root-units job conclusion `failure` | 56 |
| Root-units job conclusion `cancelled` | 3 |
| Root-units job conclusion `success` | 257 |
| Logs scanned (failure or canceled) | 59 |
| Scanned logs with a PASSED line for the test | 52 |
| Scanned logs with no line for the test | 7 |
| Scanned logs with a FAILED line for the test | 0 |

Each of the 257 successful root-units jobs ran the same shard command as R-40. Pytest exits with a nonzero code when a test fails. A successful job therefore means no test failed in that shard. The record uses this rule as an inference, not as a log line.

The 7 logs with no test line are not counted as PASSED or FAILED. The record does not inspect them. Unverified item U-9 lists them.

Two runs give direct evidence:

- Run 37138384453 is the push run on accepted main. Its root-units job succeeded. The log shows the test as PASSED at 98 percent (R-47).
- Run 45767339705 is a failing pull request run on Nov 26, 2026. Its root-units job fails in `test_netcool_smoke_client.py`. The log shows the raw shell history test as PASSED at 97 percent (R-48).

## Failure Path With Evidence

1. The test device sends its output chunks at once, then starts a 0.2-second timer (R-04).
2. The device sends the close frame when the timer expires (R-04).
3. The reader appends each data frame to history (R-11). The reader records the output before the close (R-09).
4. During the silence, the keepalive sends a ping after 0.05 seconds (R-14). It closes the connection after 0.1 seconds of silence (R-13). The test profile sets 0.05 seconds (R-05).
5. The fake cloud answers each ping with a pong (R-23). A received pong resets the quiet timer (R-15).
6. If the pong misses the window, the keepalive raises `ConnectionClosed(code=None, dropped=True)` (R-69). The outcome maps it to DROPPED (R-08). The state becomes `failed` (R-22).
7. The assertion then reports `failed` against the expected `finished` (R-02, R-03).

Step 6 is hypothesis H1. The window is 0.05 seconds, plus or minus the 0.025-second read slice (R-67). The production default is 20 seconds (R-21). The test profile is 400 times shorter.

## Hypotheses

| ID | Hypothesis | Evidence for | Evidence against or gap | Status |
| - | - | - | - | - |
| H1 | Dead-peer close during the 0.2-second silent window | Failure path steps 1 to 7. Test profile and production default differ by 400 times (R-05, R-21). No checked log shows FAILED (R-46). | No log of the failing run. The issue omits the session reason. | Leading and unconfirmed. T006 and T007 decide it. |
| H2 | Environment difference: local Python 3.13 and an untracked `coverage.ini` | The issue names Python 3.13 and `--cov-config=coverage.ini` (issue body). | The pin is 3.15 (R-36). CI uses 3.15 (R-37). `coverage.ini` is absent (R-29, R-30). | Confounder. T006 uses 3.15.2 and no `coverage.ini`. |
| H3 | Candidate server change causes the failure | The failing run used the candidate test file set (R-25). | The change adds a None guard. For a None handler, the old and new forms both skip `on_connect` (U-1). Main already uses the `getattr` form (R-26). | Excluded unless the log shows the fake cloud as the cause. |
| H4 | Order-dependent shared state from tests that run earlier in the same scope | AGENTS.md requires repair when a test fails in a full run and passes alone (R-55). | The CI scan shows no FAILED line in the full scope (R-46). The test was not run alone (U-8). | Open. T006 uses the same scope as the failing run. |
| H5 | No output before the close, which causes NO_ANSWER | Outcome row 3 gives NO_ANSWER when no output was seen (R-09). | The chunks arrive first on the same connection, so the device must fail before output. | Unlikely. |

## Controlled Run Result

No controlled run took place in this authoring step. The brief forbids test runs for this record. Task T006 runs the command in `design/quickstart.md` once. Task T007 records the signature and the hypothesis result in this section.

## Sources

| Source | Local path or URL | Use |
| - | - | - |
| Brief | `files/spec-brief.md` in the session folder | Governs this record. |
| Repository rules | `AGENTS.md` (R-54, R-55), `.github/copilot-instructions.md` (R-58, R-59), `.specify/memory/constitution.md` (R-56), `documentation/quality-gates.md` (R-57) | Rules, gates, and the owned-transport exception. |
| Templates | `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md` | Headings and layout. |
| Reference record | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (R-63, R-64) | Shape of the record. The content is not copied. |
| Failing code | Rows R-01 to R-35 | Failure path and line numbers. |
| CI | `.github/workflows/ci.yml` (R-37 to R-40), GitHub run and job API responses | Shard definition and run evidence. |
| Environment | `pyproject.toml` (R-36), `documentation/development-setup.md` (R-53), `scripts/bootstrap_worktree.py` (R-65) | Python pin and bootstrap. |
| Route | `.specify/scripts/powershell/spec-route.ps1` (R-41) | Route arithmetic. |
| mistapi | `.venv\Lib\site-packages\mistapi\websockets\__init__.py` (R-50), `.venv\Lib\site-packages\mistapi\__init__.py` (R-51), installed version 0.64.1 | The SDK WebSocket package name. No SDK insufficiency claim. |
| websocket-client | `.venv\Lib\site-packages\websocket\_core.py` (R-52), installed version 1.9.2 | The `ping` method. |
| Python documentation | https://docs.python.org/3/builtins/functions.html#hasattr | Fetched. The page was truncated before the `hasattr` entry. Not used as evidence (U-1). |
| Container and operator docs | Not cited as evidence. The container document applies to Podman test containers, and the failing run is native. | Not applicable |
| Skills | None loaded | No Podman, Juniper device, or Python skill covers these repository claims. |
| Mist API OpenAPI file and coverage documents | Not cited | No Mist REST endpoint is in scope. The coverage documents `documentation/MIST_API_GET_ENDPOINTS.md` and `documentation/MIST_API_MISSING_ENDPOINTS.md` do not apply. |

## Unverified

| ID | Claim | Reason it is unverified | Effect on the record |
| - | - | - | - |
| U-1 | `hasattr(None, "on_connect")` returns False in Python. | The fetched documentation page was truncated before the `hasattr` entry. No local source holds the entry. | H3 exclusion relies on this claim. Main already uses the `getattr` form (R-26), so the record does not depend on U-1 for the fix. |
| U-2 | The ping and pong round trip has a budget of about 25 to 75 milliseconds. | The budget follows from the constants at keepalive lines 34 and 37 and the read slice at shell client line 123. No measurement exists. | H1 likelihood is not quantified. |
| U-3 | H1 caused the local failure. | No log of the failing run exists in the repository. | T006 and T007 test the claim. |
| U-4 | The local failure ran on Python 3.13 on macOS. | The issue body states it. The record cannot check the local host. | D-5 uses 3.15.2 for the controlled run. |
| U-5 | The owner's local checkout held an untracked `coverage.ini`. | The issue command names the file. The repository tree has no such file (R-29, R-30). | H2 remains a confounder. |
| U-6 | The private log SHA256 values in the issue match the private files. | The private files are not in the repository. | The record quotes the hashes only as issue text. |
| U-7 | The #3761 reservation covers only the `ShellLogAssertions` class. | The issue 3761 title names the shell log assertion test. The owner did not confirm the scope. | The follow-up does not edit `ShellLogAssertions`. |
| U-8 | The failing test passes when run alone. | The record runs no test. | H4 remains open. |
| U-9 | The reason for the 7 logs with no test line. | The record does not open those logs. | These logs do not count as PASSED or FAILED. |
| U-10 | GitHub keeps logs for every run in the window. | The record does not check retention. | A missing log reduces the scanned count. |
| U-11 | The mistapi WebSocket package has no shell endpoint. | The record reads only the package file list (R-50). It does not read the module bodies. | The record makes no SDK insufficiency claim. |
