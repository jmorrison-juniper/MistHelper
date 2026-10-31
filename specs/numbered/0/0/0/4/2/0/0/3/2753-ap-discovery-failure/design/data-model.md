# AP discovery contract

## Site collection

A successful SDK pagination result supplies the ordered site records.
An empty collection is valid only when the read succeeds.
No field or persisted schema changes.

## Failure transition

When site pagination raises, discovery logs the organization context and raises the same exception.
It does not scan a first-page subset.
Migration stops before plan rendering, confirmation, backup, or device updates.

## Preserved boundaries

Site and AP identifier handling remains unchanged.
Successful AP filtering remains unchanged.
Per-site device-read failures remain outside the scope.
