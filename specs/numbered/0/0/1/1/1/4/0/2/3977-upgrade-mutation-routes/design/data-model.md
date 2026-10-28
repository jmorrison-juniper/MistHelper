# Data Model: Upgrade Mutation Routes

## Request dependencies

| Field | Meaning | Lifetime |
| --- | --- | --- |
| Operator | The authenticated operator record for the active request | One request |
| Cloud session | The Mist session owned by that operator | Borrowed for one request |
| Database router | The request's persistence boundary | One request, closed at teardown |
| Mutation services | Lazy service construction with the request session and router | One request |
| Action store | The durable ArangoDB journal with actor-scoped records | Shared service, called within one request |

The provider caches one dependency record on the Flask request. A later resolution in that request returns the same record. A new request receives a new router and service factory.

## Mutation records

**Run action** contains the actor scope, run identifiers, requested action, confirmation and preview evidence, idempotency key, action state, and outcome. Existing persistence rules remain unchanged.

**Comparison approval** contains the run identifier, approved and rejected items, operator notes, approval flag, operator identity, and UTC approval time. Existing database updates and audit rules remain unchanged.

## Validation and state rules

- The provider rejects an absent operator or unusable cloud session before it creates request resources.
- The action store must support its existing durable operations before a run mutation begins.
- The existing run-control service verifies authorization, preview evidence, typed confirmation, site locks, and actor scope before it writes.
- A missing dependency or failed write cannot create a successful action or approval response.
