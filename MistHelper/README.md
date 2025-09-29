# MistHelper
Network Operations & Data Export Tool for Juniper Mist Cloud

**Operation Count:** The code currently defines 100 actionable menu entries (1–8, 11–89, 90–99) with some gaps for future expansion.

MistHelper is a production-focused Python application that streamlines large‑scale Juniper Mist Cloud data extraction, enrichment, transformation, and limited lifecycle operations. It supports both interactive (menu) and fully automated CLI execution, with flexible output to either CSV files or a relational SQLite database that uses natural/composite business keys (no artificial surrogate IDs for core entities). The codebase emphasizes safety, transparency, and predictable behavior—aligned with the included internal Agents Guide and NASA/JPL style defensive programming practices.

**NEW: SSH Remote Access** - MistHelper now supports containerized deployment with SSH server for remote access. Connect via SSH to run MistHelper in isolated sessions with automatic session management and multi-user support.

---
## 1. Why This Rewrite?
The previous README was partially outdated. Key discrepancies corrected here:
1. Operation Count: The code currently defines 97 actionable menu entries (1–65, 70–78, 79–80, 90–97) – not a fixed “96” set. Some originally documented WebSocket shell outputs (81–83) are no longer present in `menu_actions`.
2. File Naming Differences: Actual code exports `OrgApiTokens.csv`, `OrgPsks.csv`, `OrgRfTemplates.csv`, etc. (case-sensitive differences from older docs). A weekly combined inventory is written under `CombinedInventory_ByWeek/` plus per‑operation CSVs in `data/`.
3. SSH Command Runner: Enhanced SSH Runner (option `97`) now uses a fallback CSV at `data/SSH_COMMANDS.CSV` (legacy root location still accepted temporarily).
4. Heavy / Long‑Running Operations: Options 14 (port stats) and 18 (full site config) are intentionally excluded from automated systematic test mode due to extreme duration and rate‑limit pressure.
5. WIP Operations: 63–65 are explicitly flagged in code as work‑in‑progress and may change schema/output without notice.

This README reflects the current actual logic inside `MistHelper.py` (≈22k lines) as of 2025‑09‑23.

---
## 2. Core Capabilities
* Multi‑mode execution: interactive menu or direct CLI (`--menu <id>`)
* Dual output backends: CSV (simple exchange) or SQLite (`data/mist_data.db`) with adaptive schema strategies
* Hybrid primary key strategy: natural keys when stable IDs exist, composite keys for time‑series, and guarded fallback
* Adaptive dependency and import system (`GlobalImportManager`) with UV→pip fallback and optional auto‑upgrade (disable in containers)
* Intelligent rate limiting & pacing (delay metrics + tuning persistence via `delay_metrics.json`, `tuning_data.json`)
* Robust flattening + sanitization pipeline for nested API JSON
* Optional fuzzy address normalization (scourgify + rapidfuzz; safe fallbacks if not installed)
* Enhanced SSH execution framework (Paramiko) with validation, shell mode, per‑host logging stubs (option 97)
* Systematic safe‑operation test harness (`--test`) with skip logic for unsafe / interactive / destructive items
* Container ready (Podman first, Docker compatible) with two build profiles (`Containerfile` simple, `Dockerfile` with HEALTHCHECK + UV logic)
* Defensive logging: `script.log` plus targeted debug gating

---
## 3. Directory & Runtime Layout
| Path | Purpose |
|------|---------|
| `MistHelper.py` | Primary monolithic implementation (menu, exports, SSH, persistence) |
| `data/` | SQLite DB (`mist_data.db`), generated CSV outputs, derived artifacts |
| `CombinedInventory_ByWeek/` | Time‑series weekly inventory snapshots |
| `data/SSH_COMMANDS.CSV` | Fallback SSH command list (legacy root path still supported) |
| `delay_metrics.json` / `tuning_data.json` | Adaptive rate / tuning persistence |
| `script.log` | Unified runtime log |
| `run-misthelper.py` | Podman helper wrapper (auto builds & runs container) |
| `Dockerfile` / `Containerfile` | Two container strategies (UV hybrid vs simplified SSL‑bypass) |
| `compose.yml` | Orchestrated service definition (uses `Containerfile` by default) |
| `agents.md` | Internal “Agents Guide” (style, safety, refactor guidance) |

All export CSVs are now written inside `data/` (the code enforces a data directory even if a legacy doc claims root CSV placement).

---
## 4. Installation and Setup

### Step 1: Get the Code
Download or clone MistHelper to your local machine:
```powershell
git clone https://github.com/jmorrison-juniper/MistHelper.git
cd MistHelper
```

### Step 2: Create a Virtual Environment
Always use a virtual environment to keep your Python packages organized:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
Install the required Python packages using either UV (recommended) or pip:

**Option A: Using UV (Faster, Recommended)**
```powershell
python -m pip install uv
uv pip install -r requirements.txt
```

**Option B: Using pip (Standard)**
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Your Environment
Create your configuration file from the template:
```powershell
cp documentation\sample.env .env
```

Edit `.env` file with your settings:
- **Required:** Set `MIST_APITOKEN` to your Mist API token
- **Optional but Helpful:** Set `org_id` to skip organization selection
- **Optional:** Configure SSH settings for device commands

To get your API token:
1. Login to https://manage.mist.com
2. Go to Organization → API Tokens  
3. Create a new token with appropriate permissions
4. Copy the token to your `.env` file

### Step 5: Test Your Setup
Verify everything works:
```powershell
python MistHelper.py --help
python MistHelper.py --menu 1
```

---
## 5. How to Run MistHelper

### Interactive Menu Mode (Beginner Friendly)
Simply run the script and choose from the menu:
```powershell
python MistHelper.py
```

### Direct Command Mode (For Automation)
Run specific operations directly:
```powershell
# Export organization inventory
python MistHelper.py -M 11

# Export sites information  
python MistHelper.py -M 12

# Run gateway synthetic tests (fast mode)
python MistHelper.py -M 16 --fast

# Export data to SQLite database
python MistHelper.py -M 11 --output-format sqlite
```

### Test Mode (Verify Everything Works)
Run automated tests on safe operations:
```powershell
python MistHelper.py --test
```

### Common Useful Commands
```powershell
# Get help with all options
python MistHelper.py --help

# Run with detailed logging for troubleshooting
python MistHelper.py -M 11 --debug

# SSH into devices (requires SSH configuration in .env)
python MistHelper.py -M 97

# Fast mode for large organizations
python MistHelper.py -M 16 --fast
```

### Working with Output Files
MistHelper creates organized output in the `data/` directory:
- **CSV files:** Easy to open in Excel or import elsewhere
- **SQLite database:** Use `data/mist_data.db` for complex queries
- **Weekly inventory:** Time-series data in `CombinedInventory_ByWeek/`

View SQLite data:
```powershell
sqlite3 data\mist_data.db
```
```sql
.tables
SELECT COUNT(*) FROM listOrgSites;
```

---
## 6. Command Line Interface
Primary flags (from argparse block near end of file):
| Flag | Purpose |
|------|---------|
| `-O, --org` | Organization ID |
| `-M, --menu <id>` | Execute a single menu action non‑interactively |
| `-S, --site` | Human-readable site name |
| `-D, --device` | Human-readable device name |
| `-P, --port` | Port ID |
| `--output-format {csv,sqlite}` | Select output backend (default csv) |
| `--test` | Run systematic safe‑operation test suite |
| `--fast` | Enable fast mode heuristics (threading & reduced retries) |
| `--skip-deps` | Skip dependency auto‑install / upgrade phase |
| `--debug` | Enable debug output (includes detailed table data in logs) |
| `--delay <seconds>` | Fixed delay between loop iterations (in seconds) |
| `--address-check` | Enable external address validation using Nominatim API |
| `--skip-ssl-verify` | Skip SSL certificate verification for external API calls |
| `--no-env` | Disable .env file loading for SSH operations |

Examples (PowerShell friendly):
```powershell
python .\MistHelper.py -M 11 --output-format sqlite
python .\MistHelper.py -M 13 --output-format sqlite --fast
python .\MistHelper.py --test --output-format sqlite --debug
```

Interactive fallback occurs if no `-M/--menu` is supplied.

---
## 7. Output & Data Model
### CSV
* Written under `data/` automatically (code ensures directory exists)
* Multiline fields sanitized (line breaks replaced with `\n`)
* Nested structures flattened: dotted / hierarchical keys converted with underscores + index suffixes

### SQLite (set `--output-format sqlite` or `OUTPUT_FORMAT=sqlite` env)
Adaptive strategy (see `ENDPOINT_PRIMARY_KEY_STRATEGIES` mapping):
1. Natural Primary Key: Entities with stable `id` (sites, devices, templates)
2. Composite Primary Key: Event/time‑series metrics (e.g., `device_id + timestamp`)
3. Auto‑Increment w/ Unique Constraint: Aggregated license or summary endpoints lacking stable composite identity

Upserts use `INSERT OR REPLACE` when natural/composite keys are in effect. Index selection is dynamic per endpoint (org/site/device/time fields prioritized). Metadata fields `misthelper_created_time` & `misthelper_updated_time` are appended for auditing.

Inspecting the DB:
```bash
sqlite3 data/mist_data.db
.tables
.schema getOrgInventory
SELECT COUNT(*) FROM listOrgSites;
```

---
## 8. Menu Actions (Current Truth)
Below is the authoritative (condensed) list derived directly from `menu_actions` in code. WIP = unstable schema, DESTRUCTIVE = requires explicit user confirmation & caution.

| Range | Focus | Highlights |
|-------|-------|-----------|
| 1–4 | Alarms & Definitions | Org alarms, device events, audit logs (24h), gateway management IPs |
| 11–28 | Org Inventory & Enrichment | Sites, devices, stats, ports, VPN, synthetic tests, templates, location & address enrichment |
| 29–34 | Site‑Scoped | Per‑site ports, clients, devices, Wi‑Fi sessions, chassis info |
| 35–39 | Template Bundles | Unified export of gateway/network/RF/site/AP templates |
| 40–44 | Clients & Security | Wired/wireless clients, rogue entities, security policies + events aggregation |
| 45–59 | Configuration & Admin | Licenses, PSKs, webhooks, WLANs (org/site), admins, MSP, SSO, usage, MX Edge |
| 60–62 | Monitoring / Analytics | Firmware upgrade status, inventory diff (address similarity), Marvis AI actions |
| 63–65 | WIP Bulk History | 52‑week device events, 52‑week audit logs, gateway config extraction (heavy) |
| 66–69 | Insights API Operations | Organization & site SLE metrics, client insights, general insight metrics |
| 70–74 | Interactive Views | Selection, inventory browser, device stats/tests/config views |
| 75–76 | Continuous Loops | Core dataset refresh + continuous collection cycle |
| 77–78 | Processing & Support | SFP transceiver merge, site support package generation |
| 79–80 | CLI / WebSocket | Interactive CLI, ARP via WebSocket (other earlier WebSocket commands removed) |
| 81–86 | Advanced Insights | Device insights, const definitions, organization insights, anomaly metrics |
| 5–8, 87–89 | WebSocket Commands | MAC table (switches), forwarding table (gateways), routing table (switches - BGP/OSPF/Static), SSR/SRX routing (128T/SRX gateways - Advanced BGP analysis), device ping, ARP, and service ping via WebSocket (real-time output) |
| 90–93 | DESTRUCTIVE Ops | AP firmware upgrade strategies, reboots, virtual chassis conversions |
| 94–96 | Status / Integrity | VC conversion status, gateway stats w/ freshness, WAN port conflict detection |
| 97 | SSH Runner | Enhanced SSH command execution (auto-detect credentials & command file) |
| 98 | SSH by Template | SSH runner targeting gateways by template name (online with management IPs only) |
| 99 | Switch Firmware | **DESTRUCTIVE**: Advanced switch firmware upgrade with mode selection |

Important Notes:
* Options 14 & 18 are resource‑intensive (multi‑hour) and skipped during `--test`.
* 63–65 intentionally marked WIP; expect evolution.
* 90–93, 99 should never be scripted unattended without explicit review.

---
## 9. Systematic Test Mode (`--test`)
Behavior:
* Dynamically enumerates safe menu items (GET, non‑interactive, non‑destructive)
* Skips heavy, WIP, interactive, WebSocket, continuous, destructive operations (documented inline in code)
* Executes in optimized order (fastest endpoints first) to minimize cumulative runtime
* Saves partial results even on rate limiting or exceptions

You can combine with `--output-format sqlite` and `--fast`:
```bash
python MistHelper.py --test --output-format sqlite --fast
```

---
## 10. Enhanced SSH Command Runner (Option 97)
Features:
* Auto‑detects hostname, username, password from `.env` (if supplied)
* Falls back to a CSV command list when no explicit `--command` passed (preferred path: `data/SSH_COMMANDS.CSV`, legacy root file still supported)
* Shell mode with adaptive reading & timeout safeguards
* Structured logging (per‑host log concept; ensure directory creation if extending)

Note: Legacy root `SSH_COMMANDS.CSV` is auto-detected if the `data/` copy is absent; you will see an informational message. Migrate to `data/` to suppress it.

### SSH by Gateway Template (Option 98)
Features:
* Integrates with Menu Option 4 (Gateway Management IPs) for target discovery
* Filters gateways by user-selected template name AND online status
* Only targets gateways with configured management IPs
* Interactive template selection with gateway counts
* Uses same SSH configuration as Option 97 (`.env` and `data/SSH_COMMANDS.CSV`)
* Provides confirmation before execution with target list preview

---
## 11. Rate Limiting & Performance
* Adaptive delays stored in `delay_metrics.json`
* Safe concurrency mediated by semaphores + environment‑driven thread limits (`FAST_MODE_MAX_CONCURRENT_CONNECTIONS`)
* Heavy operations log progress early, large loops chunked
* Fallback strategies engage when optional performance libraries are unavailable

---
## 12. Address Normalization & Similarity
If `usaddress-scourgify` and `rapidfuzz` are installed, address comparison for inventory reconciliation (menu 61) uses:
* Normalization pipeline (parse & canonicalize fields)
* Token sort ratio fuzzy scoring fallback (difflib fallback if rapidfuzz absent)
* Threshold configurable via future `.env` variable (documented in Agents Guide; ensure to add if implementing enhancement)

---
## 13. Security & Safety
| Area | Practice |
|------|---------|
| Credentials | Loaded from `.env`, never logged in cleartext |
| Destructive Ops | Uppercase warnings + explicit invocation required |
| File Output | Filenames sanitized; path traversal blocked in helpers |
| SSH | Paramiko host key auto‑add restricted to trusted internal contexts (document inline if expanding) |
| Logging | Secrets & tokens excluded; debug gating prevents noisy stdout |
| Data Integrity | Natural/composite PK strategies avoid silent duplication |

Before extending destructive workflows, replicate existing confirmation pattern and add SECURITY comments as per `agents.md`.

---
## 14. Containers & SSH Remote Access

### Container Build Strategies
Two build strategies:
1. `Containerfile` (simple, pip only, SSL bypass env overrides for constrained corporate PKI)
2. `Dockerfile` (multi‑path UV attempt + HEALTHCHECK)

### Local Container Usage
Compose example (interactive shell):
```bash
docker compose build
docker compose run --rm misthelper python MistHelper.py
```

Podman helper (auto build + run):
```powershell
python .\run-misthelper.py
```

### SSH Remote Access (NEW)
MistHelper now supports SSH server deployment for remote access with automatic session management:

#### Quick Start - SSH Server
```powershell
# Build and start SSH server container
python .\run-misthelper.py --ssh

# Connect from any SSH client
ssh -p 2200 misthelper@localhost
# Password: misthelper123!
```

#### SSH Server Features
- **Automatic Session Management**: Each SSH connection creates an isolated MistHelper session
- **Multi-User Support**: Multiple users can connect simultaneously with session isolation
- **Session Persistence**: Sessions persist until you explicitly exit
- **Auto-Restart**: If MistHelper crashes, the session automatically restarts
- **ForceCommand Architecture**: Direct launch into MistHelper (no shell access for security)

#### SSH Connection Details
| Setting | Value | Notes |
|---------|-------|-------|
| **Port** | 2200 | Avoids conflict with system SSH (port 22) |
| **Username** | misthelper | Fixed username for all connections |
| **Password** | misthelper123! | Default password (change in production) |
| **Host Keys** | Auto-generated | Unique per container instance |

#### SSH Session Management
Each SSH connection automatically:
1. Creates a unique session ID based on connection details
2. Sets up an isolated working directory (`/app/sessions/session_<id>/`)
3. Launches MistHelper with container detection
4. Handles clean exit and session cleanup
5. Provides session restart on unexpected termination

#### SSH Usage Examples
```bash
# Connect and run interactively
ssh -p 2200 misthelper@localhost

# Connect with specific SSH client settings
ssh -p 2200 -o StrictHostKeyChecking=no misthelper@localhost

# From Windows with built-in SSH client
ssh -p 2200 misthelper@127.0.0.1
```

#### SSH Architecture Details
- **ForceCommand**: SSH forces execution of MistHelper (no shell access)
- **Session Isolation**: Each connection gets independent session directory
- **Container Detection**: MistHelper automatically detects SSH container mode
- **Session Cleanup**: Automatic cleanup on connection termination
- **Multi-User**: Supports multiple simultaneous SSH connections

#### SSH Security Considerations
- SSH server runs on non-standard port 2200
- ForceCommand prevents shell access (application-only access)
- Session directories are isolated between connections
- Default credentials should be changed in production environments
- Host key verification recommended for production use

#### SSH Troubleshooting
| Issue | Solution |
|-------|----------|
| Connection refused | Ensure container is running: `docker ps` |
| Wrong password | Default is `misthelper123!` |
| Permission denied | Check SSH client settings, try `-o StrictHostKeyChecking=no` |
| Session not starting | Check container logs: `docker logs <container>` |
| Port conflict | Ensure port 2200 is available |

Persisted artifacts appear under local `data/` bind mount.

---
## 15. Development Notes
Recommended incremental refactor targets (mirrors Agents Guide Section 18):
* Extract API domain modules: `api_ops/`, `output/`, `ssh/`
* Add unit tests for validators (hostname, port, command sanitation)
* Migrate SSH command CSV → structured JSON + schema validation
* Introduce optional structured JSON logging mode (feature flag)
* Implement `--list-operations` CLI flag (enumerate menu descriptors machine‑readably)

Coding Style Essentials:
* Explicit naming, early validation + early return
* All network calls wrapped with logging context and coarse-grained exception handling
* Restrict broad except clauses; log with context

---
## 16. Troubleshooting Quick Table
| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| Empty CSV | Missing org_id / expired token | Verify `.env`, re-run |
| Slow runs / many 429s | Hitting rate limits | Space requests, enable `--fast`, avoid heavy options concurrently |
| SQLite table missing | First run not completed or permission issue | Re-run with `--output-format sqlite` and check write perms on `data/` |
| SSH runner fails | Missing `paramiko` or creds | Ensure `paramiko` installed; add SSH vars to `.env` |
| WIP export fails | Endpoint schema drift | Treat 63–65 as non-stable; review code before relying |
| **SSH connection refused** | **Container not running** | **Check `docker ps`, restart with `python run-misthelper.py --ssh`** |
| **SSH wrong password** | **Using incorrect credentials** | **Default password is `misthelper123!`** |
| **SSH session won't start** | **ForceCommand or session issues** | **Check container logs, verify SSH server is running** |
| **SSH port conflict** | **Port 2200 already in use** | **Stop other services on port 2200 or modify container config** |
| **Multiple SSH sessions interfering** | **Session isolation problem** | **Each connection should get unique session ID - check logs** |

---
## 17. Contributing
1. Fork & branch (`feat/<topic>` or `fix/<issue>`)  
2. Add/adjust tests where logic changes (start with validators)  
3. Keep commits focused; annotate with tags (`[FEAT]`, `[FIX]`, `[REF]`, `[DOC]`)  
4. Update this README if public behavior or filenames change  
5. Run `--test` (when feasible) before submitting PR  

License: MIT (see `pyproject.toml`).

---
## 18. Roadmap (Short Horizon)
* Structured operation registry + `--list-operations`
* Modular extraction of SSH runner + validators
* Optional JSON log output mode
* Test harness for primary key strategy correctness
* Address verification toggle documented (when externally validated)

---
## 19. Support Flow
1. Run with `--debug` and reproduce
2. Inspect `script.log` (search for failing menu ID)
3. Confirm token validity (menu 11 success?)
4. Try alternate output backend (`--output-format csv` vs `sqlite`)
5. Open issue with log excerpt (redact org/site/device IDs if required by policy)

---
## 20. Attribution
Built for operational reliability and clarity in large enterprise / NOC contexts. See `agents.md` for internal safety and refactor guidance.

---
## 21. Changelog

### Version 25.09.29.17.05
- **Enhanced**: Menu option 7 title - Updated to "Show routing table on switches via WebSocket (Switch L3 routing - BGP/OSPF/Static)" for clarity
- **Enhanced**: Menu option 8 title - Updated to "Show SSR/SRX routing table via dedicated API (128T/SRX gateways - Advanced BGP analysis)" for device specificity
- **Enhanced**: SSR routing table display - Added complete data table with all BGP attributes including Route Name, Selection Reason, Weight, Metric, Local Preference, AS Path, and VRF
- **Enhanced**: Protocol selection flexibility - Users can now skip protocol specification to let API use its default behavior, choose specific protocols (bgp/any/ospf/static/direct/evpn), or get comprehensive routing views
- **Enhanced**: Data presentation - Comprehensive routing table with full untruncated data display showing complete BGP route analysis including peer names, selection criteria, and all BGP path attributes
- **Enhanced**: Menu categorization - Clear device-specific separation between switch routing (Option 7) and SSR/SRX gateway routing (Option 8) for improved operational clarity

### Version 25.09.29.16.15
- **Added**: Menu option 8 - SSR/SRX routing table using dedicated API function (advanced BGP/OSPF analysis with VRF support)
- **Enhanced**: Dedicated SSR/SRX routing API - Uses mistapi.api.v1.sites.devices.showSiteSsrAndSrxRoutes for structured routing queries
- **Added**: Advanced routing table parameters - Protocol filtering, BGP neighbor analysis, VRF-aware queries, HA cluster node selection
- **Added**: BGP route direction analysis - Received/advertised route inspection for BGP neighbors with structured output
- **Enhanced**: Device compatibility validation - Specific checks for SSR (128T) and SRX devices with compatibility warnings
- **Added**: Real-time refresh options - Configurable interval and duration for dynamic routing table monitoring
- **Enhanced**: Parameter validation - Structured input validation using utils_show_route schema from OpenAPI specification
- **Added**: Routing table comparison - Option 8 (dedicated API) vs Option 7 (generic WebSocket) for different use cases
- **Enhanced**: Documentation - Clear distinction between generic routing table (7) and SSR-specific routing table (8) functions
- **Fixed**: Menu organization - Filled gap at option 8 to improve numerical sequence and reduce confusion

### Version 25.09.29.14.45
- **Added**: Menu option 7 - Show routing table command for switches/routers/SSR devices via WebSocket (RIB - Routing Information Base)
- **Enhanced**: Routing table diagnostics - Comprehensive routing protocol information (BGP, OSPF, static routes) with filtering capabilities
- **Added**: Multi-format routing table parsing - Support for various device vendor output formats with intelligent parsing strategies
- **Enhanced**: Interactive parameter collection - Optional filtering by protocol, prefix, VRF, neighbor, and node for targeted routing analysis
- **Added**: Routing vs forwarding table distinction - Clear documentation explaining RIB (Routing Information Base) vs FIB (Forwarding Information Base)
- **Enhanced**: Device compatibility validation - Comprehensive checks for Layer 3 routing capabilities on switches, routers, and SSR devices
- **Enhanced**: Default protocol behavior - Changed default from 'bgp' to 'any' to show all route types unless specifically filtered
- **Enhanced**: Juniper routing table parsing - Improved multi-line route entry parsing with proper protocol/admin distance extraction
- **Enhanced**: Table display formatting - Removed truncation limits to show full routing data without ellipsis cutoffs
- **Fixed**: prettytable import errors - Corrected class reference from prettytable.PrettyTable() to PrettyTable() following established import patterns
- **Fixed**: Syntax errors - Resolved orphaned elif statements from parser refactoring

### Version 25.01.02.18.30
- **Added**: Menu option 6 - Show forwarding table command for gateway/SSR devices via WebSocket (Layer 3 routing table)
- **Enhanced**: WebSocket device commands - Expanded support for both Layer 2 (MAC table) and Layer 3 (forwarding table) operations
- **Added**: Gateway/SSR compatibility checks - Device-specific guidance and troubleshooting for forwarding table operations
- **Enhanced**: Menu organization - Filled numbering gap between option 5 and 11 to improve menu structure
- **Added**: Layer 3 routing diagnostics - Comprehensive forwarding table information for packet routing decisions
- **Enhanced**: Device type validation - Improved device compatibility warnings for Layer 3 vs Layer 2 operations

### Version 25.09.26.16.45
- **CRITICAL FIX**: Switch firmware model filtering - Added missing device model compatibility validation for option 99 (switch firmware upgrades)
- **Enhanced**: Firmware version selection - Now filters available firmware versions by actual switch models in the organization inventory
- **Enhanced**: Model compatibility display - Firmware version selection now shows compatible switch models for each available version
- **Enhanced**: Safety improvements - Prevents selection of incompatible firmware versions that could cause upgrade failures
- **Added**: Fallback firmware entry - Manual firmware version specification with compatibility warnings when no compatible versions found
- **Enhanced**: Error handling - Improved messaging when no compatible firmware versions are available for detected switch models
- **Fixed**: Security vulnerability - Eliminated potential firmware compatibility mismatches that could cause network device failures

### Version 25.09.26.14.14
- **Added**: Menu option 99 - Advanced Switch firmware upgrade with mode selection (By Site or By Template)
- **Added**: Switch firmware upgrade system - Complete enterprise-grade switch firmware management 
- **Added**: FirmwareManager class - Extended with comprehensive switch firmware methods including execute_switch_firmware_upgrade_with_mode_selection(), bulk_upgrade_switch_firmware_by_site(), upgrade_switch_firmware_by_gateway_template()
- **Added**: Switch-specific API parameters - Proper reboot=True, snapshot=True for Junos devices, no P2P support
- **Added**: Gateway Template integration for switches - Reuses existing template infrastructure for consistent site grouping
- **Added**: Switch device discovery - Automatic enumeration using listSiteDevices(type="switch") with proper filtering
- **Added**: Switch firmware validation - Version availability checking via listOrgAvailableDeviceVersions(type="switch")
- **Added**: Switch upgrade strategies - Big bang, canary, RRM, and serial upgrade modes with network-aware safety warnings
- **Added**: Enhanced safety prompts - Network disruption warnings specific to switch operations requiring maintenance windows
- **Enhanced**: Destructive operation tracking - Added option 99 to systematic test exclusions for safe automated testing
- **Enhanced**: Documentation - Updated README with switch firmware capabilities and operation count (now 98 total menu options)
- **Enhanced**: CSV export system - Switch upgrades export to data/ActiveSwitchUpgradeOperations.csv with comprehensive tracking

### Version 25.09.26.14.30
- **Fixed**: Menu option 60 (Firmware status check) - Eliminated double scope selection prompts by creating direct FirmwareManager path
- **Fixed**: DateTime error handling - Enhanced timestamp validation for firmware upgrade status with proper type checking and exception handling
- **Fixed**: Firmware status implementation - Removed duplicate scope selection logic in check_firmware_upgrade_status_impl()
- **Enhanced**: Error reporting - Improved datetime.fromtimestamp() error handling with specific exception types and debug logging
- **Enhanced**: Code stability - Added input validation for timestamp values before datetime conversion
- **Fixed**: User experience - Single scope selection prompt for option 60 eliminating confusing double prompts

### Version 25.09.26.11.15
- **Added**: FirmwareManager class - Comprehensive firmware management system for Mist Access Points
- **Enhanced**: Menu option 90 - Consolidated firmware upgrade with mode selection (By Site or By Template)
- **Added**: Interactive mode selection - Choose between site-based or template-based upgrades at runtime
- **Added**: Template-based AP firmware upgrades with Gateway Template selection and site count display
- **Enhanced**: Firmware upgrade architecture - Refactored existing functions into class-based structure
- **Added**: Automatic site discovery and AP enumeration across all sites in selected template
- **Enhanced**: User experience - Single menu option with clear workflow branching
- **Enhanced**: Backward compatibility - All existing functionality maintained with improved organization
- **Enhanced**: Code organization - NASA/JPL compliant safety architecture with comprehensive validation
- **Documented**: Complete firmware upgrade workflow including site auto-upgrade configuration behavior

### Version 25.01.08.15.30
- **Added**: Menu option 5 - MAC table WebSocket command for switches with real-time streaming output
- **Enhanced**: WebSocket completion detection - Fixed chunking issue in message parsing for improved performance  
- **Enhanced**: Device filtering - Fixed type=all parameter handling to correctly show switches in device selection
- **Enhanced**: MAC table completion - Smart detection completes in ~5 seconds instead of 60s timeout when all entries received
- **Enhanced**: WebSocket debugging - Added comprehensive debug logging for troubleshooting message segmentation
- **Added**: Switch-only filtering for MAC table operations to ensure compatibility with supported device types
- **Enhanced**: Pattern matching - Robust handling of "ethernet switching table" vs "thernet switching table" chunking variations
- **Verified**: MAC table retrieval tested on EX4100-F-12P switch with 44 entries, optimal performance confirmed

### Version 25.09.25.14.30
- **Fixed**: Menu option 78 (Generate support package) file path permissions - now properly writes to data/ directory
- **Fixed**: Menu option 80 (ARP WebSocket output) file path permissions - now properly saves to data/ directory  
- **Fixed**: Menu option 85 variable scope error - removed duplicate logging statement
- **Fixed**: SSH logging operations - all SSH functions now use proper data/per-host-logs/ directory structure
- **Enhanced**: Container security compliance - all file I/O operations now respect container volume mounting
- **Enhanced**: Configuration management - moved all hardcoded values from run-misthelper.py to .env file
- **Added**: Configurable SSL settings (PYTHONHTTPSVERIFY, SSL_VERIFY, CA bundles) in .env
- **Added**: Configurable container networking (network name, subnet, driver) in .env
- **Added**: Configurable package management settings (UV check, auto-install, dependencies) in .env
- **Added**: Configurable container runtime settings (image name, container names, SSH port) in .env
- **Added**: Configurable file paths (data directory, script log, env file locations) in .env
- **Added**: Configurable container mount paths for custom deployment scenarios in .env
- **Enhanced**: sample.env template with complete configuration options and documentation
- **Verified**: Comprehensive network data capture functionality working correctly

### Version 25.09.23.00.00
- Initial comprehensive README rewrite to match current codebase
- Added SSH remote access capabilities with containerized deployment
- Enhanced menu operation documentation with current truth from code
- Added systematic test mode and performance optimization features

---
**MistHelper** – Practical, transparent data operations for Juniper Mist Cloud.

