### Fixed

- `APICoreFetchUtils.all_sites_with_limit` and `all_inventory_with_limit` now raise `APIFetchError` when the Mist API returns an HTTP error instead of silently returning an empty list. (#4762)
