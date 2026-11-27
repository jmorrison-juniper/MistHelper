# Publication Gate Checklist: Isolate Network Routing Support Modules

**Purpose**: Record the conditions that must be met before publication (decision D-13 in `design/research.md`).
**Created**: 2026-11-26
**Feature**: `tasks.md` T-PR and T-MERGE

## Conditions

- [ ] 1. Open draft PR #4208 closes, merges, or stops changing `tests/guardrails/test_src_public_symbol_preservation.py`. Status: not met. PR #4208 is open and draft, updated 2026-11-22.
- [ ] 2. The orchestrator records a narrow handoff for `tests/unit/test_routing_utils.py` from the scope of issue #4728. Status: not met. Issue #4728 is open.
- [ ] 3. The coordinator assigns the serial pull request slot to issue #4006. Status: not met. No assignment appears in the issue comments through 2026-11-11.
- [ ] 4. The refreshed change passes `T-LOCAL-GATES` after a rebase onto current `origin/main`. Status: not met. The gates did not run in this authoring run.
- [x] 5. No new hold appears on issue #4006 after its last comment. Status: met for the check on 2026-11-26. The issue reports a last update on 2026-11-11, and no later comment exists.

## Result

Four of five conditions are not met. FR-021 stays open. T-PR and T-MERGE stay open until all five conditions are met.

## Human Decisions

None. The five conditions use the coordination rules of the repository. They do not fall under the four human categories in section 6 of the brief.
