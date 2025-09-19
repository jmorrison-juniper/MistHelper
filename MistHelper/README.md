# MistHelper

Network Operations & Data Export Tool for Juniper Mist Cloud

</div>

**Operation Count:** The code currently defines 91 actionable menu entries (1–4, 11–89, 90–98) with some gaps for future expansion.

MistHelper is a production-focused Python application that streamlines large‑scale Juniper Mist Cloud data extraction, enrichment, transformation, and limited lifecycle operations. It supports both interactive (menu) and fully automated CLI execution, with flexible output to either CSV files or a relational SQLite database that uses natural/composite business keys (no artificial surrogate IDs for core entities). The codebase emphasizes safety, transparency, and predictable behavior—aligned with the included internal Agents Guide and NASA/JPL style defensive programming practices.

---
## 1. Why This Rewrite?
The previous README was partially outdated. Key discrepancies corrected here:
1. Operation Count: The code currently defines 97 actionable menu entries (1–65, 70–78, 79–80, 90–97) – not a fixed “96” set. Some originally documented WebSocket shell outputs (81–83) are no longer present in `menu_actions`.
2. File Naming Differences: Actual code exports `OrgApiTokens.csv`, `OrgPsks.csv`, `OrgRfTemplates.csv`, etc. (case-sensitive differences from older docs). A weekly combined inventory is written under `CombinedInventory_ByWeek/` plus per‑operation CSVs in `data/`.
3. SSH Command Runner: Enhanced SSH Runner (option `97`) now uses a fallback CSV at `data/SSH_COMMANDS.CSV` (legacy root location still accepted temporarily).
4. Heavy / Long‑Running Operations: Options 14 (port stats) and 18 (full site config) are intentionally excluded from automated systematic test mode due to extreme duration and rate‑limit pressure.
5. WIP Operations: 63–65 are explicitly flagged in code as work‑in‑progress and may change schema/output without notice.

This README reflects the current actual logic inside `MistHelper.py` (≈19k lines) as of 2025‑09‑18.

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
## 4. Installation (Local)
Choose one path:

### Option A: Quick Start (pip)
```bash
git clone https://github.com/jmorrison-juniper/MistHelper.git
cd MistHelper
python -m venv .venv
./.venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
python MistHelper.py
```

### Option B: Prefer UV (If Allowed)
```bash
python -m pip install uv
git clone https://github.com/jmorrison-juniper/MistHelper.git
cd MistHelper
uv pip install -r requirements.txt
python MistHelper.py
```

---
## 5. Environment Configuration (`.env`)
Minimal required variables:
```env
MIST_HOST=api.mist.com
MIST_APITOKEN=replace_with_org_admin_token
org_id=replace_with_org_uuid

# Optional Tuning (defaults shown)
CSV_FRESHNESS_MINUTES=15
AUTO_UPGRADE_UV=true
AUTO_UPGRADE_DEPENDENCIES=true
UPGRADE_CHECK_TIMEOUT=30
FAST_MODE_MAX_RETRIES=3
FAST_MODE_DEVICES_PER_THREAD=10
FAST_MODE_MAX_CONCURRENT_CONNECTIONS=8
FAST_MODE_USE_CONNECTION_AWARE_THREADING=true
```
Security note: Never commit `.env`. The code auto‑loads using `python-dotenv` if present, else a manual fallback parser.

Organization ID can be copied from the Mist UI URL (`org_id=<uuid>`). If omitted, some paths invoke interactive selection via `mistapi.cli.select_org`.

---
## 6. Command Line Interface
Primary flags (from argparse block near end of file):
| Flag | Purpose |
|------|---------|
| `--menu/-M <id>` | Execute a single menu action non‑interactively |
| `--output-format {csv,sqlite}` | Select output backend (default csv) |
| `--test` | Run systematic safe‑operation test suite |
| `--fast` | Enable fast mode heuristics (threading & reduced retries) |
| `--skip-deps` | Skip dependency auto‑install / upgrade phase |
| `--debug` | Elevate logging for troubleshooting |
| `--address-check` | (If implemented) enable address normalization checks |

Examples (PowerShell friendly):
```powershell
python .\MistHelper.py --menu 11 --output-format sqlite
python .\MistHelper.py --menu 13 --output-format sqlite --fast
python .\MistHelper.py --test --output-format sqlite --debug
```

Interactive fallback occurs if no `--menu` is supplied.

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
| 87–89 | WebSocket Commands | Device ping, ARP, and service ping via WebSocket (real-time output) |
| 90–93 | DESTRUCTIVE Ops | AP firmware upgrade strategies, reboots, virtual chassis conversions |
| 94–96 | Status / Integrity | VC conversion status, gateway stats w/ freshness, WAN port conflict detection |
| 97 | SSH Runner | Enhanced SSH command execution (auto-detect credentials & command file) |
| 98 | SSH by Template | SSH runner targeting gateways by template name (online with management IPs only) |

Important Notes:
* Options 14 & 18 are resource‑intensive (multi‑hour) and skipped during `--test`.
* 63–65 intentionally marked WIP; expect evolution.
* 90–93 should never be scripted unattended without explicit review.

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
## 14. Containers
Two build strategies:
1. `Containerfile` (simple, pip only, SSL bypass env overrides for constrained corporate PKI)
2. `Dockerfile` (multi‑path UV attempt + HEALTHCHECK)

Compose example (interactive shell):
```bash
docker compose build
docker compose run --rm misthelper python MistHelper.py
```

Podman helper (auto build + run):
```powershell
python .\run-misthelper.py
```

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
**MistHelper** – Practical, transparent data operations for Juniper Mist Cloud.

