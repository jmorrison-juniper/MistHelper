# History: Why This Rewrite?

The previous README was partially outdated compared to the current codebase. Key discrepancies that were corrected:

1. **Operation Count**: MistHelper now has 209 actionable menu entries (1-209)
2. **File Naming**: Actual output files use names like `OrgApiTokens.csv`, `OrgPsks.csv`, etc. Weekly inventory is stored in `CombinedInventory_ByWeek/`
3. **SSH Command Runner**: The Enhanced SSH Runner (menu 175) uses a fallback CSV located at `data/SSH_COMMANDS.CSV`, not the root directory
4. **Heavy Operations**: `src/utils/operation_registry.py` marks menus 14, 18-19, 59, 97-101, and 153 as `resource_intensive`, so `--test` skips them
5. **Category Source**: The registry decides what `--test` runs. No page should hardcode a category list, because the registry is the only source of truth.

The rewrite ensured the documentation accurately reflects the codebase as it exists today, not a historical snapshot.
