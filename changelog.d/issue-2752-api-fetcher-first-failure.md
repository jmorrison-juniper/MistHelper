### Preserve first failure status in the API fetcher retry loop

- **Fixed**: `APIDataFetcher` logs the HTTP status of each failed attempt and the first and last status when all attempts fail. Part of #2752.
