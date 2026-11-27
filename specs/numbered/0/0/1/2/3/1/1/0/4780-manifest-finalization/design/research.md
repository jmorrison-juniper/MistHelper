# Research: Hardware Manifest Finalization After a File Lock

Each decision names the chosen option, the other options, the reason, and the risk. Each code fact cites a path and a line. The Remote Verification table lists every remote check. The same 82 checks appear in `remote_checks` in `4780-STATUS.json`, in the same order.

## R1. Symptom Chain on Main

- **Decision**: Treat the defect as a durable-state and truthfulness defect. Do not name a lock holder.
- **Facts**:
  - A refused replace retries four times, then raises (rows 2 and 3). `Metadata.write` sets the in-memory status to failed and raises (rows 1 and 5). The durable file keeps the last snapshot (row 8). That snapshot writes the target state `running` (row 7).
  - The artifact status becomes failed in memory (row 16). `finish_parent` ignores the boolean result (row 20).
  - The aggregate target status reads completed when every target completed (row 18). The parent state then reads FINISHED (rows 20 and 21).
  - The CLI partial rule counts target outcomes only (row 30). The CLI then prints `Run status: complete` (row 31).
- **Alternatives considered**:
  - (a) Remove the lock source. Rejected: the issue says not to infer the cause.
  - (b) Add retries. Rejected: retries exist since PR #4924 (rows 2 and 3).
  - (c) Chosen: fix the durable state and the reported status.
- **Reason**: The facts prove the chain from the refused write to the CLI line. The chain holds for every lock holder.
- **Risk**: A lock that never clears still fails the run. Mitigation: bounded finalization, the marker, and the evidence task.

## R2. Lock Holder

- **Decision**: Name no holder. Task T019 collects evidence. Task T020 applies only when the evidence names an in-process reader.
- **Hypotheses (not facts)**:
  - H-1: An in-process reader. Admission scans every run folder (row 11). `owner_pid` reads each `manifest.json` without the record lock (row 12). A live run can hold a read handle when its own replace runs.
  - H-2: An external process. The code comment names a sync client or a virus scanner (row 69). The local checkout sits in a OneDrive folder. That location can hold a file open. This fact is an environment observation, not a code fact.
  - H-3: The archive reader. `Streams.archive` reads `manifest.json` (row 13). This read runs after completion, so it is unlikely to block a replace.
- **Alternatives considered**:
  - (a) Remove the in-process reader now (H-1). Rejected: the change would guess the cause.
  - (b) Wait for evidence before any change. Rejected: the durable-state defect exists for every holder.
  - (c) Chosen: fix the durable state now, collect evidence, and apply a conditional reader fix.
- **Risk**: The lock may last longer than the finalization budget. Mitigation: the marker and the failed parent state.

## R3. Defer or Fail Closed on an In-Run Refusal

- **Decision**: A refused in-run manifest replace defers while the record stays writable (FR-003).
- **Facts**: Each refused in-run write fails the record (row 5). Validation then refuses later hardware saves (row 10). The `replace` docstring states that one refusal must not fail the whole batch (row 69).
- **Alternatives considered**:
  - (a) Keep fail-closed behavior (current). Rejected: one short lock ends the batch.
  - (b) Chosen: defer the write, and fail only at finalization.
  - (c) Retry each in-run write with the full budget. Rejected: each target then waits up to 0.75 seconds while it holds the record lock (rows 9 and 2 through 3). A persistent lock adds that wait to every target.
- **Risk**: After a crash, a native file can exist without a durable manifest entry. Mitigation: later writes and finalization list the file, and the file stays on disk (TEST-07).

## R4. In-Run Retry Budget and Fast Path

- **Decision**: Keep the four-wait budget for the first refusal (row 2). Each later in-run write tries once (FR-001 and FR-004).
- **Alternatives considered**:
  - (a) Use the full budget for each in-run write. Rejected: the total delay grows with the target count under a persistent lock.
  - (b) Chosen: one try after the first deferred write.
  - (c) No in-run retry. Rejected: the short-lock behavior from PR #4924 would end.
- **Risk**: A short lock that recurs after the first deferral gets no wait. Mitigation: finalization retries with seven waits.

## R5. Finalization Budget

- **Decision**: Seven waits of 0.05, 0.1, 0.2, 0.4, 0.8, 1.6, and 3.2 seconds. The total is 6.35 seconds (FR-002).
- **Alternatives considered**:
  - (a) Reuse the 0.75-second budget. Rejected: too short for a lock that lasts beyond it.
  - (b) Chosen: 6.35 seconds.
  - (c) Unbounded retries. Rejected: the CLI and the portal would hang.
- **Reason**: Finalization runs after every target stops (row 68). The wait therefore blocks no target.
- **Risk**: A failed run reports up to 6.35 seconds later. Mitigation: a Caution statement in the operator guide (task T018).

## R6. Terminal Durable State

- **Decision**: Write `finalization-failed.json` when the final replace stays refused (FR-008).
- **Alternatives considered**:
  - (a) Keep only the last complete manifest (current). Rejected: the durable file reads `writing` after the run ends. The issue reports this state.
  - (b) Chosen: a separate marker, written with the atomic replace.
  - (c) Rewrite `manifest.json` in place. Rejected: a reader can see partial content (FR-014).
- **Reason**: The marker uses another file name. A lock on `manifest.json` does not block it.
- **Risk**: A new file appears in the run folder. Mitigation: the archive reads only the record files and `manifest.json` (row 13). The orphan scan reads only `manifest.json` (row 12).

## R7. Parent State on a Failed Finalization

- **Decision**: The parent state becomes FAILED with the reason "The batch output could not be finalized." (FR-012).
- **Alternatives considered**:
  - (a) Keep FINISHED (current). Rejected: the parent hides an output failure (row 21).
  - (b) Chosen: FAILED.
  - (c) A new PARTIAL state. Rejected: it changes a public state for the portal.
- **Risk**: The portal shows failed for a run whose targets completed. Mitigation: the reason names the output failure. The portal reads `artifact_status`, which does not change (row 19).

## R8. CLI Partial Rule

- **Decision**: The CLI prints partial when any run output is not final. It prints one line for each unfinished run (FR-013).
- **Alternatives considered**:
  - (a) Keep the count-only rule (row 30). Rejected: it prints complete for a failed output.
  - (b) Chosen: add the artifact readiness to the rule.
  - (c) A non-zero exit code. Rejected: it adds a new exit contract for one case.
- **Risk**: A run whose targets completed can read partial when its output fails. The change is intended.

## R9. Native File After a Refused Snapshot

- **Decision**: Keep the published file, record it in the run, and report its format as completed (FR-010).
- **Facts**: `Hardware.__call__` holds the record lock, commits the file, and then takes the snapshot (rows 9, 7, and 8). A refused snapshot raises from the manifest write (row 8). `save_hardware` then records the format as failed (row 22). It also omits the file from the per-target list (row 23).
- **Alternatives considered**:
  - (a) Remove the published file. Rejected: it violates the preservation rule.
  - (b) Chosen: keep the file, and report the format as completed.
  - (c) Keep the format failed. Rejected: a valid reply reads as failed, and the operator reruns the target.
- **Risk**: A completed format sits in a run with failed output. Mitigation: the parent state and the CLI status report the output failure.

## R10. Evidence Fields in Events

- **Decision**: Add `errno`, and `winerror` when present, to each refused-write event. Never add a path (FR-011).
- **Alternatives considered**:
  - (a) Add the local path. Rejected: the existing test forbids paths in logs (row 71).
  - (b) Add a full traceback. Rejected: the traceback text holds the local path. The plan records this as a principle V failure.
  - (c) Chosen: integer codes only.
- **Risk**: The change does not meet the traceback clause of principle V. The plan records the gap and a follow-up issue.

## R11. Mist Transport and SDK

- **Decision**: No change. The change does not call mistapi (FR-015).
- **Facts**: The owned WebSocket client class stays at row 42. The constitution allows an owned transport only with SDK insufficiency proof (row 72). This change makes no transport claim.
- **Alternatives considered**:
  - (a) Own a new transport. Rejected: no SDK insufficiency proof exists.
  - (b) Change an SDK call. Rejected: no SDK call changes.
  - (c) Chosen: no change.
- **Not read**: The pinned SDK at `.venv\Lib\site-packages\mistapi` and the Mist OpenAPI file. The record makes no SDK or endpoint claim. A later change that adds one must read and cite both sources.

## R12. Test Approach

- **Decision**: Inject refusals with `LockedReplace` (row 35). Record waits with the `waits` fixture (row 36). Each test runs without real sleeps and without a real lock (FR-017).
- **Alternatives considered**:
  - (a) Real Windows locks. Rejected: the timing depends on the host, so each run differs.
  - (b) Chosen: injected refusals.
  - (c) Mock the whole service. Rejected: it hides the file behavior that the defect depends on.
- **Risk**: The test double differs from a real Windows sharing violation. Mitigation: evidence task T019.

## R13. Linked Work and Overlap

- **Decision**: Branch `fix/4780-manifest-finalization`. Issue #4780 owns the finalization defect.
- **Facts from read-only GitHub checks**:
  - Issue #4780: OPEN. Labels `bug` and `web-portal`. Created 2026-11-11. No comments.
  - Linked PRs: none. The search for "4780" returned PR #974 only. PR #974 is MERGED. Its body reports a test count and does not name issue #4780.
  - PR #4924: MERGED on 2026-11-26. Its body states `Closes #4926`. It added the short-lock retry in `Metadata.replace` (rows 2 and 3).
  - Issue #4926: CLOSED. Title: "Runtime: PermissionError in the batch manifest replace on Windows."
  - Issues #4920, #4931, and #4933: CLOSED. Issue #4773: OPEN. Issue #4773 is the acceptance source for this run.
  - Overlap scan (row 48): the open pull requests change none of the files in the plan.
- **Alternatives considered**:
  - (a) Reopen #4926. Rejected: PR #4924 closed it, and its retry works.
  - (b) Chosen: issue #4780 owns the finalization defect.
- **Risk**: A later pull request can touch the same files. Mitigation: repeat the overlap scan before the pull request (task T-PR).

## R14. Skills and External Sources

- **Skills**: None loaded. No listed skill covers Python file replace on Windows. The issue is not a Podman question and not a Juniper device question.
- **External sources**: No URL was fetched. The Windows behavior of `os.replace` is unverified (U-3).

## Remote Verification

Ref: `main`. The full-tree call returned 11404 entries, and the result was not truncated. Each blob SHA comes from the remote tree or from the contents API. Each cited line came from the remote file content. The table lists 82 checks. The `remote_checks` array in `4780-STATUS.json` lists the same 82 checks in the same order.

| # | Claim | Path | Blob SHA | Result | Line |
|---|-------|------|----------|--------|------|
| 1 | Manifest write failure logs the manifest error event | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 458 |
| 2 | Replace waits 0.05, 0.1, 0.2, and 0.4 seconds | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 461 |
| 3 | Final try raises its own error | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 483 |
| 4 | Staged manifest file name is `.manifest.tmp` | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 452 |
| 5 | Manifest failure sets the record status to failed | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 457 |
| 6 | Finish writes the final manifest | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 264 |
| 7 | Snapshot sets each target state to running | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 135 |
| 8 | Snapshot writes the manifest after each saved format | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 140 |
| 9 | Hardware save holds the record lock before commit | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 121 |
| 10 | Validation refuses a record that is not writing | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 160 |
| 11 | Prepare runs orphan cleanup before admission | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 238 |
| 12 | Orphan owner check reads manifest.json without the record lock | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 595 |
| 13 | Archive reads manifest.json for the ZIP | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 677 |
| 14 | Service root is data/websocket-streams | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 786 |
| 15 | Result write holds the record lock | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 92 |
| 16 | Artifact state becomes failed on a refused manifest write | `src/mist/realtime/websocket_streams/intake/start_request/models.py` | 2051af84d481e092ff5cfc98a8ece7406fb4159b | present | 272 |
| 17 | Finish returns the manifest result as a boolean | `src/mist/realtime/websocket_streams/intake/start_request/models.py` | 2051af84d481e092ff5cfc98a8ece7406fb4159b | present | 250 |
| 18 | Aggregate target status is completed when every target completed | `src/mist/realtime/websocket_streams/intake/start_request/models.py` | 2051af84d481e092ff5cfc98a8ece7406fb4159b | present | 334 |
| 19 | Summary publishes artifact_status | `src/mist/realtime/websocket_streams/intake/start_request/models.py` | 2051af84d481e092ff5cfc98a8ece7406fb4159b | present | 311 |
| 20 | Finish parent ignores the finish result | `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py` | 7b4d167ff9b9c14388742eeefd6d8a3a14aa7ec9 | present | 347 |
| 21 | Batch finished reason text | `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py` | 7b4d167ff9b9c14388742eeefd6d8a3a14aa7ec9 | present | 354 |
| 22 | Save hardware records a failed format after a refused write | `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py` | 7b4d167ff9b9c14388742eeefd6d8a3a14aa7ec9 | present | 799 |
| 23 | Save hardware appends the published file names | `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py` | 7b4d167ff9b9c14388742eeefd6d8a3a14aa7ec9 | present | 792 |
| 24 | Admission binds the batch after the manager accepts it | `src/mist/realtime/websocket_streams/web/services/operations/sessions.py` | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 557 |
| 25 | Admission refusal discards the private run folder | `src/mist/realtime/websocket_streams/web/services/operations/sessions.py` | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 933 |
| 26 | BatchRunResult class | `src/operations/exporting/ex_hardware_inventory/run/batch.py` | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 100 |
| 27 | Run waits for the batch with BatchWatcher | `src/operations/exporting/ex_hardware_inventory/run/batch.py` | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 232 |
| 28 | RunCollector class | `src/operations/exporting/ex_hardware_inventory/operation.py` | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 101 |
| 29 | Run loop returns the flag named `cancelled` | `src/operations/exporting/ex_hardware_inventory/operation.py` | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 116 |
| 30 | CLI partial rule counts target outcomes only | `src/operations/exporting/ex_hardware_inventory/operation.py` | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 305 |
| 31 | CLI prints the run status line | `src/operations/exporting/ex_hardware_inventory/console.py` | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 118 |
| 32 | Final gate reads artifact_status | `src/operations/exporting/ex_hardware_inventory/run/watch.py` | fc086a6ace02b49280dd184c4831bf15d1c0b154 | present | 82 |
| 33 | Test asserts the record fails at the first refusal | `tests/unit/websocket_streams/web/test_ws_artifact_replace.py` | 5ae414bd50b1981677ca0b57de099519608d9dcd | present | 169 |
| 34 | Test expects the last complete manifest after a refused replace | `tests/unit/websocket_streams/web/test_ws_artifact_replace.py` | 5ae414bd50b1981677ca0b57de099519608d9dcd | present | 223 |
| 35 | Test double refuses replace calls | `tests/unit/websocket_streams/web/test_ws_artifact_replace.py` | 5ae414bd50b1981677ca0b57de099519608d9dcd | present | 31 |
| 36 | Fixture records waits | `tests/unit/websocket_streams/web/test_ws_artifact_replace.py` | 5ae414bd50b1981677ca0b57de099519608d9dcd | present | 55 |
| 37 | Manifest failure test keeps partial state and external files | `tests/unit/websocket_streams/web/test_ws_output_boundaries.py` | 3d825760c383d6e6c742bcc7f4156362d3655c8c | present | 167 |
| 38 | Artifact failure test keeps artifact status failed | `tests/unit/websocket_streams/live/sessions/test_ws_session_manager.py` | 504c531665e06d5d7a46ba8546e708dfbf96dc25 | present | 415 |
| 39 | Native files survive expiry and restart | `tests/unit/websocket_streams/web/test_hardware_native_acceptance.py` | 176188efcafd1c9fe1f5193014995992aed7e9f0 | present | 353 |
| 40 | Tests check the run status lines | `tests/unit/ex_hardware_inventory/test_hardware_operation.py` | 98c4fab6e596b00d245652545bd832a59a4ced07 | present | 156 |
| 41 | Orphan admission test checks process ownership | `tests/unit/websocket_streams/web/test_ws_orphan_retention.py` | b8d7c0ea9ad1caed71b35ae6bdc21938d262d321 | present | 16 |
| 42 | Owned WebSocket client class | `src/mist/realtime/websocket_streams/live/transport/stream_client.py` | 391b9ebb688360926e9734d2ed7424354348c498 | present | 198 |
| 43 | Durable write rule forbids success before verified write | `.specify/memory/constitution.md` | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 319 |
| 44 | Five-item rule | `.specify/memory/constitution.md` | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| 45 | Action logging rule | `.specify/memory/constitution.md` | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| 46 | Concurrency work needs a specification | `.specify/memory/constitution.md` | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 436 |
| 47 | Writing style section | `AGENTS.md` | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| 48 | Parallel work rule requires an open PR overlap check | `AGENTS.md` | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 244 |
| 49 | Python 3.15 requirement | `.github/copilot-instructions.md` | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| 50 | Local gates table | `.github/copilot-instructions.md` | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| 51 | Changelog fragment naming rule | `.github/copilot-instructions.md` | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 452 |
| 52 | Lint path variables for mypy, vulture, pydocstyle, and interrogate | `.github/workflows/ci.yml` | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 53 | Writing gate section | `documentation/quality-gates.md` | 6776d334cca5d9b43273473a06da367a65605c6d | present | 277 |
| 54 | Sentence that says manifest.json records partial outcomes | `documentation/operator-guide.md` | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 392 |
| 55 | Fragment naming table | `changelog.d/README.md` | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| 56 | Base five route calculation | `.specify/scripts/powershell/spec-route.ps1` | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| 57 | Five-child guard | `.specify/scripts/powershell/spec-route.ps1` | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 92 |
| 58 | Heading for user scenarios in the spec template | `.specify/templates/spec-template.md` | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 11 |
| 59 | Constitution check heading in the plan template | `.specify/templates/plan-template.md` | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 44 |
| 60 | Format heading in the tasks template | `.specify/templates/tasks-template.md` | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 20 |
| 61 | Notes heading in the checklist template | `.specify/templates/checklist-template.md` | 806657da09d1058823923e346a323b633114971a | present | 35 |
| 62 | Reference record spec exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| 63 | Reference record research exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md` | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 1 |
| 64 | Route folder `specs/numbered/0/0/1/2/3/1/1/0` is absent | `specs/numbered/0/0/1/2/3/1/1/0` | none | absent | 0 |
| 65 | No path that contains 4780 exists | Any path that contains 4780 | none | absent | 0 |
| 66 | Publish stage refuses an existing destination | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 205 |
| 67 | Checked relative path rule for native files | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 301 |
| 68 | Finish parent docstring says finalization runs after every target stops | `src/mist/realtime/websocket_streams/live/sessions/manager/factory.py` | 7b4d167ff9b9c14388742eeefd6d8a3a14aa7ec9 | present | 346 |
| 69 | Replace docstring names a sync client or a virus scanner | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 465 |
| 70 | Test expects the replace to raise after the last try | `tests/unit/websocket_streams/web/test_ws_artifact_replace.py` | 5ae414bd50b1981677ca0b57de099519608d9dcd | present | 98 |
| 71 | Test asserts that log text holds no temporary path | `tests/unit/websocket_streams/web/test_ws_artifact_replace.py` | 5ae414bd50b1981677ca0b57de099519608d9dcd | present | 171 |
| 72 | Owned transport exception requires SDK insufficiency proof | `.specify/memory/constitution.md` | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 282 |
| 73 | Numeric records use the fixed base-5 route under specs/numbered | `.github/copilot-instructions.md` | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| 74 | CLI flow test reads run folder manifests | `tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py` | 45d5e244020455a9c8876841f807d28481482106 | present | 159 |
| 75 | Batch unit test file exists | `tests/unit/ex_hardware_inventory/run/test_hardware_batch.py` | 3f9bf7b59f7f1a04169c7d2eff787c69c09bb2a7 | present | 1 |
| 76 | Project configuration file exists | `pyproject.toml` | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 1 |
| 77 | Test quality settings file exists | `.github/test-quality-config.toml` | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 1 |
| 78 | Test quality baseline file exists | `.github/test-quality-baseline.json` | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 1 |
| 79 | Guardrail baseline file exists in the guardrails folder | `tests/guardrails/process_folder_baseline.json` | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 1 |
| 80 | Record status defaults to writing | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 68 |
| 81 | Output limit is 63 MiB | `src/mist/realtime/websocket_streams/web/services/operations/artifacts.py` | 19249d12238025825c1a208696fff30b2e82c73a | present | 778 |
| 82 | MistHelper.py is the entry point and the menu, with the menu flag | `.github/copilot-instructions.md` | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 155 |

## Linked Work (GitHub, Read-Only)

The linked-work facts appear in R13. Each GitHub read used the account from the environment. No write command ran.

## Sources

Local sources, read in full or by range:

- `AGENTS.md` (repository root) and `.github/copilot-instructions.md`.
- `.specify/memory/constitution.md`, and the four templates in `.specify/templates/`.
- The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. Heads of its spec, plan, tasks, research, analysis, data model, and requirements checklist were read.

Searched by term, then read at the matching lines:

- `documentation/quality-gates.md`, `documentation/operator-guide.md`, `documentation/architecture.md`, `documentation/development-setup.md`, and `documentation/container-deployment.md`.

Source, test, and configuration files named in the Remote Verification table. Each cited line was read.

Not read: the Mist OpenAPI file and the pinned SDK (see R11).

No URL was fetched.

## Unverified

- **U-1**: The lock holder. Reason: no runtime evidence exists. Owner: task T019.
- **U-2**: The `errno` and `winerror` values of the observed `PermissionError`. Reason: the issue names the exception type only.
- **U-3**: The Windows sharing rule behind a `PermissionError` from `os.replace`. Reason: no CPython source was read and no URL was fetched.
- **U-4**: The meaning of "CLI status: incomplete" and "Durable report status: pending" in the issue. Reason: the code has no matching literal. The CLI prints `partial` or `complete` (row 31).
- **U-5**: The longest real lock duration. Reason: no runtime data exists. The 6.35-second budget is a design decision (D-4).
- **U-6**: Whether the CLI and the portal share one process during a batch. Reason: the repository does not state the deployment. This fact changes the likelihood of H-1.
