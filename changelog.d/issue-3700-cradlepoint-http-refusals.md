### Fixed

- Menu 245 now rejects HTTP refusals and unavailable transport statuses before
  it constructs or writes a Cradlepoint status record.
  Valid HTTP 200 integration status data and empty-body behavior remain unchanged.
  The failure notice names the operation and status without exposing the response body.
  This change repairs issue #3700. Related campaigns #2746 and #2747 remain open.
