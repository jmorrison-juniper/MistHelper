# Live Check Checklist: Editor Import Diagnostics

**Purpose**: Track the owner-run live editor check for the 27 current paths (task T010).
**Created**: 2026-11-26
**Feature**: `spec.md` in this folder

Each open item names its cause. Each item closes only when its evidence row exists.

- [ ] LIVE-01 The editor window opens the worktree root as its only folder (FR-001). Explanation: open. The owner run has not started.
- [ ] LIVE-02 The worktree interpreter is selected for Pylint and the Python extension (FR-002). Explanation: open. The owner run has not started.
- [ ] LIVE-03 The Pylint output shows the working directory and the command source (FR-003). Explanation: open. The output needs a running Pylint server.
- [ ] LIVE-04 Each of the 27 current paths shows zero E0401 diagnostics (FR-004). Explanation: blocked. The macOS Screen Recording permission is missing (comment of 2026-10-31).
- [ ] LIVE-05 Each of the 27 current paths shows zero E0611 diagnostics (FR-004). Explanation: blocked. The macOS Screen Recording permission is missing (comment of 2026-10-31).
- [ ] LIVE-06 One evidence row exists for each current path (FR-005). Explanation: open. The rows follow `design/contracts/editor-evidence.md`.
- [ ] LIVE-07 The evidence rows are posted on issue #4126 with user-profile segments redacted (FR-014). Explanation: open. The post follows LIVE-06.
- [ ] LIVE-08 The issue stays open until LIVE-04 and LIVE-05 pass for all 27 paths (FR-010). Explanation: open. The closure hold applies.
