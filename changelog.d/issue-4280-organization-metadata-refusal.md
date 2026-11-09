### Organization metadata refusal

- **Fixed**: The export checks the HTTP result before it accepts an organization name.
  The manager logs status. It excludes response contents, exception text, and generated paths. It uses `Unknown` after refusal or invalid metadata. Issue #4280.
