### Fixed

- The operation labels no longer show internal tracking numbers such as
  `issue #1802` and `spec 899 / issue #1407`. Fifteen labels changed in the
  portal, on the command line, and in the menu reference (#3219).
- Menu 236 now promises 33 site count operations, which is the number its
  chooser offers. The label said 32 (#3219).

### Added

- `tests/unit/web_portal/test_portal_label_accuracy.py` compares each promised
  operation count against the table that its chooser prints, and it rejects an
  internal tracking number in any label (#3219).
