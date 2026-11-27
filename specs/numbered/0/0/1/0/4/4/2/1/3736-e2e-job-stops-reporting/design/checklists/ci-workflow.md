# CI Workflow Checklist: E2E stall diagnostics

**Purpose**: Check each workflow value that this change keeps or changes.
**Created**: 2026-11-26
**Feature**: `spec.md` (FR-005, FR-006, FR-008, FR-009)

Each item below records a value on `main` at blob `d51efbc13c0f0a2076680030ed8be7ef7cf64523`.
Items marked Open name the implementation task that verifies them.

## Values verified on main now

- [x] Trigger blocks are unchanged. The workflow starts from pull requests, the merge group, pushes to `main`, and manual dispatch.
- [x] `playwright_shards` keeps `timeout-minutes: 20` at line 782.
- [x] The aggregator `playwright` keeps the name `E2E smoke tests` at line 955.
- [x] The aggregator keeps `timeout-minutes: 5` at line 962.
- [x] The aggregator keeps `needs: playwright_shards` and fails when a shard does not succeed.
- [x] The pytest command keeps `--timeout=180` at line 909.
- [x] The shard diagnostics upload keeps `if: ${{ failure() || cancelled() }}` at line 939.
- [x] No `paths-ignore` filter appears in the workflow.

## Planned changes, open until implementation

- [ ] Open: T005. The shard diagnostics path adds `test-artifacts/e2e-stack-dumps.txt` at lines 943 to 946.
- [ ] Open: T006. The cancel message at lines 948 to 952 names the job limit and the concurrency cancel.
- [ ] Open: T007. A guard test reads the diagnostics path and the cancel condition from the workflow.
- [ ] Open: T011. A guard test keeps the shard limit, the aggregator limit, and the pytest flag unchanged.
