# Feature specification: Portal request resources

**Issue**: #3834

## Problem

The portal needs an explicit boundary for request-owned resources. Startup must
not create a second database connection for this future integration.

## Required behavior

1. Normal startup installs one resource provider.
2. The new provider opens no additional external connection at startup.
3. A request validates the existing operator before it constructs storage.
4. An absent or stale identity causes a typed authentication error.
5. One authenticated request owns one real `DatabaseRouter`.
6. Repeated resolution in one request returns the same resource graph.
7. Different request contexts receive different routers.
8. Existing factory teardown closes each owned router once.
9. Teardown does not close the borrowed Mist session.
10. Complete E2E overrides install no production provider or resource.

## Preserved behavior

The action repository and storage bootstrap keep their startup order and
behavior. The four service installers also keep their current behavior.

Services and mutation routes remain unchanged for #3977. This issue adds only
the explicit future integration boundary.

## Success criteria

- the new provider opens no additional external connection at startup.
- Default WSGI startup installs the provider.
- Existing startup storage calls still execute in their current order.
- Authentication failure constructs no database configuration or router.
- Focused tests block all external connections.
- The authorized file list contains no route file.
