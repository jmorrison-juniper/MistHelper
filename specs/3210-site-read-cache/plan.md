# Implementation Plan: Reuse the organization site reads for one minute

**Issue**: #3210 | **Spec**: [spec.md](spec.md)

## Design

1. New class `CloudReadCache` in `src/upgrade_portal/runtime/cloud_cache.py`:
   a monotonic clock, a lock for the threads of the server, an ordered map with
   a size bound, copies in and copies out, and no empty answer.
2. `select.default_cloud_read` looks up the key before the software
   development kit call, and keeps the answer after the page walk.
3. `CLOUD_READ_TTL_SECONDS = 60` and `CLOUD_READ_CACHE_LIMIT = 256` sit beside
   `CLOUD_READS`.

An injected reader (every test seam) bypasses the cache, because only
`default_cloud_read` uses it.

## Risks

- A site that the operator adds in the Mist dashboard shows in the picker at
  most 60 seconds later.
- The device count of a site can be one minute old. The inventory page reads
  the live list.
