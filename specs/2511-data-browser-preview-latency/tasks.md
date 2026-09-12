# Tasks

## Completed

- [x] Rename the branch to `perf/2511-data-browser-preview-latency`.
- [x] Create a read-only worktree for commit `29fcb967`.
- [x] Read the prior benchmark harness and reuse it.
- [x] Add a profile harness with `cProfile`.
- [x] Measure state A, state B, and state C with the same harness.
- [x] Confirm duplicate JSON Lines parse work before editing.
- [x] Confirm common-path tail deque append work before editing.
- [x] Repair JSON Lines detection so the first item is reused.
- [x] Remove common-path tail appends after the requested page starts.
- [x] Add unit tests for JSON Lines single-pass detection.
- [x] Add unit tests for high filtered CSV page parity.
- [x] Run the parity harness for states A, B, and C.
- [x] Run local validation commands.

## Follow-up

- [ ] Watch the pull request checks after the push.
- [ ] Remove the `in-progress` label when the substantive checks pass.
- [ ] Merge the pull request with squash when the merge state is clean.
- [ ] Remove the baseline worktree after the merge.
