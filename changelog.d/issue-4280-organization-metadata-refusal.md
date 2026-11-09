### Organization metadata refusal

- **Fixed**: The export checks the HTTP result before it accepts an organization name.
  The manager logs status, not response contents, exception text, or generated paths. It uses `Unknown` after refusal or invalid metadata. Issue #4280.
