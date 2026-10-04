### Fixed

- The public symbol guard no longer stops with a `KeyError` after the source
  package move merged. The guard compares the work tree against the
  `origin/main` archive of `src`. That baseline now holds the four domain
  roots, so the guard maps each domain root to itself and keeps the refusal
  for an unknown package name. Issue #3851.
