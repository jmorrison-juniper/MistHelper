### Recover stale portal reads safely

- **Fixed**: The portal retries a stale GET or HEAD connection once, never retries a write, and reports failed pick-list reads. Issue #3732.
