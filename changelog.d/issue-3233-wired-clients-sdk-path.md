### Fixed

- Client pick lists in the portal now hold the wired clients of a site. The
  route called a function from the wrong SDK module, so every wired query
  failed, and a site with only wired clients offered an empty list (#3233).

### Added

- `tests/unit/web_portal/test_portal_sdk_calls.py` resolves every Mist SDK
  call in `web_portal/` against the installed SDK. It found one more missing
  function, in the Maps page, which #3236 tracks (#3233).
