### Prefer available uv for worktree dependency installation

- **Changed**: Worktree setup selects uv once per invocation and targets the explicit virtual environment interpreter.
  It uses pip only when uv is absent.
  uv children use copy mode and system certificate trust.
  Issue #3399.
- **Fixed**: Working pip mirrors and extra sources remain selected.
  Public fallback excludes inherited and saved extra indexes without changing caller settings or configuration files.
  Each file receives an independent child environment.
  Installation failures stop setup without an installer retry.
  Failed attempts report duration and safe installer, file, and status context.
  Browser trust, account checks, paths, and package pins remain unchanged.
  Issue #3399.
