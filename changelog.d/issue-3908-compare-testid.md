### Fixed

- Gave the compare picker alert its own identifier, `compare-refusal`, so a
  browser test no longer matches two elements on that page, and added a site
  identifier to each capture choice, so a test pairs two captures of one site.
  Issues #3908 and #3909.
