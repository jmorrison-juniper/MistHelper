# Implementation Plan: Hardware Manifest Finalization After a File Lock

**Branch**: `fix/4780-manifest-finalization` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/3/1/1/0/4780-manifest-finalization/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

A refused manifest replace leaves the durable `manifest.json` at `writing`. The in-memory record then fails, and every later target stops. The parent state and the CLI status do not show the failed output. This plan makes four changes. A refused in-run write defers to finalization. Finalization gets its own bounded retry budget. A failed finalization writes a marker, sets the parent to FAILED, and marks the CLI partial. Failure events gain integer error codes. No lock holder is named until runtime evidence exists.

## Technical Context

**Language/Version**: Python 3.15 (`.github/copilot-instructions.md:20`).

**Primary Dependencies**: None new. The change uses the Python standard library and the existing structured logger. The change does not call `mistapi`.

**Storage**: Run folders under `data/websocket-streams/<run id>/` (`src/mist/realtime/websocket_streams/web/services/operations/artifacts.py:786`). Each run folder holds native files, `manifest.json`, and the new `finalization-failed.json` marker.

**Testing**: pytest. Tests inject refusals of `os.replace` and record `time.sleep` waits (`tests/unit/websocket_streams/web/test_ws_artifact_replace.py:31` and `:55`).

**Target Platform**: Windows 11 (the reported platform), macOS, Linux, and the Podman container.

**Project Type**: A portal service and a CLI operation in an existing repository.

**Performance Goals**: Finalization waits at most 6.35 seconds in total. An in-run write waits at most 0.75 seconds for its first refusal. A later in-run write does not wait.

**Constraints**: Product output stays under `data/`. The run folder keeps the existing 63 MiB output limit (`artifacts.py:778`). Each function keeps the five-parameter, five-block, and 25-line limits from the constitution (`.specify/memory/constitution.md:38`).

**Scale/Scope**: One run folder for each batch. The target limit does not change.

## Constitution Check

*Gate: passes before research. Re-checked after design: one rule fails, principle V, with a recorded reason. No other rule fails.*

| Principle or rule | Result | Reason |
|-------------------|--------|--------|
| I. Five-item rule | Pass | No new module and no new direct child in a noncompliant parent. The route folder `specs/numbered/0/0/1/2/3/1` grows from three to four children. `Metadata` reaches five methods, and `BatchArtifactStorage` keeps five. |
| II. Class-based architecture | Pass | The change adds fields and methods to existing classes. It adds no wrapper function. |
| III. Safety first | Pass | Quota and link refusals still fail the record. The marker and the temporary files stay inside the run folder. No new input is added. |
| IV. Full deployment pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step. |
| V. Observability and logging | Fail | Error events keep the exception name and add integer codes (`artifacts.py:458`). A full traceback is not added, because the traceback text holds the local data path. The existing test forbids paths in logs (`test_ws_artifact_replace.py:171`). A follow-up issue must add a redacted traceback. |
| VI. Inline comments | Pass | Each changed line gets an inline comment in the same edit. Tasks T009 to T017 require it. |
| VII. Action logging | Pass | Each finalization replace and each marker write logs an `info` line before and a `debug` line after. |
| Mist transport | Pass | No REST request and no WebSocket transport change. See the Mist gate below. |
| Output backends | Pass | `DataExporter` writes do not change. The CLI report still uses `DataExporter`. |
| Operational store | Pass | Not used. The marker is an artifact file, not a coordination record. |
| Database keys | Pass | No endpoint strategy and no table changes. |
| Data directory | Pass | The marker and the staged files stay in the run folder under `data/websocket-streams`. |
| Container security | Pass | No change to the container user or to data permissions. |
| Zscaler and proxy | Pass | No container build and no push. |
| Menu operations | Pass | No menu is added. `README.md` does not change. |
| Testing | Pass | Eleven test cases cover each user story (see the Test Plan). Existing assertions stay unless the Test Plan revises them. |
| Security findings | Pass | No suppression comment is added. |
| Documentation | Pass | The operator guide sentence and the changelog fragment change in the same branch. |
| Escalation | Pass | Concurrency and persistence work needs this specification (`.specify/memory/constitution.md:436`). |
| Multi-agent git | Pass | Branch `fix/4780-manifest-finalization`. The open-PR overlap scan found no conflict (research R13). |

**Mist Cloud gate**:

- REST methods added: none.
- Owned WebSocket transport added: none. The transport contract tests stay unchanged.
- SDK insufficiency proof: not required, because no transport change exists.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/1/1/0/4780-manifest-finalization/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      manifest-json.md
      cli-status.md
      log-events.md
    checklists/
      requirements.md
      persistence.md
```

The feature root holds five children. The `design` folder holds five children. Each subfolder holds five children or fewer.

### Source Code (repository root)

The change edits existing files only. It adds no source module and no source directory.

### Structure decision

The record uses the managed root `specs/numbered/` and the fixed eight-level base-5 route (`.github/copilot-instructions.md:159`). The route folder `specs/numbered/0/0/1/2/3/1/1/0` does not exist on main, so this record creates `1/1` and `0` below the existing `3/1` folder. Folder `3/1` grows from three to four children.

### Folder debt

Folders `specs/numbered/0/0/1/2` and `specs/numbered/0/0/1/2/3` already hold five children. This change adds no child to either folder. No remediation action is needed for this change.

## Architecture

### Finalization (`BatchArtifactStorage.finish`, `artifacts.py:255-267`)

1. Under the record lock, store the final outcomes and the partial flag.
2. If the output format has reports, publish them. A failed publish sets the status to failed.
3. If the status is not failed, set the status to ready.
4. Replace the manifest with the finalization budget of seven waits.
5. On success, set the complete flag and return.
6. On refusal, set the status to failed and partial, log the finalization error, write the marker, and raise the contract error.

### In-run writes (`Hardware._snapshot` and `BatchArtifactWriter.write_result`)

1. The first refused in-run replace uses the in-run budget of four waits.
2. A refused replace sets the manifest stale flag, logs the error, and returns to the caller. The record stays writable.
3. Each later in-run write tries once, without waits.
4. A quota refusal, a link refusal, or a status refusal still raises. The record stays failed.

### Parent and CLI

- `finish_parent` (`src/mist/realtime/websocket_streams/live/sessions/manager/factory.py:345-355`) sets FAILED when finalization returns False.
- `OrganizationBatchRun.run` (`src/operations/exporting/ex_hardware_inventory/run/batch.py:213-239`) records the artifact readiness of each run.
- `RunCollector` (`src/operations/exporting/ex_hardware_inventory/operation.py:101`) collects the names of unfinished runs. `_collect` (`operation.py:296-306`) sets partial when any run is unfinished.
- `HardwareConsole.finished` (`src/operations/exporting/ex_hardware_inventory/console.py:106-118`) prints one line for each unfinished run before the run status.

### Evidence

- Each refused replace logs `errno`, and `winerror` when Windows gives one.
- No event logs a path or a secret.

## File-by-File Change Map

| Path | Action | Purpose | Requirements |
|------|--------|---------|--------------|
| `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | Modify | Add the `manifest_stale` field. Defer refused in-run writes. Add the finalization budget. Add the marker method. Add error codes. Remove the staged temporary file on refusal. | FR-001 to FR-011, FR-014 |
| `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py` | Modify | Set the parent state to FAILED when finalization fails. | FR-012 |
| `src/operations/exporting/ex_hardware_inventory/run/batch.py` | Modify | Add `BatchRunResult.artifact_ready` and read it after each run. | FR-013 |
| `src/operations/exporting/ex_hardware_inventory/operation.py` | Modify | Collect unfinished run names in `RunCollector`. Set partial in `_collect`. | FR-013 |
| `src/operations/exporting/ex_hardware_inventory/console.py` | Modify | Print one line for each unfinished run. | FR-013 |
| `tests/unit/websocket_streams/web/test_ws_artifact_replace.py` | Modify | Add TEST-01 to TEST-05. Revise TEST-10. | FR-002, FR-003, FR-006 to FR-009, FR-011, FR-017 |
| `tests/unit/websocket_streams/web/test_ws_output_boundaries.py` | Modify | Revise TEST-11. | FR-008, FR-009 |
| `tests/unit/websocket_streams/web/test_hardware_native_acceptance.py` | Modify | Add TEST-06 and TEST-07. | FR-003 to FR-005, FR-010 |
| `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py` | Modify | Add TEST-08. | FR-012 |
| `tests/unit/ex_hardware_inventory/test_hardware_operation.py` | Modify | Add TEST-09. | FR-013 |
| `documentation/operator-guide.md` | Modify | Describe the marker, the partial status, and the wait at line 392. | FR-008, FR-013 |
| `changelog.d/issue-4780-manifest-finalization.md` | Add | One `Fixed` fragment that names issue 4780. | Changelog rule (`.github/copilot-instructions.md:452`) |
| `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | Modify (conditional) | Skip live run folders in `Retention.cleanup_orphans`. Only when task T019 names an in-process reader. | FR-010, FR-016 |
| `tests/unit/websocket_streams/web/test_ws_orphan_retention.py` | Modify (conditional) | Test the skip. Only with the conditional change above. | FR-016 |

## Test Plan

| ID | File | Case | Requirements |
|----|------|------|--------------|
| TEST-01 | `test_ws_artifact_replace.py` | A finalization lock that clears within the budget publishes ready. Waits match the finalization budget. | FR-002, FR-006, SC-001 |
| TEST-02 | `test_ws_artifact_replace.py` | A finalization lock that stays keeps the last complete manifest, sets the record to failed and partial, and writes the marker. | FR-007, FR-008, FR-014, SC-002 |
| TEST-03 | `test_ws_artifact_replace.py` | A marker write that also refuses logs both errors, does not raise an unexpected exception, and leaves the record failed. | FR-008, SC-004 |
| TEST-04 | `test_ws_artifact_replace.py` | A refused write removes its staged file. A directory at the staged path is not removed. | FR-009 |
| TEST-05 | `test_ws_artifact_replace.py` | Error events carry `errno` and `winerror` when present, and no local path. | FR-011, FR-016, SC-004 |
| TEST-06 | `test_hardware_native_acceptance.py` | One refused in-run replace defers. The second target saves. Later in-run writes try once without waits. The final manifest lists both files. | FR-003, FR-004, FR-005, SC-003 |
| TEST-07 | `test_hardware_native_acceptance.py` | A native file published before a refused snapshot stays on disk after expiry and restart, and its format reads completed. | FR-010 |
| TEST-08 | `test_ws_session_manager.py` | A failed finalization sets the parent state to FAILED. | FR-012 |
| TEST-09 | `test_hardware_operation.py` | A run whose output is not final prints one unfinished-run line and the partial run status. | FR-013 |
| TEST-10 | `test_ws_artifact_replace.py` (revised) | A refused in-run write defers. The record stays writing and stale. Finalization then fails the record. This replaces the assertion at `:169` that the record fails at the first refusal. | FR-003, FR-007, FR-017 |
| TEST-11 | `test_ws_output_boundaries.py` (revised) | A failed final manifest also leaves the marker, removes the staged file, and keeps external files. | FR-008, FR-009 |

The existing test `test_a_lock_that_stays_raises_after_the_last_try` (`test_ws_artifact_replace.py:98`) keeps its assertions. It covers FR-001. The existing test `test_a_lock_that_stays_leaves_the_last_complete_manifest_in_place` (`test_ws_artifact_replace.py:223`) keeps its assertions. It covers FR-014. The existing test `test_batch_artifact_failure_remains_failed_after_manifest_write` (`test_ws_session_manager.py:415`) keeps its assertions.

## Logging and Evidence

| Event | Level | Fields | When |
|-------|-------|--------|------|
| `web.artifact.batch.manifest.error` | ERROR | `status` (exception name), `errno`, `winerror` when present | An in-run or final manifest replace is refused |
| `web.artifact.batch.finalize.error` | ERROR | `reason_code` with the value `manifest_not_final` | Finalization fails |
| `web.artifact.batch.marker.error` | ERROR | `status`, `errno`, `winerror` when present | The marker write is refused |
| `web.artifact.replace.retry` | INFO | `errno`, `winerror` when present | Each wait of the replace |

## Dependencies

No new package. No dependency manifest changes.

## Risks and Mitigations

- **R-1**: Finalization can add up to 6.35 seconds to a failed run. Mitigation: finalization runs after every target stops (`factory.py:346`). The operator guide gives a Caution statement (task T018).
- **R-2**: A deferred write can leave a native file without a durable manifest entry after a crash. Mitigation: later in-run writes and finalization list the file. The native file stays on disk. Test TEST-07 covers the file.
- **R-3**: The marker is a new file in the run folder. Mitigation: the archive reads only the record files and `manifest.json` (`artifacts.py:677`). The orphan scan reads only `manifest.json` (`artifacts.py:595`).
- **R-4**: JSON Lines batches also use the finalization budget. Mitigation: the budget is bounded. The operator guide describes the wait.
- **R-5**: The parent state changes to FAILED for a run whose targets completed. Mitigation: the reason text names the output failure. The portal reads `artifact_status` as before.
- **R-6**: The lock may last longer than the budget. The fix would then fail the run without a repair. Mitigation: the marker, the failed parent state, the partial CLI status, and the evidence task T019.
- **R-7**: The test double differs from a real Windows lock. Mitigation: evidence task T019 runs the authorized read-only acceptance on one organization.

## Rollback Steps

1. Before merge, close the pull request, or push a revert commit to the feature branch. Do not force-push.
2. After merge, create a branch from `main`. Revert the squash commit in a new pull request.
3. A run folder that holds `finalization-failed.json` keeps its native files. Remove the marker by hand only when the operator no longer needs the run.

Warning: Deleting a run folder deletes its native files, and the deletion cannot be undone. Keep the folder until the operator confirms that the data is no longer needed.

The manifest format does not change. No data migration is needed.

## Complexity Tracking

No constitution violation needs a tracked exception. The principle V gap is listed in the Constitution Check with its reason.
