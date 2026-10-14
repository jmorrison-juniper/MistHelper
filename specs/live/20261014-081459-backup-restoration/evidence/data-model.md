# Data model: Backup restoration

## Bundle

Retain the predecessor format: `created_at`, `record_count`, `sha256`, and `records`.
Each record contains `scope`, `id`, and complete `settings`.
Require exact format keys, unique scope identifiers, valid UUIDs, finite JSON, and a UTC creation time.
The input is a private regular file with one link and the current account as owner.
Reject traversal, symbolic links, public access, excessive bytes, and duplicate JSON keys.

## Plan

Bind the original bundle digest, current cloud, selected records, organization membership, and current complete snapshots.
Hold settings with hidden representations.
Expose only validated scope identifiers, counts, known excluded field names, and warnings.
Order organizations before sites. Require selected parent organizations for selected sites.

## Result

Use three disjoint collections: completed, failed, and remaining.
Remove a target from remaining only when its write and saved-state check succeed or it is the failed target.
A failed target may contain a saved but unverified change.
The remaining targets have no attempted writes.

## State transitions

Selection -> validated preview -> exact confirmation -> fresh reads -> verified recovery bundle -> ordered writes -> verified completion.
Any pre-write failure stops with zero writes.
Any write or saved-state failure stops with a partial result.
No automatic rollback or write retry occurs.
