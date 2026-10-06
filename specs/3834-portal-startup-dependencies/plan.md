# Implementation plan: Portal request resources

## Scope

Add request-owned resource construction to `app/wiring.py`. Use the existing
factory teardown for the owned router.

Do not change a route, a service, the action repository, or storage bootstrap.
Issue #3977 owns later route and service integration.

## Design

`PortalDependencyProvider` holds no external resource. On the first explicit
resolution in an authenticated request, it performs these steps:

1. Read the operator through `current_operator()`.
2. Validate the borrowed Mist session methods.
3. Build `DatabaseConfig` through `DatabaseConfig.from_env()`.
4. Build the real `DatabaseRouter`.
5. Cache an immutable resource record in Flask `g`.
6. Put the owned router in `g.database_router`.

Factory teardown already closes `g.database_router`. The provider never puts
the borrowed cloud session in `g.mist_session`.

## Tests

The focused test package proves startup order, lazy construction,
authentication refusal, request caching, request isolation, teardown ownership,
constructor compatibility, and E2E isolation.

## Validation

Run the focused tests and each changed-file quality gate. Run the test-quality
ratchet after the implementation commit and before the single push.
