# Data model

## Prepared operation

Private fields: complete domain plan, verified backup paths, owner, and source identity.
Public fields: opaque reference, workflow kind, state, creation time, progress, and sanitized scope rows.
States: queued, preparing, ready, applying, complete, partial, failed, cancelled, interrupted.
Only ready can become applying. Confirmation consumes readiness once under a lock.

## Backup

Retain created_at, record_count, sha256, and records.
Each record has scope, canonical identifier, and complete settings.
Per-record parsing and shape checks protect resources without limiting aggregate bytes or sites.
The checksum covers the canonical record sequence. It is not an authenticity signature.

## Progress row

Fields: scope, identifier, organization name, site name, backup status, and application status.
Never include settings, model-independent policy siblings, credentials, or source file paths.
Sort site presentation by case-insensitive name and identifier.

## Lifecycle

Active jobs remain available through valid request waits.
Persistent status distinguishes interruption from completion.
An interrupted apply never resumes automatically. The operator must prepare a new operation.
