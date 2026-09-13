# Enhanced SSH Command Runner

## Menu 175: Interactive SSH Runner

Category: `destructive`. The operation runs commands on live network devices.

Features:
- Auto-detects hostname, username, password from `.env` (if supplied)
- Falls back to a CSV command list when no explicit `--command` passed (preferred path: `data/SSH_COMMANDS.CSV`, legacy root file still supported)
- Shell mode with adaptive reading & timeout safeguards
- Structured logging (per-host log concept; ensure directory creation if extending)

> **Note:** Legacy root `SSH_COMMANDS.CSV` is auto-detected if the `data/` copy is absent; you will see an informational message. Migrate to `data/` to suppress it.

## Menu 176: SSH by Gateway Template

Category: `destructive`. The operation runs commands on live network devices.

Features:
- Integrates with menu 31 (Export gateway management overlay IPs) for target discovery
- Filters gateways by user-selected template name AND online status
- Only targets gateways with configured management IPs
- Interactive template selection with gateway counts
- Uses the same SSH configuration as menu 175 (`.env` and `data/SSH_COMMANDS.CSV`)
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
