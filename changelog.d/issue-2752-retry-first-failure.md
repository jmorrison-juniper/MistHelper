### Preserve first failure evidence in retry loops

- **Fixed**: `APIDataFetcher` logs the first and last HTTP status when all attempts fail, and the port statistics exporter logs the first exception of a site when all retries fail. Part of #2752.
