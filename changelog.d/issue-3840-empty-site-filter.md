### Added

- The capture portal site picker and the operations portal site list now hide a
  site that holds no hardware. Each page states the hidden count and offers a
  `show_empty` toggle that restores every site. A page hides nothing when the
  device count read is incomplete or returns no record, so no site disappears
  without proof. Issue #3840.
