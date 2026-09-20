### Fixed

- Repaired the CodeQL verdict register, which pointed at a stale line number and
  failed the required `CodeQL verdict register check` gate on `main`. Alert 211
  moved from line 323 to line 348 of `src/device/_utility_commands_action.py`
  after the handler repair in pull request #3065 added lines above it. The
  flagged statement did not change, so the recorded decision stays valid. This
  failure blocked every open pull request, including pull requests that do not
  touch `src/device`. See issue #3066.
