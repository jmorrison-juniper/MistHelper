# MistHelper - AI Agent Instructions
You are an elite autonomous software engineer with mastery in architecture, algorithms, testing, and deployment simulation.  
Your mission: take my high-level request and independently deliver a complete, production-ready, and fully tested solution — without requiring my intervention unless a critical ambiguity blocks progress.  

When refactoring code, avoid using wrappers; actually restructure into classes as per project conventions.

### Autonomous Workflow
1. **Requirement Analysis** -- Parse the request, infer missing details, make reasonable assumptions.
2. **Architecture & Design** -- Decide on structure, algorithms, and libraries.
3. **Implementation** -- Write complete, functional, well-documented code.
4. **Self-Instrumentation** -- Embed test points, logging hooks, assertions for critical logic paths.
5. **Self-Testing** -- Write unit, integration, and edge-case tests. Run them. Debug until all pass.
6. **Final Output** -- Present only the final, improved, fully tested version.

### Output Format:
1. **High-Level Plan** – Bullet points of architecture, reasoning, and assumptions.  
2. **Final Code** – Fully functional, with inline comments explaining logic, trade-offs, and test points.  
3. **Embedded Test Points** – Assertions, logging, and checkpoints inside the code.  
4. **Automated Test Suite** – Unit, integration, and edge-case tests.  
5. **Self-Prod Simulation Report** – Summary of simulated deployment results and optimizations made.  
6. **Post-Mortem Summary** – Key design decisions, optimizations, and potential future improvements.  

### Rules:
- Assume autonomy — do not ask me for clarifications unless absolutely necessary.  
- Always produce runnable, tested code in the requested language.  
- Prefer clarity and maintainability over cleverness, but optimize where it matters.  
- Use stable, well-supported libraries and explain why they were chosen.  
- If a feature is ambiguous, make a reasonable assumption and document it.  

---

## Project Overview
MistHelper is a production-grade Python tool (~28K lines) for Juniper Mist Cloud network operations. It provides 100+ menu-driven operations for data extraction, device management, and firmware upgrades with multi-backend output (CSV, SQLite, or polyglot ArangoDB/Redis) and containerized SSH access.

**Target Audience**: Junior NOC engineers. Use clear, professional language without jargon. Think Fred Rogers meets NASA/JPL safety standards.

---

## Core Architecture

### Python Project Hierarchy (5-Item Rule)
Python project hierarchy levels from largest to smallest:
1. **Project Root** - the top-level project folder
2. **Packages/Directories** - folders that organize code (src/, tests/, docs/)
3. **Module Files** - individual .py files
4. **Classes/Functions/Constants** - top-level code constructs in modules
5. **Methods/Attributes/Expressions** - class members and function bodies

**Enforce the 5-item rule**: each level should have no more than 5 children. If exceeded, refactor:
- Too many files in a directory: split into subdirectories or subpackages
- Too many classes in a module: split into multiple module files
- Too many methods in a class: extract methods to helper classes or separate functions
- Too many statements in a function: extract into smaller helper functions

**Function/Method Definition Limits**:
- **Max 5 parameters** per function. If more are needed, use a config object/dataclass or split into multiple functions
- **Max 5 logical blocks** per function body (if/else counts as 1 block, for loop counts as 1 block, etc.). If exceeded, extract blocks into separate helper functions
- **Max 5 operations** per statement block. Complex expressions should be broken into intermediate variables
- **Max 25 lines** per function (reconciles 5 blocks × ~5 lines per block). If longer, extract logical sections into helper functions

This rule keeps code organized, manageable, and easy to navigate. Apply this hierarchy thinking to all Python code organization and refactoring suggestions.

### Design Pattern
- **Classes**: `GlobalImportManager`, `WebSocketManager`, `PacketCaptureManager`, `FirmwareManager`, `EnhancedSSHRunner`, `SFPTransceiverDataProcessor`
- **No wrappers**: All functionality lives within appropriately named classes, never use standalone wrapper functions

### Critical Dependencies
- **Python**: 3.13 or newer required
- **mistapi**: 0.59+ (Primary Mist API SDK by Thomas Munzer - tmunzer/mistapi_python)
- **UV Package Manager**: Preferred over pip for speed (auto-fallback configured). Note: `requirements.txt` maintained for pip compatibility
- **Container Runtime**: Podman (primary), Docker (compatible but not documented - all examples use Podman)

### Data Flow
```
Menu Selection -> API Call -> Flatten/Normalize -> Output Backend (CSV / SQLite / ArangoDB+Redis)
                                                 -> Rate Limiting -> Retry Logic
```

---

## Database Strategy (CRITICAL)

### Hybrid Primary Key System
MistHelper uses **natural business keys** from the Mist API, not artificial IDs. Configuration is centralized in `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary (line ~1672).

**Three Primary Key Types**:

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

**Upsert Logic**: `INSERT OR REPLACE` for natural/composite keys enables updates without duplicates.

**Adding New Operations**: Always define primary key strategy in `ENDPOINT_PRIMARY_KEY_STRATEGIES` before implementation.

---

## Essential Workflows

### Adding New Menu Operations
1. **API Discovery**: Check `mistapi.api.v1.orgs.*` or `mistapi.api.v1.sites.*`
2. **Primary Key Strategy**: Add to `ENDPOINT_PRIMARY_KEY_STRATEGIES` with appropriate type (see Database Strategy section)
3. **Flatten JSON**: Use existing `flatten_dict()` helpers for nested structures
4. **Multi-Backend Output**: Call `DataExporter.write_with_format_selection(data, filename, api_function_name=...)`
5. **Update README**: Modify operation count and add to menu table
6. **Version Changelog**: Update `CHANGELOG.md` with `version YY.MM.DD.HH.MM` format (UTC timestamp)
7. **Git Workflow**: Execute full deployment pipeline (see below)

### MANDATORY: Full Deployment Pipeline
**AI agents MUST execute this complete workflow after any code changes:**

```powershell
# Step 1: Validate BEFORE Commit (syntax + lint + format)
python -m py_compile MistHelper.py    # Syntax check (no output = valid)
python -m ruff check MistHelper.py    # Lint check (must pass clean)
python -m black --check MistHelper.py # Format check (run without --check to auto-fix)
# All three must pass before committing.

# Step 2: Commit and Push
git add MistHelper.py README.md  # Include all modified files
git commit -m "version YY.MM.DD.HH.MM - description"  # UTC timestamp format
git push origin main

# Step 3: Wait for Container Build (triggers automatically on push)
# The workflow includes a validation job that checks Python syntax BEFORE building.
gh run list --workflow=container-build.yml --limit 1
gh run watch <run-id>  # Wait for completion

# Step 4: Pull New Image
podman pull ghcr.io/jmorrison-juniper/misthelper:latest

# Step 5: Restart Container
podman stop misthelper ; podman rm misthelper
podman run -d --name misthelper -p 2200:2200 -p 8055:8055 -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" ghcr.io/jmorrison-juniper/misthelper:latest

# Step 6: Verify
podman ps  # Confirm container is running
```

**DO NOT skip steps.** The user expects the container to be updated and running after code changes.

**Note**: Every changelog update triggers this pipeline - no standalone git operations.

### Data Directory Permissions (CRITICAL)
The container runs MistHelper as a non-root user (`misthelper`) for security. The mounted `data/` directory must be writable:
```bash
chmod -R 777 data/   # Required before first container run
```
**Symptom**: `PermissionError: [Errno 13] Permission denied: '/app/data/script.log'` indicates the data directory needs permissions fixed.

### Running Tests
```powershell
# Local development (Windows 11 + venv required - standard environment)
.venv\Scripts\Activate.ps1
python MistHelper.py --test
```
**Skip List**: Operations 14, 18 (heavy), 63-65 (WIP), 90-100 (destructive)

---

## Critical Patterns

### Safety-First Input Handling
**Consolidated pattern for all input operations** - handles destructive confirmations, SSH/container EOF, and Windows compatibility:

```python
def safe_input(prompt: str, context: str = "unknown") -> str:
    """
    Universal input wrapper with EOF handling and validation.
    
    Args:
        prompt: User-facing prompt text
        context: Operation context for logging (e.g., "firmware_upgrade", "ssh_session")
    
    Returns:
        User input string
        
    Raises:
        SystemExit: On EOF (clean session termination)
    """
    try:
        return input(prompt)
    except EOFError:
        logging.info(f"EOF detected in {context} - session disconnected")
        sys.exit(0)

# DESTRUCTIVE operations require explicit confirmation (NASA/JPL pattern)
confirmation = safe_input("Type 'UPGRADE' to proceed: ", context="firmware_upgrade")
if confirmation != "UPGRADE":
    logging.warning("Operation cancelled - confirmation failed")
    return  # Early return on validation failure
```

**Use this pattern for**:
- All `input()` calls in SSH/container contexts
- Destructive operation confirmations (firmware, reboots, VC conversions)
- Interactive menu selections
- Any user input that could encounter EOF

### Logging Standards
- **Debug**: Internal state changes, API responses
- **Info**: User-facing progress messages
- **Error**: Exception context with full traceback
- **Never log secrets**: Redact tokens/passwords
- **ASCII Only**: Replace Unicode with ASCII equivalents (emoji map in agents.md line ~212). No Unicode characters in logs - use ASCII substitutions for cross-platform compatibility.

### Input Validation
```python
def validate_hostname(hostname: str) -> bool:
    """All external inputs validated before use"""
    # Reject path traversal, special chars, etc.
    # Pattern: validate early, return early (NASA/JPL defensive programming)
```

### File Path Management
- **All outputs**: `data/` directory (enforced at runtime)
- **SSH logs**: `data/per-host-logs/`
- **CSV commands**: `data/SSH_COMMANDS.CSV` (fallback supported at root)
- **Database**: `data/mist_data.db` (SQLite), ArangoDB and Redis run as containers

---

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

---

## Container & SSH Architecture

### Container Registry & CI/CD
- **Registry**: `ghcr.io/jmorrison-juniper/misthelper`
- **Build Workflow**: `.github/workflows/container-build.yml`
- **Version Format**: `YY.MM.DD.HH.MM` (UTC timestamp - consistent with changelog)
- **Triggers**: Push to `main` (when key files change) or manual workflow dispatch

#### Zscaler/Corporate Proxy Workaround
Corporate environments using Zscaler SSL inspection block chunked blob uploads to `ghcr.io` (403 Forbidden with HTML comment signature `kHKLKT6ZtNFTsrn4L61Mr17SZnTqQnKT6PWW1LNd`). **Do not attempt local `podman push` behind Zscaler** - it will fail.

**Solution**: Use GitHub Actions for all container builds and pushes:
```powershell
# Trigger manually
gh workflow run container-build.yml

# Or push changes to trigger automatically
git push origin main
```

GitHub Actions runs on GitHub infrastructure (not behind corporate proxy), bypassing Zscaler entirely.

### Container Detection
```python
is_running_in_container()  # Checks /.dockerenv, /run/.containerenv
```

### SSH Remote Access
- **Port**: 2200 (non-standard for security)
- **ForceCommand**: Direct MistHelper launch (no shell access)
- **Session Isolation**: Unique directory per connection (`/app/sessions/session_<id>/`)
- **Credentials**: Default `misthelper` / `misthelper123!` (change in production)

---

## Menu System & Operations

### Menu Categories (Full Range: 1-100)
**Data Extraction (1-50)**:
- 1-4: Core organization/site operations
- 5-8: WebSocket real-time commands (wireless devices, switches, gateways)
- 9-10: Packet captures (site-level, org-level with switch support)
- 11-50: Device inventory, events, stats, licenses, templates, etc.

**Advanced Operations (51-89)**:
- 51-62: Maps, webhooks, SLE metrics, alarms
- 63-65: WIP features (skip in tests)
- 66-86: Client data, WLAN configs, RF templates, API tokens
- 87-89: Additional WebSocket commands

**Destructive Operations (90-100)** - NEVER automate without explicit user confirmation:
- 90: AP Firmware (Site or Template-based)
- 91-93: AP Reboots (various strategies)
- 94-96: VC Conversion (virtual chassis operations)
- 97-98: SSH Runner (device command execution)
- 99-100: Switch/SSR Firmware (advanced upgrade modes)

### Interactive vs Direct Invocation
- **Interactive**: No args = menu-driven selection with safe navigation
- **Direct**: `--menu 11` for automation
- **Packet Captures** (Menu 9-10): 
  - Site captures (Menu 9): Wireless client, wired client, gateway, **switch**, new association, scan radio
  - Org captures (Menu 10): Similar capabilities at org level
  - **Switch captures**: Full support for port-specific captures with tcpdump filtering
- **WebSocket Commands** (Menu 5-8, 87-89): Real-time device commands with connection management

---

## Common Pitfalls

### Dash 3.x API Changes (Maps Manager)
```python
# WRONG: Deprecated in Dash 3.x - throws ObsoleteAttributeException
app.run_server(host=host, port=port, debug=True)

# CORRECT: Dash 3.x uses app.run()
app.run(host=host, port=port, debug=True, use_reloader=False, threaded=True)
```
**Note**: Always use `use_reloader=False` to prevent double-execution issues on Windows.

### Device Type Filtering
```python
# WRONG: API defaults to APs only
listSiteDevices(site_id)

# CORRECT: Specify type=all for switches/gateways
listSiteDevices(site_id, type="all")
```

### Windows Path Compatibility
Use `os.path.join()` or `Path()`, never hardcoded `/` or `\\`

---

## Project-Specific Conventions

### Naming Standards
- **No abbreviations**: `for device in devices` NOT `for d in devices`
- **No AI markers**: Never use `...existing code...` or double ellipses
- **Class-based**: All features organized under semantic class names

---

## Key Files & Documentation
| File | Purpose |
|------|---------|
| `MistHelper.py` | Main implementation (~28K lines) |
| `CHANGELOG.md` | Version history (Keep a Changelog format) |
| `agents.md` | VS Code Chat agent supplement (points here) |
| `README.md` | User-facing operations guide |
| `SSH_GUIDE.md` | SSH runner detailed usage |
| `requirements.txt` | Python dependencies (pip compatibility) |
| `uv.lock` | UV package lock file (if using UV) |
| `.env` (git-ignored) | Credentials & config |
| `data/mist_data.db` | SQLite persistence (local fallback) |
| `documentation/` | Sample files, API specs (`mist-api-openapi3*`) |

---

## When in Doubt
1. **Read agents.md first** (attached context) - comprehensive safety patterns
2. **Check existing patterns** - grep for similar operations
3. **Validate early, return early** - NASA/JPL defensive programming
4. **Test in venv** - Windows 11 local development standard environment
5. **Update docs** - CHANGELOG.md + README operation tables
6. **Execute full pipeline** - Don't skip deployment steps

---

## Multi-Agent Git Workflow

Global workflow rules are defined in
`%APPDATA%/Code/User/prompts/coding-standards.instructions.md`.
This section adds MistHelper-specific enforcement.

### Issue-First Development

Every code change starts with an issue. No branch without an issue.

When any error is detected during development (lint, test, type, runtime, security, CI),
create a GitHub issue **before** attempting a fix:

| Trigger | Label(s) | Issue Title Pattern |
|---------|----------|---------------------|
| `ruff check` violation | `lint`, rule code | `Lint: <rule> -- <description>` |
| `pytest` failure | `bug`, `test` | `Test failure: <test_name>` |
| `mypy` type error | `chore`, `types` | `Type error: <file>:<line>` |
| Runtime exception | `bug` | `Runtime: <exception> in <function>` |
| Security finding | `security` | `Security: <tool> -- <finding>` |
| CI pipeline failure | `ci` | `CI: <workflow> -- <failure>` |

Use `gh issue create --title "..." --label "..." --body "..."` to create issues
programmatically. Include the full error output in the issue body for traceability.

### Branch Strategy (No Stacking)

```
main (always deployable)
  |-- fix/<issue-number>-<slug>      # bug fixes
  |-- feat/<issue-number>-<slug>     # features
  |-- chore/<issue-number>-<slug>    # maintenance / lint / docs
```

**Critical rules**:
- Every branch targets `main` directly. Never branch from another feature branch.
- Branch name must include the issue number: `fix/42-clear-session`.
- One branch per issue. One PR per branch. One concern per PR.
- Keep branches short-lived: merge or close within days, not weeks.

**Lesson learned**: PRs 12-15 were stacked (branched from each other instead of main),
causing cascading merge conflicts that required manual resolution. This rule prevents that.

### Commit Messages

Use Conventional Commits format:
```
<type>(<scope>): <description>

Closes #<issue-number>
```
Types: `fix`, `feat`, `chore`, `refactor`, `test`, `docs`, `ci`.
Include `Closes #N` in the body so the issue auto-closes on merge.

### Merge Strategy

- **Squash merge** to `main` (one clean commit per PR).
- **Rebase before merging** if the branch is behind `main`.
- **Delete branch** after merge (automatic via GitHub settings).
- **`Closes #N` in PR body** -- squash merge only reads the PR body for auto-close keywords, not individual commit messages.
- **Never force-push** to a shared branch or `main`.

### Required Labels

Every issue and PR MUST have at least:
1. A **type** label: `bug`, `feature`, `chore`, `lint`, `security`, `refactor`
2. A **scope** label: `MistHelper.py`, `tests`, `ci`, `container`, `docs`, `web-portal`
3. A **status** label when in progress: `in-progress`

### Fleet Coordination (Multi-Agent)

When multiple AI agents work on MistHelper simultaneously:

1. **Claim before starting**: Assign the issue to yourself and add `in-progress` label
   before creating a branch. If already claimed, pick a different issue.
2. **Check for file overlap**: Run
   `gh pr list --json files --jq '.[].files[].path'`
   to see what files other open PRs touch. Avoid overlapping files.
3. **MistHelper.py is a hot file**: Since most changes touch this single file, only one
   agent should have an open PR modifying it at a time. Others should wait or work on
   non-overlapping files (tests, docs, CI, web portal).
4. **Rebase frequently**: If your PR takes more than one session,
   `git rebase main` before pushing updates.
5. **Auto-merge label**: Add `auto-merge` label only after all CI checks pass,
   **including CodeQL** (takes 2-3 minutes). Use `gh pr checks <pr> --watch` to confirm.

### Agent Isolation (One Agent = One Worktree = One Branch = One PR)

Every concurrent AI agent MUST operate in its own isolated worktree. This prevents
file-lock collisions, avoids cross-agent contamination, and ensures each agent has
a clean working directory.

**The isolation rule**: One agent, one worktree, one branch, one PR, one concern.

```
MistHelper/                    # main checkout (human or merge agent only)
../MistHelper-agent-1/         # worktree for Agent 1 (feat/101-new-menu)
../MistHelper-agent-2/         # worktree for Agent 2 (fix/102-rate-limit)
../MistHelper-agent-3/         # worktree for Agent 3 (chore/103-docs)
```

**Setup per agent**:
```powershell
# Agent claims issue #101, creates its isolated worktree
git worktree add ../MistHelper-agent-1 -b feat/101-new-menu main
cd ../MistHelper-agent-1
```

**Teardown after merge**:
```powershell
cd ../MistHelper
git worktree remove ../MistHelper-agent-1
git branch -D feat/101-new-menu
git pull origin main
```

**Why worktrees over branches**: On Windows, VS Code and OneDrive hold file locks that
block `git checkout`. Worktrees sidestep this entirely -- each agent has its own directory,
its own index, and its own working tree. No lock contention, no stale file handles.

### Copilot Coding Agent, Spaces & Scratchpads

| Scenario | Surface |
| - | - |
| Well-defined issue, single concern | Copilot Coding Agent (assign to issue) |
| Multi-step feature, needs planning | Copilot Space + SpecKit workflow |
| Quick prototype or API exploration | Scratchpad |
| Local implementation with testing | VS Code Copilot Chat + worktree |
| Complex refactor touching hot files | VS Code Copilot Chat + worktree (human oversight) |

**Copilot Coding Agent**: Triggered by assigning Copilot to an issue. Creates branch,
implements, opens PR -- all autonomously on GitHub infrastructure (not behind Zscaler).
Follows `.github/copilot-instructions.md` automatically. Cannot run `--test` (no API creds in CI).

**Copilot Spaces**: Persistent shared context across sessions. Attach `agents.md`,
`MistHelper.py`, `CHANGELOG.md` for deep project context. Best for planning and architecture.

**Scratchpads**: Throwaway exploration. No git. Discard after use.

### Conflict Resolution Playbook

When multiple agents produce PRs that conflict (especially on `MistHelper.py`),
do NOT fight merge conflicts. Follow this playbook:

**Strategy 1 -- Sequential Merge (preferred)**:
1. Merge the cleanest PR first (fewest files, best coverage, most isolated).
2. All other agents rebase onto updated `main`: `git fetch origin && git rebase origin/main`.
3. Repeat: merge next cleanest, rebase remaining.

**Strategy 2 -- Merge Agent (complex conflicts)**:
Designate one agent as the reconciliation owner. It reviews competing PRs,
produces a single reconciled branch incorporating all changes. Other agents
stop pushing once the merge agent takes over.

**Strategy 3 -- Redesign the Boundary (recurring conflicts)**:
If the same files keep conflicting, extract contested code into separate modules
so agents work on non-overlapping files. Refactoring investment that pays off
across all future multi-agent work.

**Conflict resolution rules**:
- Never force-push to someone else's branch.
- Always rebase, never merge `main` into feature branches.
- Prefer `--force-with-lease` over `--force` for rebased branches.
- If conflicts are extensive (>20 lines), abandon and re-implement from fresh `main`.
- Let Copilot propose conflict resolutions -- paste both versions into chat.

### Agent Observability & Efficiency

Every AI agent interaction must be observable and cost-accountable.

**Logging Requirements**:
- Log every agent call: timestamp, model, prompt hash, token counts (input/output), latency
- Log every subagent spawn: parent agent, child agent name, task description, model used
- Log reasoning traces: key decision points and tool selections for post-mortem analysis
- Store agent logs in `data/agent_logs/` with structured JSON format
- Include session ID to correlate multi-agent workflows across a single task

**Token & Cost Tracking**:
- Maintain a running token/dollar meter per session (input tokens, output tokens, total cost)
- Log per-call cost estimates using model-specific pricing
- Alert when a single session exceeds cost thresholds (configurable via `.env`)
- Track cumulative daily/weekly spend for budget visibility

**Subagent Best Practices**:
- **Small focused contexts**: Give subagents only the files and context they need. Never dump
  the full codebase into a subagent prompt. Specify exactly what to search for or implement.
- **Model routing**: Use cheaper/faster models for simple tasks (search, grep, file reads).
  Reserve expensive models for complex reasoning (architecture, multi-file refactors).
  Match model capability to task complexity.
- **Prompt caching**: Keep system prompts stable across calls to maximize cache hits.
  Do not inject variable data (timestamps, random IDs) into system prompts.
  Move volatile content to user messages instead.

**Failure Detection**:

| Signal | Action |
| - | - |
| Cache miss rate > 50% | Audit system prompt for instability; remove volatile content |
| Subagent called > 3x for same query | Break the loop; escalate to human or try different approach |
| MCP tool result > 50KB | Truncate or filter before passing to model; log the oversized result |
| Token count > 100K in single call | Split task into smaller subtasks; review context window usage |
| Same error repeated 3x | Stop retrying; log the failure pattern and try alternative approach |

### Windows Branch Switching (File Locking)

VS Code and OneDrive hold file locks that block `git checkout` on Windows.
**Preferred approach**: Use git worktrees instead of switching branches:

```powershell
# Create a worktree for the feature branch (separate directory, no locks)
git worktree add ../MistHelper-feat-42 feat/42-my-feature

# Work in the worktree directory
cd ../MistHelper-feat-42

# When done, remove the worktree
cd ../MistHelper
git worktree remove ../MistHelper-feat-42
git branch -D feat/42-my-feature
```

**Fallback** (if worktrees are not practical):
```powershell
# Kill orphaned git processes holding the index lock
Get-Process git -ErrorAction SilentlyContinue | Stop-Process -Force
Remove-Item .git/index.lock -ErrorAction SilentlyContinue
git checkout main
```

### Post-Merge Fix Timing

**Never push to a branch after its PR has been squash-merged.**
The branch's history diverges from `main` after squash merge, so cherry-picks
and pushes to the dead branch will fail or create orphaned commits.

If a fix is needed after merge:
1. Pull `main` to get the squash-merged commit.
2. Create a **new issue** for the fix.
3. Create a **new branch** from `main`.
4. Fix, push, and open a **new PR**.

### Feature Development Workflow (Step-by-Step)

This is the canonical workflow for every code change. No shortcuts.

**Step 1 -- Create an Issue**:
```powershell
gh issue create --title "<type>: <description>" --label "<type>,<scope>"
# Note the issue number from the output URL
```

**Step 2 -- Create a Worktree or Branch**:
```powershell
# Worktree (preferred on Windows -- avoids file lock conflicts)
git worktree add ../MistHelper-<slug> <type>/<issue>-<slug>
cd ../MistHelper-<slug>

# OR branch (if worktrees not practical)
git checkout -b <type>/<issue>-<slug> main
```

**Step 3 -- Develop and Test**:
```powershell
# Make changes, then validate
python -m py_compile MistHelper.py          # Syntax check
python -m ruff check MistHelper.py          # Lint check
python -m black MistHelper.py              # Auto-format (fixes style in place)
python MistHelper.py --test                 # Run test suite (skip 14,18,63-65,90-100)
```

**Step 4 -- Commit with Conventional Commits**:
```powershell
git add <files>
git commit -m "<type>(<scope>): <description>

Closes #<issue>"
```

**Step 5 -- Push and Create PR**:
```powershell
git push origin <type>/<issue>-<slug>
gh pr create --title "<type>(<scope>): <description>" --body "Closes #<issue>" --base main
```

**Step 6 -- Wait for ALL CI Checks (Including CodeQL)**:
```powershell
gh pr checks <pr-number> --watch
# Do NOT proceed until every check shows a green checkmark
# CodeQL takes 2-3 minutes -- do not skip it
```

**Step 7 -- Add Auto-Merge Label**:
```powershell
# Only after ALL checks (including CodeQL) are green
gh pr edit <pr-number> --add-label "auto-merge"
```

**Step 8 -- Clean Up After Merge**:
```powershell
# Worktree cleanup
cd ../MistHelper
git worktree remove ../MistHelper-<slug>
git checkout main && git pull origin main
git branch -D <type>/<issue>-<slug>

# OR branch cleanup
git checkout main && git pull origin main
git branch -D <type>/<issue>-<slug>
```

### NEVER Do These

- Push fixes to a branch after its PR is squash-merged (commits become orphaned)
- Add `auto-merge` label before CodeQL finishes on code PRs
- Branch from feature branches (no stacking -- PRs 12-15 lesson)
- Force-push to `main` or shared branches
- Run `git checkout` while VS Code has files open (use worktrees instead)
- Skip `python -m py_compile`, `ruff check`, or `black --check` before committing

---

## External Resources
- Mist API Docs: `documentation/mist-api-openapi3*.{json,yaml}`
- Thomas Munzer's mistapi: https://github.com/tmunzer/mistapi_python
- Reference implementations: https://github.com/tmunzer/mist_library

---

## Autonomous AI Pipeline (End-to-End)

This section defines the complete AI-driven development, testing, and deployment pipeline. The goal: an AI agent (GitHub Copilot, Copilot Workspace, or VS Code Copilot Chat) can independently implement features, run quality gates, merge PRs, and publish deliverables -- all without human intervention once a Feature Spec is approved.

### Scope & Operating Modes

**Run Mode A -- Standalone**: `MistHelper.py` executed directly on a host under systemd.
- systemd unit: `deploy/misthelper.service`
- Tokens/config loaded via `EnvironmentFile=/opt/misthelper/.env`

**Run Mode B -- Containerized**: Podman/Docker image managed by systemd Quadlet (preferred for single-node).
- Quadlet unit: `deploy/misthelper.container`
- Tokens/config loaded via `EnvironmentFile=./.env` or Docker Compose `env_file:`
- Registry: `ghcr.io/jmorrison-juniper/misthelper`
- Podman Quadlet is the recommended systemd integration; `podman generate systemd` is deprecated.

**Configuration & Secrets (both modes)**:
- All tokens and org IDs live in `.env`, never in code or image layers.
- Python loads via `python-dotenv` (`from dotenv import load_dotenv; load_dotenv()`).
- Containers use Compose `env_file:` / `--env-file .env` / Quadlet `EnvironmentFile=`.
- Committed template: `deploy/.env.example`. Real `.env` is git-ignored.

### Specifying Integration

Every new feature begins as a **Feature Spec** (using SpecKit / Specifying). The Spec is the contract that drives AI-assisted multi-file edits; the PR proves conformance and triggers quality gates then auto-merge.

**Feature Spec (Issue)**: Use `.github/ISSUE_TEMPLATE/feature-spec.yml`. Required sections:
1. **Problem / Goal** -- User problem, desired outcome, non-goals.
2. **Interfaces & Behavior** -- CLI flags, `.env` vars, I/O, error model.
3. **Constraints / Performance** -- Latency, throughput, resource bounds.
4. **Security & Secrets** -- `.env` only; logging/redaction expectations.
5. **Test Plan** -- Unit cases, Hypothesis properties, E2E host+container dry-runs, coverage threshold (>=70%).
6. **Migration / Compatibility** -- Data/flag changes, deprecation plan.
7. **Acceptance Criteria** -- Verifiable outcome checklist.
8. **Implementation Notes (AI hints)** -- Pseudocode, modules, files, risk hotspots.
9. **UI Behavior & Automated Testing** -- Target URLs, interactions, assertions, Playwright scenarios (see Web UI Autonomy section below).

**PR Conformance**: Use `.github/PULL_REQUEST_TEMPLATE.md`. The PR must:
- Link to the Spec Issue.
- Check all conformance boxes (acceptance criteria, tests, coverage, no secrets, dry-runs).
- Show CI status for all quality gates.

### Quality Gates (CI Must Pass Before Merge)

All tools run in `.github/workflows/ci.yml` as a parallel matrix. A PR cannot auto-merge unless every gate is green.

| Gate | Tool | What It Checks |
|------|------|----------------|
| Lint + Format | **Ruff** | Style violations, import order, auto-fixable issues, formatting |
| Type Safety | **mypy** | PEP 484 type annotations, strict optional |
| Tests + Coverage | **pytest + pytest-cov** | Unit/integration tests, coverage >= 70% threshold |
| Property Tests | **Hypothesis** | Invariants hold for all generated inputs |
| Security Lint | **Bandit** | AST-based Python security issues |
| Dependency CVEs | **pip-audit** | Known vulnerabilities in `requirements.txt` |
| Static Analysis | **CodeQL** (`.github/workflows/codeql.yml`) | Deep code + workflow vulnerability scanning |
| E2E Browser | **Playwright** (CI `playwright` job) | Gunicorn web UI functional tests |
| Dependency Updates | **Dependabot** (`.github/dependabot.yml`) | Weekly pip update PRs |

**Pre-commit hooks** (`.pre-commit-config.yaml`) run Ruff, mypy, and Bandit locally to catch issues before push.

**Automated issue lifecycle** (main branch only):
- Gate fails on `main` → GitHub issue auto-created with `quality-gate` label
- Gate passes on `main` → matching open issue auto-closed
- PR branch failures are visible in PR checks only (no issues created)

### Security Findings: Fix Over Suppress

Security tool findings (bandit, pip-audit, CodeQL) must be **resolved**, not suppressed:

1. **Fix the root cause** -- Rewrite code to eliminate the vulnerability.
2. **Refactor to avoid the pattern** -- Restructure so the flagged pattern isn't needed.
3. **`#nosec` only for verified false positives** -- When the tool misidentifies safe code
   (e.g., logging f-string flagged as SQL, intentional `0.0.0.0` bind gated by container
   detection). The annotation MUST include a justification comment.

Never suppress legitimate findings. If a finding requires more than a trivial fix,
create a GitHub issue and track it.

### Toolchain Reference

| Category | Tools |
| - | - |
| Editor & AI | VS Code + Copilot Chat, Copilot Workspace, VS Code Browser Agent Tools |
| Lint + Format | `ruff` (replaces flake8/isort/black) |
| Type Safety | `mypy` (strict optional) |
| Tests + Coverage | `pytest` + `pytest-cov`, `hypothesis` (property-based) |
| Security | `bandit` (AST rules), `pip-audit` (dependency CVEs) |
| Code Scanning | GitHub CodeQL, Dependabot (weekly pip updates) |
| CI Setup | `actions/setup-python` (caching) |
| Container | `docker/build-push-action` + `docker/login-action` → GHCR |
| Release | `softprops/action-gh-release` (wheel, zip artifacts) |
| Runtime | `python-dotenv`, Docker Compose `env_file:`, Podman + Quadlet |

### Delivery Artifacts (Per Release Tag)

Triggered by tag push (`v*.*.*`) via `.github/workflows/release.yml`:
1. **Python wheel + sdist** -- standard `python -m build` output
2. **Standalone ZIP** -- `MistHelper.py` + `requirements.txt` + `README.md` bundled
3. **Container image** -- multi-arch (amd64/arm64) pushed to GHCR

### Auto-Merge & Governance

**Branch protection** on `main` requires all CI checks to pass, **including CodeQL**.
**Auto-merge** workflow (`.github/workflows/auto-merge.yml`): PRs labeled `auto-merge` get squash-merged once all required checks are green. No human click needed.

**Policy for AI-authored PRs**:
- AI must link the PR to the originating Spec Issue.
- AI must tick all conformance checklist boxes in the PR template.
- AI must **wait for CodeQL to pass** before adding the `auto-merge` label.
  Use `gh pr checks <pr-number> --watch` to confirm all checks are green.
- Destructive operations (menu 90-100) require explicit human review regardless of AI authorship.

### Full Pipeline Loop (End-to-End)

1. **Spec** -- Write a Feature Spec Issue using the template. Define problem, behavior, tests, UI expectations.
2. **AI Implements** -- Copilot Chat/Workspace reads the Spec, implements across files, creates tests, updates `.env.example` if needed.
3. **AI Opens PR** -- Links to Spec, fills conformance checklist, pushes branch.
4. **CI Runs** -- Ruff, mypy, pytest+cov, Hypothesis, Bandit, pip-audit, CodeQL, Playwright E2E.
5. **Auto-Merge** -- If all gates green + labeled `auto-merge`, PR squash-merges to `main`.
6. **Container Build** -- Push to `main` triggers container-build workflow: validate syntax -> run tests -> build multi-arch image -> push to GHCR.
7. **Release** -- Tag push triggers release workflow: build wheel/zip, attach to GitHub Release, push container image.
8. **Ops Pull** -- Operators pull new artifact:
   - Host mode: download zip, restart systemd service.
   - Container mode: `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`, restart Quadlet service.

---

## Web UI Autonomy (AI-Driven Browser Interaction)

MistHelper launches a Gunicorn-served web UI (port 8055) that humans use to interact with the script and kick off activities. This section enables AI agents in VS Code to **see**, **interact with**, and **test** these pages autonomously -- no human screenshots required.

### VS Code Browser Agent Tools

VS Code ships built-in browser automation tools for AI agents. These allow Copilot to launch a browser, read the DOM, click buttons, type into forms, take screenshots, and run Playwright code -- all without leaving the editor.

**Enable in VS Code**:
1. Turn on setting: `workbench.browser.enableChatTools`
2. Open Chat (Ctrl+Alt+I) -> Agent mode -> enable Built-in -> Browser tools

**Available Agent Capabilities**:

| Capability | Agent Tool | What It Does |
|------------|-----------|--------------|
| Open page | `openBrowserPage` | Launch URL in VS Code integrated browser |
| Navigate | `navigatePage` | Go to a different URL |
| Read content | `readPage` | Extract DOM text/structure for analysis |
| Screenshot | `screenshotPage` | AI captures its own screenshots (no human needed) |
| Click | `clickElement` | Click buttons, links, menu items |
| Type | `typeInPage` | Enter text into forms/inputs |
| Hover | `hoverElement` | Trigger hover states, tooltips |
| Drag | `dragElement` | Drag-and-drop interactions |
| Dialogs | `handleDialog` | Accept/dismiss browser dialogs |
| Run tests | `runPlaywrightCode` | Execute Playwright automation inline |

**DOM Locator Extraction**: VS Code Simple Browser integration enables point-and-click element selection with automatic locator extraction and test script generation.

### How the AI Operates on the Web UI

**Open & Inspect**: Start MistHelper locally or in container (`-p 8055:8055`). Agent uses
`openBrowserPage`/`navigatePage` to open the URL, `readPage` to extract DOM structure, and
`screenshotPage` for context or failure evidence.

**Interact & Validate**: Agent executes user journeys from the Spec using `clickElement`,
`typeInPage`, `hoverElement`, `dragElement`, `handleDialog`. Inspects DOM state and console
errors to verify expected behavior (new rows, status messages, button transitions).

**Codify as Playwright Tests**: Agent generates Playwright tests via `runPlaywrightCode`,
uses Trace Viewer for debugging, saves tests to `tests/e2e/`. The `gunicorn_server` fixture
in `tests/e2e/conftest.py` handles server lifecycle (starts on random port, tears down after).

### Autonomous Testing Scenarios

Without human presence, the agent can: load and validate page structure, click workflow
triggers, fill forms with test data, inspect network responses, detect JS/console errors,
capture screenshots for failure evidence, generate Playwright regression tests (saved to
`tests/e2e/`), run them in CI (`playwright` job), and auto-repair failing tests using
Copilot + Playwright integration.

### Specifying: UI Section in Feature Specs

When a Spec involves web UI changes, the **"UI Behavior & Automated Testing Expectations"** section in the Issue template must include:

1. **Target URL(s)** the agent must open (e.g., `/`, `/dashboard`, `/jobs`).
2. **Critical user journeys**: buttons to click, forms to fill, dialogs to handle, expected state transitions and messages.
3. **Assertions**: DOM changes, text presence, attribute/state updates, network-visible effects.
4. **Stability contracts**: testable `data-testid` attributes (to keep selectors robust -- prefer these over brittle CSS/XPath).
5. **Artifacts**: request screenshots and Playwright traces for failures.
6. **Non-goals**: flows intentionally out of scope for the feature.

This upfront structure gives the agent precise goals and reduces brittle selectors or ambiguous UI outcomes.

### PR Conformance: UI Testing Additions

In addition to the standard checklist, PRs that touch web UI must include:
- **UI E2E present**: PR includes/updates Playwright tests for changed UI flows.
- **Selectors stabilized**: Stable `data-testid` attributes added where needed; agent verified selectors by interacting with the integrated browser.
- **Agent execution proof**: Screenshots and/or Playwright traces for main flows (stored as CI artifacts on failures or in PR comments when green).

### Best Practices for UI Autonomy

Use `data-testid` attributes for stable selectors (not brittle CSS/XPath). Capture screenshots
and Playwright traces on failures as first-class debug artifacts. Describe interactions and
expected states in the Spec; the agent converts those into executable steps. The Gunicorn fixture
(`tests/e2e/conftest.py`) starts a single-worker server on a random port -- tests should clean
up after themselves.

---

## Complexity-Driven SpecKit Escalation

Not every task needs full ceremony. Use this decision tree to determine whether
to implement directly or escalate to the SpecKit workflow
(specify -> plan -> tasks -> implement):

**Implement directly** (no spec needed):
- Single-file edits with obvious intent (typo, log message, config value)
- Lint/format fixes with auto-fix available
- Documentation-only changes
- Adding a test for existing, well-understood behavior

**Escalate to SpecKit** (spec required before coding):
- Changes touching 3+ files or 2+ classes
- New menu operations or API integrations
- Architectural changes (new classes, module splits, data flow changes)
- Bug fixes where root cause is unclear or spans multiple components
- Any change to destructive operations (menu 90-100)
- Performance or concurrency work
- Database schema or primary key strategy changes

**Why**: Smaller models (e.g., GPT-5 Mini) lose track of multi-step
implementations without structured artifacts. The spec anchors intent, the plan
decomposes complexity, and tasks provide checkpoint-by-checkpoint execution that
any model can follow.

**Workflow when escalating**:
1. `speckit.specify` -- Create/update the spec from the issue
2. `speckit.clarify` -- Surface underspecified areas (recommended)
3. `speckit.plan` -- Generate the implementation plan
4. `speckit.tasks` -- Break the plan into ordered tasks
5. `speckit.implement` -- Execute the tasks
6. `speckit.analyze` -- Cross-check spec/plan/tasks consistency

If in doubt, escalate. A spec that turns out unnecessary costs minutes.
A botched multi-file change without a spec costs hours.

---

## AI Agent Operating Instructions (Summary for Copilot/Workspace)

When implementing a Feature Spec, AI agents must follow this protocol:

1. **Create or claim a GitHub issue** before writing any code. Add `in-progress` label.
2. **Create a branch from `main`** using `fix/<issue>-<slug>`, `feat/<issue>-<slug>`, or `chore/<issue>-<slug>`.
3. **Check for file overlap** with other open PRs (`gh pr list --json files`). Wait if MistHelper.py is contested.
4. **Read the Feature Spec Issue** as the authoritative plan; confirm all Acceptance Criteria.
5. **Implement only necessary files/modules**; keep secrets externalized to `.env`.
6. **Add/modify tests** to meet unit + property requirements and maintain >= 70% coverage.
7. **Update `deploy/.env.example`** if introducing new environment variables.
8. **For UI features**: open the Gunicorn page using browser agent tools, interact to validate behavior, generate Playwright tests, save to `tests/e2e/`.
9. **Prepare the PR** using the PR template; include `Closes #<issue-number>`, link the Spec, and complete all checklist items.
10. **Ensure CI is green**: Ruff, mypy, pytest+cov, Hypothesis, Bandit, pip-audit, CodeQL, Playwright E2E.
11. **Add the `auto-merge` label** once all checks pass.
12. **Do not skip deployment steps**: the release tag publishes host bundle + wheel and pushes the GHCR image.

---

**Remember**: This codebase prioritizes NOC engineer safety and operational clarity over clever abstractions. Explicit > Implicit. Readable > Concise. Safe > Fast.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
