### Changed

- Renamed the upgrade portal end-to-end site helper from `_first_site_id` to
  `_listed_site_id` in `test_existing.py` and `test_stop.py`. The helper returns
  the identifier of a site that the picker lists, so the name now states the
  result instead of a list position. Issue #3936.
