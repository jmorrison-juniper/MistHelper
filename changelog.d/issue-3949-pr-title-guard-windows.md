### Fixed

- The pull request title guard test now accepts the Windows error class for a
  directory open and for an absent parent path. Windows raises
  `PermissionError` and `FileNotFoundError` where Linux raises
  `IsADirectoryError` and `NotADirectoryError`. The guard behavior does not
  change, because both platforms return the same exit code and the same
  message. Issue #3949.
