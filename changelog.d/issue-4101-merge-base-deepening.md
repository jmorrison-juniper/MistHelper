### Fixed

- The source symbol preservation guard now deepens a shallow checkout until it reaches the
  merge base, and it names the checkout depth when it cannot reach one. The previous message
  read as a lost module-level symbol, which is a stop-everything event in this repository.
  Issue #4101.
