# History: Why This Rewrite?

The previous README was partially outdated compared to the current codebase. Key discrepancies that were corrected:

1. **Operation Count**: MistHelper now has 161 actionable menu entries (0-160), with some gaps reserved for future expansion
2. **File Naming**: Actual output files use names like `OrgApiTokens.csv`, `OrgPsks.csv`, etc. Weekly inventory is stored in `CombinedInventory_ByWeek/`
3. **SSH Command Runner**: The Enhanced SSH Runner (option 97) uses a fallback CSV located at `data/SSH_COMMANDS.CSV`, not the root directory
4. **Heavy Operations**: Options 14 (port stats for all sites) and 18 (site settings for all sites) are excluded from `--test` mode due to multi-hour runtime
5. **WIP Operations**: Options 63-65 are explicitly flagged as work-in-progress with unstable schemas

The rewrite ensured the documentation accurately reflects the codebase as it exists today, not a historical snapshot.
