### Fixed

- Cut the container start from about seven minutes to a few seconds. Startup set
  the session owner with one recursive walk of the whole data mount, which held
  14521 files across 19.9 GB on the reporting workstation. The container
  reported `unhealthy` for the whole walk, so an operator could not tell a slow
  start from a failed one. Startup now sets the owner on the paths a session
  writes. See issue #3138.
