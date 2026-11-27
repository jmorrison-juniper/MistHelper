# Implementation Plan: WAN Duplicate Sample Coverage

**Branch**: `fix/4681-wan-duplicate-sample-coverage` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `specs/numbered/0/0/1/2/2/2/1/1/4681-wan-duplicate-sample-coverage/spec.md`. The route is the eight-digit base-5 encoding of issue 4681.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The fix counts each expected interval once in the 10-minute gateway path. It rejects a conflicting duplicate before publication. The summary adds a sample-count guard. The defect exists only on the PR #4208 head, so the fix waits for that pull request.

## Technical Context

**Language/Version**: Python 3.15. See `.github/copilot-instructions.md`, section "Language and environment", line 18.

**Primary Dependencies**: mistapi 0.64.1 installed at `.venv\Lib\site-packages\mistapi-0.64.1.dist-info`. The pin is `mistapi>=0.64.0,<0.65`.

**Storage**: None for this fix. Snapshot data stays in memory. Persistence is unchanged.

**Testing**: pytest through `python -m pytest`. Unit tests live in `tests/unit/wan_performance/`.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Python web portal backend with collection and domain packages.

**Performance Goals**: Unchanged. Each 10-minute metric reads at most six points.

**Constraints**: Five-item rule. Five parameters or fewer per function. Twenty-five lines or fewer per function. Inline comments on each changed line. Action logging. ASCII log output.

**Scale/Scope**: Two source files, two test files, one documentation file, and one changelog fragment.

## Constitution Check

*Gate result: fail now. Pass after PR #4208 releases both files.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The fix adds no file and no directory child. PR #4208 raises `collection/` and `domain/` to six children. Both are recorded as existing debt. |
| II. Class-Based Architecture | Pass | The fix edits methods in existing classes. It adds no standalone function. |
| III. Safety-First | Pass | Each timestamp and value passes validation before use. The input path does not change. |
| IV. Full Deployment Pipeline | Pass (planned) | Tasks `T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, and `T-MERGE` cover each step. |
| V. Observability and Logging | Pass (planned) | New log lines use ASCII. They show counts and timestamps only. |
| VI. Inline Comments | Pass (planned) | Each changed executable line gets a same-line comment. |
| VII. Action Logging | Pass (planned) | `GatewayInsights._sample_points` logs before validation and after it. |
| Technology: mistapi only | Pass | The request does not change. The code makes no direct HTTP request. |
| Technology: owned WebSocket transport | Not applicable | The fix adds no WebSocket transport. |
| Technology: dependencies | Pass | No manifest changes. The `pip-audit` gate does not apply. |
| Technology: primary keys | Pass | Points keep the timestamp as the natural key inside one hour. No new key appears. |
| Technology: containers | Not applicable | No container runs for this fix. |
| Documentation | Pass (planned) | `documentation/wan-performance.md` gets the coverage rule. `README.md` has no WAN text. |
| Release notes | Pass (planned) | One fragment: `changelog.d/issue-4681-wan-duplicate-sample-coverage.md`. |
| SpecKit escalation | Pass | The fix touches two source files and two classes. This spec and plan apply. |
| Branch naming | Pass (planned) | The branch is `fix/4681-wan-duplicate-sample-coverage`. |
| Required labels | Pass | Issue #4681 carries `bug`, `web-portal`, and `in-progress`. |
| One open pull request per file | Fail now | PR #4208 owns both files. The owner holds issue #4681 until the release. Pass after the merge. |

## Architecture

The data path for one 10-minute port sample runs in this order:

1. `GatewayInsights._collect` selects the gateway and the port.
2. `GatewayInsights._metrics` calls the SDK once for each rate.
3. `GatewayInsights._sample` builds one insight sample for each rate.
4. `GatewayInsights._sample_points` validates timestamps and values. The fix changes this step.
5. `GatewayInsights._utilization` pairs the receive and transmit points.
6. `GatewayInsights._congestion_metric` reports minutes only from six known intervals.
7. `CalendarSummaries` builds hourly measurements.
8. `CongestionDurations._threshold` adds minutes only for complete hours. The fix changes this step.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/2/1/1/4681-wan-duplicate-sample-coverage/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
    checklists/
```

### Source Code (repository paths)

| Path | Action | Change |
| - | - | - |
| `src/interfaces/wan_performance/collection/snapshot_client.py` | Modify | `GatewayInsights._sample_points`, PR #4208 head lines 309 to 328. Keep one point for each expected interval. Reject a conflicting duplicate. |
| `src/interfaces/wan_performance/domain/summary.py` | Modify | `CongestionDurations`, PR #4208 head lines 390 to 423. Add the class attribute `SAMPLES_PER_HOUR` with value 6 after the class docstring. Require `metric.sample_count == cls.SAMPLES_PER_HOUR` in `_threshold`. |
| `tests/unit/wan_performance/test_gateway_insights.py` | Modify | Add three duplicate tests, two congestion tests, and one utilization test. |
| `tests/unit/wan_performance/test_calendar_summaries.py` | Modify | Add two congestion tests for five samples and six samples. |
| `documentation/wan-performance.md` | Modify | Update lines 321 and 431 with the one-count rule and the conflict rule. |
| `changelog.d/issue-4681-wan-duplicate-sample-coverage.md` | Add | One `###` heading and one `**Fixed**` bullet that names issue #4681. |

No module is added or deleted. No top-level name is added to `snapshot_client.py` or `summary.py`.

### Design of the Snapshot Fix

- Keep the expected-interval set and the membership check at PR #4208 head lines 320 to 323.
- Normalize each point with the existing rate factor and `_rate_value`.
- Keep one normalized value for each timestamp.
- Raise `ValueError` when a repeated timestamp has a different normalized value.
- Return one point for each expected interval, in timestamp order.
- Log an `info` line before the validation and a `debug` line after it. Log counts only.

The count, coverage, utilization, alignment, and congestion code read the unique points. Their logic needs no change. Warning: a repeated point left in the list inflates `sample_count` and `coverage_fraction`. The fix must remove the repeat before those lines run.

## Complexity Tracking

| Violation | Status | Reason | Remediation |
| - | - | - | - |
| `GatewayInsights._sample_points` has six parameters | Touched existing violation | The fix keeps the signature to limit the change. | Separate issue. Reduce the signature with a contract tuple. |
| `GatewayInsights` has more than five methods | Touched existing violation | The class already exceeds the limit. The fix adds no method. | Separate issue. Split the gateway insight code. |
| `collection/` and `domain/` have six children | Existing debt from PR #4208 | PR #4208 adds the sixth child. The fix adds no child. | Separate issue after PR #4208 merges. |
| `summary.py` has twelve top-level names | Existing debt from PR #4208 | The module has eleven classes and one logger. The fix adds an attribute, not a top-level name. | Separate issue. |

## Dependencies

- PR #4208 merges or releases both affected files. This dependency blocks implementation.
- The mistapi 0.64.1 SDK in `.venv\Lib\site-packages\mistapi`.
- The Python 3.15 environment. Bootstrap steps appear in the `.venv` section of `documentation/development-setup.md`.
- The existing gateway insight fixture helper in `tests/unit/wan_performance/test_gateway_insights.py`, at lines 693 to 711.
- `documentation/wan-performance.md`, which PR #4208 adds.

## Risks and Mitigations

- Caution: A change to a PR #4208 file causes a merge conflict. Mitigation: FR-012 and task T002 hold the fix until the release.
- Risk: PR #4208 changes its lines before the merge. Mitigation: task T001 repeats the remote checks, and task T003 reads the merged code again.
- Risk: Mist never repeats a timestamp. Mitigation: the fix is defensive. The assumption appears in `spec.md`.
- Risk: A conflicting duplicate stops the scheduled refresh. Mitigation: the refresh logs the failure. The next scheduled run tries again.
- Risk: The summary guard drops a valid six-sample hour. Mitigation: task T005 and success criterion SC-002 keep the positive case.
- Risk: The documentation drifts from the code. Mitigation: FR-011 and the `git grep` check in task T011.

## Rollback Steps

1. Create a revert commit for the fix on `main`.
2. Confirm that the revert restores the prior `_sample_points` body in `snapshot_client.py`.
3. Remove the changelog fragment in the same revert if the release notes no longer describe the change.

Warning: A force push rewrites the shared history of `main`. Create a revert commit instead.

## Contracts

- `design/contracts/insight-sample.md` defines the Mist insight request, the response, and the normalized sample.
- `design/contracts/congestion-summary.md` defines the rule that admits an hour to congestion durations.
