# Local close research

## Decision

Keep the raw descriptor open until the active receive returns.
Use one runtime per connection so close and receive share ownership.

## Evidence

Clean main `03e609b828d949cc8d983571209d95bd708a7956` reproduces the reported live state under a controlled native schedule.
CPython copies a raw descriptor into `pollfd` before it releases the interpreter lock and calls `poll`.
Local close can abort and close that descriptor before the native call starts.
An unrelated idle socket can receive the same descriptor.
The pending receive then waits on that socket for its original ten-second timeout.
The existing two-second stopped-state assertion fails with `LIVE`.

The session-only diagnostic interposes at the native poll boundary.
It does not replace WebSocket methods.
Complete output is in the session artifact `native-fd-before.log`.
A separate 500-stop probe with descriptor allocation pressure passed.
This proves a reachable race, not the exact native schedule of every prior failure.

## Alternatives

A reader join does not preserve descriptor ownership and changes the stop contract.
A timeout increase hides the race.
An event check alone cannot protect a descriptor already copied by native receive.
An independent lock in each runtime cannot protect two runtime instances around the same socket.
The selected design shares the runtime and aborts before acquiring its receive lock.
