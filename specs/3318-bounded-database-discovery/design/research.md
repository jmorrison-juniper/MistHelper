# Research: Bounded database discovery

## Decision: Use finite daemon workers

Python `socket.getaddrinfo` does not accept a resolver deadline.
A TCP socket timeout does not bound the name lookup inside `socket.create_connection`.
A timed-out caller cannot stop the operating system resolver.

Use at most two daemon threads and two outstanding queries.
Retain each timed-out lookup in the active map until its worker finishes.
This prevents duplicate active work for the same name and unlimited work after repeated timeouts.

**Alternatives considered**: A new executor for each request creates unlimited blocked work.
A normal thread executor also joins its workers during process shutdown.
A subprocess resolver adds process transport and packaging behavior that this central repair does not need.

## Decision: Keep a finite cache

Use 30-second monotonic expiry for both successful and failed answers.
Use least-recently-used eviction to limit the cache to 128 query results.
Keep active work separate from cache storage.
Cache eviction must not create a duplicate active lookup.

**Alternatives considered**: A permanent failure cache prevents recovery.
An unbounded dictionary accepts unlimited configured query identities.
A wall-clock deadline changes when the host clock changes.

## Decision: Resolve without a service port

The central DNS check uses `AF_UNSPEC` and `SOCK_STREAM` without a port.
Include hostname, family, and socket type in the key.
Keep default protocol and flags fixed.
Reuse the returned address family, socket type, protocol, and numeric address for TCP probes.

**Alternatives considered**: Calling `socket.create_connection` with the original hostname repeats unbounded DNS.
Replacing configured names with localhost rejects legitimate remote databases.
Treating every host outside a container as unreachable has the same defect.

## Decision: Preserve the existing driver boundary

`DatabaseConfig.from_env` decides standalone mode from DNS, not TCP readiness.
One resolved backend keeps required credential validation active.
The portal correctly retries an absent store handle.
Do not change that retry or cache an absent handle permanently.

The original preparation pass left the owned ArangoDB writer unchanged.
It proved that its raw preflight still blocked in partial-backend mode.
The preserved preparation commit retains that historical evidence.

The coordinator released the Redis and capture-store preflights after fresh exact ownership checks.
The later local source grant releases the inherited ArangoDB preflight on the accepted position-25 predecessor.
All three preflight paths now use the shared resolver.
Preserve the original driver hostnames and URLs.
Do not replace them with numeric addresses, because that change can break TLS/SNI.
Preserve every declared-index and data behavior outside the released preflight.
The local source grant does not authorize publication.

## Decision: Use controlled evidence

Use stand-in resolver results, events, sockets, and a monotonic cache clock.
Measure caller duration with the real monotonic clock.
Release every controlled blocked lookup and join its worker during cleanup.
Do not present this evidence as a new Windows production measurement.
