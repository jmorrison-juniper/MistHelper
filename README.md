# MistHelper
Network Operations & Data Export Tool for Juniper Mist Cloud

**Operation Count:** The code currently defines 112 actionable menu entries (1–10, 11–89, 90–106, 107–111, 112) with some gaps for future expansion.

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
| 5–8 | WebSocket Commands | MAC table (switches), forwarding table (gateways), routing table (switches - BGP/OSPF/Static), SSR/SRX routing (128T/SRX gateways - Advanced BGP analysis) |
| 9–10 | Packet Capture | Site & org-level packet captures (wireless/wired/gateway/**switch**/scan/MxEdge) with WebSocket streaming |
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
| 87–89 | WebSocket Device Commands | Device ping, ARP, and service ping via WebSocket (real-time output) |
| 90–93 | DESTRUCTIVE Ops | AP firmware upgrade strategies, reboots, virtual chassis conversions |
| 94–96 | Status / Integrity | VC conversion status, gateway stats w/ freshness, WAN port conflict detection |
| 97 | SSH Runner | Enhanced SSH command execution (auto-detect credentials & command file) |
| 98 | SSH by Template | SSH runner targeting gateways by template name (online with management IPs only) |
| 99 | Switch Firmware | **DESTRUCTIVE**: Advanced switch firmware upgrade with mode selection |
| 100 | SSR Firmware | **DESTRUCTIVE**: Advanced SSR firmware upgrade with mode selection |
| 102 | WLAN RADIUS Timers | Manage WLAN RADIUS authentication timers for site or template WLANs |
| 103–104 | Gateway Template WAN2 | Set site variables & migrate templates to use {{wan2_interface}} variable |
| 105 | Template Config Extract | Extract DIA_Pico (traffic steering) & Picocell (application policy) to JSON |
| 106 | Template Config Apply | **DESTRUCTIVE**: Replicate extracted configs to other templates with confirmation |
| 107 | Create Test Sites | **DESTRUCTIVE**: Create 137 test sites from NorthAmericanTestSites.csv - Real landmarks across 13 North American countries |
| 108 | Country RF Templates | **DESTRUCTIVE**: Create country-specific RF templates and assign sites to matching templates (auto/default settings) |
| 109 | AP Model Device Profiles | **DESTRUCTIVE**: Scan org for AP models and create Device Profile per model with inherit/auto settings |
| 110 | Assign APs to Profiles | **DESTRUCTIVE**: Assign APs to Device Profiles matching their model type (AP-{model}) - Skips APs without matching profiles |

Important Notes:
* Options 14 & 18 are resource‑intensive (multi‑hour) and skipped during `--test`.
* 63–65 intentionally marked WIP; expect evolution.
* 90–93, 99–100 should never be scripted unattended without explicit review.

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

License: AGPL-3.0-only (see `pyproject.toml`).

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

```json
{
  "changelog": [
    {
      "version": "25.12.12.21.55",
      "date": "2025-12-12",
      "changes": {
        "feature_additions": [
          "Drawing Tools now functional: Save shapes to Mist API",
          "Drawing mode selector: Choose between Zone, Wall, Path, or Measurement mode",
          "Save Last Shape button: Saves drawn shape to Mist based on selected mode",
          "Zone creation: Draw rectangle, enter name, save as location zone via createSiteZone API",
          "Wall segment creation: Draw line, save as wall_path via updateSiteMap API",
          "Validation path creation: Draw line, save as sitesurvey_path via updateSiteMap API",
          "Delete All Paths: Clears sitesurvey_path array via updateSiteMap API",
          "Delete All Walls: Clears wall_path nodes via updateSiteMap API"
        ],
        "enhancements": [
          "Zone name input field appears when Zone mode is selected",
          "Clear All Drawings button with guidance to use eraser tool",
          "Success/error feedback messages for all save operations"
        ],
        "refactoring": [
          "Removed old placeholder drawing tool buttons (Insert Path/Rectangle/Wall)",
          "Drawing tools now use dropdown mode selector instead of separate buttons"
        ]
      }
    },
    {
      "version": "25.12.12.21.50",
      "date": "2025-12-12",
      "changes": {
        "bug_fixes": [
          "Fixed client refresh coordinates: API returns pixels directly, not meters - removed erroneous PPM multiplication",
          "Client dots now stay visible after refresh instead of disappearing off-screen",
          "Client label annotations now update positions during live refresh"
        ],
        "enhancements": [
          "Added coordinate sample logging to verify refresh data",
          "Added warning log if Clients trace not found during refresh",
          "Removed visibility toggle override during refresh to preserve user settings"
        ]
      }
    },
    {
      "version": "25.12.12.21.35",
      "date": "2025-12-12",
      "changes": {
        "enhancements": [
          "Changed browser tab title from 'Dash' to 'MistHelper Map Viewer'"
        ]
      }
    },
    {
      "version": "25.12.12.21.30",
      "date": "2025-12-12",
      "changes": {
        "bug_fixes": [
          "Suppressed 'Updating...' flash in browser tab during auto-refresh callbacks"
        ],
        "enhancements": [
          "Set update_title=None on Dash app to prevent tab title flicker from 1-second countdown interval"
        ]
      }
    },
    {
      "version": "25.12.12.21.20",
      "date": "2025-12-12",
      "changes": {
        "bug_fixes": [
          "Fixed live refresh trace name mismatch: callback searched for 'wifi client' but trace was named 'Clients'",
          "Client position refresh now correctly updates the map visualization"
        ],
        "enhancements": [
          "Upgraded refresh trace logging from debug to info level for visibility"
        ]
      }
    },
    {
      "version": "25.12.12.17.15",
      "date": "2025-12-12",
      "changes": {
        "enhancements": [
          "Moved live refresh controls from sidebar to header bar for better visibility",
          "Added countdown timers showing seconds until next client refresh and minutes:seconds until RF heatmap refresh",
          "Countdown updates every second when auto-refresh is enabled",
          "Compact refresh control panel with dark background in header"
        ],
        "refactoring": [
          "Added refresh-times-store to track last refresh timestamps for countdown calculation",
          "Added 1-second countdown-tick-interval for real-time countdown display",
          "Updated refresh callbacks to return both figure and refresh times"
        ]
      }
    },
    {
      "version": "25.12.12.16.45",
      "date": "2025-12-12",
      "changes": {
        "feature_additions": [
          "Live data refresh: map viewer now supports automatic refresh of client positions (every 30 seconds) and RF heatmap (every 5 minutes)",
          "Auto-refresh toggle: checkbox in sidebar to enable/disable live data updates",
          "Manual refresh button: 'Refresh Now' button for on-demand data updates",
          "Refresh status indicator: shows current auto-refresh state and timing intervals"
        ],
        "enhancements": [
          "dcc.Store component: stores site_id, map_id, PPM, and map dimensions for refresh callbacks",
          "dcc.Interval components: two separate intervals for clients (30s) and coverage (5min) with disabled-by-default state",
          "Callback architecture: separate callbacks for toggle, client refresh, and coverage refresh with proper state management",
          "API session reference: refresh callbacks use stored API session for authenticated requests"
        ],
        "logging": [
          "Added 'Live data refresh:' prefix to all refresh-related log entries for easy filtering",
          "Logs include timestamp, client counts (WiFi vs Wired), and coverage point counts"
        ]
      }
    },
    {
      "version": "25.12.12.15.35",
      "date": "2025-12-12",
      "changes": {
        "feature_additions": [
          "Unscaled map detection: warns user when map has PPM=0 (not scaled in Mist Portal)",
          "User guidance message: directs users to Location -> Floorplans -> select image -> SET SCALE in Mist Portal"
        ],
        "enhancements": [
          "Explicit warning in console when map_ppm is 0 or missing"
        ]
      }
    },
    {
      "version": "25.12.12.15.30",
      "date": "2025-12-12",
      "changes": {
        "feature_additions": [
          "PPM auto-correction: calculates actual PPM from client x/x_m and y/y_m coordinate ratios",
          "PPM mismatch detection: warns when calculated PPM differs from map stored PPM by more than 10%"
        ],
        "bug_fixes": [
          "RF coverage heatmap now displays correctly on maps where Mist stored incorrect PPM",
          "Fixed heatmap only covering upper-left corner of map due to coordinate scaling mismatch"
        ],
        "enhancements": [
          "Uses first 10 clients with both pixel and meter coordinates to calculate average PPM",
          "Logs PPM validation results (pass/mismatch) with exact values for debugging"
        ]
      }
    },
    {
      "version": "25.12.12.14.30",
      "date": "2025-12-12",
      "changes": {
        "enhancements": [
          "Added heatmap coordinate debug logging to script.log",
          "Logs coverage X/Y ranges in both pixels and meters for PPM validation"
        ],
        "compatibility": [
          "Fixed compose.yml port mappings (2200:2200, 8050:8050)",
          "Fixed volume mount syntax from named volume to bind mount (./data:/app/data:rw)"
        ]
      }
    },
    {
      "version": "25.12.09.14.44",
      "date": "2025-12-09",
      "changes": {
        "compatibility": [
          "Replaced the MIT license file with the official AGPL-3.0 text and updated project metadata (pyproject classifiers, Dockerfile/Containerfile OCI labels, Starlink dashboard header) to keep every artifact aligned."
        ],
        "documentation": [
          "README and READY_FOR_MIGRATION license references now call out AGPL-3.0-only so downstream consumers see the correct terms immediately."
        ]
      }
    },
    {
      "version": "25.12.04.14.15",
      "date": "2025-12-04",
      "changes": {
        "feature_additions": [
          "RF Coverage heatmap: switched to Plotly Heatmap trace with smooth interpolation for better visual quality",
          "Auto-scaled RSSI color range: dynamically adjusts red/blue gradient to actual min/max values in coverage data for maximum contrast",
          "Color scale legend: added colorbar showing RSSI range in dBm with tick marks on right side of map",
          "Orientation indicators: directional dots now always visible for all devices including 0-degree orientation for clarity"
        ],
        "enhancements": [
          "Heatmap interpolation: zsmooth='best' provides smooth color transitions between grid points",
          "Gap interpolation: connectgaps=True fills in missing grid cells for complete coverage visualization",
          "Debug logging: added per-device orientation logging to script.log for troubleshooting",
          "Coordinate system fix: corrected AP orientation angle conversion (Mist 0°=north to math coordinates with Y-axis flip)"
        ],
        "bug_fixes": [
          "AP orientation dots: fixed angle calculation to properly convert Mist orientation (0°=up) to standard cartesian coordinates",
          "Y-axis correction: subtracted Y component in dot placement because Mist uses top-left origin with Y increasing downward",
          "Zero-degree visibility: removed conditional that hid orientation dots when angle=0"
        ]
      }
    },
    {
      "version": "25.12.04.13.15",
      "date": "2025-12-04",
      "changes": {
        "feature_additions": [
          "RF Coverage heatmap overlay: real-time RSSI grid visualization from Mist API location/coverage endpoint",
          "Signal strength color coding (RSSI scale): red (strongest, near 0 dBm), orange (strong >-60dBm), yellow (medium >-70dBm), green (weak >-80dBm), blue (weakest, near -120 dBm)",
          "Map origin marker: coordinate reference point toggle for debugging and validation",
          "RF Diagnostics Heatmap layer control: toggleable coverage overlay in Infrastructure section",
          "Map Origin layer control: show/hide coordinate system origin point"
        ],
        "api_changes": [
          "Added /api/v1/sites/{site_id}/location/coverage API integration with resolution=fine, duration=24h, type=client parameters",
          "Coordinate conversion: API returns METERS, converted to PIXELS using map PPM (pixels per meter)",
          "Coverage data structure: result_def array defines field indices for x, y, max_rssi, avg_rssi values"
        ],
        "enhancements": [
          "RSSI tooltip: hover over grid cells shows Max RSSI and Avg RSSI in dBm",
          "Grid size calculation: coverage gridsize (meters) converted to pixels for proper visualization scale",
          "Error handling: graceful degradation when coverage API unavailable (backend database issues, no data)",
          "Backend error detection: psycopg2/database errors logged as warnings, not errors (expected transient issues)"
        ]
      }
    },
    {
      "version": "25.12.04.13.07",
      "date": "2025-12-04",
      "changes": {
        "feature_additions": [
          "Device status color coding: devices now display with status-based colors (green=connected, red=disconnected, orange=upgrading)",
          "Real-time upgrade status: devices actively upgrading show orange markers with progress percentage in hover tooltip",
          "Status information in tooltips: hover text includes device status (CONNECTED/DISCONNECTED/UPGRADING) and upgrade progress if applicable"
        ],
        "api_changes": [
          "Interactive Maps now uses listSiteDevicesStats API instead of listSiteDevices for real-time status information",
          "Status field and fwupdate.progress field now available for all device markers, labels, and orientation indicators"
        ],
        "enhancements": [
          "Device marker colors: dynamic color array based on individual device status instead of static type-based colors",
          "Crosshair orientation indicators: now use status-based colors matching device state",
          "Device labels: border colors match device status for consistent visual feedback",
          "Type-specific status colors: APs (green/red/orange), Switches (cyan/red/orange), Gateways (magenta/red/orange)"
        ]
      }
    },
    {
      "version": "25.12.03.17.30",
      "date": "2025-12-03",
      "changes": {
        "enhancements": [
          "Larger crosshair indicators: increased from 25px to 40px for better visibility of device orientation markers",
          "Larger orientation dots: increased from 10px to 16px with thicker lines (3px width) for improved visual clarity",
          "Increased dot distance: orientation direction indicator moved from 35px to 50px from device center",
          "Annotation toggle control: all text labels (zones, devices, clients, beacons) now hide/show with their parent layers",
          "Unified visibility management: annotations and traces both controlled by layer toggle callbacks"
        ],
        "bug_fixes": [
          "Fixed layer toggle not hiding device/client/zone/beacon text labels when layers disabled",
          "Added name metadata to all annotations for proper visibility control",
          "Client labels now properly hide when client layers are toggled off",
          "Device orientation indicators (crosshairs and dots) now hide with their parent device layer"
        ]
      }
    },
    {
      "version": "25.12.03.17.15",
      "date": "2025-12-03",
      "changes": {
        "feature_additions": [
          "Organized layer controls: Infrastructure, Beacons & Positioning, Clients, Devices, and Filters sections matching Mist portal",
          "WiFi vs Wired client separation: different markers (circle/square) and colors (green/cyan) for automatic client type detection",
          "Client-AP association lines: dotted green lines showing WiFi client connections to access points",
          "Mesh link visualization: dashed magenta lines displaying mesh topology between access points",
          "vBeacon coverage circles: power-based coverage area visualization with shaded regions",
          "Proximity zones toggle: placeholder for future proximity zone layer support",
          "Excluded clients toggle: placeholder for filtering excluded client devices",
          "Mesh associations toggle: dedicated control for showing/hiding AP mesh links",
          "Hide inactive items filter: placeholder for filtering inactive devices from display",
          "vBeacon coverage control: separate toggle for showing/hiding beacon coverage circles"
        ],
        "enhancements": [
          "Multi-checklist architecture: 5 separate checklists for granular layer management",
          "Client type detection: automatic WiFi/Wired classification based on SSID field presence",
          "Coverage radius calculation: dynamic radius based on vBeacon power level (-12 to +4 dBm range)",
          "Client-AP linking: automatic AP lookup by MAC address for association line drawing",
          "Mesh topology detection: automatic mesh uplink discovery from device mesh_uplink field",
          "Layer toggle callback: enhanced to handle multiple checklist inputs with combined layer array",
          "Map statistics: added vBeacon and BLE beacon counts to Map Info panel",
          "Add vBeacon/Beacon buttons: header toolbar buttons with green/cyan color coding"
        ],
        "api_changes": [
          "Added math.cos, math.sin, math.pi imports for parametric circle calculations",
          "Client markers: WiFi uses go.Scatter with circle symbol, Wired uses square symbol",
          "Beacon coverage: uses Plotly fill='toself' with transparent green overlay"
        ],
        "documentation": [
          "Layer controls now match Mist portal Location Settings panel organization",
          "Client separation provides visual distinction between WiFi and Wired network access"
        ]
      }
    },
    {
      "version": "25.12.03.16.47",
      "date": "2025-12-03",
      "changes": {
        "feature_additions": [
          "Auto-Zone button: AI-powered zone detection feature in header toolbar (purple highlight)",
          "Location Zones panel: dedicated sidebar section with individual zone checkboxes",
          "Zone visibility toggles: show/hide individual zones independently from checklist",
          "Selected Zone Info: displays zone name and client count when zone is clicked",
          "Zone management buttons: Edit and Remove buttons for zone operations (purple and red)",
          "Individual zone controls: checklist shows all zones with their names from API data"
        ],
        "enhancements": [
          "Auto-Zone UI: prominent purple button with robot emoji in header utilities bar",
          "Zone checklist: all zones checked by default, styled with dark theme",
          "Zone selection feedback: green highlighted text shows selected zone details",
          "Edit zone placeholder: guides to Mist API updateSiteMap for vertex modification",
          "Remove zone warning: red destructive warning for zone deletion operations",
          "Click handling: detects zone clicks from hovertext and displays zone information"
        ],
        "documentation": [
          "Added Location Zones panel matching Juniper Mist portal zone management interface",
          "Auto-Zone feature provides AI-powered automatic zone creation from wall analysis"
        ]
      }
    },
    {
      "version": "25.12.03.16.44",
      "date": "2025-12-03",
      "changes": {
        "feature_additions": [
          "Drawing Tools panel: matches Mist portal sidebar with 5 quick-action buttons",
          "Insert Path button: guides users to Draw Path tool for creating validation paths (magenta)",
          "Insert Rectangle button: guides users to Draw Rectangle tool for creating zones (cyan)",
          "Insert Wall button: guides users to Draw Path tool for creating wall segments (orange)",
          "Delete all Paths button: placeholder for removing sitesurvey_path via API (red warning)",
          "Delete all Walls button: placeholder for removing wall_path data via API (red warning)"
        ],
        "enhancements": [
          "Drawing Tools UI: color-coded buttons matching element types (magenta/cyan/orange/red)",
          "Tool guidance: status messages direct users to appropriate toolbar drawing tools",
          "Destructive warnings: delete buttons highlighted in red with bold warnings",
          "Sidebar reorganization: Drawing Tools section above Measurement Tools for better workflow",
          "Compact layout: measurement tools condensed with smaller font for space efficiency"
        ],
        "documentation": [
          "Added Drawing Tools panel matching Juniper Mist portal map editor interface",
          "Quick-action buttons provide shortcuts and guidance for common map editing tasks"
        ]
      }
    },
    {
      "version": "25.12.03.16.41",
      "date": "2025-12-03",
      "changes": {
        "feature_additions": [
          "Validation Paths display: renders sitesurvey_path data from map with magenta dotted lines",
          "Path visualization: connected line segments with diamond markers (10px, white border)",
          "Path labels: name annotation at start point with magenta background",
          "Layer toggle: added 'Validation Paths' checkbox to show/hide paths independently",
          "Map info stats: displays count of validation paths in sidebar statistics panel"
        ],
        "enhancements": [
          "Validation path styling: magenta color (#ff00ff) with dotted line style for clear differentiation",
          "Hover information: shows path name and point count on mouseover",
          "Path naming: displays custom path names or defaults to 'Path 1', 'Path 2', etc.",
          "Coordinate processing: extracts x,y from path coordinate arrays with validation",
          "Logging integration: debug messages for path rendering with point counts"
        ],
        "documentation": [
          "Added validation paths feature matching Juniper Mist portal site survey path capability",
          "Validation paths used for Wi-Fi coverage testing and performance analysis along routes"
        ]
      }
    },
    {
      "version": "25.12.03.16.39",
      "date": "2025-12-03",
      "changes": {
        "enhancements": [
          "Utilities UI redesign: replaced dropdown with horizontal button bar for cleaner interface",
          "Direct action buttons: Change Image, Remove Image, Rename, Delete as individual buttons in header",
          "Visual hierarchy: Delete button highlighted in red (#ff4444) for critical action awareness",
          "Improved spacing: buttons in header bar with inline status messages",
          "Darker header: #2a2a2a background for better contrast with map area"
        ],
        "refactoring": [
          "Callback optimization: replaced dropdown Input with multiple button Inputs using callback_context",
          "Button state tracking: uses dash.callback_context to identify which button was clicked"
        ]
      }
    },
    {
      "version": "25.12.03.16.38",
      "date": "2025-12-03",
      "changes": {
        "feature_additions": [
          "Utilities dropdown menu: matches Mist portal top-right dropdown with 4 map management operations",
          "Change Image: placeholder for updateSiteMapImage API call (requires file upload implementation)",
          "Remove Image: placeholder for deleteSiteMapImage API call with DESTRUCTIVE warning",
          "Rename Floorplan: placeholder for updateSiteMap API call (requires text input dialog)",
          "Delete Floorplan: placeholder for deleteSiteMap API call with critical DESTRUCTIVE warning"
        ],
        "enhancements": [
          "Utilities UI: dropdown positioned in header top-right matching Mist portal layout",
          "Action feedback: status messages display warnings for destructive operations",
          "Color coding: orange for caution (change/rename), red for destructive (remove/delete)",
          "Logging integration: all utility actions logged with map_id for audit trail",
          "Header redesign: title and utilities dropdown in flex layout with purple border separator"
        ],
        "documentation": [
          "Added Utilities dropdown matching Juniper Mist portal map management interface",
          "Placeholder implementations note required API integrations for full functionality"
        ]
      }
    },
    {
      "version": "25.12.03.16.35",
      "date": "2025-12-03",
      "changes": {
        "feature_additions": [
          "Set Origin feature: click map to define coordinate system origin point with blue crosshair marker",
          "Origin setting mode: toggle button activates click-to-set mode with visual feedback (purple highlight)",
          "Blue crosshair marker: 40px crosshair with center dot at origin point (matches Mist portal UI)",
          "Origin persistence: stores origin_x and origin_y in figure metadata for coordinate transformations",
          "Dynamic origin updates: crosshair marker moves when origin is repositioned via click"
        ],
        "enhancements": [
          "Set Origin UI: toggle button with mode indicator in sidebar Tools section",
          "Visual feedback: button highlights in purple when origin-setting mode is active",
          "Status display: shows current origin coordinates and confirmation when set",
          "Origin initialization: loads existing origin_x/origin_y from map data if present",
          "Interactive workflow: click button to activate, click map to set, click button again to exit mode"
        ],
        "documentation": [
          "Added Set Origin feature matching Juniper Mist portal coordinate system alignment capability"
        ]
      }
    },
    {
      "version": "25.12.03.16.32",
      "date": "2025-12-03",
      "changes": {
        "feature_additions": [
          "Set Scale tool: calibrate map PPM by drawing a line and entering its known length in meters",
          "Interactive scale calibration: matches Mist portal 'Set Scale' feature for accurate measurements",
          "Real-time measurement updates: all existing ruler measurements automatically recalculate when scale changes",
          "PPM persistence: calibrated scale stored in figure metadata and used for all future measurements",
          "User feedback: status messages show old PPM → new PPM conversion with pixel-to-meter ratio"
        ],
        "enhancements": [
          "Set Scale UI: input field for length in meters + button in sidebar Tools section",
          "Workflow guidance: numbered steps (1. Draw line, 2. Enter length) for clear user instructions",
          "Dynamic PPM: measurement callback reads current PPM from figure metadata instead of static value",
          "Scale validation: prevents setting scale with invalid/missing length or without drawn line",
          "Professional styling: scale input and button match dark theme with purple accent (#667eea)"
        ],
        "documentation": [
          "Added Set Scale feature matching Juniper Mist portal UI/UX for floor plan calibration"
        ]
      }
    },
    {
      "version": "25.12.03.16.30",
      "date": "2025-12-03",
      "changes": {
        "enhancements": [
          "Map viewer rotation indicators: replaced triangular wedges with Mist-style crosshair + directional dot",
          "Crosshair: 25px horizontal and vertical lines at device center (always visible)",
          "Directional dot: 10px marker positioned 35px from center at orientation angle (only if angle != 0)",
          "Crosshair color matches device type (green for APs, orange for switches, magenta for gateways)",
          "Dot shows orientation angle on hover for quick reference"
        ],
        "documentation": [
          "Updated rotation indicator design to match Juniper Mist portal UI/UX patterns"
        ]
      }
    },
    {
      "version": "25.12.03.16.22",
      "date": "2025-12-03",
      "changes": {
        "bug_fixes": [
          "Fixed map viewer text labels: replaced CSS text-shadow (doesn't work on SVG) with Plotly annotations",
          "Device names now have black semi-transparent background boxes with colored borders for readability",
          "Client names now have green semi-transparent background boxes for readability",
          "Zone labels now appear in upper-left corner of each zone with colored background matching zone border"
        ],
        "enhancements": [
          "Map viewer text rendering: switched from mode='markers+text' to mode='markers' + separate annotations",
          "Annotation-based labels: support bgcolor, bordercolor, borderwidth, and borderpad for professional appearance",
          "Device labels: positioned 15px above markers with device-type-specific colored borders (green/orange/magenta)",
          "Client labels: positioned 10px above markers with smaller font and green styling",
          "Zone labels: automatically positioned at min(x), min(y) coordinates (upper-left bounding box corner)",
          "Improved label positioning: all labels use xanchor/yanchor for precise placement without overlap"
        ],
        "documentation": [
          "Added technical note in CSS explaining why text-shadow doesn't work on Plotly SVG elements",
          "Removed obsolete text-shadow CSS rules that had no effect on map labels"
        ]
      }
    },
    {
      "version": "25.12.02.20.30",
      "date": "2025-12-02",
      "changes": {
        "feature_additions": [
          "Maps Manager Menu 12: Full map cloning with automatic image download and re-upload",
          "Clone includes all map properties: dimensions, PPM, orientation, walls, wayfinding paths, site survey paths",
          "Automatic image handling: downloads source map image to temp file, uploads to cloned map, cleans up temp file",
          "Complete wall_path cloning: preserves RF modeling data (critical for propagation calculations)",
          "Wayfinding data cloning: copies wayfinding_path nodes/edges and wayfinding configuration",
          "Geographic data cloning: latlng, latlng_br, origin_x, origin_y for Google Maps integration",
          "Configuration cloning: occupancy_limit, locked status, view settings, sitesurvey_path arrays",
          "Comprehensive clone summary: displays all cloned elements with confirmation of image upload status"
        ],
        "enhancements": [
          "Clone operation uses temporary files for image download/upload to avoid filesystem pollution",
          "Automatic cleanup of temporary files in all code paths (success, failure, exception)",
          "Enhanced error handling with separate warnings for download vs upload failures",
          "User-friendly progress messages at each stage: select, download, create, upload, complete",
          "Clone confirmation shows full plan before execution including image copy status",
          "Educational note: zones are site-level objects (not map objects) requiring separate cloning"
        ],
        "documentation": [
          "Added comprehensive docstring explaining full clone capability including image/walls/paths/zones",
          "Clone summary clearly shows which elements were successfully copied"
        ]
      }
    },
    {
      "version": "25.12.02.18.00",
      "date": "2025-12-02",
      "changes": {
        "feature_additions": [
          "Menu #112: Maps Manager - Comprehensive class for site floorplan and map operations with interactive sub-menu system",
          "Maps Manager Sub-menu - 19 organized operations: Data/Export (4), Management (5), Device Placement (4), Bulk Operations (3), Analytics (3)",
          "Map listing and export - List maps for sites, export all site maps to CSV/SQLite with flattened metadata and image URLs",
          "Map image download - Download full-resolution map images to organized directories (data/map_images/{site_name}/)",
          "Map details viewer - Display comprehensive map metadata: name, ID, type, dimensions, PPM, orientation, URLs, timestamps",
          "Map creation - Interactive map creation with type selection (image/google), dimension input, validation",
          "Bulk operations - Export all org maps across sites, download all images (implemented), backup maps (placeholder)",
          "Analytics reports - Maps without images report (implemented), coverage analysis (placeholder), device density (placeholder)",
          "MapsManager class - Follows established patterns: WebSocketManager, PacketCaptureManager, FirmwareManager architecture"
        ],
        "enhancements": [
          "Database schema - Added natural primary key strategies for listSiteMaps and getSiteMap with proper indexes",
          "Interactive sub-menu - Single entry point (Menu 112) with 0 to return to main menu, organized by operation category",
          "Safety features - Input validation, EOF/interrupt handling, confirmation prompts for destructive operations (placeholders)",
          "Image handling - JWT token URL support, automatic format detection (png/jpg), organized directory structure by site",
          "Progress indicators - tqdm progress bars for bulk site/map operations with descriptive labels",
          "Error handling - Graceful per-site error logging without halting bulk operations, comprehensive exception tracking"
        ],
        "documentation": [
          "Updated operation count from 111 to 112 total menu entries",
          "Added Maps Manager category section to menu_actions documentation",
          "Documented map database strategies in ENDPOINT_PRIMARY_KEY_STRATEGIES configuration"
        ]
      }
    },
    {
      "version": "25.12.02.17.15",
      "date": "2025-12-02",
      "changes": {
        "feature_additions": [
          "Gateway template lists now sorted alphabetically across all menus (93, 104, 105, 111)",
          "Improved user experience with consistent template ordering in selection prompts"
        ],
        "documentation": [
          "Updated agents.md Git workflow - clarified that staging alone does not create checkpoints",
          "Added minimal Git workflow instructions for local commits and rollback procedures",
          "Removed verbose workflow examples, keeping only essential commands for AI agents"
        ]
      }
    },
    {
      "version": "25.12.02.16.43",
      "date": "2025-12-02",
      "changes": {
        "feature_additions": [
          "Menu 104: Added bidirectional operation mode - now supports both APPLY and REVERT directions",
          "Menu 104: Users can now REVERT variable migration ({{wan2_interface}} back to ge-0/0/1)",
          "Menu 104: Added operation direction prompt after template selection (Apply variable or Revert to hardcoded)",
          "Menu 104: Both modes automatically migrate device-level port overrides to preserve static IPs",
          "Menu 104: Dynamic search/replace logic adapts to selected direction",
          "Menu 111: Created clone_gateway_templates_by_state_and_country() for geographic template cloning",
          "New menu option enables bulk gateway template creation organized by state and country codes",
          "Templates automatically named with Branch_{STATE/COUNTRY} pattern (e.g., Branch_CA, Branch_TX, Branch_US)",
          "Supports batch assignment of sites to matching templates based on geographic location"
        ],
        "bug_fixes": [
          "Menu 111: Fixed API endpoint - now uses updateSiteInfo instead of non-existent updateSite",
          "Menu 111: Fixed state extraction - now parses state codes from address field using regex",
          "Address parsing handles US/CA comma-separated format (2-letter codes with ZIP/postal)",
          "Address parsing handles MX/Central America space-separated format (state names before postal)",
          "Fixed Canadian addresses without commas: Now correctly extracts province codes (ON, BC, QC) before postal patterns",
          "Fixed Canadian postal code prefixes (G1R, L2G, V6G, T1L, T0E, R0B) being misidentified as provinces",
          "Fixed small island nations (Bahamas, Belize, Cuba, Haiti, Jamaica, Dominican Republic) now use country-only grouping",
          "Added special handling for multi-word territories: Puerto Rico, Bay Islands",
          "Fixed Panama city names (Panama City Panama) being incorrectly parsed as state",
          "Canadian province extraction now matches 2-letter code at start of address component, not embedded in postal",
          "Supports extraction from multiple address formats: US (KS 66053), CA (ON M5H 2N2), MX (Yucatan 97751)",
          "Handles address formats with embedded state codes between city names and ZIP codes",
          "Fallback logic handles missing or malformed address data gracefully"
        ],
        "testing_validation": [
          "Added --testinteractive flag for testing read-only menu options requiring user input",
          "Created run_interactive_test() function testing 22 interactive menu operations",
          "Updated --test unsafe_options skip list with menu options 103-111",
          "Added --dry-run flag support for previewing destructive operations without execution"
        ],
        "api_changes": [
          "Menu 53: Fixed export_site_specific_data to conditionally pass 'limit' parameter only when supported",
          "Added signature introspection to detect API function parameters before calling",
          "Prevents 'unexpected keyword argument limit' errors for APIs without pagination support",
          "Menu 104: Integrated --dry-run flag into update_gateway_templates_wan2_variable()"
        ],
        "performance": [
          "Fixed tqdm progress bar TypeError by using concurrent.futures.as_completed correctly",
          "Changed progress tracking to avoid dict+float type conflicts in parallel execution",
          "Menu 111 uses CSV caching to minimize API calls during state/country analysis"
        ],
        "documentation": [
          "Added detailed docstrings for clone_gateway_templates_by_state_and_country() explaining address parsing logic",
          "Documented support for US, CA, MX, CR, PA, HN, GT, and other Central American address formats",
          "Updated menu option tables with entry 111 for gateway template cloning by geography",
          "Documented --testinteractive and --dry-run CLI flag usage in help text",
          "Noted limitations: Multi-word state names (e.g., 'Quintana Roo') may capture last word only"
        ]
      }
    },
    {
      "version": "25.12.02.11.10",
      "date": "2025-12-02",
      "changes": {
        "bug_fixes": [
          "CRITICAL: Fixed multi-token API initialization - now passes all tokens as comma-separated string to mistapi",
          "Previously passed individual tokens separately, preventing mistapi from rotating through tokens on rate limits",
          "mistapi library's token rotation (HTTP 429 handling) now works correctly with multiple tokens",
          "Removed unnecessary iteration that created separate initialization attempts per token"
        ],
        "performance": [
          "Multiple API tokens now properly utilized for rate limit avoidance",
          "When one token hits 429 rate limit, mistapi automatically rotates to next token",
          "Reduces initialization attempts from N*M to M (where N=token count, M=param names)"
        ],
        "documentation": [
          "Added code comments explaining mistapi's expectation of comma-separated token string",
          "Documented that mistapi handles token rotation internally when configured correctly"
        ]
      }
    },
    {
      "version": "25.12.02.11.05",
      "date": "2025-12-02",
      "changes": {
        "bug_fixes": [
          "Fixed 'dict + float' TypeError in retry_failed_sites function when using tqdm with as_completed",
          "Resolved parameter conflict where tqdm's 'total' argument was being passed to concurrent.futures.as_completed as 'timeout'",
          "Refactored retry progress tracking to use tqdm context manager with manual update calls",
          "Changed from wrapping as_completed() directly to iterating over future list with separate tqdm progress bar"
        ],
        "performance": [
          "Retry progress bar now updates correctly without causing type errors in concurrent execution",
          "Progress tracking maintains same user experience while avoiding parameter collision"
        ]
      }
    },
    {
      "version": "25.12.02.11.15",
      "date": "2025-12-02",
      "changes": {
        "bug_fixes": [
          "Identified root cause of API session initialization failures: mistapi library v0.57.3 bug in token validation",
          "Added comprehensive traceback logging for all API session initialization attempts",
          "Reordered API session initialization to try direct token methods before env_file method",
          "Enhanced error messages with full stack traces to aid in diagnosing mistapi library issues"
        ],
        "debugging": [
          "Full exception tracebacks now logged at INFO level for API session failures (no longer requires debug mode)",
          "Traceback shows mistapi library attempting to iterate over None in privileges validation",
          "Issue occurs in mistapi.__api_session.py line 515: for priv in data_json.get('privileges')",
          "Error indicates API tokens may be expired, invalid, or returning unexpected response format"
        ],
        "documentation": [
          "Identified that error occurs when mistapi library validates tokens against Mist API",
          "Token validation failure suggests tokens need to be refreshed or regenerated",
          "mistapi library bug: does not handle missing 'privileges' key in API response gracefully"
        ]
      }
    },
    {
      "version": "25.12.02.11.00",
      "date": "2025-12-02",
      "changes": {
        "bug_fixes": [
          "Enhanced exception logging in main application error handler to capture full traceback",
          "Added comprehensive type validation for start_time variable to detect dict/float type mismatch early",
          "Added defensive type checking for API response data in fetch_site_port_stats worker function",
          "Improved error diagnostics by logging time module state when type errors occur"
        ],
        "debugging": [
          "Main exception handler now logs complete stack traces for unhandled exceptions",
          "Added early type validation to catch 'dict + float' errors at source rather than during calculation",
          "Worker function validates mistapi.get_all returns list type before processing",
          "Enhanced logging shows time module and time.time function types when errors detected"
        ]
      }
    },
    {
      "version": "25.12.01.17.40",
      "date": "2025-12-01",
      "changes": {
        "enhancements": [
          "Menu 14 (fast mode): Added extensive debug logging to track data type issues in parallel processing",
          "Added type validation logging for start_time, end_time, and duration calculations",
          "Added logging for successful_results and failed_sites return types from execute_with_connection_pool_management",
          "Added per-result type checking in flattening loop with warnings for unexpected types",
          "Added site tuple structure validation logging to diagnose dict vs tuple issues"
        ],
        "debugging": [
          "Comprehensive logging added to isolate 'dict + float' arithmetic error source",
          "All time calculations now log intermediate values and types",
          "Result list processing logs each item's type before extend operation",
          "Sites list construction logs sample entries with type information"
        ]
      }
    },
    {
      "version": "25.12.01.17.35",
      "date": "2025-12-01",
      "changes": {
        "bug_fixes": [
          "Fixed 'unsupported operand type(s) for +: dict and float' error in rate limiting calculation",
          "Removed orphaned docstring inside compute_dynamic_alpha function that was preventing proper return value",
          "Added defensive type checking for alpha value to ensure it's always a valid float before arithmetic operations",
          "Alpha value now validated and falls back to 0.3 if invalid (NaN, Inf, or wrong type)"
        ]
      }
    },
    {
      "version": "25.12.01.17.30",
      "date": "2025-12-01",
      "changes": {
        "bug_fixes": [
          "Menu 14 (fast mode): Removed invalid 'type' parameter from searchSiteSwOrGwPorts API call",
          "Fixed 'got an unexpected keyword argument type' error in parallel port stats retrieval",
          "API endpoint searches both switches and gateways by default without type filter"
        ]
      }
    },
    {
      "version": "25.12.01.17.20",
      "date": "2025-12-01",
      "changes": {
        "bug_fixes": [
          "Menu 14: Fixed crash when API returns unexpected response structure (missing 'results' key)",
          "Added KeyError recovery logic to handle malformed API responses gracefully",
          "Emergency data save now preserves all collected records before error exit"
        ],
        "performance": [
          "Menu 14 (fast mode): Added site-level parallelization for port statistics retrieval",
          "Fast mode now fetches port stats across multiple sites concurrently instead of serial org-level search",
          "Uses connection pool management with configurable concurrency (FAST_MODE_MAX_CONCURRENT_CONNECTIONS)",
          "Parallel fetching can reduce execution time from hours to minutes depending on site count"
        ],
        "enhancements": [
          "Enhanced error handling in fetch_and_display_api_data with three-layer defense against data loss",
          "Added response structure validation and logging for debugging unexpected API formats",
          "Automatic recovery attempts from alternate response structures (response.data['data'], direct lists)",
          "User-friendly messages explain partial data saves and recovery attempts",
          "Detailed debug logs capture response types and available keys for troubleshooting"
        ],
        "api_changes": [
          "Fast mode uses searchSiteSwOrGwPorts per-site instead of searchOrgSwOrGwPorts org-wide",
          "Leverages cached site list from SiteList.csv to minimize API overhead",
          "Each site fetch includes retry logic with exponential backoff",
          "Results aggregated and deduplicated across all sites"
        ],
        "documentation": [
          "Updated export_device_port_stats_to_csv docstring with performance optimization notes",
          "Added fetch_and_display_api_data docstring explaining enhanced error handling layers",
          "Documented safety features: emergency saves, structure validation, graceful degradation"
        ]
      }
    },
    {
      "version": "25.11.25.13.49",
      "date": "2025-11-25",
      "changes": {
        "bug_fixes": [
          "Menu 110: Fixed API call from assignOrgDeviceProfiles (plural) to assignOrgDeviceProfile (singular)",
          "Corrected mistapi endpoint path to match Mist API specification"
        ],
        "api_changes": [
          "Updated Device Profile assignment to use correct endpoint: mistapi.api.v1.orgs.deviceprofiles.assignOrgDeviceProfile"
        ]
      }
    },
    {
      "version": "25.11.25.13.40",
      "date": "2025-11-25",
      "changes": {
        "feature_additions": [
          "Menu 110: Assign APs to Device Profiles - Automatically assigns APs to matching Device Profiles based on model type",
          "Scans organization AP inventory and matches each AP to Device Profile with naming AP-{model}",
          "Skips APs without matching Device Profiles (no error if profile doesn't exist)",
          "Analyzes and reports APs with profiles, without profiles, and without model information",
          "Bulk assignment using Device Profile assign endpoint for efficiency"
        ],
        "api_changes": [
          "Uses mistapi.api.v1.orgs.inventory.getOrgInventory with type=ap to scan AP inventory",
          "Uses mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles with type=ap to get existing profiles",
          "Uses mistapi.api.v1.orgs.deviceprofiles.assignOrgDeviceProfiles to assign APs to profiles",
          "Assignment payload includes macs array for device assignment"
        ],
        "documentation": [
          "Menu 110 marked as DESTRUCTIVE operation requiring 'ASSIGN' confirmation",
          "Pre-assignment analysis shows counts of APs with/without matching profiles",
          "Operation count updated from 110 to 111 total menu operations",
          "Lists APs that will be skipped due to missing matching Device Profiles"
        ],
        "security": [
          "Requires explicit uppercase 'ASSIGN' confirmation before device assignment",
          "Safe input handling with EOF protection for container environments",
          "Rate limiting with 0.3s delay between AP assignments"
        ],
        "enhancements": [
          "Pre-flight analysis shows assignment plan before execution",
          "Exports successful assignments to SuccessfulAPProfileAssignments.csv with AP/profile details",
          "Exports failed assignments to FailedAPProfileAssignments.csv for troubleshooting",
          "Exports skipped APs to SkippedAPsNoMatchingProfile.csv for profile creation planning",
          "Comprehensive summary report showing successful, failed, and skipped counts",
          "Detailed logging for each AP assignment with full error context",
          "Gracefully skips APs without model information instead of failing"
        ]
      }
    },
    {
      "version": "25.11.25.13.23",
      "date": "2025-11-25",
      "changes": {
        "feature_additions": [
          "Menu 109: Create AP Model Device Profiles - Scans organization for all WiFi AP device models and creates one Device Profile per model",
          "Handles sub-model revisions (e.g., AP41US, AP41WW) as separate profiles for regional variants",
          "Creates minimal Device Profiles with inherit/auto settings for maximum flexibility",
          "Profile naming convention: AP-{model} (e.g., AP-AP41US, AP-AP41WW, AP-AP43)",
          "Detects and skips existing Device Profiles to avoid duplicates"
        ],
        "api_changes": [
          "Uses mistapi.api.v1.orgs.devices.listOrgDevices with type=ap filter to scan AP inventory",
          "Uses mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles with type=ap to check existing profiles",
          "Uses mistapi.api.v1.orgs.deviceprofiles.createOrgDeviceProfile for profile creation",
          "Device Profile payload includes only name and type=ap - all other settings inherit from templates/site/org"
        ],
        "documentation": [
          "Menu 109 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation",
          "Device Profiles created with minimal payload to ensure all settings inherit/auto by default",
          "Operation count updated from 109 to 110 total menu operations",
          "Devices without model information are logged and reported but do not block execution"
        ],
        "security": [
          "Requires explicit uppercase 'CREATE' confirmation before profile creation",
          "Safe input handling with EOF protection for container environments",
          "Rate limiting with 0.5s delay between Device Profile creations"
        ],
        "enhancements": [
          "Progress display shows unique AP models discovered across organization",
          "Exports successful creations to CreatedAPModelDeviceProfiles.csv with model/profile/ID details",
          "Exports failures to FailedAPModelDeviceProfiles.csv for troubleshooting",
          "Comprehensive summary report showing profiles created, failed, and skipped (existing)",
          "Detailed logging for each profile creation with full error context",
          "Warns about devices with missing model information for inventory visibility"
        ]
      }
    },
    {
      "version": "25.11.25.12.28",
      "date": "2025-11-25",
      "changes": {
        "feature_additions": [
          "Menu 108: Create country-specific RF templates and auto-assign sites to matching templates",
          "Scans all organization sites to identify unique country codes",
          "Creates one RF template per country with naming convention RF-{country_code} (e.g., RF-US, RF-CA, RF-MX)",
          "Auto-assigns each site to its corresponding country RF template via rftemplate_id field",
          "Detects and reuses existing country RF templates to avoid duplicates"
        ],
        "api_changes": [
          "Uses mistapi.api.v1.orgs.rftemplates.createOrgRfTemplate for template creation",
          "Uses mistapi.api.v1.sites.sites.updateSite to assign rftemplate_id to sites",
          "Uses mistapi.api.v1.orgs.sites.listOrgSites to scan site inventory",
          "Uses mistapi.api.v1.orgs.rftemplates.listOrgRfTemplates to check for existing templates"
        ],
        "documentation": [
          "Menu 108 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation",
          "RF template configuration uses default/auto settings: band_24 (20MHz auto), band_5 (40MHz auto), band_6 (80MHz auto)",
          "Operation count updated from 108 to 109 total menu operations",
          "Sites without country codes are skipped with warning message and logged"
        ],
        "security": [
          "Requires explicit uppercase 'CREATE' confirmation before template creation and site assignment",
          "Safe input handling with EOF protection for container environments",
          "Rate limiting with 0.5s delay between template creations and 0.3s between site assignments"
        ],
        "enhancements": [
          "Progress display shows country distribution and site counts per country",
          "Exports successful assignments to SuccessfulRFTemplateAssignments.csv with site/template details",
          "Exports failures to FailedRFTemplateAssignments.csv for troubleshooting",
          "Comprehensive summary report showing templates created, sites assigned, failures, and skipped sites",
          "Detailed logging for each template creation and site assignment with full error context",
          "Template reuse logic - skips creation if RF-{country} template already exists"
        ]
      }
    },
    {
      "version": "25.11.25.14.30",
      "date": "2025-11-25",
      "changes": {
        "feature_additions": [
          "Menu 107: Create 137 test sites from CSV - Generates test sites based on real North American landmarks across 13 countries",
          "NorthAmericanTestSites.csv created with 137 popular, well-known, and historical locations",
          "Geographic distribution: US (85), Canada (11), Mexico (10), Costa Rica (4), Guatemala (4), Panama (4), Bahamas (3), Belize (3), Cuba (3), Honduras (3), Jamaica (3), Dominican Republic (3), Haiti (2)",
          "Sites include complete metadata: address, coordinates (lat/lng), timezone, country code, and descriptive notes",
          "Site names use no spaces for clean URL/API compatibility (e.g., ChichenItza, CostaRicaArenalVolcano)",
          "Sites span diverse categories: ancient ruins, national parks, UNESCO sites, colonial cities, beaches, volcanoes, coral reefs"
        ],
        "api_changes": [
          "Uses mistapi.api.v1.orgs.sites.createOrgSite for site creation",
          "Implements proper site payload structure per Mist API OpenAPI specification",
          "Supports optional fields: address, country_code, latlng, timezone, notes",
          "Country codes include: US, CA, MX, GT, CR, PA, HN, BZ, BS, CU, JM, DO, HT (13 total North American nations)"
        ],
        "documentation": [
          "Menu 107 marked as DESTRUCTIVE operation requiring 'CREATE' confirmation",
          "CSV structure documented: name (required), address, country_code, lat, lng, timezone, notes",
          "Operation count updated from 107 to 108 total menu operations"
        ],
        "security": [
          "Requires explicit uppercase 'CREATE' confirmation before execution",
          "Safe input handling with EOF protection for container environments",
          "Rate limiting with 0.5s delay between site creations to avoid API throttling"
        ],
        "enhancements": [
          "Progress display shows site creation status with index counter",
          "Exports successful creations to CreatedTestSites.csv with site IDs",
          "Exports failures to FailedTestSites.csv for troubleshooting",
          "Comprehensive summary report showing total/success/failure counts",
          "Detailed logging for each site creation attempt with full error context"
        ]
      }
    },
    {
      "version": "25.11.25.09.30",
      "date": "2025-11-25",
      "changes": {
        "feature_additions": [
          "Menu 25: Added master CSV export with simplified column headers (serial, model, Street Address, City, State, Zip)",
          "Menu 25: Master inventory file exported to data/CombinedInventory_ByWeek/CombinedInventory_Master.csv",
          "Menu 25: Maintains all existing weekly CSV files and summary report functionality"
        ],
        "documentation": [
          "Menu 25: Updated function docstring to document all three output files (weekly, summary, master)"
        ]
      }
    },
    {
      "version": "25.11.21.17.00",
      "date": "2025-11-21",
      "changes": {
        "performance": [
          "Menu 104: Integrated fast mode for parallel device override migration with connection pooling",
          "Menu 104: Processes devices concurrently when fast=True and >5 devices need migration",
          "Menu 104: Uses execute_with_connection_pool_management() for semaphore-based connection limiting (8 max)",
          "Menu 104: Automatic threading strategy - connection-aware mode limits threads to connection pool capacity",
          "Menu 104: Example performance - 50 devices: Sequential ~50 API calls, Fast mode ~13 seconds with 8 parallel workers"
        ],
        "feature_additions": [
          "Menu 104: Added fast parameter to function signature for fast mode support",
          "Menu 104: Worker function migrate_single_device_override() for parallel device migrations",
          "Menu 104: Conditional execution - uses fast mode for >5 devices, falls back to sequential for smaller batches",
          "Menu 104: Retry logic inherited from execute_with_connection_pool_management() for transient failures"
        ],
        "refactoring": [
          "Menu 104: Extracted device migration logic into reusable worker function",
          "Menu 104: Sequential mode uses same worker function with dummy semaphore for code consistency",
          "Menu 104: Menu actions updated to lambda wrapper passing fast parameter"
        ],
        "logging_analytics": [
          "Menu 104: Console output shows fast mode status and connection pool usage",
          "Menu 104: Progress tracking via execute_with_connection_pool_management() batch progress bars",
          "Menu 104: Debug logging shows connection-aware vs CPU-aware threading mode selection"
        ]
      }
    },
    {
      "version": "25.11.13.16.15",
      "date": "2025-11-13",
      "changes": {
        "feature_additions": [
          "Menu 104: CRITICAL - Added automatic device override migration to preserve static IPs during template migration",
          "Menu 104: After template migration, automatically identifies devices with ge-0/0/1 port overrides",
          "Menu 104: Renames device port_config keys from 'ge-0/0/1' to '{{wan2_interface}}' to preserve static IP configurations",
          "Menu 104: Handles both base ports and subinterfaces (e.g., ge-0/0/1.70 -> {{wan2_interface}}.70)",
          "Menu 104: Generates separate device migration report (GatewayDevice_WAN2_Override_Migration.csv)",
          "Menu 104: Prevents connectivity loss at sites with locally unique static IPs (e.g., Morrison House 2.3.4.5/24)"
        ],
        "api_changes": [
          "Menu 104: Now uses updateSiteDevice API to migrate device-level port configurations",
          "Menu 104: Loads AllSiteGatewayConfigs.csv to identify devices needing override migration"
        ],
        "logging_analytics": [
          "Menu 104: Enhanced summary shows both template AND device migration statistics",
          "Menu 104: Separate success/failure tracking for template vs device migrations",
          "Menu 104: Warnings if device migrations fail (potential static IP loss)"
        ],
        "documentation": [
          "Menu 104: Updated docstring explains device override preservation critical safety feature",
          "Menu 104: Console output clearly shows two-phase migration: templates then device overrides",
          "Menu 104: Explains risk of static IP loss without device override migration"
        ]
      }
    },
    {
      "version": "25.11.13.15.45",
      "date": "2025-11-13",
      "changes": {
        "bug_fixes": [
          "CRITICAL: Menu 103 now correctly detects IP overrides on WAN subinterfaces (e.g., ge-0/0/1.70)",
          "Fixed IP config parsing to handle BOTH base ports (JSON format) and subinterfaces (flattened CSV columns)",
          "Morrison House static IP override (2.3.4.5/24 on ge-0/0/1.70) now properly detected and classified"
        ],
        "feature_additions": [
          "Menu 103: Added subinterface IP config detection - handles VLAN-tagged WAN ports",
          "Menu 103: Enhanced override reporting includes port/subinterface identifier (e.g., device@ge-0/0/1.70)",
          "Menu 103: Template subinterface comparison - checks template config for matching subinterfaces"
        ],
        "refactoring": [
          "Menu 103: Dual-path IP config extraction - tries subinterfaces first, falls back to base port JSON",
          "Menu 103: Improved logging shows which port/subinterface was detected with IP config",
          "Menu 103: Override details now format as device@port(severity:template->device:ip/netmask)"
        ]
      }
    },
    {
      "version": "25.11.13.14.30",
      "date": "2025-11-13",
      "changes": {
        "feature_additions": [
          "Menu 103: Enhanced WAN2 override detection with intelligent IP type conflict analysis",
          "Menu 103: Distinguishes CRITICAL (DHCP->Static) vs WARNING (Static->DHCP) vs INFO (same-type) overrides",
          "Menu 103: Added template vs device IP configuration comparison for all sites attached to gateway templates",
          "Menu 103: Multi-site detection - automatically checks ALL devices across ALL stores assigned to same template",
          "Menu 103: New report columns - total_override_count, critical_override_count, warning_override_count, info_override_count, override_details",
          "Menu 103: Override details include severity classification, template IP type, device IP type, and static IP addresses"
        ],
        "api_changes": [
          "Menu 103: Now loads OrgGatewayTemplates.csv for template IP type analysis and comparison"
        ],
        "logging_analytics": [
          "Menu 103: Added IP type mismatch severity classification (CRITICAL/WARNING/INFO/UNKNOWN)",
          "Menu 103: Defensive JSON parsing with graceful error handling for malformed ip_config data",
          "Menu 103: Enhanced logging shows template-to-site mapping and IP config extraction details"
        ],
        "compatibility": [
          "Menu 103: Maintains backward compatibility - override_devices field preserved for existing workflows",
          "Menu 103: Report now includes both legacy and enhanced override tracking"
        ],
        "documentation": [
          "Menu 103: CRITICAL overrides (DHCP->Static) clearly flagged for manual review priority",
          "Menu 103: User guidance explains static IPs will be lost if template DHCP applied without device overrides",
          "Menu 103: Console output shows breakdown of override severity levels with actionable next steps"
        ]
      }
    },
    {
      "version": "25.10.30.17.50",
      "date": "2025-10-30",
      "changes": {
        "bug_fixes": [
          "Fixed dependency installation workflow to follow correct sequence",
          "Corrected UV installation logic: now installs UV with pip if missing before attempting package installs"
        ],
        "refactoring": [
          "Restructured _early_dependency_check() to follow proper workflow:",
          "1. Check for missing dependencies",
          "2. Check if UV installed",
          "3. Install UV with pip if missing",
          "4. Verify UV available",
          "5. Use UV for packages (with per-package pip fallback)",
          "Added UV installation verification step after pip install of UV",
          "Improved logging to show UV installation and verification process"
        ]
      }
    },
    {
      "version": "25.10.30.19.50",
      "date": "2025-10-30",
      "changes": {
        "bug_fixes": [
          "CRITICAL: Fixed ModuleNotFoundError for paramiko when running script directly without virtual environment",
          "Fixed 'Rich library required for TUI mode' error by making dependency check dynamic",
          "Fixed UV hardlink error on Windows (os error 396) by adding automatic pip fallback",
          "Moved paramiko import from direct import (line 29) to try/except fallback block for graceful degradation"
        ],
        "feature_additions": [
          "Added _parse_requirements_file() to dynamically read all dependencies from requirements.txt",
          "Auto-installer now checks ALL packages from requirements.txt, not just hardcoded subset",
          "Added PACKAGE_IMPORT_MAP dictionary for package-to-import-name translations (websocket-client -> websocket, etc.)",
          "Enhanced logging: shows UV detection status and installation success/failure counts",
          "Auto-installer attempts UV first, automatically falls back to pip on any UV failure",
          "Added per-package retry logic: UV failure -> pip fallback for maximum compatibility",
          "Respects DISABLE_AUTO_INSTALL environment variable for container deployments"
        ],
        "refactoring": [
          "Replaced hardcoded critical_packages dict with dynamic requirements.txt parser",
          "Centralized package name mapping in PACKAGE_IMPORT_MAP constant",
          "Improved error handling for requirements.txt parsing (FileNotFoundError, parse errors)",
          "Restructured import order: early dependency check -> stdlib imports -> third-party with fallbacks",
          "Added null checks in EnhancedSSHRunner.connect() to provide clear error when paramiko unavailable",
          "Improved error messaging: suggests 'pip install paramiko' if SSH functionality unavailable"
        ],
        "compatibility": [
          "Script now runnable directly via 'python MistHelper.py' without pre-installing dependencies",
          "All requirements.txt packages auto-installed on first run (rich, sshkeyboard, pyte, etc.)",
          "Maintains backward compatibility with virtual environment workflow",
          "Container deployments unaffected (DISABLE_AUTO_INSTALL=true by default in containers)"
        ]
      }
    },
    {
      "version": "25.10.29.13.55",
      "date": "2025-10-29",
      "changes": {
        "bug_fixes": [
          "CRITICAL: Fixed menu 102 WLAN update failure - script failed with 'Unknown inheritance level: org_wlan_with_template' when applying timer changes",
          "Corrected inheritance level checks from 'wlan_template' to 'org_wlan_with_template' throughout update logic",
          "Fixed API call - now uses updateOrgWlan() to update org-level WLANs directly instead of trying to modify templates",
          "Fixed debug logging pollution - debug flag now only sets FileHandlers to DEBUG, console StreamHandlers remain at INFO",
          "Console output now clean (INFO+ only) while script.log captures full DEBUG traces"
        ],
        "refactoring": [
          "Updated WLAN update logic for org_wlan_with_template inheritance level",
          "Simplified update messages to reflect actual API operations"
        ]
      }
    },
    {
      "version": "25.10.29.00.15",
      "date": "2025-10-29",
      "changes": {
        "bug_fixes": [
          "CRITICAL FIX: Corrected WLAN template architecture completely in menu option 102",
          "Previous logic tried to extract WLANs FROM templates (templates had empty wlans arrays)",
          "Now correctly fetches org WLANs that REFERENCE templates via template_id field",
          "Fixed logic: 1) Fetch WLAN templates, 2) Determine which assigned to site, 3) Fetch org WLANs, 4) Match WLANs with template_id to assigned templates"
        ],
        "refactoring": [
          "Complete rewrite of org WLAN template section (lines 28066-28173)",
          "Renamed filtered_org_template_wlans to filtered_org_wlans for accuracy",
          "Updated inheritance level from 'wlan_template' to 'org_wlan_with_template'",
          "Simplified inheritance source description: 'Org WLAN using template: {name}'"
        ],
        "enhancements": [
          "Converted remaining progress messages to logging (only user-facing data remains as print)",
          "Debug logs now show template assignment determination before WLAN fetching",
          "Added logging for org WLAN filtering process with template_id matching"
        ],
        "documentation": [
          "Clarified architecture: WLAN templates are configuration containers, not WLAN collections",
          "Org WLANs exist independently and optionally reference templates for config inheritance",
          "Templates define what configuration to apply; WLANs reference them via template_id"
        ]
      }
    },
    {
      "version": "25.10.28.23.15",
      "date": "2025-10-28",
      "changes": {
        "feature_additions": [
          "Added debug flag support to menu option 102 for verbose WLAN template troubleshooting",
          "Debug mode shows detailed WLAN template structure, applies fields, and assignment logic in logs",
          "Use: python MistHelper.py --menu 102 --debug (output goes to data/script.log)"
        ],
        "enhancements": [
          "Debug output written to log file instead of console for cleaner user experience",
          "Detailed logging shows applies.site_ids, applies.sitegroup_ids, applies.wxtag_ids, applies.org_id",
          "Shows WLAN structure type (list vs dict) and WLAN count per template in debug logs"
        ]
      }
    },
    {
      "version": "25.10.28.22.30",
      "date": "2025-10-28",
      "changes": {
        "bug_fixes": [
          "Corrected fundamental misunderstanding of Mist template architecture in menu option 102",
          "Now correctly distinguishes between Site Templates and WLAN Templates (separate concepts)",
          "Fixed to fetch WLAN templates via /orgs/{org_id}/templates (not /wlans)",
          "Properly checks WLAN template assignment via applies.site_ids, sitegroup_ids, wxtag_ids, org_id"
        ],
        "refactoring": [
          "Renamed inheritance level from 'org_template' to 'wlan_template' for clarity",
          "Updated API routing to use updateOrgTemplate for WLAN template modifications",
          "Improved WLAN template update logic to fetch full template, modify WLAN, then update"
        ],
        "documentation": [
          "Site Templates (/sitetemplates): Full site configs with embedded WLANs",
          "WLAN Templates (/templates): WLAN-specific templates assignable to sites",
          "Org WLANs (/wlans): Standalone org-level WLANs (not template-based)"
        ]
      }
    },
    {
      "version": "25.10.28.22.09",
      "date": "2025-10-28",
      "changes": {
        "bug_fixes": [
          "Fixed org WLAN template detection in menu option 102 - now correctly matches WLANs by template_id",
          "Corrected logic to compare wlan['template_id'] with site's assigned sitetemplate_id",
          "Removed incorrect site_ids array checking (field does not exist in org WLAN API response)"
        ],
        "refactoring": [
          "Simplified org WLAN filtering to only run when site has assigned template",
          "Improved logging clarity for org WLAN template assignment detection"
        ]
      }
    },
    {
      "version": "25.10.28.21.00",
      "date": "2025-10-28",
      "changes": {
        "feature_additions": [
          "Menu option 102 now supports org-level WLAN templates in addition to site templates",
          "Detects org WLANs applied via explicit site assignment, org-wide, or WxTag matching",
          "Displays assignment method for org templates (explicit/org-wide/tag-based)"
        ],
        "enhancements": [
          "Enhanced WLAN inheritance detection across three levels: site, site_template, org_template",
          "Org WLAN template modifications now show clear impact scope (which sites affected)",
          "Improved warning messages distinguish between site template and org template changes",
          "API routing automatically selects correct update endpoint based on WLAN source level"
        ],
        "api_changes": [
          "Added listOrgWlans API call to fetch org-level WLAN templates",
          "Added updateOrgWlan API call to modify org-level WLAN templates",
          "Org WLAN filtering checks apply_to field (site/org/wxtags) and site_ids array",
          "WxTag matching compares wxtag_ids between org WLANs and site configuration"
        ]
      }
    },
    {
      "version": "25.10.21.15.00",
      "date": "2025-10-21",
      "changes": {
        "feature_additions": [
          "Interactive results grid popup - tabular API results displayed in scrollable grid",
          "Auto-detection of grid-worthy data - dicts with 'results' array of dict items",
          "Results viewer mode with dedicated navigation (Up/Down scroll, Esc to close)",
          "Grid shows 15 rows at a time with scroll indicators (showing X-Y of N)",
          "Metadata display - shows total, limit, distinct values in grid title"
        ],
        "enhancements": [
          "Results grid uses Rich Table with DOUBLE box style for prominence",
          "Columns auto-detected from first result item keys",
          "Scroll position tracked with results_scroll_offset state variable",
          "Help text dynamically shows grid controls when viewing results",
          "Grid appears automatically after successful API call with tabular data",
          "Execution state now includes 'viewing_results' for grid display mode"
        ],
        "refactoring": [
          "New _should_show_results_grid() method - determines if data is grid-displayable",
          "New _create_results_grid() method - builds Rich Table from results array",
          "Grid display integrated into create_layout() - overlays main UI",
          "Grid navigation integrated into handle_input() - Up/Down/Esc handling"
        ]
      }
    },
    {
      "version": "25.10.21.14.55",
      "date": "2025-10-21",
      "changes": {
        "bug_fixes": [
          "Optional parameters with blank input now properly skipped from API calls",
          "Fixed issue where empty optional fields were added to function params causing unwanted filters",
          "Blank Enter on optional parameter no longer adds empty string to query parameters"
        ],
        "enhancements": [
          "Parameter submission logic clarified with explicit handling for required vs optional",
          "Debug logging differentiates between 'stored' and 'skipped' parameters",
          "API calls now only include parameters explicitly provided by user or auto-filled from .env"
        ]
      }
    },
    {
      "version": "25.10.21.14.50",
      "date": "2025-10-21",
      "changes": {
        "logging_analytics": [
          "Debug result saving now captures COMPLETE raw response with all attributes",
          "New make_serializable() function preserves all object properties and nested structures",
          "Raw response saved with __type__ markers showing original class names",
          "Public attributes extracted from APIResponse objects (data, status_code, headers, etc.)",
          "Parameters properly serialized including complex objects like APISession",
          "No data loss during JSON conversion - all accessible attributes preserved"
        ],
        "enhancements": [
          "Debug JSON files now include both raw_response (complete) and parsed_data (extracted)",
          "Object introspection via dir() and getattr() captures all non-private attributes",
          "Handles nested objects recursively to preserve full response hierarchy",
          "Graceful fallback to string representation for non-serializable types"
        ]
      }
    },
    {
      "version": "25.10.21.14.45",
      "date": "2025-10-21",
      "changes": {
        "feature_additions": [
          "Hierarchical result display - API responses formatted with indented tree structure",
          "Recursive value formatting - nested dicts and lists displayed with proper hierarchy",
          "Smart truncation - long values preview with ellipsis, full data in debug JSON"
        ],
        "enhancements": [
          "Results show structure depth with indentation (dict keys, list items, nested objects)",
          "Dictionary items display with type and count header (e.g., 'results: dict (5 keys)')",
          "List items show count and preview first N items with key-value pairs",
          "Nested structures recursively formatted up to 3 levels deep",
          "Sample item display shows first 3 key-value pairs per dict in list",
          "Value strings truncated to 60 chars in nested views, 200 chars at top level"
        ],
        "refactoring": [
          "Split result formatting into _format_result_output and _format_value_hierarchical",
          "Removed old flat formatting code (_format_result_output_old)",
          "Recursive formatter handles arbitrary nesting depth with indent tracking"
        ]
      }
    },
    {
      "version": "25.10.21.14.30",
      "date": "2025-10-21",
      "changes": {
        "logging_analytics": [
          "Comprehensive debug logging added to all TUI navigation keys (UP, DOWN, Enter, Escape, Q)",
          "Main run() loop now logs every iteration, keyboard input, and state changes",
          "Terminal restoration tracked with before/after logs and exception handling",
          "Each key press logs: key type, current path, selection index, execution state",
          "Navigation operations log: start, item selection changes, completion status",
          "Loop metrics: iteration count, running flag status, Live() context entry/exit"
        ],
        "bug_fixes": [
          "Fixed syntax error from try-except indentation in create_layout",
          "Removed complex exception handling that caused indentation cascading issues",
          "Terminal restoration wrapped in try-except with detailed error logging"
        ],
        "testing_validation": [
          "Debug logging identifies exact operation before crashes occur",
          "Terminal mode transitions logged (raw mode entry, restoration, cleanup)",
          "Keyboard input traced from detection through handling to screen update"
        ]
      }
    },
    {
      "version": "25.10.21.12.18",
      "date": "2025-10-21",
      "changes": {
        "feature_additions": [
          "Dynamic JSON response parsing - extracts data from mistapi.APIResponse objects automatically",
          "Debug result logging - API responses saved to data/tui_debug_results/ when --debug flag set",
          "Smart data extraction - detects and unwraps APIResponse.data attribute",
          "Timestamped result files - each execution saved as {function_name}_{timestamp}.json"
        ],
        "enhancements": [
          "Improved result display - shows sample keys and values for dict items in lists",
          "Better preview formatting - displays first 3 items with key-value pairs for API results",
          "Result metadata - shows function name, parameters (redacted), timestamp, and parsed data structure",
          "Debug file notifications - output panel shows where debug results were saved",
          "Tip messages - suggests viewing debug logs for large datasets"
        ],
        "logging_analytics": [
          "Debug results saved as JSON with full structure (function, timestamp, parameters, data)",
          "Sensitive parameter values (password, token, key, secret) redacted in saved files",
          "Automatic directory creation - data/tui_debug_results/ created if missing",
          "Error logging for failed result saves with full traceback",
          "Debug log entries for APIResponse detection and data extraction"
        ]
      }
    },
    {
      "version": "25.10.21.12.12",
      "date": "2025-10-21",
      "changes": {
        "enhancements": [
          "Parameter prompts now display in prominent input boxes with clear headers",
          "Box-style input prompts show parameter name, requirement status, and default value",
          "Current input highlighted with white-on-gray background for visibility",
          "Previously entered parameters shown below with checkmarks",
          "Progress indicator shows N/M parameters completed",
          "Visual hierarchy: Current prompt (bold yellow box) → Previous inputs (dim with checkmarks)"
        ]
      }
    },
    {
      "version": "25.10.21.12.09",
      "date": "2025-10-21",
      "changes": {
        "feature_additions": [
          "TUI now has dedicated Output panel at bottom for API results and execution feedback",
          "Input prompts now appear within TUI (no more exiting to terminal)",
          "Real-time parameter input with visual cursor and inline editing",
          "State machine for input handling - smooth transitions between navigation and input modes"
        ],
        "enhancements": [
          "TUI stays active during function execution - no screen clearing or context switches",
          "Output panel shows execution progress (prompting → executing → completed)",
          "Previously entered parameters visible while prompting for next parameter",
          "Backspace support for editing input inline",
          "Escape cancels execution and returns to navigation mode",
          "Help text changes based on mode (navigation vs input)",
          "Smart result formatting in output panel (type, count, preview)",
          "Input mode clearly indicated with magenta Output panel border"
        ],
        "refactoring": [
          "Removed exit/re-enter Live() pattern - all interaction now within TUI",
          "Replaced external input() calls with internal state machine",
          "Added execution_state, input_buffer, output_lines state tracking",
          "Separated parameter collection (_start_function_execution), submission (_submit_parameter), and execution (_execute_function)",
          "Result formatting moved to dedicated _format_result_output method"
        ]
      }
    },
    {
      "version": "25.10.21.12.04",
      "date": "2025-10-21",
      "changes": {
        "enhancements": [
          "TUI now automatically uses values from .env file for function parameters",
          "Parameters like org_id, site_id, device_id automatically filled from environment variables",
          "No need to manually enter org_id when executing functions if configured in .env",
          "Environment values displayed with [from .env] indicator for transparency"
        ],
        "compatibility": [
          "TUI respects .env configuration for consistent behavior with menu mode",
          "All environment variable parameters (org_id, site_id, etc.) auto-populated before prompting"
        ]
      }
    },
    {
      "version": "25.10.21.11.58",
      "date": "2025-10-21",
      "changes": {
        "bug_fixes": [
          "Fixed TUI freezing after executing functions or cancelling with Ctrl+C",
          "Fixed console.clear() conflicts with Live() context causing display corruption",
          "Fixed terminal hanging when waiting for keypress after function execution",
          "Execution now properly exits Live() context before prompting for parameters"
        ],
        "refactoring": [
          "Function execution moved outside Live() context to prevent display conflicts",
          "Added pending_execution flag to defer execution until after Live() exit",
          "Replaced Rich console.print() with plain print() during function execution (outside Live context)",
          "TUI now exits Live(), executes function, waits for keypress, then re-enters Live() for navigation",
          "Cleaner separation between TUI display (Live context) and function execution (normal terminal)"
        ],
        "enhancements": [
          "Function execution no longer interferes with TUI display refresh cycle",
          "Ctrl+C during execution properly returns to TUI without freezing",
          "Terminal mode properly managed across Live() context transitions"
        ]
      }
    },
    {
      "version": "25.10.21.11.52",
      "date": "2025-10-21",
      "changes": {
        "bug_fixes": [
          "Fixed OOM (Out Of Memory) errors when executing API functions that return large results",
          "Fixed TUI crashes when displaying large API responses (thousands of items)",
          "Fixed terminal mode not being restored properly after function execution on Unix systems",
          "Terminal now properly returns to raw mode for TUI navigation after function execution completes"
        ],
        "enhancements": [
          "Smart result preview system - shows type, count, and sample items without converting entire result to string",
          "Lists/tuples: Shows item count and first 3 items with truncation indicators",
          "Dicts: Shows key count and first 5 keys for large dictionaries",
          "Strings: Truncates at 200 characters with length indicator",
          "Memory-safe handling: Never converts full result to string, uses repr() with limits",
          "Helpful tip displayed for large results (>10 items) suggesting use of main menu CSV/SQLite export options"
        ],
        "security": [
          "Result preview limits prevent memory exhaustion attacks from malformed API responses",
          "Safe repr() usage with character limits prevents infinite recursion or excessive memory use"
        ]
      }
    },
    {
      "version": "25.10.21.11.49",
      "date": "2025-10-21",
      "changes": {
        "bug_fixes": [
          "TUI items list now scrolls to follow cursor selection (viewport scrolling implemented)",
          "Items list maintains selection in center of viewport when scrolling through long lists",
          "Fixed issue where navigating to bottom items left selection off-screen"
        ],
        "enhancements": [
          "Added intelligent viewport scrolling - visible window follows cursor through item list",
          "Viewport height automatically calculated based on available panel height (minus borders)",
          "Selection stays centered in viewport when possible, adjusts near top/bottom boundaries",
          "Debug logging for viewport calculations when --debug flag is set (selection position, scroll range, visible items)"
        ],
        "logging_analytics": [
          "Added debug logs for viewport scrolling (viewport range, total items, visible items count)",
          "Added debug logs for selection highlighting (index, item name, type, viewport position)",
          "Added debug logs for scroll indicator state (can scroll up/down flags)",
          "All viewport/selection logs only appear with --debug flag to avoid log spam"
        ]
      }
    },
    {
      "version": "25.10.21.11.43",
      "date": "2025-10-21",
      "changes": {
        "performance": [
          "TUI keyboard input responsiveness improved by 10x (sleep reduced from 100ms to 10ms)",
          "TUI refresh rate increased from 4 FPS to 10 FPS for smoother visual feedback",
          "Unix escape sequence timeout reduced from 100ms to 10ms for instant escape key response",
          "Exit handling improved with explicit break check after input handling"
        ],
        "bug_fixes": [
          "TUI exit keys (Q and Escape at root) now work immediately without requiring Ctrl+C",
          "Eliminated sluggish navigation feel caused by excessive sleep intervals",
          "Fixed event loop not checking running flag properly after input handling"
        ]
      }
    },
    {
      "version": "25.10.21.17.30",
      "date": "2025-10-21",
      "changes": {
        "feature_additions": [
          "TUI Mode - Hierarchical API Explorer for mistapi package navigation",
          "Launch with --tui flag for interactive exploration of Thomas Munzer's mistapi library structure",
          "Dynamic module discovery - browse mistapi.api.v1 hierarchy (orgs, sites, msps, const, etc.)",
          "Function introspection - view signatures, parameters, and docstrings inline",
          "Interactive execution - prompt for parameters and run API calls directly from explorer",
          "Three-panel layout: breadcrumb navigation, items list, and details panel",
          "Visual indicators: modules (folder icon), functions (lightning icon), selection highlighting",
          "Cross-platform keyboard support (Windows msvcrt, Unix select) - works over SSH and containers",
          "Complete documentation in TUI_MODE_GUIDE.md with hierarchical navigation examples"
        ],
        "enhancements": [
          "MistHelperTUI class redesigned with hierarchical navigation state (current_path, breadcrumb)",
          "Dynamic discovery using Python inspect and importlib for package introspection",
          "Parameter prompting system with required/optional detection and default value support",
          "Result display with formatted preview and error handling",
          "Automatic apisession initialization and injection for API call execution",
          "Drill-down navigation (Enter on modules) and back navigation (Escape key)",
          "Real-time function signature and documentation display",
          "Educational design - learn API structure by exploring"
        ],
        "refactoring": [
          "Replaced category-based TUI with hierarchical package explorer",
          "Removed static menu_actions organization in favor of dynamic mistapi introspection",
          "Updated navigation model: drill-down/back instead of left-right category switching",
          "Enhanced layout: breadcrumb + items + details instead of categories + items"
        ]
      }
    },
    {
      "version": "25.10.14.17.00",
      "date": "2025-10-14",
      "changes": {
        "feature_additions": [
          "Loop mode now uses intelligent polling strategy instead of background threading",
          "Loop checks API for completed PCAPs (24hr window), downloads missing files, then starts new capture",
          "No duplicate downloads - checks local filesystem before downloading",
          "Loop naturally paces based on capture completion times"
        ],
        "fixes": [
          "Downloads now complete reliably without threading complexity"
        ],
        "removals": [
          "Queue-based background downloader (replaced with simpler synchronous approach)"
        ]
      }
    },
    {
      "version": "25.10.07.16.15",
      "date": "2025-10-07",
      "changes": {
        "fixes": [
          "Wired client API module - Corrected import path to mistapi.api.v1.sites.wired_clients (separate module from wireless clients)",
          "AttributeError on wired client fetch - Resolved 'module has no attribute searchSiteWiredClients' error",
          "Verified: Wireless clients use mistapi.api.v1.sites.clients.searchSiteWirelessClients",
          "Verified: Wired clients use mistapi.api.v1.sites.wired_clients.searchSiteWiredClients"
        ]
      }
    },
    {
      "version": "25.10.06.18.30",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Corrected session attribute in PCAP polling functions",
          "Site PCAP polling used self.apisession instead of self.mist_session (PacketCaptureManager attribute)",
          "Org PCAP polling used self.apisession instead of self.mist_session (PacketCaptureManager attribute)",
          "Changed self.apisession to self.mist_session in _wait_and_download_pcap() (line 4072)",
          "Changed self.apisession to self.mist_session in _wait_and_download_pcap_org() (line 4212)",
          "PCAP downloads now work correctly - polling no longer throws AttributeError",
          "Root cause: PacketCaptureManager.__init__ stores session as self.mist_session, not self.apisession"
        ]
      }
    },
    {
      "version": "25.10.06.18.25",
      "date": "2025-10-06",
      "changes": {
        "enhancements": [
          "Added comprehensive debug logging to PCAP download polling functions",
          "Site-level PCAP polling now logs every poll attempt with detailed capture state",
          "Org-level PCAP polling now logs every poll attempt with detailed capture state",
          "Logs response status code, number of captures returned, and capture found/not found status",
          "When capture found, logs all relevant fields: enabled, format, type, duration, expiry, timestamp, pcap_url",
          "Logs when pcap_url is NOT SET YET vs when it becomes available",
          "Logs available capture IDs when our capture is not found in the list",
          "Exception handling now uses exc_info=True for full traceback in logs",
          "Debug logs will reveal why PCAP downloads timeout (capture not found, pcap_url never set, API errors)",
          "Run with --debug flag to see detailed polling behavior in script.log"
        ]
      }
    },
    {
      "version": "25.10.06.18.20",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Corrected mistapi function names for listing packet captures",
          "Changed listSitePcapCaptures to correct listSitePacketCaptures (3 occurrences)",
          "Changed listOrgPcapCaptures to correct listOrgPacketCaptures (1 occurrence)",
          "Previous function names caused AttributeError when checking for existing captures",
          "Pre-check for existing captures now works correctly before launching new ones",
          "Locations: Single AP pre-check, multi-AP pre-check, site PCAP polling, org PCAP polling",
          "Function names now match mistapi SDK and Mist API operationId values",
          "operationId: listSitePacketCaptures and listOrgPacketCaptures per OpenAPI spec"
        ]
      }
    }
  ]
}
```

**Note**: The changelog above shows the most recent entries in JSON format according to agents.md guidelines (grouped by topic: fixes, enhancements, feature_additions, removals). Older entries below remain in legacy markdown format for historical reference.

---

### Legacy Entries (Converting to JSON format)

```json
{
  "changelog": [
    {
      "version": "25.10.06.18.15",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Multi-AP scan captures now use single API call with aps dictionary (correct API pattern)",
          "Changed from sequential per-AP API calls to single POST with all APs in one payload",
          "API compliance: Properly uses aps field per Mist API schema for multi-AP scan captures",
          "Error handling now correctly detects multi-AP conflicts (e.g., Recording already in progress)"
        ],
        "enhancements": [
          "Performance: Reduced API calls from N (one per AP) to 1 (single call for all APs)",
          "Multi-AP captures return single capture ID that covers all specified APs",
          "Removed per-AP success/failure tracking - API handles all APs in one transaction",
          "Payload structure: {type: scan, band: 5, ..., aps: {mac1: {...}, mac2: {...}}}",
          "Per-AP configs in aps dict inherit from parent values if not specified",
          "More reliable capture launches, better API efficiency, single capture ID to track"
        ]
      }
    },
    {
      "version": "25.10.06.18.10",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Scan radio captures now enforce Mist API minimum duration of 60 seconds",
          "Single AP scan capture duration changed from 30s default to 60s (API minimum)",
          "Multi-AP scan capture duration changed from 30s default to 60s (API minimum)",
          "Prevents confusion when API ignores duration values below 60 seconds"
        ],
        "enhancements": [
          "Duration validation now shows API requirement in error messages for clarity",
          "Warning message before duration prompt: Mist API requires minimum 60 seconds for scan captures",
          "Updated prompts to show correct range: default 60, min 60, max 86400"
        ],
        "documentation": [
          "API discovery: Mist API documentation reveals scan captures have 60-second minimum, 600-second default",
          "API schema constraint: minimum: 60.0, default: 600 for scan capture duration",
          "Note: Other capture types (wireless, wired, gateway, new association) still support 30-second minimum"
        ]
      }
    },
    {
      "version": "25.10.06.18.09",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Switch port stats now retrieved using correct API endpoint",
          "Uses searchSiteSwOrGwPorts for switches/gateways instead of getSiteDeviceStats",
          "Root cause: getSiteDeviceStats does not return port-level statistics for switches",
          "Filters port results by device MAC address to get specific switch ports",
          "Extracts port objects from results array and converts to dict by port_id"
        ],
        "enhancements": [
          "searchSiteSwOrGwPorts provides detailed port statistics (speed, duplex, status)",
          "APs continue using getSiteDeviceStats with port_stat field",
          "Code now branches based on device_type (switch/gateway vs ap)",
          "Graceful fallback to config when port search API unavailable",
          "Enhanced logging shows sample port data for troubleshooting"
        ]
      }
    },
    {
      "version": "25.10.06.18.06",
      "date": "2025-10-06",
      "changes": {
        "feature_additions": [
          "Added pre-check for existing captures before launching new ones",
          "Single AP captures now check for existing captures on that specific AP before starting",
          "Multi-AP captures now check for existing captures across all site APs before batch launch",
          "Confirmation prompt allows users to cancel or proceed when conflicts detected",
          "Pre-check calls listSitePcapCaptures() API to query active/recent captures before launch"
        ],
        "enhancements": [
          "User-friendly warning messages when capture conflicts detected: Mist only allows one capture per AP at a time",
          "Error handling now detects Recording already in progress API errors specifically",
          "Clear error messages replace raw API responses: Capture already in progress on this AP",
          "Actionable guidance when captures fail: Wait for existing captures to complete or check Mist portal to stop them",
          "Multi-AP feature now shows count of existing captures and offers cancellation before launching",
          "Prevents wasted API calls and improves user experience during capture conflicts"
        ]
      }
    },
    {
      "version": "25.10.06.18.05",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Switch port stats now correctly retrieved from API",
          "API structure: Switches use ports array field, not port_stat dict field",
          "Device differences: APs use port_stat (dict), Switches use ports (array of port objects)",
          "Automatic conversion: Converts switch ports array to dict format for consistency",
          "Port ID mapping: Uses port_id field from switch port objects as dict keys"
        ],
        "enhancements": [
          "Logging enhanced: Clearly indicates which format detected (AP-style vs switch-style)",
          "Fallback preserved: Config-based fallback still works when stats unavailable",
          "Operational data: Now correctly shows actual speed/duplex from switch statistics"
        ],
        "documentation": [
          "OpenAPI verified: Implementation matches Mist API OpenAPI 3.0 specification",
          "Uses correct stats_switch_port schema with speed and full_duplex fields"
        ]
      }
    },
    {
      "version": "25.10.06.18.00",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Speed and Duplex now show actual operational values from live stats, not configured values",
          "Data source clarification: Speed/Duplex from port_stat (actual), Profile/Description from port_config (configured)",
          "When getSiteDeviceStats available, shows real-time operational speed and duplex",
          "Port profile and description always pulled from port_config or device template",
          "Stats no longer overwritten by config - each has its proper source"
        ],
        "enhancements": [
          "When stats unavailable, displays note: Speed/Duplex showing configured values",
          "Users see what ports are actually running at, not what they're configured for",
          "Can identify speed/duplex mismatches between configured and actual",
          "Port profile from port_config.port_profile field",
          "Ready for template-based profile lookup (future enhancement)"
        ]
      }
    },
    {
      "version": "25.10.06.17.55",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Port table now displays accurate Speed, Duplex, and Profile from device config",
          "Pulls speed and duplex from port_config instead of using placeholder values",
          "When port_stat unavailable, uses real config data instead of hardcoded Unknown"
        ],
        "enhancements": [
          "Speed formatting: Handles auto, 1g, 10g formats and converts to 1000 Mbps, 10000 Mbps",
          "Duplex display: Shows actual mode - Full, Half, or Auto instead of just Yes/No",
          "Config enrichment: Merges port_stat with port_config to show configured values",
          "Port profile: Now correctly displays from port_config (Access, Trunk, custom names)",
          "Intelligent merge: Combines live stats with config to show most accurate information",
          "Speed handling: Recognizes integer Mbps values, string formats (1g), and auto",
          "String formatting: Capitalizes duplex modes for clean display",
          "Null handling: Gracefully handles missing or null values with N/A or Auto"
        ]
      }
    },
    {
      "version": "25.10.06.17.51",
      "date": "2025-10-06",
      "changes": {
        "feature_additions": [
          "Multi-AP scan captures - Select 'all' when choosing AP to launch simultaneous captures for all APs",
          "New option in AP selection menu to capture from all APs at once",
          "_start_site_scan_capture_all_aps() method - Orchestrates multi-AP capture launches",
          "get_all_ap_macs_from_site() helper function - Fetches all AP MACs from a site",
          "Batch PCAP download option - When using PCAP format with 'all' APs, offers to download all files sequentially"
        ],
        "enhancements": [
          "AP selection displays special 'all' option for launching captures across entire site",
          "Multi-AP captures show progress indicator (e.g., [3/15] Starting capture for AP...)",
          "Summary report shows successful vs failed captures after multi-AP launch",
          "Perfect for site-wide wireless surveys, interference analysis, or comprehensive RF troubleshooting"
        ]
      }
    },
    {
      "version": "25.10.06.17.50",
      "date": "2025-10-06",
      "changes": {
        "enhancements": [
          "Port selection table now displays Port Profile and Description columns",
          "Shows port configuration details for better port identification",
          "Profile column: Displays assigned port profile (e.g., Access, Trunk, custom profiles)",
          "Description column: Shows user-friendly port descriptions from device config",
          "Descriptions longer than 30 characters are truncated with ... for display",
          "Descriptions and profiles left-aligned for readability",
          "Table expands to 120 characters to accommodate new columns",
          "Config mapping: Handles port range expansion to individual port configs correctly",
          "Fallback: Shows N/A for profile and - for description when not configured",
          "Easier port identification without needing to check device config separately",
          "API efficient: Fetches device config once and maps to all individual ports"
        ]
      }
    },
    {
      "version": "25.10.06.17.44",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "PCAP download polling now starts immediately instead of waiting full capture duration",
          "Removed blocking countdown timer that made script appear hung during capture"
        ],
        "enhancements": [
          "Performance: Changed polling interval from 10 seconds to 5 seconds for faster file detection",
          "Progress display now shows elapsed time dynamically during polling",
          "Changed max wait time from 3+ minutes to capture duration + 2 minutes",
          "User sees immediate feedback with Polling for PCAP file availability message",
          "Clearer Ctrl+C cancellation message reminds users they can check portal manually",
          "Technical note: Capture runs asynchronously on Mist cloud - no need to block locally"
        ]
      }
    },
    {
      "version": "25.10.06.17.40",
      "date": "2025-10-06",
      "changes": {
        "feature_additions": [
          "Comprehensive tcpdump expression library with 40 pre-configured filters",
          "Inspired by Daniel Miessler's tcpdump tutorial (danielmiessler.com/blog/tcpdump)",
          "Basic filters: All traffic, HTTPS, HTTP/HTTPS, DNS, SSH, FTP, SMTP, ICMP, ARP",
          "Protocol filters: TCP only, UDP only, Not ICMP",
          "Direction filters: Outbound to port 443, Inbound from port 80",
          "Combined filters: Multi-port (80/443/53), Exclude SSH, TCP flags (SYN, SYN-ACK, RST, FIN)",
          "Advanced filters: Non-standard ports (>1024), Exclude ARP+DNS, Broadcast, Multicast, IPv6, VLAN",
          "Application protocols: SMB/CIFS (445), RDP (3389), NTP (123), SNMP (161), Syslog (514), DHCP (67/68), LDAP (389), MySQL (3306)",
          "Security filters: Port scans (SYN without ACK), Fragmented packets, Large packets (>1500 bytes), Retransmissions",
          "TCP flag filters: Connection attempts (SYN), Replies (SYN-ACK), Resets (RST), Close (FIN)"
        ],
        "enhancements": [
          "Organized menu with clear categories and descriptions",
          "Still allows custom tcpdump expressions for advanced users",
          "Shows applied filter expression after selection for confirmation",
          "Includes helpful examples for custom expressions (host, net, port)",
          "80-character wide formatted menu for readability"
        ]
      }
    }
  ]
    },
    {
      "version": "25.10.06.17.35",
      "date": "2025-10-06",
      "changes": {
        "configuration_changes": [
          "Packet capture default duration changed from 600 seconds (10 minutes) to 30 seconds for faster testing",
          "Packet capture default max packet length changed from 512 bytes to 1300 bytes for better payload visibility",
          "Duration validation minimum changed from 60 seconds to 30 seconds across all capture types"
        ],
        "enhancements": [
          "All capture types (wireless, wired, gateway, new association, scan) now use consistent 30-second default duration",
          "Scan radio captures now use 1300 byte max packet length by default (previously hardcoded to 512)",
          "User prompts updated to reflect new default values for better user experience"
        ]
      }
    },
    {
      "version": "25.10.06.17.30",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Port range expansion for devices using port_config fallback",
          "Port selection table now shows individual ports, not compressed ranges",
          "Example: ge-0/0/0-2 now expands to 3 separate entries: ge-0/0/0, ge-0/0/1, ge-0/0/2",
          "Port count validation now works correctly with expanded ports",
          "Each port sent to API as individual entry (required by Mist API)"
        ],
        "feature_additions": [
          "New helper function _expand_port_range_string() expands port ranges like ge-0/0/0-2, ge-0/1/2-3",
          "Regex parsing: Handles complex patterns like mge-0/2/0, xe-0/1/0-3 correctly"
        ],
        "enhancements": [
          "Fallback logic: Only applies when device uses port_config instead of port_stat",
          "Debug logs show range expansion for troubleshooting",
          "Each index in table now represents exactly one port"
        ]
      }
    },
    {
      "version": "25.10.06.17.28",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Error handling now properly displays API error messages when captures fail",
          "AttributeError when capture fails - Changed from response.text to response.data for mistapi APIResponse objects",
          "Both site and org-level capture error handlers updated with proper APIResponse handling"
        ],
        "enhancements": [
          "Error output now shows detailed error information from Mist API for troubleshooting"
        ]
      }
    },
    {
      "version": "25.10.06.17.23",
      "date": "2025-10-06",
      "changes": {
        "feature_additions": [
          "Packet capture now defaults to downloadable PCAP file format instead of WebSocket streaming",
          "Automatic PCAP file download - Mist cloud saves capture as PCAP file and provides download URL",
          "_wait_and_download_pcap() method - Polls for capture completion and downloads PCAP file to local data directory",
          "_wait_and_download_pcap_org() method - Organization-level PCAP download support for MxEdge captures",
          "_get_capture_format_selection() helper method - Centralized format selection logic to avoid code duplication",
          "Polling mechanism - Smart retry logic waits up to 3 minutes for PCAP file URL after capture completes",
          "Download validation - HTTP status checking and file size reporting for successful downloads"
        ],
        "enhancements": [
          "Format selection UI - Changed default from stream to PCAP file (option 1 now default)",
          "Capture workflow - Conditional branching based on format type (pcap vs stream vs tzsp)",
          "User experience - Progress display during capture wait period with countdown timer",
          "File output - PCAP files saved to data/PacketCapture_{capture_id}.pcap for easy Wireshark analysis",
          "Error handling - Provides manual download URL if automatic download fails"
        ],
        "fixes": [
          "API function names - Corrected from startSitePcapCapture to startSitePacketCapture",
          "All capture types now support format selection - Added to wireless client, wired client, gateway, new association, and scan radio captures",
          "Site and org-level capture methods - Both now properly handle pcap format with file downloads"
        ],
        "documentation": [
          "Updated inline comments to reflect new default behavior (PCAP files vs streaming)"
        ]
      }
    },
    {
      "version": "25.10.06.17.20",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Enforced API limit of maximum 6 ports per packet capture",
          "Port selection now rejects more than 6 ports with clear error message",
          "API was returning 400 - max 6 ports allowed error - now caught before submission"
        ],
        "enhancements": [
          "User guidance: When device has more than 6 ports, all ports option is disabled",
          "Added prominent warning banner showing API LIMITATION: Maximum 6 ports per capture",
          "Smart default: All ports only available when device has 6 or fewer ports",
          "Specific selection: Users must select up to 6 individual ports when more are available",
          "Range validation: Validates port count after range expansion (e.g., 0-3 = 4 ports)",
          "Enhanced error logging when user attempts to exceed 6-port limit",
          "UX clarity: Prompt now says Enter your choice (up to 6 ports) instead of default: all ports"
        ]
      }
    },
    {
      "version": "25.10.06.17.10",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Ports dict now lists actual port names instead of empty {} when all ports selected",
          "Resolved issue where captures started but no PCAP files downloaded",
          "Root cause: Empty ports dict {} violated API spec requirement for explicit port name listing",
          "Solution: When user selects all ports, helper now returns both selection AND available ports list",
          "Payload building now always includes actual port names (e.g., ge-0/0/0, ge-0/0/1)",
          "Switch captures: Fixed for both specific port selection and all ports scenarios",
          "Gateway captures: Same fix applied - actual port names now listed in payload",
          "Payload structure: Correct format switches: {MAC: {ports: {ge-0/0/0: {}, ge-0/0/1: {}}}}"
        ],
        "feature_additions": [
          "Interactive tcpdump expression menu with common filter examples",
          "Filter options: All traffic, HTTPS (443), HTTP/HTTPS, DNS (53), SSH (22), ICMP, ARP, or custom"
        ],
        "enhancements": [
          "User experience: Replaced free-text expression entry with guided menu selection",
          "Clarity: Menu shows exactly what each filter does (e.g., port 443 for HTTPS)",
          "PCAP format now labeled as recommended for downloadable files",
          "Testing validated: Confirmed GUI successfully creates PCAP files with proper port listing",
          "Loop mode ready: Fixes enable proper PCAP downloads during continuous capture loops",
          "Enhanced logging shows port list expansion when all ports selected"
        ],
        "documentation": [
          "Added documentation note about pcap vs stream format",
          "API discovery: API docs show stream only, but testing confirms pcap works and generates downloads"
        ]
      }
    },
    {
      "version": "25.10.06.17.05",
      "date": "2025-10-06",
      "changes": {
        "feature_additions": [
          "Interactive port selection with live status for switch and gateway captures",
          "Added prompt_select_ports_from_device() helper - displays port status from device stats",
          "Fetches real-time port information via getSiteDeviceStats() API",
          "Display shows port name, status (UP/DOWN), speed (Mbps), and duplex mode",
          "Supports single port, multiple ports (comma-separated), ranges (0-3), or all",
          "Automatically excludes management/internal ports (fxp, em, me, vme, irb, lo, vlan)",
          "Natural sorting: Ports displayed in logical order (ge-0/0/0, ge-0/0/1, ge-0/0/2, etc.)"
        ],
        "enhancements": [
          "Smart default: Press Enter with no input to capture on ALL ports (simplified from connected-only)",
          "Switch capture now uses interactive port selector instead of manual entry",
          "Gateway capture now uses interactive port selector instead of manual entry",
          "Visual table with 80-character formatted display",
          "Port selection now mandatory - API requires at least one port or all ports specified",
          "GUI parity: Matches Mist GUI behavior where users see available ports and select visually",
          "Range validation prevents selecting non-existent port indices",
          "Full debug trace of port discovery, selection parsing, and user choices",
          "Graceful fallback if stats unavailable or device not found",
          "Seamless drop-in replacement for previous text-based port input",
          "Clear messaging when device has no port information available",
          "Default behavior changed - pressing Enter now selects ALL ports (not just connected)",
          "Removed all connected ports option - use Enter for all, or specify individual ports"
        ],
        "fixes": [
          "MAC address comparison now normalizes both input and device MACs (removes colons/hyphens)",
          "Device not found error when API returns MAC in different format (with or without colons)",
          "Handles MAC addresses as strings with colons (20:93:39:05:17:80) or plain integers (209339051780)",
          "Fallback logic: When port_stat unavailable, automatically tries device port_config instead",
          "Gracefully handles switches that are offline or not yet reporting stats",
          "Added logging of available stats keys and config keys for troubleshooting"
        ]
      }
    },
    {
      "version": "25.10.06.17.02",
      "date": "2025-10-06",
      "changes": {
        "feature_additions": [
          "Switch packet capture support (Menu 9, Option 4)",
          "Full switch packet capture with port selection and filtering",
          "Capture from all ports or specify individual ports (e.g., ge-0/0/0,ge-0/0/1)",
          "Per-port or global tcpdump expressions for traffic filtering",
          "Loop mode support for continuous switch monitoring",
          "Added prompt_select_switch_mac_from_site() helper for interactive switch selection",
          "Multicast traffic filtering option for wireless and wired client captures",
          "New includes_mcast parameter (default: false) to include/exclude multicast traffic"
        ],
        "enhancements": [
          "API leverages type: switch with switches configuration structure",
          "Follows same patterns as gateway and client captures (60s min duration, format selection)",
          "Clarified capture type descriptions in menu and configuration screens",
          "Client Capture (Wireless) = Ongoing traffic from ALREADY CONNECTED clients",
          "New Association Capture = NEW connection attempts (802.11 auth/assoc handshakes only)",
          "Menu now shows brief description of each capture type for easier selection",
          "Confirmed all client capture payloads match API specification exactly"
        ],
        "fixes": [
          "Corrected gateway capture payload structure to match API specification",
          "Gateway capture was using flat gateway_mac and port_id fields (incorrect)",
          "Gateway capture now uses gateways object with MAC as key and nested ports structure",
          "Changed port selection from simple wan/lan/all to specific port names (e.g., ge-0/0/0)",
          "Added max_pkt_len: 1500 to gateway payloads (API requirement)",
          "Prevents Error 400 No connected SSRs or feature not supported due to malformed payload",
          "Gateway payload structure now identical to switch payload pattern"
        ],
        "documentation": [
          "Updated copilot-instructions.md to reflect switch capture capability",
          "Menu option 4 in site packet capture, new _start_site_switch_capture() method"
        ]
      }
    },
    {
      "version": "25.10.06.17.00",
      "date": "2025-10-06",
      "changes": {
        "feature_additions": [
          "Menu options 9-10 - Comprehensive packet capture management for Juniper Mist environments",
          "PacketCaptureManager class - Full-featured packet capture orchestration with WebSocket streaming",
          "Site packet capture (Option 9) - Wireless client, wired client, gateway, new association, and scan radio captures",
          "Organization packet capture (Option 10) - MxEdge captures for org-level Mist Edges with TZSP support",
          "WebSocket streaming integration - Real-time packet monitoring with progress display",
          "MAC address validation - Format checking and normalization for all MAC address inputs",
          "Capture format options - Stream to Mist Cloud or TZSP stream to remote host (Wireshark)",
          "Advanced scan capture - Band selection (2.4/5/6 GHz), channel, bandwidth, and tcpdump expression support",
          "Capture session export - Automatic CSV/SQLite export of capture configuration and session details"
        ],
        "enhancements": [
          "Capture type support - Client (wireless/wired), Gateway, New Association, Scan Radio, and MxEdge capture modes",
          "Interactive configuration - Guided parameter collection with validation for all capture types",
          "Safety validations - Duration limits (60-86400s), packet count constraints (0-10000), max packet length (64-2048 bytes)",
          "Documentation - Comprehensive inline documentation with API endpoint references and usage examples",
          "Operation count - Updated to 103 total menu operations (added packet capture operations)"
        ],
        "fixes": [
          "Test harness - Added options 9-10 to systematic test skip list (interactive operations)"
        ]
      }
    },
    {
      "version": "25.12.02.11.50",
      "date": "2025-12-02",
      "changes": {
        "bug_fixes": [
          "Environment variable isolation - Clear MIST_APITOKEN from environment during individual token attempts to prevent mistapi from auto-loading all tokens",
          "Token pre-validation - Test tokens for rate limiting before passing to mistapi to avoid validation failures",
          "as_completed parameter fix - Use explicit fs= keyword argument to prevent positional parameter confusion with tqdm"
        ],
        "enhancements": [
          "Rate limit detection - Pre-check tokens against /api/v1/self endpoint to identify rate-limited tokens before initialization",
          "Token filtering - Automatically skip rate-limited tokens and only pass working tokens to mistapi",
          "Detailed logging - Added per-token validation logging showing HTTP status codes and rate limit details"
        ],
        "compatibility": [
          "mistapi auto-load workaround - Prevents mistapi's automatic MIST_APITOKEN environment loading from interfering with single-token initialization",
          "Rate limit resilience - Detects 429 responses during pre-validation and skips those tokens"
        ]
      }
    },
    {
      "version": "25.12.02.11.35",
      "date": "2025-12-02",
      "changes": {
        "bug_fixes": [
          "Individual token retry - Enhanced rate limit handling to try each API token individually when multi-token initialization fails",
          "Token iteration strategy - Changed from single token fallback to sequential token testing until finding a working token",
          "Rate limit resilience - Continues attempting remaining tokens even when some are rate-limited or invalid"
        ],
        "enhancements": [
          "Detailed token logging - Added per-token attempt logging showing token index and masked token values (first 4 and last 4 characters)",
          "Clear success reporting - Logs which specific token succeeded when multiple tokens are configured",
          "Comprehensive failure tracking - Reports when all tokens have been exhausted with clear summary"
        ],
        "compatibility": [
          "mistapi NoneType workaround - Works around mistapi library bug that crashes on rate-limited token validation responses",
          "Multi-token reliability - Ensures at least one non-throttled token can initialize even when others are rate-limited"
        ]
      }
    },
    {
      "version": "25.12.02.11.20",
      "date": "2025-12-02",
      "changes": {
        "bug_fixes": [
          "Rate limit fallback - Added graceful degradation when multi-token initialization hits rate limits during token validation",
          "Single token fallback - Automatically falls back to first token when mistapi library encounters NoneType iteration errors (indicates rate-limited /api/v1/self responses)",
          "Token validation resilience - Detects and logs rate limiting during token validation with informative warning messages"
        ],
        "compatibility": [
          "mistapi rate limit handling - Workaround for mistapi library's inability to handle 429 responses during token privilege validation",
          "API throttling resilience - Allows MistHelper to initialize even when API is temporarily throttling token validation requests"
        ]
      }
    },
    {
      "version": "25.10.06.11.40",
      "date": "2025-10-06",
      "changes": {
        "enhancements": [
          "Console log level filtering - Early logging setup now respects CONSOLE_LOG_LEVEL environment variable (defaults to INFO)",
          "Startup experience - Changed API page size configuration message from INFO to DEBUG level to reduce console clutter",
          "Log output clarity - DEBUG messages only appear in file logs, keeping console output clean for normal operation",
          "Configuration consistency - Early logging setup now matches GlobalImportManager._setup_logging() pattern for log level handling"
        ],
        "fixes": [
          "Early logging handler configuration - Console and file handlers now properly respect environment-specified log levels from startup"
        ]
      }
    },
    {
      "version": "25.10.06.11.22",
      "date": "2025-10-06",
      "changes": {
        "fixes": [
          "Early logging configuration - Moved logging setup to execute immediately after imports to prevent Python from creating default handler",
          "Root directory pollution - Eliminated blank script.log file creation in root directory by configuring logging before any logging calls",
          "Logging initialization timing - Added early basicConfig() call with FileHandler for data/script.log before PerformanceMonitor and other early code executes"
        ],
        "enhancements": [
          "Module-level logging safety - Early logging setup ensures all module-level logging calls (lines 63, 151, 175, 179, 215, 217) write to data/script.log"
        ],
        "documentation": [
          "Identified root cause - Python's logging module creates default handler in current directory when logging methods called before configuration",
          "ASCII character map - Comprehensive emoji to ASCII replacement table added to agents.md for NASA/JPL compliance (21 emoji replacements documented)"
        ]
      }
    },
    {
      "version": "25.10.02.16.07",
      "date": "2025-10-02",
      "changes": {
        "fixes": [
          "SSH EOF handling - Added comprehensive EOF (End-of-File) error handling for all interactive input() calls to prevent SSH session crashes",
          "Container SSH stability - Fixed EOF when reading a line errors in SSH sessions by wrapping input calls with graceful exception handling",
          "Container ForceCommand execution - Corrected background process issue that was breaking interactive terminal input in SSH environment"
        ],
        "feature_additions": [
          "safe_input() helper function - Centralized input handling with proper EOF and KeyboardInterrupt exception management",
          "Non-ASCII character cleanup - Systematically replaced remaining Unicode characters with ASCII equivalents throughout codebase for NASA/JPL compliance"
        ],
        "enhancements": [
          "Session disconnection handling - SSH disconnections now gracefully exit with proper error logging instead of crashing the application",
          "Destructive operation safety - Applied EOF protection to critical confirmation prompts for virtual MAC conversion, firmware upgrades, and device conversions",
          "Containerfile efficiency - Removed duplicate dependency installations and improved container build process for faster deployments"
        ]
      }
    },
    {
      "version": "25.09.30.18.30",
      "date": "2025-09-30",
      "changes": {
        "feature_additions": [
          "Menu option 100 - SSR firmware upgrade with comprehensive mode selection (site-based and Gateway Template-based upgrades)",
          "SSR-specific safety framework - Enhanced critical infrastructure warnings for WAN connectivity disruption, SD-WAN tunnel impact, and branch office connectivity",
          "Session Smart Router detection - Smart filtering for SSR models (SSR120, SSR130, SSR1200, SSR1300, SSR1400, VM-SSR) from gateway inventory",
          "Conservative upgrade defaults - Serial upgrade strategy and recovery snapshots enabled by default for routing infrastructure safety",
          "Comprehensive confirmation system - Multi-layer safety confirmations with UPGRADE SSR FIRMWARE typed confirmation requirement"
        ],
        "enhancements": [
          "FirmwareManager class - Extended with complete SSR firmware upgrade capabilities following established patterns from AP and switch upgrades",
          "Template-based upgrades - Reuses existing Gateway Template infrastructure for unified SSR upgrade orchestration across multiple sites",
          "Upgrade parameter configuration - SSR-optimized settings including reboot requirements, snapshot management, and HA coordination considerations",
          "Audit logging - Complete operation tracking with SSR-specific context and routing infrastructure impact documentation",
          "Error handling - SSR-specific error scenarios with WAN connectivity and SD-WAN tunnel re-establishment guidance",
          "Systematic testing - Added menu option 100 to destructive operations skip list for safe automated testing"
        ],
        "fixes": [
          "Menu structure - Clean integration without wrapper functions, direct FirmwareManager method calls for consistent architecture"
        ]
      }
    },
    {
      "version": "25.09.30.15.52",
      "date": "2025-09-30",
      "changes": {
        "fixes": [
          "Unicode encoding error - Replaced Unicode arrow characters (→) with ASCII equivalents (->) to prevent Windows logging crashes",
          "Windows compatibility - All console output now uses ASCII-safe characters to prevent encoding errors on Windows systems"
        ],
        "feature_additions": [
          "Firmware downgrade detection - Added intelligent version comparison to prevent API-rejected downgrades before upgrade attempts",
          "Version comparison algorithm - Robust firmware version parsing handles SSR version formats (6.3.4-7.r2, 6.3.5-37.sts)"
        ],
        "enhancements": [
          "Downgrade validation - Pre-flight version checking identifies and skips devices requiring downgrades with clear user messaging",
          "Error classification - Downgrade fw version not allowed API responses now treated as validation warnings rather than critical errors"
        ]
      }
    },
    {
      "version": "25.09.30.15.47",
      "date": "2025-09-30",
      "changes": {
        "feature_additions": [
          "Version comparison logic - Cross-references current device firmware versions against target version before upgrade attempts"
        ],
        "enhancements": [
          "Firmware version validation - Added pre-upgrade version checking to skip devices already at target firmware version",
          "Smart error handling - Already at requested fw version API responses now treated as informational rather than errors",
          "User feedback - Clear messaging about devices skipped due to version matches, with upgrade vs skip counts",
          "Debug information - Enhanced logging shows current to target version transitions for devices needing upgrades"
        ],
        "fixes": [
          "Error classification - Devices already at target version no longer counted as upgrade failures in operation summary"
        ]
      }
    },
    {
      "version": "25.09.30.15.45",
      "date": "2025-09-30",
      "changes": {
        "fixes": [
          "SSR reboot parameter logic - Corrected inverted reboot_at logic that was disabling reboots when auto_reboot=True",
          "API parameter validation - When auto_reboot=True, now omits reboot_at parameter to use API default timing instead of setting reboot_at=-1 (which disables reboot)"
        ],
        "enhancements": [
          "Error response extraction - Improved API error response parsing to capture detailed error information from multiple response attributes",
          "Debug logging - Enhanced response debugging to show status codes, headers, and response content when text is unavailable"
        ],
        "documentation": [
          "Added clear parameter behavior - reboot_at=-1 disables reboot, omitting parameter uses default timing"
        ]
      }
    },
    {
      "version": "25.09.30.15.41",
      "date": "2025-09-30",
      "changes": {
        "feature_additions": [
          "Cross-reference validation - SSR devices are now validated against org-level inventory to ensure they are recognized as upgradeable SSRs",
          "Device eligibility checks - Only devices confirmed in organization SSR inventory proceed to upgrade process"
        ],
        "enhancements": [
          "SSR device validation - Added comprehensive validation against organization SSR inventory before upgrade attempts",
          "Debug logging - Added detailed request body logging and device validation status for troubleshooting SSR upgrade issues",
          "Error handling - Enhanced error response logging to capture API response details for 400 Bad Request errors",
          "Progress reporting - More detailed status messages showing validated device counts and inventory verification"
        ]
      }
    },
    {
      "version": "25.09.30.15.31",
      "date": "2025-09-30",
      "changes": {
        "fixes": [
          "SSR upgrade API 400 Bad Request error - Added missing required channel parameter to upgrade request body",
          "Undefined variable error - Added proper ssr_models definition before device filtering in upgrade execution"
        ],
        "enhancements": [
          "SSR upgrade confirmation - Simplified confirmation phrase from UPGRADE SSR FIRMWARE to UPGRADE for user convenience",
          "API compliance - SSR upgrade requests now include all required parameters per OpenAPI schema (device_ids, channel, version, strategy)"
        ]
      }
    },
    {
      "version": "25.09.30.15.24",
      "date": "2025-09-30",
      "changes": {
        "fixes": [
          "SSR firmware upgrade implementation - Corrected API endpoints from sites.devices.upgradeDevices to orgs.ssr.upgradeOrgSsrs with proper parameter mapping",
          "Parameter validation - Removed invalid force, reboot, and snapshot parameters; replaced with proper SSR parameters (device_ids, version, channel, strategy, reboot_at)",
          "Device discovery for SSRs - Updated listSiteDevices calls to use type=gateway parameter for proper SSR device filtering",
          "Option 100 SSR upgrade - Corrected undefined variable errors and implemented proper org-level SSR upgrade workflow",
          "API endpoint corrections - All SSR operations now use proper mistapi.api.v1.orgs.ssr module instead of generic device endpoints"
        ],
        "feature_additions": [
          "SSR firmware version discovery - Implemented listOrgAvailableSsrVersions API with indexed selection interface for proper version management",
          "Device type tracking - Enhanced upgrade status monitoring to display distribution across AP, Switch, and SSR device types"
        ],
        "enhancements": [
          "Upgrade monitoring (Option 60) - Added comprehensive SSR upgrade monitoring using listOrgSsrUpgrades API with device type distribution tracking"
        ]
      }
    },
    {
      "version": "25.09.29.17.05",
      "date": "2025-09-29",
      "changes": {
        "enhancements": [
          "Menu option 7 title - Updated to Show routing table on switches via WebSocket (Switch L3 routing - BGP/OSPF/Static) for clarity",
          "Menu option 8 title - Updated to Show SSR/SRX routing table via dedicated API (128T/SRX gateways - Advanced BGP analysis) for device specificity",
          "SSR routing table display - Added complete data table with all BGP attributes including Route Name, Selection Reason, Weight, Metric, Local Preference, AS Path, and VRF",
          "Protocol selection flexibility - Users can now skip protocol specification to let API use its default behavior, choose specific protocols (bgp/any/ospf/static/direct/evpn), or get comprehensive routing views",
          "Data presentation - Comprehensive routing table with full untruncated data display showing complete BGP route analysis including peer names, selection criteria, and all BGP path attributes",
          "Menu categorization - Clear device-specific separation between switch routing (Option 7) and SSR/SRX gateway routing (Option 8) for improved operational clarity"
        ]
      }
    },
    {
      "version": "25.09.29.16.15",
      "date": "2025-09-29",
      "changes": {
        "feature_additions": [
          "Menu option 8 - SSR/SRX routing table using dedicated API function (advanced BGP/OSPF analysis with VRF support)",
          "Advanced routing table parameters - Protocol filtering, BGP neighbor analysis, VRF-aware queries, HA cluster node selection",
          "BGP route direction analysis - Received/advertised route inspection for BGP neighbors with structured output",
          "Real-time refresh options - Configurable interval and duration for dynamic routing table monitoring",
          "Routing table comparison - Option 8 (dedicated API) vs Option 7 (generic WebSocket) for different use cases"
        ],
        "enhancements": [
          "Dedicated SSR/SRX routing API - Uses mistapi.api.v1.sites.devices.showSiteSsrAndSrxRoutes for structured routing queries",
          "Device compatibility validation - Specific checks for SSR (128T) and SRX devices with compatibility warnings",
          "Parameter validation - Structured input validation using utils_show_route schema from OpenAPI specification",
          "Documentation - Clear distinction between generic routing table (7) and SSR-specific routing table (8) functions"
        ],
        "fixes": [
          "Menu organization - Filled gap at option 8 to improve numerical sequence and reduce confusion"
        ]
      }
    },
    {
      "version": "25.09.29.14.45",
      "date": "2025-09-29",
      "changes": {
        "feature_additions": [
          "Menu option 7 - Show routing table command for switches/routers/SSR devices via WebSocket (RIB - Routing Information Base)",
          "Multi-format routing table parsing - Support for various device vendor output formats with intelligent parsing strategies",
          "Routing vs forwarding table distinction - Clear documentation explaining RIB (Routing Information Base) vs FIB (Forwarding Information Base)"
        ],
        "enhancements": [
          "Routing table diagnostics - Comprehensive routing protocol information (BGP, OSPF, static routes) with filtering capabilities",
          "Interactive parameter collection - Optional filtering by protocol, prefix, VRF, neighbor, and node for targeted routing analysis",
          "Device compatibility validation - Comprehensive checks for Layer 3 routing capabilities on switches, routers, and SSR devices",
          "Default protocol behavior - Changed default from bgp to any to show all route types unless specifically filtered",
          "Juniper routing table parsing - Improved multi-line route entry parsing with proper protocol/admin distance extraction",
          "Table display formatting - Removed truncation limits to show full routing data without ellipsis cutoffs"
        ],
        "fixes": [
          "prettytable import errors - Corrected class reference from prettytable.PrettyTable() to PrettyTable() following established import patterns",
          "Syntax errors - Resolved orphaned elif statements from parser refactoring"
        ]
      }
    },
    {
      "version": "25.09.26.16.45",
      "date": "2025-09-26",
      "changes": {
        "fixes": [
          "Switch firmware model filtering - Added missing device model compatibility validation for option 99 (switch firmware upgrades)",
          "Security vulnerability - Eliminated potential firmware compatibility mismatches that could cause network device failures"
        ],
        "feature_additions": [
          "Fallback firmware entry - Manual firmware version specification with compatibility warnings when no compatible versions found"
        ],
        "enhancements": [
          "Firmware version selection - Now filters available firmware versions by actual switch models in the organization inventory",
          "Model compatibility display - Firmware version selection now shows compatible switch models for each available version",
          "Safety improvements - Prevents selection of incompatible firmware versions that could cause upgrade failures",
          "Error handling - Improved messaging when no compatible firmware versions are available for detected switch models"
        ]
      }
    },
    {
      "version": "25.10.27.17.00",
      "date": "2025-10-27",
      "changes": {
        "feature_additions": [
          "Menu option 60 - NEW: Continuous monitoring mode (option 5) for real-time upgrade tracking",
          "Auto-refresh capability - Monitors active upgrades with 7-second refresh cycle until completion or cancellation",
          "Full device scanning - Each refresh queries ALL devices (not just initial set), detecting new upgrades automatically",
          "Live dashboard - Clear screen display showing only devices currently upgrading with progress bars",
          "Smart exit - Automatically exits when all upgrades complete or user presses Ctrl+C",
          "Monitoring iterations - Displays refresh count and active device count per cycle"
        ],
        "enhancements": [
          "Scope options expanded - Added option 5 for continuous monitoring alongside existing 1-4 scopes",
          "Operational visibility - NOC engineers can now monitor upgrade progress without manual refreshes",
          "Dynamic device tracking - New devices starting upgrades mid-monitoring are detected and displayed",
          "Real-time progress - Each iteration fetches fresh API data showing current progress percentages",
          "Stale filtering - Monitoring mode applies same stale upgrade detection as standard mode"
        ],
        "user_interface": [
          "Clear screen refresh - Platform-aware screen clearing (cls/clear) for clean display updates",
          "Exit instructions - Clear prompts showing Ctrl+C to exit and auto-exit on completion",
          "Progress tracking - Visual progress bars and status display updated every 7 seconds",
          "Scan notification - Each refresh shows 'Scanning all devices' to indicate fresh API query"
        ]
      }
    },
    {
      "version": "25.10.27.16.45",
      "date": "2025-10-27",
      "changes": {
        "fixes": [
          "Menu option 60 - CRITICAL FIX: Stale completed upgrades no longer shown in real-time progress table",
          "Progress filtering - Devices showing 100% complete for more than 1 hour are treated as completed, not active",
          "Status accuracy - Fixed issue where APs with 'inprogress' status at 100% from weeks ago appeared as actively upgrading",
          "Active upgrades scope - Option 3 now correctly excludes stale completed upgrades from results"
        ],
        "api_changes": [
          "Stale status handling - Mist API sometimes leaves devices in 'inprogress' status after completion; now detected by checking progress=100 + timestamp age",
          "Completion detection - Upgrades older than 1 hour at 100% progress are automatically reclassified as completed"
        ],
        "enhancements": [
          "Smart filtering - Real-time dashboard only shows genuinely active upgrades, not old completed ones with stale API status",
          "CSV clarity - Stale upgrades marked as '[===============] 100% (Complete - Stale)' to distinguish from active upgrades",
          "Summary accuracy - Upgrades in progress count now excludes stale 100% completions for accurate operational visibility"
        ]
      }
    },
    {
      "version": "25.10.27.16.30",
      "date": "2025-10-27",
      "changes": {
        "fixes": [
          "Menu option 60 - CRITICAL FIX: SSR upgrade progress now included in real-time progress table display",
          "Status handling - Added 'downloading' as recognized active upgrade status alongside 'inprogress' and 'upgrading'",
          "Progress display - SSR devices in downloading phase now show progress bars in CSV export and console dashboard",
          "Scope filtering - Active upgrades filter (option 3) now properly includes SSR devices with downloading status"
        ],
        "api_changes": [
          "SSR upgrade status support - Mist API returns 'downloading' status for SSR/Gateway devices during firmware download phase",
          "Multi-stage upgrade tracking - Full lifecycle support: downloading -> upgrading/inprogress -> success/upgraded/completed"
        ],
        "enhancements": [
          "Complete device coverage - All device types (AP, Switch, Gateway, SSR) now tracked across all upgrade phases",
          "Progress visibility - SSR downloads with progress percentages (e.g., 90%) now visible in dashboard table"
        ]
      }
    },
    {
      "version": "25.10.27.16.15",
      "date": "2025-10-27",
      "changes": {
        "fixes": [
          "Menu option 60 - CRITICAL FIX: Organization-wide device stats now properly includes all device fields and fwupdate data",
          "API field retrieval - Using fields='*' parameter to retrieve all available fields including fwupdate for complete device information",
          "Data completeness - Org-wide queries now return device ID, name, MAC, model, type, version, site info AND firmware upgrade status"
        ],
        "api_changes": [
          "API behavior discovery - Mist listOrgDevicesStats requires explicit fields parameter, using fields='*' to get comprehensive data including fwupdate field",
          "Field specification - When fields parameter is used with specific field name, only that field is returned; fields='*' gets all fields including optional ones"
        ],
        "enhancements": [
          "Org-wide status monitoring - Now fully functional with complete device information and upgrade progress tracking across all sites",
          "Data consistency - Organization-wide and site-specific queries now return equivalent device and firmware status information"
        ]
      }
    },
    {
      "version": "25.10.27.16.00",
      "date": "2025-10-27",
      "changes": {
        "fixes": [
          "Menu option 60 - Fixed status categorization to handle actual API response values (success/upgrading) in addition to documented values (upgraded/inprogress)",
          "Progress display logic - Corrected to show completion status for devices with 'success' status instead of showing N/A",
          "Status filtering - Active upgrades filter now properly includes both 'inprogress' and 'upgrading' status devices",
          "Upgrade completed counter - Now properly counts devices with both 'upgraded' and 'success' status values"
        ],
        "api_changes": [
          "API inconsistency handling - Added support for actual API response values that differ from OpenAPI schema documentation",
          "Device type variance - Gateway/SSR devices return 'upgrading' and 'success' while APs use 'inprogress' and 'upgraded'"
        ],
        "enhancements": [
          "Status value mapping - Code now handles both documented enum values and actual device-specific response values",
          "Error resilience - Progress tracking works correctly regardless of which status value variant the API returns"
        ]
      }
    },
    {
      "version": "25.10.27.15.30",
      "date": "2025-10-27",
      "changes": {
        "feature_additions": [
          "Real-time progress monitoring - Menu option 60 now displays live upgrade progress with ASCII progress bars showing percentage completion (0-100%)",
          "Visual progress indicators - Added create_progress_bar() helper function generating [=========>          ] style progress bars for console and CSV output",
          "Progress analytics - Average progress calculation across all in-progress upgrades with visual representation",
          "Progress distribution tracking - Devices categorized into progress ranges (0-25%, 26-50%, 51-75%, 76-99%, 100%) for quick status assessment",
          "Active upgrade dashboard - Dedicated section showing up to 20 devices currently upgrading with device name, type, site, and real-time progress",
          "Enhanced CSV export - New FW Progress Display field with visual progress bars exported alongside numeric percentage for spreadsheet analysis"
        ],
        "enhancements": [
          "Menu option 60 - Comprehensive firmware upgrade status monitoring leveraging fwupdate.progress field from Mist API device stats",
          "Progress tracking infrastructure - Added progress_total, progress_count, and devices_upgrading tracking to firmware status summary",
          "API field utilization - Full implementation of fwupdate_stat schema including progress (0-100), status (inprogress/failed/upgraded), timestamp, and will_retry fields",
          "User experience - Clear tabular display of upgrading devices sorted by progress percentage (highest first) showing devices closest to completion",
          "Status visualization - Progress bars adapt to upgrade state: active progress for inprogress, Complete for upgraded, FAILED for failed upgrades"
        ],
        "api_changes": [
          "Device stats API integration - Leverages listOrgDevicesStats and listSiteDevicesStats endpoints to retrieve fwupdate field with real-time progress data",
          "API field documentation - Confirmed fwupdate_stat schema from Mist OpenAPI spec with progress (0-100 integer), status enum, status_id, timestamp, and will_retry boolean"
        ],
        "documentation": [
          "API research findings - Documented fwupdate field structure and upgrade status tracking capabilities available in Mist API",
          "Progress monitoring guide - Clear explanation of how progress percentage maps to upgrade stages and device states"
        ]
      }
    },
    {
      "version": "25.09.26.14.30",
      "date": "2025-09-26",
      "changes": {
        "fixes": [
          "Menu option 60 (Firmware status check) - Eliminated double scope selection prompts by creating direct FirmwareManager path",
          "DateTime error handling - Enhanced timestamp validation for firmware upgrade status with proper type checking and exception handling",
          "Firmware status implementation - Removed duplicate scope selection logic in check_firmware_upgrade_status_impl()",
          "User experience - Single scope selection prompt for option 60 eliminating confusing double prompts"
        ],
        "enhancements": [
          "Error reporting - Improved datetime.fromtimestamp() error handling with specific exception types and debug logging",
          "Code stability - Added input validation for timestamp values before datetime conversion"
        ]
      }
    },
    {
      "version": "25.09.26.14.14",
      "date": "2025-09-26",
      "changes": {
        "feature_additions": [
          "Menu option 99 - Advanced Switch firmware upgrade with mode selection (By Site or By Template)",
          "Switch firmware upgrade system - Complete enterprise-grade switch firmware management",
          "FirmwareManager class - Extended with comprehensive switch firmware methods including execute_switch_firmware_upgrade_with_mode_selection(), bulk_upgrade_switch_firmware_by_site(), upgrade_switch_firmware_by_gateway_template()",
          "Switch-specific API parameters - Proper reboot=True, snapshot=True for Junos devices, no P2P support",
          "Gateway Template integration for switches - Reuses existing template infrastructure for consistent site grouping",
          "Switch device discovery - Automatic enumeration using listSiteDevices(type=switch) with proper filtering",
          "Switch firmware validation - Version availability checking via listOrgAvailableDeviceVersions(type=switch)",
          "Switch upgrade strategies - Big bang, canary, RRM, and serial upgrade modes with network-aware safety warnings",
          "Enhanced safety prompts - Network disruption warnings specific to switch operations requiring maintenance windows"
        ],
        "enhancements": [
          "Destructive operation tracking - Added option 99 to systematic test exclusions for safe automated testing",
          "Documentation - Updated README with switch firmware capabilities and operation count (now 98 total menu options)",
          "CSV export system - Switch upgrades export to data/ActiveSwitchUpgradeOperations.csv with comprehensive tracking"
        ]
      }
    },
    {
      "version": "25.09.26.11.15",
      "date": "2025-09-26",
      "changes": {
        "feature_additions": [
          "FirmwareManager class - Comprehensive firmware management system for Mist Access Points",
          "Interactive mode selection - Choose between site-based or template-based upgrades at runtime",
          "Template-based AP firmware upgrades with Gateway Template selection and site count display",
          "Automatic site discovery and AP enumeration across all sites in selected template"
        ],
        "enhancements": [
          "Menu option 90 - Consolidated firmware upgrade with mode selection (By Site or By Template)",
          "Firmware upgrade architecture - Refactored existing functions into class-based structure",
          "User experience - Single menu option with clear workflow branching",
          "Backward compatibility - All existing functionality maintained with improved organization",
          "Code organization - NASA/JPL compliant safety architecture with comprehensive validation"
        ],
        "documentation": [
          "Complete firmware upgrade workflow including site auto-upgrade configuration behavior"
        ]
      }
    },
    {
      "version": "25.09.25.14.30",
      "date": "2025-09-25",
      "changes": {
        "fixes": [
          "Menu option 78 (Generate support package) file path permissions - now properly writes to data/ directory",
          "Menu option 80 (ARP WebSocket output) file path permissions - now properly saves to data/ directory",
          "Menu option 85 variable scope error - removed duplicate logging statement",
          "SSH logging operations - all SSH functions now use proper data/per-host-logs/ directory structure"
        ],
        "configuration_changes": [
          "Configurable SSL settings (PYTHONHTTPSVERIFY, SSL_VERIFY, CA bundles) in .env",
          "Configurable container networking (network name, subnet, driver) in .env",
          "Configurable package management settings (UV check, auto-install, dependencies) in .env",
          "Configurable container runtime settings (image name, container names, SSH port) in .env",
          "Configurable file paths (data directory, script log, env file locations) in .env",
          "Configurable container mount paths for custom deployment scenarios in .env"
        ],
        "enhancements": [
          "Container security compliance - all file I/O operations now respect container volume mounting",
          "Configuration management - moved all hardcoded values from run-misthelper.py to .env file",
          "sample.env template with complete configuration options and documentation",
          "Comprehensive network data capture functionality working correctly"
        ]
      }
    },
    {
      "version": "25.11.03.17.15",
      "date": "2025-11-03",
      "changes": {
        "enhancements": [
          "Menu #102: Enhanced to always show calculated 802.1X timer values regardless of fast_dot1x_timers setting",
          "When fast_dot1x_timers disabled: Shows both current standard defaults AND what calculated values would be if enabled",
          "Provides complete visibility into timer behavior for informed decision-making"
        ]
      }
    },
    {
      "version": "25.11.03.17.00",
      "date": "2025-11-03",
      "changes": {
        "feature_additions": [
          "Menu #102: Added behavior calculation preview before applying RADIUS timer changes",
          "Displays calculated authentication timeout behavior based on server count and retry settings",
          "Shows fast_dot1x_timers impact with calculated quiet-period, transmit-period, and other 802.1X values",
          "Provides expected client experience timing for success and failure scenarios",
          "Includes server selection mode impact (ordered vs unordered failover behavior)"
        ]
      }
    },
    {
      "version": "25.10.31.16.00",
      "date": "2025-10-31",
      "changes": {
        "security": [
          "Menu #103: Added VRE site exclusion - Sites beginning with 'VRE' now automatically skipped",
          "Menu #104: Added VRE site filtering - VRE sites excluded from template impact analysis",
          "VRE sites protected from WAN2 interface variable operations per security policy"
        ]
      }
    },
    {
      "version": "25.10.31.15.15",
      "date": "2025-10-31",
      "changes": {
        "bug_fixes": [
          "Menu #28: Fixed subinterface detection - Now checks for both underscore and dot patterns",
          "Override detection now includes port_config_{port}_ AND port_config_{port}. patterns",
          "Resolves issue where subinterface configs (e.g., {{wan2_interface}}.70, ge-0/0/1.100) were not detected"
        ]
      }
    },
    {
      "version": "25.10.31.15.00",
      "date": "2025-10-31",
      "changes": {
        "bug_fixes": [
          "Menu #103: Fixed subinterface detection pattern - Now checks for dot notation (e.g., {{wan2_interface}}.70)",
          "Override detection now includes: ge-0/0/1_, ge-0/0/1., {{wan2_interface}}_, {{wan2_interface}}.",
          "Resolves issue where variable-based subinterface configs ({{wan2_interface}}.70) were not detected"
        ]
      }
    },
    {
      "version": "25.10.31.14.30",
      "date": "2025-10-31",
      "changes": {
        "bug_fixes": [
          "Menu #103: Fixed override detection to include {{wan2_interface}} configurations",
          "Override detection now checks BOTH ge-0/0/1 AND {{wan2_interface}} port names",
          "Resolves issue where sites with variable-based port configs were not flagged for manual review"
        ],
        "enhancements": [
          "Updated CSV report column from 'has_ge001_overrides' to 'has_wan2_overrides' for clarity",
          "Improved console output messaging to reflect dual detection (hardcoded + variable ports)"
        ]
      }
    },
    {
      "version": "25.10.31.14.00",
      "date": "2025-10-31",
      "changes": {
        "enhancements": [
          "Menu #28: Expanded port coverage - Now searches 6 total ports for overrides instead of 3",
          "Added variable-based port detection - Now includes {{wan1_interface}}, {{wan2_interface}}, {{wan3_interface}} in addition to ge-0/0/0, ge-0/0/1, ge-0/0/2",
          "Comprehensive WAN interface auditing - Identifies both hardcoded and variable-based port configurations"
        ]
      }
    },
    {
      "version": "25.10.31.11.30",
      "date": "2025-10-31",
      "changes": {
        "enhancements": [
          "Menu #104: Enhanced subinterface support - Now handles port subinterfaces like 'ge-0/0/1.70' by replacing only port prefix",
          "Smart pattern replacement - Converts 'ge-0/0/1.70' to '{{wan2_interface}}.70' preserving VLAN/unit suffixes",
          "Improved port detection logic - Distinguishes between exact matches, subinterfaces, and complex port ranges"
        ]
      }
    },
    {
      "version": "25.11.07.00.10",
      "date": "2025-11-07",
      "changes": {
        "feature_additions": [
          "Menu #9: Added tcpdump packet filter selection to Wireless Client Capture (option 1)",
          "Menu #9: Added tcpdump packet filter selection to Wired Client Capture (option 2)",
          "Menu #9: Both client capture types now have access to 40 pre-canned filter options"
        ],
        "enhancements": [
          "Menu #9: Client captures can now filter by protocol, port, direction, application, and security patterns",
          "Menu #9: Consistent filtering capabilities across all applicable capture types (Client, Gateway, Switch, MxEdge)"
        ]
      }
    },
    {
      "version": "25.11.07.00.05",
      "date": "2025-11-07",
      "changes": {
        "feature_additions": [
          "Menu #10: Added tcpdump packet filter selection with 40 pre-canned filter options",
          "Menu #10: Comprehensive filter categories - Basic, Protocol, Direction, Combined, Advanced, Application, Security",
          "Menu #10: Custom tcpdump expression support for advanced filtering",
          "Menu #10: Filter examples include HTTPS, DNS, SSH, TCP flags, port scans, fragmented packets, and more"
        ],
        "enhancements": [
          "Menu #10: Packet filter now displayed in capture configuration summary",
          "Menu #10: Reuses existing _get_tcpdump_expression_selection() method from site captures (menu 9)"
        ]
      }
    },
    {
      "version": "25.11.07.00.01",
      "date": "2025-11-07",
      "changes": {
        "bug_fixes": [
          "Menu #10: Enforced Mist API limitation - Only 1 MxEdge can be captured at a time for organization-level captures",
          "Menu #10: Enforced Mist API limitation - Only 1 port can be captured per MxEdge",
          "Menu #10: Removed multi-selection options that exceeded API constraints",
          "Menu #10: Updated user prompts to clearly indicate single MxEdge/single port requirement",
          "Menu #10: Simplified configuration summary for single MxEdge/port captures"
        ]
      }
    },
    {
      "version": "25.11.06.23.57",
      "date": "2025-11-06",
      "changes": {
        "enhancements": [
          "Menu #10: Enhanced MxEdge selection display with comprehensive status information",
          "Menu #10: Shows mxagent running state (Running/Stopped)",
          "Menu #10: Shows tunterm running state (Running/Stopped)",
          "Menu #10: Displays uptime in days and hours format",
          "Menu #10: Improved display layout with clearer service status indicators"
        ]
      }
    },
    {
      "version": "25.11.06.23.51",
      "date": "2025-11-06",
      "changes": {
        "bug_fixes": [
          "Menu #10: Fixed MxEdge status retrieval - Now correctly fetches status from listOrgMxEdgesStats API endpoint",
          "Menu #10: Status field only available in stats API, not in base listOrgMxEdges call - Added proper stats fetch before display"
        ]
      }
    },
    {
      "version": "25.11.06.23.42",
      "date": "2025-11-06",
      "changes": {
        "enhancements": [
          "Menu #10: Indexed port selection - Select ports by index number (0,1,2) instead of typing port names",
          "Menu #10: Per-MxEdge port selection - Individual port selection for each selected MxEdge",
          "Menu #10: Improved workflow - Port selection happens before format/duration configuration",
          "Menu #10: Clear ONLINE/OFFLINE status display for MxEdges (instead of generic 'connected' status)",
          "Menu #10: Enhanced configuration summary showing selected ports per MxEdge"
        ]
      }
    },
    {
      "version": "25.11.06.23.35",
      "date": "2025-11-06",
      "changes": {
        "feature_additions": [
          "Menu #10: Multiple MxEdge selection support - Capture from multiple MxEdges simultaneously using comma-separated indices",
          "Menu #10: Interface status display - Shows UP/DOWN status, speed, and MAC address for each port before capture",
          "Menu #10: Real-time interface discovery via getOrgMxEdgeStats API for informed port selection"
        ],
        "enhancements": [
          "Menu #10: Improved user workflow with interface visibility before configuration",
          "Menu #10: Multi-device payload building for organization-level captures"
        ]
      }
    },
    {
      "version": "25.11.06.23.31",
      "date": "2025-11-06",
      "changes": {
        "bug_fixes": [
          "Menu #10: Fixed payload structure for MxEdge packet captures - Changed from 'ports' array to 'interfaces' object per API specification",
          "Menu #10: Corrected API request format to match Mist API documentation for organization-level MxEdge captures"
        ]
      }
    },
    {
      "version": "25.11.06.23.28",
      "date": "2025-11-06",
      "changes": {
        "bug_fixes": [
          "Menu #10: Fixed AttributeError - Corrected self.apisession reference to self.mist_session to match PacketCaptureManager initialization"
        ]
      }
    },
    {
      "version": "25.11.06.23.22",
      "date": "2025-11-06",
      "changes": {
        "enhancements": [
          "Menu #10: Organization Packet Capture now fetches and displays indexed list of MxEdges for selection",
          "Menu #10: Shows MxEdge name, model, and online status for easier identification",
          "Menu #10: Eliminated manual UUID entry requirement - automated selection workflow"
        ]
      }
    },
    {
      "version": "25.11.05.14.36",
      "date": "2025-11-05",
      "changes": {
        "enhancements": [
          "Menu #106: Smart policy positioning - When 14+ policies exist, Picocell inserted at position 14 (pushes policies 14+ back one position)",
          "Menu #106: Enhanced audit logging - Position tracking for policy insertions"
        ]
      }
    },
    {
      "version": "25.11.05.00.00",
      "date": "2025-11-05",
      "changes": {
        "feature_additions": [
          "Menu #105: Extract Gateway Template Configuration - Save DIA_Pico (traffic steering) and Picocell (application policy) configs to JSON",
          "Menu #106: Apply Gateway Template Configuration (DESTRUCTIVE) - Replicate extracted configs to other templates with preview and confirmation",
          "JSON-based config replication system for SSR gateway template standardization"
        ],
        "enhancements": [
          "Two-phase extraction/application workflow with JSON intermediate storage",
          "Configuration preview before destructive operations",
          "Audit trail CSV report generation for applied configurations",
          "Support for multiple destination template selection (comma-separated)",
          "Merge logic for updating existing or adding new path preferences and service policies"
        ],
        "documentation": [
          "Updated operation count to 107 total menu entries"
        ]
      }
    },
    {
      "version": "25.10.30.00.00",
      "date": "2025-10-30",
      "changes": {
        "feature_additions": [
          "Menu #103: Set WAN2 Interface Site Variable - Configure 'wan2_interface' site variable across selected sites",
          "Menu #104: Update Gateway Templates to Use WAN2 Variable (DESTRUCTIVE) - Replace hardcoded 'ge-0/0/1' port references with {{wan2_interface}} variable",
          "Site variable management - Set 'wan2_interface'='ge-0/0/1' via updateSiteSettings API for template-based WAN migration",
          "Gateway template modification - Replace hardcoded port names with variable placeholders in port_config",
          "Override detection and flagging - Identify sites with ge-0/0/1 device-level overrides requiring manual review",
          "Audit reporting - CSV reports for variable assignment status and template modification results"
        ],
        "enhancements": [
          "WAN migration workflow - Two-phase approach: site variable setup (103) then template migration (104)",
          "Safety confirmations - Menu #104 requires uppercase 'MIGRATE' confirmation before modifying templates",
          "Bulk operations - Support for all sites or selective site/template targeting",
          "API integration - Uses getSiteSetting, updateSiteSettings, getOrgGatewayTemplate, updateOrgGatewayTemplate",
          "Comprehensive reporting - WAN2_SiteVariable_Report.csv and GatewayTemplate_WAN2_Migration_Audit.csv"
        ],
        "documentation": [
          "Updated operation count to 105 total menu entries",
          "Added gateway template variable operations section to menu structure",
          "Documented WAN2 migration workflow and safety requirements"
        ]
      }
    },
    {
      "version": "25.09.23.00.00",
      "date": "2025-09-23",
      "changes": {
        "documentation": [
          "Initial comprehensive README rewrite to match current codebase",
          "Enhanced menu operation documentation with current truth from code"
        ],
        "feature_additions": [
          "SSH remote access capabilities with containerized deployment",
          "Systematic test mode and performance optimization features"
        ]
      }
    },
    {
      "version": "25.07.08.15.30",
      "date": "2025-07-08",
      "changes": {
        "feature_additions": [
          "Menu option 5 - MAC table WebSocket command for switches with real-time streaming output",
          "Switch-only filtering for MAC table operations to ensure compatibility with supported device types"
        ],
        "enhancements": [
          "WebSocket completion detection - Fixed chunking issue in message parsing for improved performance",
          "Device filtering - Fixed type=all parameter handling to correctly show switches in device selection",
          "MAC table completion - Smart detection completes in ~5 seconds instead of 60s timeout when all entries received",
          "WebSocket debugging - Added comprehensive debug logging for troubleshooting message segmentation",
          "Pattern matching - Robust handling of ethernet switching table vs thernet switching table chunking variations",
          "MAC table retrieval tested on EX4100-F-12P switch with 44 entries, optimal performance confirmed"
        ]
      }
    },
    {
      "version": "25.07.07.11.35",
      "date": "2025-07-07",
      "changes": {
        "fixes": [
          "Client selection API endpoints - Corrected to use searchSiteWirelessClients and searchSiteWiredClients (not list* functions)",
          "AttributeError on client fetch - Resolved module has no attribute listSiteWirelessClients error"
        ],
        "enhancements": [
          "API response handling - Properly extracts results key from search endpoint pagination structure"
        ]
      }
    },
    {
      "version": "25.07.07.11.30",
      "date": "2025-07-07",
      "changes": {
        "feature_additions": [
          "Interactive client selection for wireless/wired captures - Browse currently connected clients with hostname, IP, SSID/VLAN info",
          "Client selection helper function prompt_select_client_mac_from_site() - Lists all wireless and wired clients at selected site",
          "Loop Mode to ALL capture types - Wireless Client (1), Wired Client (2), Gateway (3), New Association (4), Scan Radio (5)",
          "Rich client table with Index, Hostname/User, MAC, IP, Connection Type (Wireless/Wired), SSID/VLAN columns",
          "Manual MAC entry option (m) if client not in connected list or for offline planning"
        ],
        "enhancements": [
          "Client capture workflow - Choose from live client list or manually enter MAC address (fallback option)",
          "Unified loop mode prompt across all capture types - Consistent user experience for continuous monitoring"
        ]
      }
    },
    {
      "version": "25.07.07.11.00",
      "date": "2025-07-07",
      "changes": {
        "feature_additions": [
          "Continuous Loop Mode for packet captures - Automatically restarts captures when complete for continuous monitoring",
          "Background download queue - PCAP files download in background thread while next capture starts immediately",
          "Graceful interruption - Ctrl+C cleanly stops loop and waits for pending downloads to complete",
          "Per-capture iteration tracking - Each capture numbered and logged for easy correlation with downloaded files",
          "Threaded downloader with Queue-based job management for efficient background processing"
        ],
        "enhancements": [
          "Intelligent capture completion detection - Polls for capture completion (enabled=False or duration elapsed) separately from PCAP download availability",
          "Loop mode workflow - 5-second delay between captures to avoid API rate limits, 30-second retry on conflicts"
        ]
      }
    },
    {
      "version": "25.07.07.10.25",
      "date": "2025-07-07",
      "changes": {
        "enhancements": [
          "User experience - Removed repetitive warning about existing captures already in progress (moved to debug logging only)",
          "User experience - Removed redundant NOTE: Mist API requires minimum 60 seconds message (validation still enforced, just cleaner UI)",
          "Packet capture workflow - Reduced visual clutter while maintaining all validation and safety checks in background"
        ]
      }
    },
    {
      "version": "25.07.07.10.20",
      "date": "2025-07-07",
      "changes": {
        "fixes": [
          "Packet capture duration validation - Updated ALL capture types (wireless client, wired client, gateway, new association) to enforce API-mandated 60-second minimum",
          "Duration validation messages - Added explicit API constraint explanations: Mist API requires minimum 60 seconds for all packet captures"
        ],
        "enhancements": [
          "Duration defaults - Changed from 30s to 60s across all capture types to match API requirements and prevent silent API overrides to 600s default",
          "API compliance - Prevents user confusion when requesting 30s captures but receiving 600s captures due to API rejecting sub-60s durations"
        ],
        "documentation": [
          "API discovery - Confirmed via OpenAPI spec that ALL capture types (client, new_assoc, gateway, radiotap, scan) have minimum: 60 and default: 600 constraints"
        ]
      }
    },
    {
      "version": "25.07.07.10.15",
      "date": "2025-07-07",
      "changes": {
        "fixes": [
          "PCAP download polling - Fixed API response structure handling (response.data contains dict with results key, not direct list)",
          "Warning spam - Eliminated Expected list but got dict warnings by properly parsing API pagination structure"
        ],
        "enhancements": [
          "Response type detection - Added logic to extract results key from dict or handle direct list responses for both site and org-level captures",
          "Debug logging - Improved clarity of polling logs showing when results extraction occurs vs direct list handling"
        ]
      }
    },
    {
      "version": "25.07.07.10.05",
      "date": "2025-07-07",
      "changes": {
        "fixes": [
          "Added type checking and defensive handling for API response data in PCAP polling",
          "listSitePacketCaptures sometimes returns list of strings instead of list of dictionaries",
          "Added isinstance() checks before calling .get() on capture objects",
          "Prevents AttributeError: str object has no attribute get"
        ],
        "feature_additions": [
          "Logs data type of response.data (e.g., Received data type: class list)",
          "Logs raw captures data to reveal unexpected response structures",
          "Skip non-dict items in capture list with warning instead of crashing",
          "Safe ID extraction that handles both dict and string items"
        ],
        "enhancements": [
          "Continues polling after encountering unexpected data types",
          "Both _wait_and_download_pcap() and _wait_and_download_pcap_org() functions enhanced"
        ]
      }
    },
    {
      "version": "25.07.02.18.30",
      "date": "2025-07-02",
      "changes": {
        "feature_additions": [
          "Menu option 6 - Show forwarding table command for gateway/SSR devices via WebSocket (Layer 3 routing table)",
          "Gateway/SSR compatibility checks - Device-specific guidance and troubleshooting for forwarding table operations",
          "Layer 3 routing diagnostics - Comprehensive forwarding table information for packet routing decisions"
        ],
        "enhancements": [
          "WebSocket device commands - Expanded support for both Layer 2 (MAC table) and Layer 3 (forwarding table) operations",
          "Menu organization - Filled numbering gap between option 5 and 11 to improve menu structure",
          "Device type validation - Improved device compatibility warnings for Layer 3 vs Layer 2 operations"
        ]
      }
    }
  ]
}

---
**MistHelper** – Practical, transparent data operations for Juniper Mist Cloud.
