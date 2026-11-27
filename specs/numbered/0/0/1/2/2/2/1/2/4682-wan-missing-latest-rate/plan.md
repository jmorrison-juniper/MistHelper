# Implementation Plan: Report a missing latest WAN rate

**Branch**: `fix/4682-wan-missing-latest-rate` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/2/2/1/2/4682-wan-missing-latest-rate/spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/2/2/1/2/spec.md`. The route comes from `Resolve-SpecFeaturePath` with number 4682 (`spec-route.ps1` line 34, R-71).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Change the rate sample builder so the latest expected interval alone sets `value`. A missing latest value gives `value` None and a reason. The change lands after pull request 4208 merges. It adds five tests, one guide sentence, and one release-note fragment.

## Technical Context

- **Language/Version**: Python 3.15 or newer. `pyproject.toml` requires `>=3.15` (copilot-instructions.md line 20, R-72).
- **Primary Dependencies**: mistapi 0.64.1, pinned `>=0.64.0,<0.65` (R-52). No new package.
- **Storage**: none changed. Existing history stores keep the same fields.
- **Testing**: pytest. The Tests gate is `python -m pytest tests/unit/wan_performance/test_gateway_insights.py` for this change (copilot-instructions.md line 61, R-29).
- **Target Platform**: Windows 11, macOS, and Linux. The change builds no path string.
- **Project Type**: Flask web portal and command-line tool.
- **Performance Goals**: no change. The helper checks at most six interval starts per metric.
- **Constraints**: five parameters or fewer, five blocks or fewer, and 25 lines or fewer per function. Inline comments, action logging, ASCII logs, and STE prose are required.
- **Scale/Scope**: two metrics per selected port per refresh. Six ten-minute intervals per hour for ports. One hourly interval for gateway scope.

## Constitution Check

*GATE: Must pass before implementation starts. Re-check after the change.*

| Rule | Result | Reason |
| - | - | - |
| Five-Item Rule (constitution.md line 40, R-23) | Pass, with recorded debt | The change adds no module or directory. `GatewayInsights._sample` has six parameters excluding `cls` before the change (R-55). The change adds none. |
| Eight-level base-5 route (constitution.md line 58, R-24, and copilot-instructions.md lines 159-161, R-27) | Pass | The route `0\0\1\2\2\2\1\2` follows the algorithm in `spec-route.ps1` lines 4-30 (R-37, R-38). Folder `2/2` gains one child and holds four (R-22). Folders `2/2/2` and `2/2/2/1` hold one child each. The feature root holds five. |
| Class-based design (constitution.md Principle II) | Pass | The new helper is a static method on `GatewayInsights`. |
| Safety-first input (constitution.md Principle III) | Pass | The change adds no prompt and no destructive operation. Existing validators stay in place. |
| Full deployment pipeline (constitution.md Principle IV) | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step. |
| Observability (constitution.md Principle V) | Pass | New log lines use ASCII text and report counts or states only. No secret enters a log. |
| Inline comments (constitution.md Principle VI, line 204, R-25) | Pass with FR-011 | Each touched line receives an inline comment. |
| Action logging (constitution.md Principle VII, line 235, R-26) | Pass with FR-011 | `_sample` has no logging today. The change adds logging to the whole touched function. |
| mistapi only (constitution.md technology constraints) | Pass | The change reuses `getSiteInsightMetricsForGateway` (R-50). It adds no HTTP call. |
| Test containers (container-deployment.md line 141, R-40) | Not applicable | No container starts. The tests run in the project environment. |
| Output backends, data directory, database keys | Not applicable | The change alters no export, output file, or key. |
| Security findings (AGENTS.md, section "Security findings") | Not applicable | No security tool reports a finding for these lines. |
| Documentation (AGENTS.md, section "Documentation", R-77) | Pass | Task T004 updates the guide in the same change. |
| Specifications (AGENTS.md line 345, R-43) | Pass | This record exists. The change touches four files. |
| Changelog (copilot-instructions.md line 451, R-31) | Pass | Task T005 adds one fragment. |
| Live Mist calls (issue 4682) | Pass | No live call ran in the drafting pass. No test calls the live API. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/2/1/2/4682-wan-missing-latest-rate/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      rate-sample.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

```text
src/interfaces/wan_performance/collection/snapshot_client.py
tests/unit/wan_performance/test_gateway_insights.py
documentation/wan-performance.md
changelog.d/issue-4682-wan-missing-latest-rate.md
```

**Structure Decision**: Modify the existing collection module and its test module. Add no package, module, or directory under `src/` or `tests/`.

## Architecture and Trace

The affected path starts at the portal and ends at the builder. Each line number refers to pull request 4208 head `843be63` (R-53 to R-63).

```text
web_portal/app.py line 214 registers wan_performance_bp
src/interfaces/wan_performance/presentation/live_routes.py line 327 handles refresh_port
src/interfaces/wan_performance/collection/live_service.py line 63 calls collect_for_port
src/interfaces/wan_performance/collection/snapshot_client.py line 154 selects the 10m interval
src/interfaces/wan_performance/collection/snapshot_client.py lines 235-246 calls the mistapi method
src/interfaces/wan_performance/collection/snapshot_client.py line 282 selects the last valid value
```

The main path does not have the defect:

- `web_portal/app.py` line 213 registers `wan_dashboard_bp` on main (R-08).
- `src/interfaces/portals/wan_dashboard/routes.py` line 140 handles the insights request (R-09).
- `src/interfaces/portals/wan_dashboard/services/__init__.py` line 597 reads cached insights (R-10). Its rate series keep index positions at lines 314 and 362 (R-12, R-13).
- `src/interfaces/portals/wan_dashboard/static/dashboard.js` line 534 reads the last hourly row (R-15).

## Change Map

| Path | Action | Change |
| - | - | - |
| `src/interfaces/wan_performance/collection/snapshot_client.py` | Modify | Add a static helper that finds the latest expected interval. Change `GatewayInsights._sample` to use it. Add inline comments and action logging. |
| `tests/unit/wan_performance/test_gateway_insights.py` | Modify | Add five test functions after the selected-port tests. Reuse the `responses` helper (R-65). |
| `documentation/wan-performance.md` | Modify | Add one sentence to the missing-value rules near line 152 (R-67). |
| `changelog.d/issue-4682-wan-missing-latest-rate.md` | Add | Add one `### Fixed` heading and one bullet that names issue 4682. |

No file is deleted.

## Design of the Fix

1. Compute the latest expected start. Add `interval_seconds` times `maximum_samples` minus one to `start`.
2. Find the interval whose timestamp is the same instant as the latest expected start. Compare instants, not text.
3. If that interval holds a number, set `value` to that number. Otherwise set `value` to None.
4. Set `missing_reason` to None when `value` is a number.
5. Otherwise set `missing_reason` to "The latest interval has no value." when `raw_values` holds at least one value. Otherwise set it to "The API snapshot has no value.".

The helper receives the points, the start, the interval seconds, and the maximum count. It has four parameters.

## Dependencies

- Pull request 4208 must merge, or close with the file released (D-1).
- No new package. No workflow change. No configuration change.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| Pull request 4208 changes the target lines before its merge. | Task T001 re-reads the target function after the merge. |
| Operators miss an earlier value after the fix. | `raw_values` keeps the earlier values. The reason text explains the gap. |
| The snapshot `partial` flag stays false for a missing latest rate. | D-6 records the choice. Analysis item AN-5 records the residual risk. |
| Response timestamps mark interval ends, not starts. | The current code already rejects that format (R-56 and R-78). Unverified item U-1 remains open. |
| Pull request 4208 closes unmerged. | D-1 names the fallback. Open a new record for `GatewayInsightSampleBuilder.build` on main. |

Caution: An edit to `snapshot_client.py` before the merge conflicts with pull request 4208.

Warning: Deleting a work branch before its pull request exists can remove the only reference to its commits.

## Rollback

Revert the squash commit on main through a new branch and a new pull request.

Caution: A revert restores the defect until a new fix lands. The revert is recoverable.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `GatewayInsights._sample` has six parameters excluding `cls` (R-55) | The port path already calls this signature | A signature change widens the review scope. The change keeps the count and records the debt. |
