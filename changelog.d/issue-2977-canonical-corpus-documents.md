### Canonical Juniper corpus payloads

- **Fixed**: Equal bytes from different PDF URLs, names, or categories now share one new stored payload.
  The state and manifests retain every source record and original name.
  Valid aliases resume without another fetch.
  A persistent metadata cache avoids repeated full-corpus hashing.
  Historical files remain unchanged. Issue #2977.
