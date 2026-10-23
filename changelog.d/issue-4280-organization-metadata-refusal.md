### Organization metadata refusal

- **Fixed**: Organization name lookup now rejects unsuccessful HTTP results and reports failure without response contents.
  Refused or invalid metadata retains the explicit `Unknown` label. Issue #4280.
