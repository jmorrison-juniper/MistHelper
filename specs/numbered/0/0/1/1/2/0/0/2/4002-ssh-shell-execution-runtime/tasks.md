# Tasks: SSH Shell Execution Runtime Package

## Move and update the package

- [x] Move `shell_execution/` under `ssh/runtime/` with `git mv`.
- [x] Update runtime imports, test imports, mock targets, and the T013b path comment.
- [x] Preserve `ShellExecutor` and `_CollectState` without wrappers or aliases.

## Add verification records

- [x] Add the exact old-to-new paths to the symbol-preservation guard.
- [x] Add focused SSH and runtime structure checks with invalid-layout tests.
- [x] Add the issue-specific changelog fragment.

## Validate and commit

- [ ] Run focused tests and required quality gates.
- [ ] Commit with `Closes #4002` and the Copilot co-author trailer.
