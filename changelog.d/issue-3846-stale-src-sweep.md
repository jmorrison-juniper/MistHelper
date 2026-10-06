### Fixed

- The worktree bootstrap now removes each orphaned package directory under the
  source root. A leftover empty directory made ruff read a stale name as a
  first-party package, so a local run reported import-order findings that the
  continuous integration run never reported. The sweep keeps the cache
  directory of the source root, and it keeps any directory that holds a real
  file. See issue #3846.
