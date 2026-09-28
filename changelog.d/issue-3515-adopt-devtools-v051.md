### Development tooling on devtools release v0.5.2

- **Changed**: The development requirements pin release v0.5.2 of
  `misthelper-devtools`, and each caller of a shared workflow pins the same
  commit. The CodeQL workflow calls the shared CodeQL workflow. The CI jobs run
  the `codeql-verdict-register`, `bandit-exclude-check`, `diagram-refs`, and
  `exclusion-drift` commands and the `mermaid-lint` action. The pre-commit file
  adds the `markdown-link-check` hook. Issue #3515.
- **Fixed**: After a merge, the auto-merge workflow no longer starts a second
  run of `ci.yml`, `codeql.yml`, or `container-build.yml` on a tip that a run
  already covers. The run list of GitHub can answer from old data. The shared
  workflow of release v0.5.2 looks for a run on the tip commit itself. Issue
  #3515 and jmorrison-juniper/misthelper-devtools#32.
- **Removed**: The local copies of the CodeQL register, diagram, exclusion
  drift, Mermaid, test shard, and worktree cleanup scripts, their tests, and the
  portable gate template. The `pytest-chunks` and `worktree-cleanup` commands
  replace the shard and cleanup scripts. Issue #3515.
