# Implementation Plan: Raw shell history test failure (issue 3767)

**Branch**: `docs/3767-raw-shell-history-failed` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/spec.md`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. This record has no `contracts/` folder.

## Summary

The failing test passed in every scanned CI log that named it. The local failure has no recorded session reason. The leading hypothesis is a keepalive dead-peer close. The test profile allows 0.1 seconds of silence. The raw-output device sends its close frame 0.2 seconds after the last output frame. This plan confirms the branch with one controlled run. The plan changes no repository file in this record. A fixture change follows only after owner authorization.

## Technical Context

**Language/Version**: Python 3.15.2. `pyproject.toml` line 23 requires 3.15 or newer.

**Primary Dependencies**: websocket-client 1.9.2 installed in `.venv`. mistapi 0.64.1 installed in `.venv`, with the pin `mistapi>=0.64.0,<0.65`. pytest with pytest-timeout 2.4.0 from `pyproject.toml` line 111.

**Storage**: Not applicable. The test writes no product output.

**Testing**: pytest. The test uses the fake Mist cloud under `tests/unit/websocket_streams/live/transport/fake_mist_cloud/`.

**Target Platform**: Windows 11, macOS, and Linux. The CI shard runs on `ubuntu-latest`.

**Project Type**: Single Python project with a `src/` package tree.

**Performance Goals**: The wait helper allows 2.0 seconds for each state change. The accepted-main line is `timeout: float = 2.0` at line 101 of the test file.

**Constraints**: No test weakening, timeout change, retry to green, fixture override, or source bypass in this record. The owned transport exception stays unchanged.

**Scale/Scope**: One test file and one fixture class change, if authorized. This record adds eight Markdown files.

## Constitution Check

*GATE: Must pass before research. Re-check after design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The route is base-5 for 3767, which is `110032`, padded to `00110032`. `.specify/scripts/powershell/spec-route.ps1` line 17 sets base 5. The feature root holds five children or fewer. |
| II. Class-Based Architecture | Pass | This record adds no code. A future change edits the existing `RawOutputDevice` class and adds no wrapper. |
| III. Safety-First | Pass | This record changes no input handling, no destructive operation, and no credential handling. |
| IV. Full Deployment Pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step. No task pushes to `main`. |
| V. Observability and Logging | Pass | The record uses ASCII. The controlled run reads existing structured log events. |
| VI. Inline Comments | Pass | This record adds no code. A future change must comment each changed line. |
| VII. Action Logging | Pass | This record adds no code. A future change keeps the existing log events. |
| Temporary Owned WebSocket Transport | Pass | The record proposes no new owned transport. The existing SDK contract test stays unchanged. The SDK WebSocket package is `mistapi.websockets`. |
| Test Containers | Pass | Not triggered. The controlled run is native and starts no container. |
| File Paths | Pass | The controlled run writes only under `test-artifacts/`. |
| Output Backends, Operational Store, Database Keys, Data Directory | Pass | Not triggered. The record changes no product output, no key, and no store. |
| Container Security and Zscaler | Pass | Not triggered. The record builds and pushes no container. |

## Implementation Outline

The failing path runs from the shell runner to the session state. The order below follows the calls in the accepted-main code.

```text
ShellRunner (runners.py line 45 on current main)
  -> TerminalReading.run (lifecycle/reading.py)
       -> ShellFrameReader.read (transport/shell_client.py)
            -> FrameReader.read (transport/runtime/reader/frame_reader.py)
                 -> KeepaliveController.on_quiet (transport/runtime/reader/keepalive.py)
       -> TerminalOutcomes.finish (lifecycle/outcomes.py)
            -> StreamSession state and reason (sessions/record/session.py)
```

The dead-peer branch raises `ConnectionClosed` with `code=None` and `dropped=True`. `TerminalOutcomes.finish` maps that close to the DROPPED outcome when output already arrived. The test then reads the FAILED state. The DROPPED reason text is the one that the outcome table names.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

The `contracts/` folder is omitted. This change alters no interface, menu, command-line option, or API shape.

### Source Code (repository root)

```text
tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py   # Conditional change, task T008
test-artifacts/3767/                                                # Git-ignored run output, task T006
```

## File-by-File Change Map

| Path | Action | Reason |
| - | - | - |
| `specs/numbered/0/0/1/1/0/0/3/2/3767-raw-shell-history-failed/` | Add eight files | The record for issue 3767. |
| `tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py` | Modify, only after authorization | Change the close timing in `RawOutputDevice.on_connect` only. |
| `test-artifacts/3767/` | Add at run time | Store the controlled-run log and the junit file. Git ignores this folder. |

## Dependencies

- Python 3.15.2 from `uv python install 3.15.2`, as `.github/copilot-instructions.md` describes.
- The dependency set from `requirements-dev.txt`, which the bootstrap script installs.
- No new package. This record changes no dependency manifest.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| The dead-peer hypothesis H1 is wrong. | The controlled run classifies the branch first. A different signature stops the work and starts a new record. |
| A fixture change hides a real ordering defect. | Keep the `FINISHED` assertion and the exact history assertion. Review that output frames precede the close frame. |
| A closing keyword closes the issue before the cause is confirmed. | The orchestrator reviews the pull request body before merge. The analysis record lists this risk. |
| The #3760 and #3761 reservations still apply. | The follow-up checks the reservation status before editing the shared fixture file. |
| The local Python 3.13 result does not match 3.15. | The controlled run uses Python 3.15.2 only. A 3.13 result is not evidence for the pinned environment. |
| The CI runner timing differs from the local run. | Task T-REMOTE-CI watches the remote run. A remote failure stops the merge gate. |

## Rollback Steps

1. For this record, close the pull request without merge and delete the branch `docs/3767-raw-shell-history-failed`.
2. After a merge of this record, revert its merge commit on `main` through a new pull request.
3. For an authorized fixture change, revert the test-file commit through a new pull request.
4. Delete the git-ignored folder `test-artifacts/3767/` when the investigation ends.

## Complexity Tracking

No constitution rule requires a complexity entry for this record.
