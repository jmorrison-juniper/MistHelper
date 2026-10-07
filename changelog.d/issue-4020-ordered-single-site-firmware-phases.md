### Changed

- The upgrade capture portal now sends the firmware of one device family inside
  the phase of that family. A gateway that fails to settle holds the firmware of
  the switches and the access points below it, so the site keeps its path to the
  cloud. A refused cloud call ends the run with no retry, and each accepted
  upgrade identifier survives. The portal completes the terminal phase records
  and the post-check capture after a later refusal (issue #4020).
- The firmware plans of one site now leave the service in one order: the
  gateways, then the switches, then the access points. The selection order of
  the operator no longer decides that order (issue #4020).
- The portal now rejects an empty, unknown, or mixed-family firmware plan before
  one cloud write, and the run records the validation failure (issue #4020).
- The portal now persists each accepted version group before it sends the next
  group. A durable operator stop blocks the next firmware call and completes
  through the normal stopped-run path. The accepted-row write now preserves a
  stop that another portal worker stores at the same time (issue #4020).
- The operator stop now writes only the stop fields of the run record, so it
  preserves an accepted upgrade identifier that the submitter stores at the same
  time. One run-scoped gate now covers the stop check, the firmware call, and
  the accepted-row write, so no firmware call starts after the operator asks for
  the stop (issue #4020).
- A stop that an operator sends while the portal asks for the run gate now wins
  that gate, so no firmware call starts after it. A refused cloud call now
  writes its reason inside the same gate. The move of a run into the state
  `stopping` now writes the state alone, so it keeps every concurrent result.
  A stopped run that captured no post-check now names that lost evidence
  (issue #4020).
