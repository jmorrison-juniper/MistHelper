### Fixed

- The source symbol preservation guard now compares a branch against its own
  merge base instead of the moving `origin/main` tip. A worktree that trails the
  baseline no longer reports a phantom symbol loss. The guard also prints the
  count of modules, baseline symbols, and package-data files that it read. It
  names the rebase remedy when the worktree trails the baseline. The CI shard
  that runs the guard now fetches the full history. See issue #3896.
