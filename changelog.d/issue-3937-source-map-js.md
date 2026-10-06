### The ops portal lockfile uses a safe source-map-js version

- **Security**: The `ops-portal` lockfile now locks `source-map-js` at 1.2.2.
  Version 1.2.1 has the high advisory GHSA-68fv-2mgg-jv7q, and the
  `npm audit` gate failed on each pull request. Issue #3937.
