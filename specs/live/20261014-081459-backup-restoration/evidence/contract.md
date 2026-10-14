# Contract: Backup restoration

## CLI

Menu 306 selects an existing private bundle by displayed identifier.
It selects saved records and explicitly binds the active cloud.
It displays sanitized effects and requires exact `RESTORE`.
Dry run, EOF, interrupt, and cancellation never send settings writes.

## Graphical portal

Use a nested blueprint under the existing protected operations routes.
The page provides dynamic backup and record selectors, cloud binding, preview, typed confirmation, and results.
Use stable `data-testid` attributes.
No file upload, arbitrary filesystem path, complete settings download, or posted settings body is accepted.

List responses expose only bundle identifiers, timestamps, record counts, and scope identifiers.
Preview responses expose only an opaque token, sanitized target metadata, exclusions, counts, and warnings.
Apply requests contain only the preview token and exact confirmation.
Tokens are bounded, expire after ten minutes, bind to a browser session, and permit one application.
Existing address protection and CSRF protection apply to every restore route.

## SDK

Use only settings reads, settings updates, and complete organization site lists.
Every response status and data shape must validate.
No write retry occurs.
Compare the complete writable saved state and relevant identity fields after each write.
Ignore only documented server-managed changes.

## Safety boundaries

Verify the source bundle again at application.
Verify every current recovery record before the first write.
Recheck cloud, membership, and settings freshness before writing.
Refresh each target immediately before its write.
The SDK offers no conditional settings PUT. Document the remaining read/write race rather than claiming atomic cloud updates.
