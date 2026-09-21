### Fixed

- A container build no longer ignores a change silently. The repository holds
  `Dockerfile` and `Containerfile`, and the two had drifted by 33 lines. Podman
  prefers `Containerfile` and Docker prefers `Dockerfile`, so a change that
  landed in one file repaired one build only. A `podman build` reported success
  while it ignored an edit made to `Dockerfile`. The two files are now
  byte-identical, and a guard test fails when they drift. Issue #3130.
