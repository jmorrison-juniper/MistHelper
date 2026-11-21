### Deployed inventory for cross-org renewal report

- **Fixed**: Menu 308 now exports deployed inventory detail and organization/device-type summary rows separately from unassigned stock inventory. Issue #4858.
- **Fixed**: Menu 308 now exports one combined organization inventory summary for deployed, stock, and all inventory identities. Issue #4858.
- **Fixed**: Menu 308 now reports SSR devices separately from gateway devices. Issue #4858.
- **Fixed**: Menu 308 now preserves physical VC chassis serials and exposes VC and chassis identity fields. Issue #4858.
- **Fixed**: Menu 308 now expands logical Virtual Chassis records into one deployed row per physical member serial. Issue #4858.
- **Fixed**: Standalone mode disables shared Redis request accounting, and locked header-only CSV files use a UTC timestamped fallback. Issue #4858.
- **Fixed**: Startup loads `.env` before logging setup, so `LOGGING_LOG_LEVEL` suppresses lower-severity file records. Issue #4858.
- **Fixed**: Startup routes structlog database records through the same console and file levels. Issue #4858.
