### Git-reading guards no longer fail inside a full test run

- **Fixed**: Three guards that read git passed alone and failed inside a full
  test run. The editor terminal injects a git configuration set through
  `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_n`, and `GIT_CONFIG_VALUE_n`, and one
  value is empty. On Windows an assignment of an empty string removes the
  variable from the process block that a child reads, so git counted three
  entries, found two, and stopped with `fatal: unable to parse command-line
  config`. The guards now build a git environment that drops an unusable
  configuration set and keeps a whole one. Issue #3022.
