# Research: Site Lock Refusal Logging

## Decision 1: Keep log records at the route and lock layers

**Decision**: Record HTTP refusal details in the route layer. Record the six silent lock-module refusal raises where the lock decision occurs.

**Rationale**: The route knows the HTTP status. The lock module knows the lock reason and safe owner digest.

**Alternatives considered**: A single route-only log misses lock-module decisions outside the HTTP route. A single lock-only log cannot report the HTTP status.

## Decision 2: Preserve current response behavior

**Decision**: Add log calls without changing control flow, raises, return values, response bodies, statuses, or decision order.

**Rationale**: Issue #3506 requests an evidence repair, not a lock behavior change.

**Alternatives considered**: Changing refusal handling would widen scope and could weaken the lock.

## Decision 3: Assert on log record structure

**Decision**: Test record levels, logger names, and argument values. Do not match message text.

**Rationale**: Message text can change while the useful record fields remain stable.

**Alternatives considered**: Matching message words can pass after the logger stops emitting records.
