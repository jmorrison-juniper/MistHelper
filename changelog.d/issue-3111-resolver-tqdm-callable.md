### Fixed

- Menu 34 no longer fails when it reaches its progress bar. The source
  dependency resolver returned the `tqdm` module instead of the `tqdm`
  callable, so every progress-bar call raised
  `TypeError: 'module' object is not callable`. Menu 17 and menu 24 held the
  same latent fault, and an empty data set hid it. The resolver now returns the
  named attribute for each such package. Issue #3111.
