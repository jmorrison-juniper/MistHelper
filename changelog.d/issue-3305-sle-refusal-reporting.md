### SLE metric refusal reporting (menu 73)

- **Fixed**: Menu 73 reports HTTP refusals at the error level with the status,
  endpoint, and site identifier. It no longer reports a refusal as empty metrics.
  Refusals and exceptions do not create a replacement empty export.
  Successful empty responses retain their empty export.
  Failure logs omit secret values. Issue #3305.
