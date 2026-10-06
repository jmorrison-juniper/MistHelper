# Feature specification: Portal startup dependencies

**Issue**: #3834

## Problem

Normal startup calls `create_app()` without dependency overrides. The previous
wiring built services during startup from absent `MIST_CLIENT` and `DB_ROUTER`
values. Startup appeared healthy, but registered service routes had invalid
collaborators.

## Required behavior

1. Normal startup stores dependency construction rules only.
2. Startup opens no Mist, ArangoDB, or Redis connection.
3. A protected request validates the signed operator before storage access.
4. One request builds one service graph from its authenticated Mist session.
5. Flask `g` caches the graph for that request only.
6. Request teardown closes each request-owned database client.
7. Teardown does not close the registry-owned Mist session.
8. Complete test overrides keep precedence over production defaults.
9. Missing identity returns the established HTTP 401 response.
10. Unavailable required storage returns the established HTTP 503 response.
11. Capture, upgrade, comparison, and run-control routes resolve dependencies
    only when the request needs them.

## Preserved behavior

This change does not alter authorization, confirmation text, rollback,
responses, audit rules, persistence rules, firmware actions, captures,
comparisons, settle checks, or worker behavior.

## Success criteria

- The default factory starts with no external call.
- An authenticated request receives the existing service classes.
- Two concurrent operators receive different request-owned clients.
- A partial database failure closes its client and starts no cloud call.
- The focused issue tests pass without a production credential.
