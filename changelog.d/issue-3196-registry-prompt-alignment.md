### Fixed

- The web portal now offers one input control for each prompt an operation
  reaches, in the order the operation reads them. Menus 229, 236, and 261 ask
  for their first answer before the site, so each one now shows that choice
  first and the site second (#3196). Menus 211, 212, and 246 reach an
  identifier prompt that rejects an empty answer, so each one now shows a
  control for that identifier instead of reporting a complete run that wrote
  nothing (#3181, #3184).
- Menus 69 and 86 no longer ask for a client. Both export data for a whole
  site and never read a client value. The control they carried could not fill
  for most sites, so the Run control stayed unusable (#3191).
- Menu 241 starts a metrics server that serves until an operator stops it, so
  the portal now names it command-line only instead of starting a run that
  fails after two minutes with a misleading reason (#3182).

### Added

- `tests/unit/web_portal/test_portal_required_controls.py` now fails when a row
  declares a control that no prompt reads. An extra control makes the operator
  answer a question the run discards, and an empty pick list then blocks a run
  for a value the operation never wanted (#3198).
