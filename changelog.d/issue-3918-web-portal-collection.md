### Fixed

- The web portal prompt audit test now skips when the optional
  `misthelper_devtools` prompt audit tool is absent. A module-level import
  stopped collection of the whole `tests/unit/web_portal` directory. See
  issue #3918.
