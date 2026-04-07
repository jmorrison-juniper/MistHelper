# Quickstart — SSID Template Consolidation (Feature 018)

1. Ensure your `.env` contains `MIST_TARGET_SSID` and optionally `MIST_TEMPLATE_BASENAME`.
2. Run `python MistHelper.py` and select the new menu option `SSID Template Consolidation` (menu 159).
3. Run Phase 1 to collect data and review the CSV/SQLite report in `data/`.
4. Run Phase 2 after reviewing and confirming the site variables to be written.
5. Run Phase 3 to assign site groups, Phase 4 to create templates, and Phase 5 to disable old SSIDs when ready.

Notes:
- Always run Phase 1 first. Use the cached data option only when you are sure it is fresh.
- Destructive writes require typing `CONFIRM` exactly at prompts.
- PSK sites are excluded from writes and must be reconfigured manually.
