# Research: Capture Request Dependencies

**Feature**: [spec.md](../spec.md)

## Decision

Use the existing authenticated request dependency provider to construct `CaptureService` on demand.

## Rationale

The provider validates the operator before it opens storage, caches one graph per request, and assigns the database router to the existing teardown lifecycle. The capture service already accepts a Mist client, a database router, and an audit logger.

The default factory currently installs a capture service with missing Mist and database dependencies. The route reads that invalid service directly and does not consult the request provider.

## Alternatives Considered

- Keep the startup service and detect missing attributes in the route. Rejected because every request would need to inspect service internals.
- Build one service during application startup. Rejected because operator sessions and database resources belong to each request.
- Remove the capture-service override. Rejected because tests and existing callers use that injection seam.

## Research Scope

No new Mist endpoint, SDK transport, database schema, or external library is required. The focused tests use fake sessions and routers and make no external request.
