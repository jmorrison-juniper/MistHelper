### Remove unused container output defaults

- **Removed**: Option 2 removes the unused `OUTPUT_FORMAT=sqlite` declarations
  from the SSH session script, `Dockerfile`, and `Containerfile`. Issue #3314.
- **Fixed**: The SQLite instruction now requires `--output-format sqlite`.
  The CSV default and explicit SQLite selection remain unchanged.
  Compose polyglot configuration and readiness behavior remain unchanged. Issue #3314.
