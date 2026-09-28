### Development tooling on devtools release v0.5.1

- **Changed**: The development requirements pin release v0.5.1 of
  `misthelper-devtools`, and each caller of a shared workflow pins the same
  commit. The CodeQL workflow calls the shared CodeQL workflow. The CI jobs run
  the `codeql-verdict-register`, `bandit-exclude-check`, `diagram-refs`, and
  `exclusion-drift` commands and the `mermaid-lint` action. The pre-commit file
  adds the `markdown-link-check` hook. Issue #3515.
- **Removed**: The local copies of the CodeQL register, diagram, exclusion
  drift, Mermaid, test shard, and worktree cleanup scripts, their tests, and the
  portable gate template. The `pytest-chunks` and `worktree-cleanup` commands
  replace the shard and cleanup scripts. Issue #3515.
