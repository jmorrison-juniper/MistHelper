### Fixed

- The source symbol preservation guard now compares a branch against its own
  merge base instead of the moving `origin/main` tip. A worktree that trails the
  baseline no longer reports a phantom symbol loss. The guard also prints the
  count of modules and the count of package-data files that it read, and it
  names the rebase remedy when the worktree trails the baseline. See issue #3896.
