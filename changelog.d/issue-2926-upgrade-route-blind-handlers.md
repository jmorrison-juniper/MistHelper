### Fixed

- The upgrade portal now names the cause when a site inventory read, a session
  site lock write, or a run state read fails. Each of the three handlers wrote
  one warning that named the site or the run and nothing else, so an operator
  could not tell a refused token from a timeout from a damaged record. Each one
  now carries the class, the message, and the trail of the fault at the same
  severity as before (issue #2926).
