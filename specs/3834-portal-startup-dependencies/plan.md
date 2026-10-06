# Implementation plan: Portal startup dependencies

## Scope

Implement the repair in the six approved production files.

- `app/wiring.py` owns request dependency construction.
- `app/factory.py` closes the request-owned database client.
- Capture and upgrade routes resolve their service lazily.
- Comparison routes resolve the service and database gateway lazily.
- Run-control routes resolve the action repository lazily.

Do not change service modules, worker code, destructive controls, or storage
implementations.

## Design

`PortalServiceProvider` stores immutable portal settings. It holds no live
client. On the first protected request, it performs these steps:

1. Read the operator from the existing identity registry.
2. Validate the operator Mist session.
3. Open one verified ArangoDB client.
4. Build a small database gateway for existing service contracts.
5. Build the existing audit, capture, upgrade, settle, and comparison services.
6. Build the existing durable action repository.
7. Cache the complete graph in Flask `g`.
8. Register the owned database client for request teardown.

The provider never closes the borrowed Mist session.

## Tests

The issue test package proves:

- Default startup opens no external dependency.
- A signed request builds the existing service graph.
- Missing identity stops before storage.
- Database failure returns a safe refusal.
- Concurrent requests use different database clients.
- Request teardown closes each owned database client.

## Validation

Run the focused issue tests and related route tests. Run the Python quality,
security, complexity, symbol, changelog, prose, and diff gates that apply.
