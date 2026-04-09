# Enhanced SSH Command Runner

## Option 97: Interactive SSH Runner

Features:
- Auto-detects hostname, username, password from `.env` (if supplied)
- Falls back to a CSV command list when no explicit `--command` passed (preferred path: `data/SSH_COMMANDS.CSV`, legacy root file still supported)
- Shell mode with adaptive reading & timeout safeguards
- Structured logging (per-host log concept; ensure directory creation if extending)

> **Note:** Legacy root `SSH_COMMANDS.CSV` is auto-detected if the `data/` copy is absent; you will see an informational message. Migrate to `data/` to suppress it.

## Option 98: SSH by Gateway Template

Features:
- Integrates with Menu Option 4 (Gateway Management IPs) for target discovery
- Filters gateways by user-selected template name AND online status
- Only targets gateways with configured management IPs
- Interactive template selection with gateway counts
- Uses same SSH configuration as Option 97 (`.env` and `data/SSH_COMMANDS.CSV`)
- Provides confirmation before execution with target list preview

## Configuration

Set these in your `.env` file:
- `SSH_USERNAME` - Default SSH username
- `SSH_PASSWORD` - Default SSH password
- `SSH_PORT` - SSH port (default: 22)

## Command CSV Format

The `data/SSH_COMMANDS.CSV` file contains commands to execute on devices:

```csv
command
show version
show interfaces
show route summary
```

For detailed SSH runner documentation, see the [SSH Guide](https://github.com/jmorrison-juniper/MistHelper/blob/main/documentation/SSH_GUIDE.md).
