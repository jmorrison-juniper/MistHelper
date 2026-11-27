# Implementation Plan: WAN history replay safety

**Branch**: `jmorrison-juniper-4200-migrate-mistwanperformance` (candidate branch of pull request #4208) | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/3/1/3/3/4793-wan-history-replay/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

The SQLite and Arango writers on the candidate branch already accept unchanged replays. This plan closes four gaps. The Arango writer does not verify its commit. A rollback error can hide the original error. One API response can overwrite a conflicting duplicate without a report. No committed test covers repeated API samples through the selected-port path. The plan adds no Mist request and no new module.

## Technical Context

**Language/Version**: Python 3.15, the repository standard.

**Primary Dependencies**: `python-arango==8.3.7` (RC-28). Flask serves the portal, and this change does not edit it. No new dependency.

**Storage**: The SQLite file that `HistorySelection.open` returns (RC-47). ArangoDB collections `wan_performance_hours` and `wan_performance_samples` (RC-30, RC-33).

**Testing**: pytest. SQLite tests use real databases under `tmp_path`. Arango tests use `MagicMock`. The selected-port tests patch `GatewayInsights.collect_for_port` (RC-46).

**Target Platform**: Windows 11, macOS, Linux, and the Podman container.

**Project Type**: Bug fix in the existing WAN performance feature under `src/interfaces/wan_performance/`.

**Performance Goals**: No change. One selected-port refresh writes six API samples and one poll sample at most (RC-58).

**Constraints**: The five-child rule (RC-10). No new Mist request (FR-012). A confirmed Arango commit before success (RC-11). Existing structure debt is recorded in Complexity Tracking.

**Scale/Scope**: Three source modules, three test modules, two documents, and this record.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Rule | Result | Reason |
|------|--------|--------|
| I. Five-Item Rule | Pass | No module, class, or folder joins a noncompliant parent. The record route adds one child to `specs/numbered/0/0/1/2/3/1`, which holds three children on `main` (RC-68). The base-5 route rule is in RC-09. Existing debt appears in Complexity Tracking. |
| II. Class-based design | Pass | No standalone function is added. The rollback reuses `ArangoArchive._abort`, a class member (RC-65). |
| III. Safety first | Pass | No keyboard input is added. The new error text names a time and no secret. |
| IV. Full deployment pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step, including the `container-build.yml` revision check. |
| V. Observability and logging | Pass | New log lines use `%s` values and ASCII text. No secret reaches a log line. |
| VI. Inline comments | Pass | Each new executable line carries an inline comment. Tasks T009 to T012 require it. |
| VII. Action logging | Pass | The Arango commit check logs an info line before the commit and a debug line after it. |
| Mist transport | Pass | No REST or WebSocket call is added (FR-012). |
| Output backends | Pass | `HistorySelection.open` still selects the backend from the existing output setting (RC-47). |
| Operational store | Pass | FR-007 makes the Arango upsert verify the commit before it reports success (RC-11). |
| Database keys | Pass | The sample key is the natural key of `SampleMeasurement` (RC-45). No new strategy is needed. |
| Data directory | Pass | Tests use `tmp_path`. Product output stays in the existing SQLite file. |
| Container security | Pass | No container, user, or volume changes. |
| Zscaler and proxy | Pass | This change runs no local `podman push`. |
| Testing | Pass | Seven new tests and ten existing tests cover the change. Tasks T001 to T012 name them. |
| Security findings | Pass | No suppression comment is added. |
| Documentation | Pass | `documentation/wan-performance.md` and `changelog.d/pr-4208.md` change in T013. |
| Audience standard | Pass | The spec and the record use plain language (RC-13). |
| Escalation | Pass | The change touches three source modules and three test modules, so a spec is required. |
| Multi-agent git | Pass | The change uses one candidate branch and no stacked branch. The rebase precedes the push (RC-12). The issue carries `bug`, `web-portal`, and `in-progress`. |

For repository structure and generated files:

- The commit subject and the pull request title use Conventional Commits, for example `fix(wan-performance): reject unconfirmed Arango commits`.
- The change adds one record folder. It edits one existing fragment, `changelog.d/pr-4208.md`.
- Existing folder debt is recorded in Complexity Tracking. No new debt is added to a folder.
- Product output stays under `data/`. Test output uses `tmp_path`.

For a feature that uses Juniper Mist Cloud:

- Every REST request uses a working mistapi method. This change adds no REST request.
- The feature owns no WebSocket transport.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/1/3/3/4793-wan-history-replay/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      sample-replay.md
    checklists/
      requirements.md
```

### Source Code (repository root)

| Path | Action | Change |
|------|--------|--------|
| `src/interfaces/wan_performance/integration/arango_history.py` | Modify | Verify the commit result in `ArangoHistory.upsert` (FR-007). Reuse `ArangoArchive._abort` in the rollback branch (FR-008). |
| `src/interfaces/wan_performance/integration/record_codec.py` | Modify | Add the source time to the changed-data error text (FR-013). |
| `src/interfaces/wan_performance/collection/snapshot_records.py` | Modify | Reject two different values for one metric and timestamp in `SnapshotRates._rate_samples` (FR-009). |
| `tests/unit/wan_performance/test_history_repository.py` | Modify | Add tests N1, N2, and N3. Return True from the mocked commit in three existing Arango tests (FR-002). |
| `tests/unit/wan_performance/test_snapshot_records.py` | Modify | Add tests N4 and N5 (FR-009). |
| `tests/unit/wan_performance/test_live_service.py` | Modify | Add tests N6 and N7 with real SQLite under `tmp_path` (FR-010, FR-012). |
| `documentation/wan-performance.md` | Modify | State the rules of FR-004, FR-007, and FR-009 in the raw sample section (lines 437 to 443). Align the Arango commit sentence (line 46) (FR-014). |
| `changelog.d/pr-4208.md` | Modify | Name the within-response rule in the #4793 sentence (line 19) (FR-014). |
| `specs/numbered/0/0/1/2/3/1/3/3/4793-wan-history-replay/` | Add | This record. |

Not changed: `src/interfaces/wan_performance/integration/sqlite_history.py` (verified in T001), `src/interfaces/wan_performance/collection/live_service.py`, `src/interfaces/wan_performance/presentation/live_routes.py` (Decision D-6), `src/interfaces/wan_performance/integration/history_repository.py`, and `src/interfaces/wan_performance/collection/snapshot_client.py`.

## Architecture

The refresh path on the candidate branch:

```text
POST /refresh-port  (live_routes.py, lines 326 to 343)
  -> LiveService.refresh_port  (live_service.py, lines 56 to 83)
  -> GatewayInsights.collect_for_port  (snapshot_client.py, line 121)
  -> SnapshotRecords.build_samples -> SnapshotRates._rate_samples  (snapshot_records.py, lines 230 to 255)
  -> HistorySelection.open  (history_repository.py, lines 212 to 219)
  -> SQLiteHistory.upsert  (sqlite_history.py, lines 103 to 157)
     or ArangoHistory.upsert  (arango_history.py, lines 133 to 183)
  -> SampleReplayPolicy  (record_codec.py, lines 400 to 431)
```

The SQLite path checks each sample key inside one transaction (RC-32). The Arango path checks each sample key inside one transaction (RC-34). Both paths reject a changed payload (RC-37, RC-38).

## Complexity Tracking

Constitution Principle I requires this table. Each row names an existing violation in a touched module. Each row also names a separate remediation action.

| Violation | Location | Why it stays | Simpler alternative rejected because | Remediation action |
|-----------|----------|--------------|--------------------------------------|--------------------|
| `ArangoHistory.upsert` spans 51 lines, and the limit is 25 | `arango_history.py`, lines 133 to 183 | The batch writes hourly and sample documents in one transaction. | A helper method makes `ArangoHistory` six methods, and the limit is five. | Open a follow-up issue. Move batch assembly and sample replay into a helper class in a nested package. |
| `SnapshotRates._rate_samples` spans 26 lines, and the limit is 25 | `snapshot_records.py`, lines 230 to 255 | The function groups two metrics by timestamp. | A helper method makes `SnapshotRates` six methods, and the limit is five. | Open a follow-up issue. Move the grouping into a helper class in a nested package. |
| `record_codec.py` holds five top-level classes, and the limit is five | `record_codec.py` | The module holds the existing codecs. | A new exception class becomes a sixth child. Decision D-6 defers it. | Open a follow-up issue. Move `SampleReplayPolicy` into a nested package. |
| `ArangoHistory` holds five methods, and the limit is five | `arango_history.py` | The class holds the public history API. | A new method breaks the limit. | Covered by the first remediation action. |

## Dependencies

- `python-arango==8.3.7` (RC-28). Its `commit_transaction` returns `bool` (RC-63).
- The local gate tools in `requirements-dev.txt`, named in `.github/copilot-instructions.md` (RC-16).
- The candidate branch of PR #4208. Its merge waits for the owner decision in Decision D-8.
- Issue #4200 stays open until the owner closes the feature scope.

## Risks and Mitigations

| Risk | Effect | Mitigation |
|------|--------|------------|
| The candidate branch conflicts with `main`. GitHub reports `CONFLICTING`, and the branch is 52 commits behind. | The rebase stops, or a large conflict forces a restart. | Rebase first in T-PR. `AGENTS.md` says to abandon a branch when a conflict covers more than 20 lines. Stop and report instead. |
| A changed source value blocks a whole batch. | A refresh fails until the API sample leaves the window. | Decision D-2 keeps the rule. FR-013 names the source time in the error. Open a follow-up issue for operator handling. |
| A live API response gives two values for one metric and timestamp. | `_rate_samples` rejects that response. | Decision D-3 keeps the rule. Identical duplicates still pass (test N5). |
| A driver returns a value other than True from the commit. | A write fails after a successful commit. | The pin RC-28 and the upstream source RC-63 fix the return type. Test N1 covers the False case. |
| Mocked Arango tests return a non-True commit. | Three existing tests fail. | Task T009 sets the commit mock to return True in those tests. |
| The portal shows generic text for a conflict. | The operator cannot tell the cause from the page. | Unresolved item U-1 in `analysis.md`. Open a follow-up issue. |
| The unfinished #4200 feature reaches `main`. | Users see incomplete WAN pages. | Decision D-8 requires owner approval before the merge. |
| Structure debt grows. | Review effort rises. | Complexity Tracking names each touched violation with a remediation action. |

## Rollback Steps

1. Before the merge, remove the fix commits from the candidate branch with `git revert`, and push without force.
2. After the merge, open a new pull request from `main` that reverts the squash commit.
3. If only the Arango commit check fails in production, revert that check commit. Keep the tests that document the gap.

Warning: a force push rewrites the candidate branch. A force push can remove commits that another agent added.

Caution: a revert of the squash commit also removes this record folder. Keep the folder when the revert changes only code.

## Contracts

The folder `design/contracts/` holds one contract. The file `sample-replay.md` defines the write rules, the error texts, and the logging rules for the three writers.

## Next Step

Run the tasks in `tasks.md` in order. Phase 2 tests come before Phase 3 changes. Each Phase 2 test that targets missing behavior (N1 to N4) must fail before its Phase 3 change.
