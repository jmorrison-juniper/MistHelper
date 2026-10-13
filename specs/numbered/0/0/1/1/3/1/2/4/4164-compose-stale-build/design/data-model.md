# Data Model: Prevent Unsafe Stale Builds

This change defines no application data entity or persistent data record.

The helper reads the local `HEAD` revision and the fetched `origin/main` revision. It uses their commit relationship only to decide whether a local build may start.

The helper selects either the existing published image name or the local-only image name. It restores the previous environment value after the compose provider exits.
