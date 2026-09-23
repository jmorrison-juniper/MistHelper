### Fixed

- The operations page now offers a site control for every operation that needs
  one. Thirty-three operations reached a site prompt with no control on the
  page. Each one printed all 143 sites to the log, read a closed input stream,
  and failed with "No site selected". A full sweep proved that every one of the
  thirty-three failed every time. Issues #3179, #3151, and #3152.

### Added

- `tools/prompt_audit.py` reports the interactive prompts that each portal
  operation reaches. It reads the menu table, walks the call graph of each
  handler, and names the prompts in order. A guard test reads the same report,
  so a new operation that needs a control cannot ship without one.
