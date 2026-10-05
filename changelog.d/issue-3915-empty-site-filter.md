### Changed

- The map viewer site picker now hides a site that holds no hardware of any type. The
  `GET /api/maps/sites` response reports the hidden count as `empty_sites_hidden`. The
  `show_empty=1` argument shows every site again. A missing device count hides no site,
  so an API fault cannot remove a real site from the picker. Issue #3915.
- The operations portal and the map viewer now share one `EmptySiteFilter` class, so both
  pickers apply the same rule. Issue #3915.
