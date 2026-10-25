# Mutation Route Contract

## Scope

This change keeps existing route paths and success response bodies. It changes how the protected handlers obtain their dependencies.

## Dependency behavior

| Route group | Request dependencies | Refusal behavior |
| --- | --- | --- |
| Firmware start, status, and cancel | Current operator's cloud session and request database router | Return an error when the provider or service is unavailable. Do not call a mutation service. |
| Run-control action and reconciliation | Authenticated actor, request resources, and the existing durable action store | Preserve current authorization, preview, confirmation, site-lock, idempotency, and durable-write checks. |
| Comparison approval | Authenticated operator, request database router, and request audit logger | Return `401` without an operator. Return `503` before a write when a required resource is unavailable. |

The read-only comparison-results route is unchanged. The feature adds no route, request field, response field, or Mist REST endpoint.

## Test boundary

Tests replace the cloud session, router, services, and action store with fakes. A refusal test must prove that the fake mutation method receives no call. Approval tests must ignore an untrusted actor header and audit the authenticated operator.
