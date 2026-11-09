### Organization metadata refusal

- **Fixed**: The export checks the HTTP result before it accepts an organization name.
  The manager logs the status, not response contents or generated paths. It uses `Unknown` after refusal or invalid metadata. Issue #4280.
