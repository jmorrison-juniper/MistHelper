# Publication Checklist: Hardware CLI failure reporting

**Purpose**: Confirm each publication step before the pull request opens and before it merges.
**Created**: 2026-11-26
**Feature**: `tasks.md` tasks T-PR, T-REMOTE-CI, and T-MERGE

- [x] Issue 4773 carries the label `in-progress`. The issue JSON read on 2026-11-26 shows the label.
- [ ] Issue 4779 carries the label `in-progress` before T-PR. Open until T-PR completes.
- [ ] The publication branch is named `feat/4773-transceiver-master-report` (decision D-2). Open until T-PR completes.
- [ ] The pull request title is `feat(web-portal): add EX transceiver master report and CLI collection`. Open until T-PR completes.
- [ ] The pull request body contains `Closes #4779` and `Refs #4773` (check C-1). Open until T-PR completes.
- [ ] The changelog fragment keeps the name `issue-4773-transceiver-master-report.md` (`changelog.d/README.md` lines 32 and 33). Open until T-PR completes.
- [ ] The remote tree shows the five changed files with blob SHAs (check C-2). Open until T-REMOTE-CI completes.
- [ ] Auto-merge waits for each required check and for the orchestrator authorization. Open until T-MERGE completes.
- [ ] The worktree is removed only after its status reports a clean state. Open until T-MERGE completes.
