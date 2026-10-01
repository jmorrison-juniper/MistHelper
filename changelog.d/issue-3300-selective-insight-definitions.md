### Selective insight definition refresh

- **Fixed**: Site, client, device, and organization insight exports refresh only `insight_metrics`.
  The 24-hour cache rule, CSV columns, metric order, and caller output behavior remain unchanged.
  Failed refreshes retain the first error and HTTP status without reporting success from an existing CSV.
  The full-definition export retains dynamic discovery and special handling.
  See [issue #3300](https://github.com/jmorrison-juniper/MistHelper/issues/3300)
  and related [issue #3266](https://github.com/jmorrison-juniper/MistHelper/issues/3266).
