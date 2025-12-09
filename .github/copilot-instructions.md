# MistHelper - AI Agent Instructions

## Project Overview
MistHelper is a production-grade Python tool (~28K lines) for Juniper Mist Cloud network operations. It provides 100+ menu-driven operations for data extraction, device management, and firmware upgrades with dual output (CSV/SQLite) and containerized SSH access.

**Target Audience**: Junior NOC engineers. Use clear, professional language without jargon. Think Fred Rogers meets NASA/JPL safety standards.

## Core Architecture

### Monolithic Design Pattern
- **Single File**: `MistHelper.py` contains all logic (~29K lines)
- **Why**: Simplifies deployment and container builds for NOC environments
- **Classes**: `GlobalImportManager`, `WebSocketManager`, `PacketCaptureManager`, `FirmwareManager`, `EnhancedSSHRunner`, `SFPTransceiverDataProcessor`
- **No wrappers**: All functionality lives within appropriately named classes, never use standalone wrapper functions

### Critical Dependencies
- **mistapi**: Primary Mist API SDK by Thomas Munzer (tmunzer/mistapi_python)
- **UV Package Manager**: Preferred over pip for speed (auto-fallback configured)
- **Container Runtime**: Podman-first, Docker-compatible

### Data Flow
```
Menu Selection -> API Call -> Flatten/Normalize -> Output Backend (CSV or SQLite)
                                                 -> Rate Limiting -> Retry Logic
```

## Database Strategy (CRITICAL)

### Hybrid Primary Key System
MistHelper uses **natural business keys** from the Mist API, not artificial IDs:

1. **Natural PK**: Entities with stable UUIDs (`sites`, `devices`, `templates`)
   ```python
   'listOrgSites': {
       'type': 'natural_pk',
       'primary_key': ['id'],  # API-provided UUID
       'indexes': ['org_id', 'name', 'country_code']
   }
   ```

2. **Composite PK**: Time-series data (`events`, `stats`, `metrics`)
   ```python
   'searchOrgDeviceEvents': {
       'type': 'composite_pk',
       'primary_key': ['id', 'device_id', 'timestamp']
   }
   ```

3. **Auto-increment with Unique**: Aggregated/summary data without stable keys
   ```python
   'getOrgLicensesSummary': {
       'type': 'auto_increment_with_unique',
       'primary_key': ['misthelper_internal_id']
   }
   ```

**Configuration**: `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary (line ~1672)
**Upsert Logic**: `INSERT OR REPLACE` for natural/composite keys enables updates without duplicates

## Essential Workflows

### Adding New Menu Operations
1. **API Discovery**: Check `mistapi.api.v1.orgs.*` or `mistapi.api.v1.sites.*`
2. **Primary Key Strategy**: Add to `ENDPOINT_PRIMARY_KEY_STRATEGIES` with appropriate type
3. **Flatten JSON**: Use existing `flatten_dict()` helpers for nested structures
4. **Dual Output**: Call `write_data_with_format_selection(data, filename, api_function_name=...)`
5. **Update README**: Modify operation count and add to menu table
6. **Version Changelog**: Update README with `version YY.MM.DD.HH.MM` format

### Git Workflow Rule
**Every changelog update = immediate `git add`** (agents.md requirement)

### Running Tests
```powershell
# Local development (Windows 11 + venv required)
.venv\Scripts\Activate.ps1
python MistHelper.py --test
```
**Skip List**: Operations 14, 18 (heavy), 63-65 (WIP), 90-100 (destructive)

## Critical Patterns

### Safety-First Coding
```python
# DESTRUCTIVE operations require explicit confirmation
confirmation = safe_input("Type 'UPGRADE' to proceed: ")
if confirmation != "UPGRADE":
    return  # NASA/JPL: early return on validation failure
```

### Logging Standards
- **Debug**: Internal state changes, API responses
- **Info**: User-facing progress messages
- **Error**: Exception context with full traceback
- **Never log secrets**: Redact tokens/passwords
- **ASCII Only**: Replace Unicode with ASCII equivalents (emoji map in agents.md line ~212)

### Input Validation
```python
def validate_hostname(hostname: str) -> bool:
    """All external inputs validated before use"""
    # Reject path traversal, special chars, etc.
```

### File Path Management
- **All outputs**: `data/` directory (enforced at runtime)
- **SSH logs**: `data/per-host-logs/`
- **CSV commands**: `data/SSH_COMMANDS.CSV` (fallback supported at root)
- **Database**: `data/mist_data.db`

## Rate Limiting & Performance

### Adaptive Delay System
- **Metrics File**: `delay_metrics.json` (persistent PID-like control)
- **Tuning Data**: `tuning_data.json` (endpoint-specific learning)
- **Default Page Size**: `DEFAULT_API_PAGE_LIMIT=1000` (configurable via `MIST_PAGE_LIMIT`)

### Fast Mode
```python
--fast  # Reduces retries, increases concurrency
FAST_MODE_MAX_CONCURRENT_CONNECTIONS=8  # Environment tunable
```

## Container & SSH Architecture

### Container Detection
```python
is_running_in_container()  # Checks /.dockerenv, /run/.containerenv
```

### SSH Remote Access
- **Port**: 2200 (non-standard for security)
- **ForceCommand**: Direct MistHelper launch (no shell access)
- **Session Isolation**: Unique directory per connection (`/app/sessions/session_<id>/`)
- **Credentials**: Default `misthelper` / `misthelper123!` (change in production)

## Project-Specific Conventions

### Naming Standards
- **No abbreviations**: `for device in devices` NOT `for d in devices`
- **No AI markers**: Never use `...existing code...` or double ellipses
- **Class-based**: All features organized under semantic class names

### Menu System
- **Interactive**: No args = menu-driven selection
- **Direct**: `--menu 11` for automation
- **Packet Captures**: Menu IDs 9-10 for site/org packet capture operations
  - Site captures (Menu 9): Wireless client, wired client, gateway, **switch**, new association, scan radio
  - Org captures (Menu 10): Similar capabilities at org level
  - **Switch captures**: Full support for port-specific captures with tcpdump filtering
- **WebSocket Commands**: Menu IDs 5-8, 87-89 for real-time device commands

### Destructive Operations (90-100)
- AP Firmware (90): Site or Template-based
- AP Reboots (91-93): Various strategies
- VC Conversion (94-96): Virtual chassis operations
- SSH Runner (97-98): Device command execution
- Switch/SSR Firmware (99-100): Advanced upgrade modes

**Never automate these without explicit user confirmation**

## Common Pitfalls

### Device Type Filtering
```python
# WRONG: API defaults to APs only
listSiteDevices(site_id)

# CORRECT: Specify type=all for switches/gateways
listSiteDevices(site_id, type="all")
```

### EOF Handling in Containers
```python
# Always wrap input() in SSH/container contexts
def safe_input(prompt, context="unknown"):
    try:
        return input(prompt)
    except EOFError:
        logging.info(f"EOF detected in {context} - session disconnected")
        sys.exit(0)
```

### Windows Path Compatibility
Use `os.path.join()` or `Path()`, never hardcoded `/` or `\\`

## Documentation Structure
- **README.md**: User-facing operations guide (comprehensive)
- **agents.md**: Internal agent guide (attached, ~350 lines)
- **SSH_GUIDE.md**: SSH runner detailed usage
- **documentation/**: Sample files, API specs, changelogs

## Key Files Reference
| File | Purpose | Lines |
|------|---------|-------|
| `MistHelper.py` | Main implementation | ~28K |
| `agents.md` | Agent coding guide | ~350 |
| `requirements.txt` | Python dependencies | ~30 |
| `.env` (git-ignored) | Credentials & config | N/A |
| `data/mist_data.db` | SQLite persistence | Generated |

## When in Doubt
1. **Read agents.md first** (attached context) - comprehensive safety patterns
2. **Check existing patterns** - grep for similar operations
3. **Validate early, return early** - NASA/JPL defensive programming
4. **Test in venv** - Windows 11 local development standard
5. **Update docs** - README changelog + operation tables

## External Resources
- Mist API Docs: `documentation/mist-api-openapi3*.{json,yaml}`
- Thomas Munzer's mistapi: https://github.com/tmunzer/mistapi_python
- Reference implementations: https://github.com/tmunzer/mist_library

---

**Remember**: This codebase prioritizes NOC engineer safety and operational clarity over clever abstractions. Explicit > Implicit. Readable > Concise. Safe > Fast.
