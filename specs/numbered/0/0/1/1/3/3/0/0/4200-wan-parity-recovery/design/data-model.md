# Parity and measurement data model

## Comparison record

Required fields: stable row ID, source revision, source location, journey, behavior classification, destination location, evidence, test IDs, and status.
Status is one of unverified, blocked, verified, implemented, tested, or accepted.
Acceptance also requires reviewer, revision, and an approved deviation when applicable.
No absent value receives an inferred default.

## Measurement contract

Required fields: organization, site, gateway, circuit or peer identity, metric, unit, timestamp source, reporting interval, and origin.
Synthetic origin must remain distinct from live origin.
An absent timestamp prevents historical placement.
An absent or zero capacity prevents utilization calculation.
Unknown role or region prevents role or region aggregation.
Resolve gateway history from the full identity in selected gateway, circuit, or peer records.
Read gateway history only when those records resolve to exactly one organization, site, and gateway identity.

## Coverage contract

Record expected intervals, observed intervals, missing intervals, duplicates, gaps, weighting, and completeness.
Sparse samples do not establish elapsed threshold time or availability.
Approve calendar boundaries and interval semantics before calculating durations.
Do not define a 31-day read bound as a retention policy.
Keep event counts and minutes unknown when source evidence is absent or null.
Count zero only when a complete event search reports zero.
Sum event minutes only for hours with both known duration values.
Ignore ordinary records without event metrics when a period also contains event records.

## Storage contract

Reuse the configured application store.
Verify existing natural keys, scoped reads, schema version handling, concurrency, transaction behavior, and outage errors.
Key raw samples by full identity and UTC sample time. Keep sample time separate from collection time.
Treat a replay as unchanged only when all source fields match except collection time.
Keep the first stored payload. Reject changed source data at an existing key.
Keep distinct poll-time samples when their sample timestamps differ.
Define backfill and retention only after capacity and source coverage evidence.
Redis namespace, ownership, serialization, TTL, and outage semantics remain unverified until E8 passes.

## State transitions

Evidence progresses from unverified to verified only after a pinned contract review.
Implementation progresses to tested only after positive and negative assertions pass.
Tested progresses to accepted only after reviewed source comparison.
A changed source or destination revision invalidates affected acceptance decisions until review.
