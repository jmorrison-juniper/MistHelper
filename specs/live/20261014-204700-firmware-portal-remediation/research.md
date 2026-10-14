# Research

## Integrated workspace

Decision: Add dedicated category rows without making destructive menus generically runnable.
Rationale: The current category builder omits both menus and operations.html adds unrelated top-level links.
Alternative rejected: An iframe or navigation shortcut does not retain the established workspace interaction.

## Backup scale

Decision: Preserve the legacy envelope and stream records with per-record structural validation.
Rationale: The writer already produces larger valid files. The reader alone imposes 8 MiB and 1,000-record limits.
Alternative rejected: Removing all parsing protection permits unbounded untrusted records.

## Request control

Decision: Connect the settings SDK boundary to existing shared API usage and adaptive pacing.
Rationale: Direct PolicyApi calls currently bypass application pacing.
Alternative rejected: A separate counter disconnected from actual usage cannot account for concurrent consumers.

## Long jobs

Decision: Use bounded background execution, persistent sanitized progress, and single-use private plans.
Rationale: Synchronous requests and ten-minute previews fail during valid long waits.
Alternative rejected: Automatically replaying writes after process interruption can repeat uncertain changes.

## Production evidence

The parent confirmed one 17,402,805-byte backup with mode 0600.
The connected restore page reports the exact 8 MiB error and has no selectable records.
The connected policy page shows duplicate organization identifiers and visible unchecked version selectors.
No production settings were read into this repository. No connected settings write occurred.
