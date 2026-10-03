# Contracts: Bounded database discovery

## Resolver

The caller receives immutable resolved socket address records or an empty result with an explicit error.
The default caller budget is one second.
The positive and negative cache period is 30 seconds.
The key includes the actual hostname, family, and socket type.
Invalid resolver configuration raises a field-specific error.
Expected DNS errors, timeouts, and capacity refusals have structured diagnostics.
Worker capability errors remain visible rather than appearing as successful resolution.

The resolver creates at most two daemon workers and admits at most two outstanding queries.
A finite handoff queue creates no extra job behind two blocked workers.
A worker owns its slot until the operating system call finishes.
A bounded close operation never waits indefinitely.

## Central configuration

Explicit `MISTHELPER_STANDALONE=true` skips discovery.
Automatic standalone mode still requires both names to fail resolution.
One resolved name preserves partial-backend mode.
Required credential validation remains unchanged.
No configured name changes to localhost or to a container-only decision.

## Central TCP probe

The probe resolves through the shared cache.
It constructs sockets from the resolved address family, type, and protocol.
It connects to numeric addresses with the configured port.
The TCP phase has one aggregate 0.5-second budget for all returned addresses.
DNS success alone does not mean that a service is ready.

## Released preflight and driver boundary

The ArangoDB, Redis, and capture-store DNS preflights share the central resolver.
They retain original driver hostnames, configured URLs, TLS/SNI, and error types.
The inherited ArangoDB change applies only to its DNS preflight and necessary imports.
Declared-index behavior and all other writer logic remain unchanged.
The repair makes no one-second claim for driver network handshakes.

## Validation isolation

Every new resolver test uses a controlled lookup.
Every new TCP test uses a controlled socket.
No live production DNS, database, Mist API, or firmware call is permitted.
Controlled blocked lookups must finish after release.

## Delivery

The local source grant permits a verified local commit on the accepted predecessor.
Any push or pull request requires a separate explicit publication decision.
Protected merge and exact merged-main tests remain later delivery phases.
