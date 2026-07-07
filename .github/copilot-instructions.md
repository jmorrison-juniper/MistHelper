# MistHelper - AI Agent Instructions

Global coding standards (autonomous workflow, 5-item rule, inline comments, action logging, quality gates) are in `coding-standards.instructions.md` and apply automatically. This file adds MistHelper-specific guidance only.

When refactoring code, avoid using wrappers; actually restructure into classes as per project conventions.

---

## Project Overview
MistHelper is a production-grade Python tool (~28K lines) for Juniper Mist Cloud network operations. It provides 194 menu-driven operations for data extraction, device management, and firmware upgrades with multi-backend output (CSV, SQLite, or polyglot ArangoDB/Redis) and containerized SSH access.

**Target Audience**: Junior NOC engineers. Use clear, professional language without jargon. Think Fred Rogers meets NASA/JPL safety standards.

---

## Core Architecture

### Python Project Hierarchy (5-Item Rule)
See `coding-standards.instructions.md` § Structural Discipline for limits (max 5 params, 5 blocks, 25 lines).

Python hierarchy levels:
1. **Project Root** → 2. **Packages/Directories** → 3. **Module Files** → 4. **Classes/Functions/Constants** → 5. **Methods/Attributes/Expressions**

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

Use for all `input()` calls, destructive confirmations, menu selections, and any context that could encounter EOF.

### Inline Comments (NON-NEGOTIABLE)
See `coding-standards.instructions.md` § Inline Comments for full rules. Python example:

```python
result = api.get_sites(org_id)  # Fetch all sites for this org from Mist API
sites = [s for s in result if s.get("name")]  # Exclude unnamed/placeholder sites
```

### Action Logging (NON-NEGOTIABLE)
See `coding-standards.instructions.md` § Action Logging for full rules. Python example:

```python
logging.info("Fetching device list for site %s", site_id)  # Log before API call
result = api.list_devices(site_id)  # Call Mist API for all devices at this site
logging.debug("Received %d devices from API", len(result))  # Log result count after API call
```

### Logging Standards
See `coding-standards.instructions.md` § Logging Standards.
- **ASCII Only**: Replace Unicode with ASCII equivalents (emoji map in agents.md). No Unicode in logs.

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

### Menu Categories (Full Range: 1-194)

| Range | Category | Notes |
| - | - | - |
| 1-59 | Safe Org Exports | Sites (1-7), Inventory (8-14), Device stats (15-19), Events (20-26), Clients (27-30), Gateways (31-36), Templates (37-41), Config/Admin (42-50), SLE (51-55), Misc (56-59) |
| 60-96 | Interactive Safe | Site devices (60-72), Insights (73-79), Stats (80-91), Viewers (92-96) |
| 97-101, 153 | Resource Intensive | Long-running operations, bulk operations |
| 102-123 | WebSocket | Show commands (102-115), Diagnostics (116-123) |
| 124-150 | Interactive | Diagnostics (124-127), Management (128-133), Packet captures (134-135), Tools (136-147), Config (148-150) |
| 151-152 | Continuous | Monitoring loops |
| 154-194 | **Destructive** | Firmware (154-157), Reboots (158-160), VC (161-162), Templates (163-167), Site config (168-170), Test data (171-174), SSH runners (175-176), Clear/reset (177-187), Support tickets (188-193), Clone device config to gateway template (194). **NEVER automate without explicit user confirmation.** |

### Interactive vs Direct Invocation
- **Interactive**: No args = menu-driven selection with safe navigation
- **Direct**: `--menu 11` for automation

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

See `coding-standards.instructions.md` for naming standards and code readability rules.
- **Class-based**: All features organized under semantic class names, no wrapper functions

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

## Multi-Agent Git Workflow

Global workflow rules are in `git-workflow.instructions.md` (applied via `applyTo: "**"`).
This section adds MistHelper-specific overrides only.

### MistHelper-Specific Error-to-Issue Triggers

| Trigger | Label(s) | Issue Title Pattern |
|---------|----------|---------------------|
| `ruff check` violation | `lint`, rule code | `Lint: <rule> -- <description>` |
| `pytest` failure | `bug`, `test` | `Test failure: <test_name>` |
| `mypy` type error | `chore`, `types` | `Type error: <file>:<line>` |
| Runtime exception | `bug` | `Runtime: <exception> in <function>` |
| Security finding | `security` | `Security: <tool> -- <finding>` |
| CI pipeline failure | `ci` | `CI: <workflow> -- <failure>` |

**Lesson learned**: PRs 12-15 were stacked (branched from each other instead of main),
causing cascading merge conflicts. Never branch from feature branches.

### Required Labels

Every issue and PR MUST have at least:
1. A **type** label: `bug`, `feature`, `chore`, `lint`, `security`, `refactor`
2. A **scope** label: `MistHelper.py`, `tests`, `ci`, `container`, `docs`, `web-portal`
3. A **status** label when in progress: `in-progress`

### Fleet Coordination (MistHelper-Specific)

See `git-workflow.instructions.md` § Agent Coordination for general rules. MistHelper additions:

- **MistHelper.py is a hot file**: Only one agent should have an open PR modifying it at a time.
  Others should wait or work on non-overlapping files (tests, docs, CI, web portal).
- **Auto-merge label**: Wait for **CodeQL** (~2-3 min) before adding. Use `gh pr checks <pr> --watch`.

### Agent Worktree Examples

```
MistHelper/                    # main checkout (human or merge agent only)
../MistHelper-agent-1/         # worktree for Agent 1 (feat/101-new-menu)
../MistHelper-agent-2/         # worktree for Agent 2 (fix/102-rate-limit)
```

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

### Copilot Token Efficiency

See `copilot-token-efficiency.instructions.md` (applied globally via `applyTo: "**"`).

### Windows Branch Switching & Post-Merge Fix Timing

See `git-workflow.instructions.md` § Windows Branch Switching and § Post-Merge Fix Timing.

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

### Scope & Operating Modes

**Run Mode A -- Standalone**: `MistHelper.py` executed directly on a host under systemd.
- systemd unit: `deploy/misthelper.service`
- Tokens/config loaded via `EnvironmentFile=/opt/misthelper/.env`

**Run Mode B -- Containerized**: Podman/Docker image managed by systemd Quadlet (preferred for single-node).
- Quadlet unit: `deploy/misthelper.container`
- Registry: `ghcr.io/jmorrison-juniper/misthelper`
- Podman Quadlet is the recommended systemd integration; `podman generate systemd` is deprecated.

All tokens and org IDs live in `.env` (git-ignored), never in code or image layers. Committed template: `deploy/.env.example`.

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

See `coding-standards.instructions.md` § Security Findings. Project-specific tools: bandit, pip-audit, CodeQL.

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

---

## Web UI Autonomy (AI-Driven Browser Interaction)

MistHelper serves a Gunicorn web UI (port 8055). AI agents use VS Code browser tools to interact autonomously.

**Enable**: Setting `workbench.browser.enableChatTools` must be on.

**Workflow**: Open page (`-p 8055:8055`) → inspect DOM with `readPage` → execute user journeys (`clickElement`, `typeInPage`, etc.) → validate DOM state → generate Playwright tests (`runPlaywrightCode`) → save to `tests/e2e/`. The `gunicorn_server` fixture in `tests/e2e/conftest.py` handles server lifecycle.

### UI Section in Feature Specs

When a Spec involves web UI changes, include:
1. **Target URL(s)** (e.g., `/`, `/dashboard`, `/jobs`)
2. **Critical user journeys**: buttons, forms, dialogs, expected state transitions
3. **Assertions**: DOM changes, text presence, attribute/state updates
4. **Stability contracts**: `data-testid` attributes (prefer over brittle CSS/XPath)
5. **Artifacts**: screenshots and Playwright traces for failures

### PR Conformance: UI Testing

PRs touching web UI must include:
- Playwright tests for changed UI flows (saved to `tests/e2e/`)
- Stable `data-testid` attributes where needed
- Screenshots/traces as CI artifacts on failures

---

## Complexity-Driven SpecKit Escalation

See `git-workflow.instructions.md` § SpecKit Escalation for the full decision tree.

**MistHelper-specific escalation triggers**:
- Any change to destructive operations (menu 90-100)
- Database schema or primary key strategy changes
- Changes touching 3+ files or 2+ classes

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
at specs/1012-misthelper-refactor-hot-functions/plan.md
<!-- SPECKIT END -->

<!-- rtk-instructions v2 -->
# RTK — Token-Optimized CLI

**rtk** is a CLI proxy that filters and compresses command outputs, saving 60-90% tokens.

## Rule

Always prefix shell commands with `rtk`:

```bash
# Instead of:              Use:
git status                 rtk git status
git log -10                rtk git log -10
cargo test                 rtk cargo test
docker ps                  rtk docker ps
kubectl get pods           rtk kubectl pods
```

## Meta commands (use directly)

```bash
rtk gain              # Token savings dashboard
rtk gain --history    # Per-command savings history
rtk discover          # Find missed rtk opportunities
rtk proxy <cmd>       # Run raw (no filtering) but track usage
```
<!-- /rtk-instructions -->