### Fixed

- Issue #3388: the upgrade option mapper refuses non-ASCII digits and excessive representations with a named control error.
  The refusal does not repeat the entered value or Python conversion advice.
  Finite fields use their existing maximum to determine the raw digit width.
  Single-site failure counts and no-clock epoch replay retain their unbounded business ranges.
  These two fields use the active Python representation limit and preserve its disabled behavior.
  The organization percentage reader applies the same safe refusal before its earlier normalization.
