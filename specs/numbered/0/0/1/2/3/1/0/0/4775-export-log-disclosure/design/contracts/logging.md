# Export Logging Contract

For a successful CSV export, diagnostic logs report the row and field counts.
They do not contain cell values.

For inventory and gateway exports, diagnostic logs do not contain device,
site, or address values. The output files retain those values.

For a write failure, the exporter reports the failure and propagates it.
For an address parse failure, the exporter retains the existing fallback.
