# Bounded database discovery

MistHelper uses the configured database names on hosts inside and outside the compose network.
It does not replace those names with localhost.

## DNS caller budget

Each shared DNS caller waits at most one second.
The resolver stores successful and failed results for 30 seconds.
It measures cache expiry with a monotonic clock.
After expiry, the next caller checks the name again.
A changed configured name receives its own lookup.

The cache key includes the hostname, address family, socket type, default protocol, and default flags.
The lookup uses no service port.
This permits TCP probes to reuse resolved addresses with their configured ports.

## Finite resolver work

The resolver starts at most two daemon workers.
It admits at most two outstanding queries.
A finite handoff queue does not add work behind two blocked workers.
Concurrent requests for one query share its active result.
The cache holds at most 128 results.

Python cannot interrupt an operating system `getaddrinfo` call.
A caller deadline stops the caller wait, not the underlying lookup.
The blocked lookup retains its worker slot until it finishes.
Late completion does not extend an existing negative cache period.

If both slots remain occupied, a new name receives an explicit capacity failure.
That capacity failure does not create a permanent negative cache entry.
When a worker finishes, a new name can use its slot.
Daemon workers cannot prevent process shutdown.
The close operation also uses a finite join budget.

Caution: an operating system lookup that never returns holds its worker slot.
The caller still returns, but a new lookup needs a free slot.

## DNS and service readiness

DNS success does not prove that a database service is ready.
The central TCP probe uses resolved numeric addresses.
It gives each service one aggregate 0.5-second TCP budget.
It does not perform another DNS lookup through `socket.create_connection`.
It does not cache TCP readiness.

Database drivers keep their configured hostnames and URLs.
They do not receive substituted numeric addresses.
This preserves URL behavior and TLS/SNI.
Driver authentication, request verification, and network handshakes remain separate from the DNS caller budget.

| Boundary | DNS behavior | Later connection behavior |
| - | - | - |
| `DatabaseConfig.from_env` | Each configured name uses the shared one-second budget and 30-second cache. | The method opens no service connection. |
| `polyglot_hosts_unreachable` | It reuses shared DNS results. | Each service has one aggregate 0.5-second TCP budget. |
| ArangoDB writer preflight | It uses the shared resolver before client creation. | The ArangoDB driver keeps its configured URL and connection behavior. |
| Redis writer preflights | Redis TimeSeries and Redis JSON use the shared resolver. | The Redis driver keeps its original hostname and connection behavior. |
| Capture-store preflight | It uses the shared ArangoDB name result before client creation. | The verified ArangoDB client keeps its configured URL and existing request timeout. |

Explicit `MISTHELPER_STANDALONE=true` still skips discovery.
Automatic standalone mode still requires both names to fail resolution.
One resolved backend keeps partial-backend mode and required credential validation active.
CSV and SQLite behavior does not change.
An absent capture-store handle remains retryable after DNS cache expiry.
Existing callers can retain their own standalone or TCP verdict according to their previous policy.

## Connection limits

The ArangoDB writer, Redis writers, and capture store use the same bounded DNS preflight.
The preflight rejects a failed lookup before client creation.
It does not replace a configured URL with an IP address.
The ArangoDB writer retains its declared-index behavior.

The one-second deadline applies to the shared DNS caller and each DNS preflight.
It does not apply to later driver authentication, service verification, or complete router initialization.
A driver can perform its own DNS lookup during a later handshake.
This implementation does not claim a deadline for those handshakes.

## Configuration and evidence

The resolver adds no environment variable or dependency.
`ResolverLimits` defines the existing internal caller, cache, and resource settings for controlled tests.
The dedicated tests use stand-in resolvers and sockets.
They measure real caller time and inspect cache expiry, shared work, resource limits, recovery, and cleanup.
They do not use production DNS or database services.

The implementation lives in [`src/foundation/persistence/db/host_resolver.py`](../src/foundation/persistence/db/host_resolver.py).
The central callers live in [`src/foundation/persistence/db/__init__.py`](../src/foundation/persistence/db/__init__.py).
The requirements and separate publication hold live in the [issue specification](../specs/3318-bounded-database-discovery/spec.md).
The reported Windows measurements remain the evidence in [issue #3318](https://github.com/jmorrison-juniper/MistHelper/issues/3318).
Controlled local evidence is not a new Windows production measurement.
