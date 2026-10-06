### Fixed

- The SSR command verifier now ignores fenced examples before it reads inline
  commands. It reports the checked command count and fails when it finds no
  commands or cannot read a required input. Issue #3947.
