# Request resource contract

## Startup

The default factory installs one provider. The provider holds no live external
resource. The new provider opens no additional external connection at startup.

The existing action repository, service installers, and storage bootstrap keep
their current order and behavior.

## Authentication

The provider reads `current_operator()` before database construction. An absent
operator or unusable borrowed Mist session causes
`PortalAuthenticationError`.

## Construction

One authenticated request receives:

- Its existing operator record
- Its borrowed Mist session
- One owned real `DatabaseRouter`

`DatabaseConfig.from_env()` and `DatabaseRouter` run only at the first explicit
resolution in that request.

## Cleanup

Flask `g.database_router` holds the owned router. Existing factory teardown
closes it once.

The provider does not put the borrowed cloud session in `g.mist_session`.
Teardown does not close that session.

## Integration boundary

`request_dependencies()` is the explicit boundary for #3977. Services and
mutation routes remain unchanged in #3834.

## Overrides

A complete E2E override set returns before provider construction and before
production resource construction.
