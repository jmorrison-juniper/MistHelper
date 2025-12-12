# Agents Guide for MistHelper

Purpose: Enable autonomous or semi-autonomous AI coding agents (and future maintainers) to safely extend, refactor, and diagnose the MistHelper codebase without breaking production conventions or security guarantees. 

As we make updates and commits, update the ReadMe's changlelog with the current version in the following format correlating to the current date and time of when changes were made :" version YY.MM.DD.HH.MM " This can be useful for doing git commit logging/tracking too. When recording the changlog, keep it in JSON formatting with grouped topics, like "api-changes, logging/analytics, compatability, documentation, bug fixes, feature additions, performance, security, refactoring, testing/validation". Keep newest events at the top of the changelog and oldest last. An idea or item should not be spread over multiple topics. We dont need over complicated or "wordy" changelog.

## Git Workflow for Development
After updating README changelog, commit locally with `git add` + `git commit -m "version YY.MM.DD.HH.MM - description"`. Test code. If tests fail, use `git reset --soft HEAD~1` to rollback. Push multiple commits together when ready.

## MANDATORY: Full Deployment Pipeline
**AI agents MUST follow this complete workflow after any code changes:**

### Step 1: Commit and Push
```powershell
git add MistHelper.py README.md  # Add all modified files
git commit -m "version YY.MM.DD.HH.MM - description"
git push origin main
```

### Step 2: Wait for Container Build
The push triggers GitHub Actions automatically (for changes to MistHelper.py, requirements.txt, Containerfile, Dockerfile, __init__.py).
```powershell
# Check workflow status
gh run list --workflow=container-build.yml --limit 1

# Watch the build progress
gh run watch <run-id>
```

### Step 3: Pull New Image
```powershell
podman pull ghcr.io/jmorrison-juniper/misthelper:latest
```

### Step 4: Restart Container
```powershell
# Stop and remove old container
podman stop misthelper ; podman rm misthelper

# Start new container with updated image
podman run -d --name misthelper -p 2200:2200 -p 8050:8050 -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" ghcr.io/jmorrison-juniper/misthelper:latest
```

### Step 5: Verify
```powershell
podman ps  # Confirm container is running
```

**DO NOT skip steps.** The user expects the container to be updated and running after code changes.

Mist API responses are sometimes "nested". Be prepaired to handle that with JSON or otherwise.

Friendly note (new/junior engineers): This guide is meant to be calm and confidence‑building. Most operations are read-only unless clearly marked DESTRUCTIVE. If unsure, read the function header, log what you plan, then proceed in small steps.

Target audience is always a Junior NOC engineer. Language needs to match that of a business professional—avoiding abbreviations or technical jargon—while still making correct Junior NOC level references in the style of Fred Rogers (Mr. Rogers) or Bob Ross (the painter).

Coding standards need to match that of NASA/JPL and their coding guidelines for human safety.

Never use emojis, only ASCII. If emojis are found, swap them out for the nearest equivilant ASCII symbol or art.

All features, or helpers need to live under the appropietly titled/named "Class"'s for code clarity and organization. Refactor code across the script if we need to move a helper or function around that does not yet live in the correct class. Check whole script for refrences that need adjusted during the move.

Avoid "Wrapper" or functions outside classes that point inside classes.

Warnings and logs need to be accurate and valid, nothing can be presented to the user or logs if it is not 100% true. Ignoring false positive warnings or messages is unacceptable.

When searching or listing devices , the Mist API defaults to just AP's unless we specify the "type=all" flag.

During development we will be using a windows 11 machine on VS-code and always testing in  a python virtual enviroment, make sure command syntax during testing is correct.

Dependencies: Managed via runtime import logic and `requirements.txt` (prefers UV if available, else pip). Containers: Podman wording preferred but remain engine‑neutral (Podman or Docker both work). 

---
## Container Registry & CI/CD

### GitHub Container Registry
- **Registry**: `ghcr.io/jmorrison-juniper/misthelper`
- **Build Workflow**: `.github/workflows/container-build.yml`
- **Version Format**: `YY.MM.DD.HH.MM` (UTC timestamp, matching commit version format)

### Building Containers Locally
```powershell
# Build with timestamp version
$version = Get-Date -Format "yy.MM.dd.HH.mm"
podman build -t ghcr.io/jmorrison-juniper/misthelper:$version -t ghcr.io/jmorrison-juniper/misthelper:latest -f Containerfile .
```

### Zscaler/Corporate Proxy Issue (CRITICAL)
Corporate environments using Zscaler SSL inspection will **block container pushes** to ghcr.io. Symptoms:
- 403 Forbidden during chunked blob upload
- Error contains HTML comment: `kHKLKT6ZtNFTsrn4L61Mr17SZnTqQnKT6PWW1LNd` (Zscaler signature)
- Occurs even with valid authentication and Zscaler CA certificates installed

**Root Cause**: Zscaler DLP policies block large HTTP PUT/POST requests to container registries.

**Solution**: Use GitHub Actions for all container pushes:
```powershell
# Manual trigger
gh workflow run container-build.yml

# Check status
gh run list --workflow=container-build.yml --limit 1
gh run watch <run-id>
```

GitHub Actions runs on GitHub infrastructure (not behind corporate proxy), bypassing Zscaler entirely. The workflow automatically:
1. Builds the container using `Containerfile`
2. Tags with timestamp version and `latest`
3. Pushes to `ghcr.io/jmorrison-juniper/misthelper`

### Workflow Triggers
- **Automatic**: Push to `main` that changes `MistHelper.py`, `requirements.txt`, `Containerfile`, `Dockerfile`, or `__init__.py`
- **Manual**: Actions tab -> "Build and Push Container" -> "Run workflow"

Always activate a Python virtual environment before local runs.

Always read the documentation folder contents when starting on changes.

Always read the entire script contents from the root directory in full, without skipping, before making edits.

Never use shorthand or abbreviations in function, loop, or variable naming. Example, never use "for i in images" or similar shorthand.

Do not use double ellipses or any other give-away that the code might have been written by an AI agent.

If adding new features: include similar inline SECURITY comments for potentially risky behavior.

If introducing new persistent artifacts, prefer storing them under `data/` unless they are time-series or operational logs (then use a dedicated folder).

---
## 1. Mist API Ecosystem Reference
MistHelper depends on the `mistapi` Python package authored by Thomas Munzer (GitHub: tmunzer, ID: 5295774). Understanding the broader ecosystem helps with development decisions and potential integration opportunities.

### Core Dependencies
| Package | Author | Repository | Purpose |
|---------|---------|-----------|---------|
| mistapi | Thomas Munzer | tmunzer/mistapi_python | Primary Mist API SDK - core dependency for all API operations |

### Related Ecosystem Projects (Thomas Munzer)
| Repository | Stars | Description | Relevance to MistHelper |
|------------|-------|-------------|------------------------|
| mist_library | 45 | Collection of Python scripts for Mist operations | Reference implementations and examples |
| mistapi_python | 11 | Core Python SDK for Mist API | Direct dependency - source of our API client |
| mist-utils | Various | Additional utilities and tools | Potential feature inspiration |

### Integration Notes
- Thomas Munzer maintains the core mistapi package that powers MistHelper's API functionality
- His mist_library repository contains reference implementations that can guide feature development
- When adding new API operations, check Thomas's repositories for existing patterns and best practices
- Consider contributing improvements back to the mistapi package when beneficial for the broader community

### Future Development Considerations
- Monitor Thomas Munzer's repositories for API updates and new features
- Reference his implementation patterns when extending MistHelper functionality
- Consider collaboration opportunities for shared tooling needs
- Maintain compatibility with upstream mistapi package changes

---
## 2. Architectural Concepts
| Do | Don't |
|----|-------|
| Use existing validators and logging patterns | Don't print raw exceptions without context |
| Keep destructive features isolated & labeled | Don't auto-run destructive code in tests |
| Sanitize filenames & paths | Don't assume OS-specific safe names |
| Update README when adding menu ops | Don't let documentation drift or stagnate |
| Respect concurrency limits | Don't spawn unbounded threads |
| Provide clear user console feedback | Don't overwhelm with verbose raw logs unless debugging |


- Primary entrypoint: `MistHelper.py`

- Data output locations:
  - SQLite DB: `data/mist_data.db`
  - CSV outputs: `data` subfolder
  - Per-host SSH logs: `data/per-host-logs/`

- Main Log file: `data/script.log`

- Configuration: `.env` (never commit credentials) – supports Mist API + SSH credentials + tuning flags.


## 3. Architectural Concepts
| Area | Pattern | Notes |
|------|---------|-------|
| API Operations | Menu-based dispatch | Each menu option corresponds to a data retrieval/export routine. |
| Data Storage | Dual format output | CSV (human) + SQLite (relational queries). |
| Key Strategy | Natural/Composite keys | Avoid synthetic IDs where feasible. |
| SSH Execution | `EnhancedSSHRunner` | Supports shell vs exec modes, validation heavy, per-host logs. |
| Logging | Unified root logger and `ssh_runner_v2` for ssh sessions | Debug traces gated by level; emojis avoided and replaced where found with ASCII. |
| Validation | Static utility methods | `validate_hostname`, `validate_port`, `validate_command`, `sanitize_filename`, etc. |
| Concurrency | `ThreadPoolExecutor` | Thread count bounded to host CPU logical cores; avoid oversubscription. |
| Fallback Data | CSV command file | Now located at `data/SSH_COMMANDS.CSV`. |
| Security | Input/path sanitization | Block path traversal, restricted filenames, sensitive values not echoed. |
| Firmware Upgrades | Strategy orchestration | big_bang, canary, rrm, serial + P2P sharing + scheduling + auto-upgrade config. |
| Address Intelligence | Multi-pass normalization | Unicode cleanup, parsing, similarity scoring, optional Nominatim validation. |

---
## 3. Coding Style & Conventions
- Prefer explicit, human readable names; no cryptic abbreviations, or single letter variables or placeholders.
- Use f-strings for formatting.
- Early-return on validation failures with clear error/log messages.
- Console output uses terminal friendly ASCII for status clarity; retain consistency.
- Logging: Always log internal detail via `logger.debug()`; user-facing prints remain concise.
- Validation: Always validate external inputs (hostnames, ports, commands, thread counts) before acting.
- Resource Limits: Enforce boundaries (max hosts, max commands, output size truncation logic, timeouts for loops/shell reads).
- Safety Prompts: Destructive workflows (firmware upgrades, reboots, virtual chassis conversions) enforce uppercase confirmation tokens—never bypass these.

---
## 4. Security & Safety Principles
| Concern | Practice |
|---------|----------|
| Credentials | Loaded from `.env`; never hardcode or print sensitive tokens/passwords. |
| File Paths | Reject traversal (`..`, absolute paths for restricted calls). |
| Filenames | Sanitize + avoid Windows reserved names. |
| SSH Host Keys | Auto-add only for trusted internal network (explicit comment present). |
| Command Injection | Only execute commands provided through validated, user-intended sources. |
| Log Hygiene | Avoid writing secrets to logs; redact if adding new sensitive fields. |
| Destructive Safeguards | Explicit waiver prompts | Firmware upgrades, reboots, chassis conversions require banner + confirmation keyword. |
| External APIs | Optional address validation | Nominatim lookups only when user enables `--address-check`. |


---
## 5. Logging Model
- Root/application logger writes to `script.log` (already configured externally in startup logic).  
- SSH subsystem uses logger name: `ssh_runner_v2` (propagates upward).  
- DO: Use `logger.debug` for granular tracing; keep user prints minimal.  
- DO NOT: Add second file handlers in utilities (avoid duplicate log lines).  
- When adding heavy loops, provide periodic progress debug lines rather than per-item if >100 items.

---
## 6. Data Output & File Layout
| Path | Purpose |
|------|---------|
| `data/mist_data.db` | Central SQLite database. |
| `data/SSH_COMMANDS.CSV` | SSH fallback commands (moved from root). |
| `CombinedInventory_ByWeek/` | Weekly inventory time-series CSVs (naming: `YYYY_Week_##.csv`). |
| `per-host-logs/` | Isolated SSH session logs: `ssh_output_<sanitized-host>_<timestamp>.log`. |
| Root CSVs | One-off export artifacts (operation-specific). |

---
## 7. EnhancedSSHRunner Design Notes
Key behaviors:
- Input validation for host, user, port, command, thread counts.
- Two execution modes: direct (`exec_command`) and shell (`invoke_shell`) with adaptive reading loop.
- Output sanitation: removes prompt artifacts and ephemeral cleanup noise.
- Per-host log writer closure encapsulated with safe encoding + truncation handling.
- Threaded multi-host execution collects structured summary dict.
- Line-level tracer (debug-only) uses `sys.settrace` within bounded line region—avoid expanding its scope casually.
- Per-host secure log files use sanitized filenames and restrictive permissions.

When modifying:
- Keep timeouts adjustable through existing arguments.
- Preserve output cleaning pipeline; add new artifact filters only if necessary and justified.
- Validate new configuration via existing static validators or add companion methods.

---
## 8. Adding a New Menu Operation (Pattern)
1. Determine API endpoint + data shape.  
2. Implement fetch function with retry logic, rate-limit friendliness, and logging.  
3. Normalize/flatten JSON: maintain consistent field naming; avoid nested raw JSON unless justified; reuse existing helpers.  
4. Persist to both CSV & SQLite (if output format chosen).  
5. Use natural primary keys (business identifiers) for DB table—fallback to composite or autoincrement only if no stable key.  
6. Update README tables (operation number, description, output file) upon definition or modification.  
7. If operation is DESTRUCTIVE or disruptive, add uppercase warning banner + explicit confirmation phrase.  
8. Add to systematic test inclusion if read-only.  
9. Flag destructive operations clearly with `DESTRUCTIVE` label and require explicit user confirmation.

Checklist for DB table creation:
- Unique constraint or primary key defined.  
- Indices on frequently filtered columns (IDs, timestamps).  
- Consistent timestamp format (ISO 8601 preferred if present).  


## 9. Validation & Resource Limits Summary
Bullet summary:
- Thread count: Max CPU thread count.
- Shell read no-data timeout: Approximately 3 seconds after last data; total maximum 120 seconds.
- Output size (shell): Truncation safeguards (100MB cap).

Maintain or lower limits unless there's a measured requirement; justify increases.

---
## 10. Performance & Stability Considerations
- Avoid blocking UI/CLI with long synchronous loops without progress indication.
- For large API enumerations: batch requests + respect rate limiting.
- For multi-host SSH: ensure executor shutdown always occurs (use context manager as current code does).
- Memory: stream large outputs instead of accumulating if adding huge exports (>100MB) unless compression planned.

---
## 11. Dependency Management
- Dependencies declared in `requirements.txt`—retain version lower bounds. 
- Avoid adding heavy dependencies unless critical (risk: container build complexity).
- Use UV to install or update if update is availible. Use pip to install UV if UV is missing.
- If adding: update README (Installation + Advanced Features) and note any platform caveats.

---
## 12. Testing Strategy (Current State & Suggestions)
Current: Manual/systematic `--test` mode for non-destructive operations.  
Suggested enhancements (agents MAY implement gradually):
- Add lightweight unit tests for validators (hostname, port, command parsing).  

---
## 13. Common Error Patterns & Handling
Structured list (add entries as they are discovered; keep concise and action focused):
- Scenario: (Example placeholder) API rate limit exceeded.
  - Current Handling: Adaptive delay logic increases wait based on recent failures.
  - Recommended Agent Action: Inspect `delay_metrics.json`; avoid adding parallel burst calls; reuse existing rate limiter.
- Scenario: (Placeholder) SQLite unique constraint error during bulk insert.
  - Current Handling: Exception logged; operation continues for remaining rows.
  - Recommended Agent Action: Confirm natural key choice; if legitimate duplicates, consider UPSERT pattern (document before implementing).
- Scenario: (Placeholder) SSH command timeout in shell mode.
  - Current Handling: Read loop times out after configured idle period; partial output saved.
  - Recommended Agent Action: Review timeout constants before extending; add progress debug logs instead of lengthening broadly.
- Scenario: (Placeholder) Missing environment variable (e.g., API token).
  - Current Handling: Script logs error and aborts relevant operation.
  - Recommended Agent Action: Add explicit validation helper if expanding required variables; never print secret value.

Add new scenarios following the same three-line pattern for clarity and consistency.



---
## 14. Glossary
- "Natural Key": Business meaningful primary key (e.g., device ID from API).  
- "Fallback CSV": The `data/SSH_COMMANDS.CSV` list used if no command specified.  
- "Shell Mode": Paramiko interactive channel for network devices requiring paginated output handling.  
- "Direct Mode": `exec_command` execution without interactive shell.  

---
## 15. Agent Action Checklist
Before starting a change:
- [ ] Identify all references (use project-wide search) for symbols you're modifying.
- [ ] Confirm no secrets will be exposed.
- [ ] Note any file moves (update paths + docstrings + README if user-facing).

When adding feature:
- Implement function with logging + validation.
- Support both CSV and SQLite outputs if data export.
- Choose natural primary keys; add indices if large tables expected.
- Provide user-friendly console messages with ASCII.
- Update README operation table or a dedicated section.

After change:
- Run grep for old names/paths (e.g., previous file path).
- Verify no accidental debug artifacts left (temporary prints, tracer expansions).
- Ensure new folders created are added to `.gitignore` if volatile.
- Confirm moved resource exists in new location (`data/...`).


- Logging: Add structured JSON log option for automation contexts.

## 16. Safe Refactor Strategy
- Incremental “measure twice, cut once” approach:
- Isolate: Extract a cohesive group (e.g., address parsing) into a new module; preserve public signatures.
- Cover: Add minimal tests (happy path + 1 edge case) before changing logic.
- Annotate: Add docstrings + SECURITY comments at IO & user input seams.
- Verify: Run `--test` mode plus targeted manual menu option; inspect `script.log` for anomalies.
- One intent per PR: do not mix feature + refactor.


---
## 17. Emoji to ASCII Replacement Character Map

Character,Unicode,Emoji Replacement,Usage Context
•,U+2022,🔘,"Bullet point, status indicator"
→,U+2192,➡️,"Direction, flow, next step"
←,U+2190,⬅️,"Back, previous step"
↑,U+2191,🔼,"Upload, increase"
↓,U+2193,🔽,"Download, decrease"
✓,U+2713,✅,"Success, check"
✗,U+2717,❌,"Failure, error"
⚠,U+26A0,⚠️,Warning
★,U+2605,🌟,"Highlight, favorite"
☁,U+2601,☁️,"Cloud, network"
☀,U+2600,🌞,"Online, active"
☕,U+2615,☕️,"Idle, break"
⌛,U+231B,⏳,"Waiting, loading"
⚡,U+26A1,⚡️,"Fast, power"
♻,U+267B,♻️,"Refresh, recycle"
∞,U+221E,🔁,"Loop, unlimited"
π,U+03C0,🧠,"Math, AI, ML"
Σ,U+03A3,📊,"Summation, statistics"
Δ,U+0394,🔺,"Change, delta"
λ,U+03BB,🤖,"Lambda, functional logic"
─,U+2500,➖,"Line, divider"
│,U+2502,📊,"Vertical bar, chart"
┌,U+250C,📈,"Top-left corner, graph"
┐,U+2510,📉,"Top-right corner, graph"
└,U+2514,📈,"Bottom-left corner, graph"
┘,U+2518,📉,"Bottom-right corner, graph"
┼,U+253C,➕,"Intersection, grid"
█,U+2588,🟥,"Full block, progress"
▓,U+2593,🟧,"Medium block, progress"
▒,U+2592,🟨,"Light block, progress"
░,U+2591,⬜,"Minimal block, progress"
≠,U+2260,❎,"Not equal, mismatch"
≈,U+2248,🔁,"Approximately equal, loop"
≥,U+2265,🔼,Greater than or equal
≤,U+2264,🔽,Less than or equal
§,U+00A7,📜,"Section, documentation"
¤,U+00A4,💰,"Currency, value"


---
## 18. Summary
- Follow checklists above to maintain reliability. 
- Emphasize clarity, explicit safety prompts, and minimal surface area changes. 
- If uncertain: log intent, add a narrow TODO, proceed conservatively.

End of agents guide.
