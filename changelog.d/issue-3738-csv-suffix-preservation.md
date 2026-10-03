### Preserve CSV filename suffixes

- **Fixed**: CSV exports preserve an existing `.csv` suffix in every ASCII
  letter case. Menu 64 now writes the advertised `SiteWiFiClients.CSV` filename.
  SQLite table names and other backend identities remain unchanged. Issue #3738.
