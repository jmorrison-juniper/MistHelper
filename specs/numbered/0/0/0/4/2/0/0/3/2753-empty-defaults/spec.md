# Issue 2753 firmware input defaults

## Problem

The firmware upgrade workflow uses an empty default when it reads a site identifier.
An invalid identifier can then reach the Mist API and produce a misleading site result.

## Scope

This batch reviews 36 empty-default candidates in five firmware orchestration modules.
It repairs only the site identifier candidate because the other 35 candidates are deliberate
optional, display, compatibility, or error-state sentinels.

## Requirements

- Validate the site identifier before firmware API calls.
- Treat a missing, blank, or non-string site identifier as a failed site.
- Preserve the existing structured failure result and operator log.
- Do not change the known blind exception handler in `bulk_switch_upgrader.py`.
- Add a behavior test that rejects a non-string identifier.

## Out of scope

- The remaining issue #2753 candidates.
- Credential, organization identifier, and site identifier candidates owned by other issues.
- The deliberate RRM dry-run sentinel.
