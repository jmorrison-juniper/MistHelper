<!--
  Sync Impact Report
  ==================
  Version change: (none) -> 1.0.0 (initial ratification)
  Modified principles: N/A (first version)
  Added sections:
    - Core Principles (5): Five-Item Rule, Class-Based Architecture,
      Safety-First, Full Deployment Pipeline, Observability & Logging
    - Technology & Compatibility Constraints
    - Development Workflow & Quality Gates
    - Governance
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md: no changes needed
      (Constitution Check section is generic; gates are evaluated at
       plan-fill time against this constitution)
    - .specify/templates/spec-template.md: no changes needed
      (spec template is technology-agnostic; constitution gates apply
       at review time, not at template level)
    - .specify/templates/tasks-template.md: no changes needed
      (task categories already support parallel/sequential and
       user-story grouping; no principle-driven task types added)
    - .github/prompts/speckit.*.prompt.md: no changes needed
      (command files reference constitution generically)
  Follow-up TODOs: None
-->

<!-- Global coding standards (5-Item Rule, class-based architecture,
     safety-first input, logging, quality gates) are defined in the
     user-level VS Code instructions file:
       %APPDATA%/Code/User/prompts/coding-standards.instructions.md
     This constitution extends those global standards with
     MistHelper-specific principles and constraints. -->

# MistHelper Constitution

## Core Principles

### I. Five-Item Rule (Structural Discipline)

Every level of the project hierarchy MUST contain no more than five
children. Violations MUST be resolved by extracting into sub-levels
before merging.

Hierarchy levels (largest to smallest):
1. Project Root
2. Packages / Directories
3. Module Files
4. Classes / Functions / Constants
5. Methods / Attributes / Expressions

Function and method hard limits:
- **Max 5 parameters** per function. If more are needed, use a config
  object or dataclass, or split into multiple functions.
- **Max 5 logical blocks** per function body (an if/else counts as one
  block, a for-loop counts as one block, etc.). If exceeded, extract
  blocks into helper functions.
- **Max 5 operations** per statement block. Complex expressions MUST be
  broken into intermediate variables.
- **Max 25 lines** per function (5 blocks x ~5 lines). If longer,
  extract logical sections into helper functions.

**Rationale**: Keeps code navigable, reviewable, and maintainable for
junior NOC engineers who are the primary audience.

### II. Class-Based Architecture (No Wrappers)

All functionality MUST live within semantically named classes. Standalone
wrapper functions that merely delegate to a class method are prohibited.
When refactoring, code MUST be restructured into proper classes — not
wrapped.

Class naming examples from the codebase:
`GlobalImportManager`, `WebSocketManager`, `PacketCaptureManager`,
`FirmwareManager`, `EnhancedSSHRunner`, `SFPTransceiverDataProcessor`,
`DataExporter`, `GatewayExportUtils`.

Variable and iterator naming MUST use full words — no abbreviations:
`for device in devices` NOT `for d in devices`.

AI-generated marker text (`...existing code...`, double ellipses) MUST
never appear in committed code.

**Rationale**: Classes provide clear ownership, discoverability, and
testability. Full names reduce cognitive load for operators reading
unfamiliar code.

### III. Safety-First (NON-NEGOTIABLE)

All input handling MUST use the `safe_input()` pattern with EOF handling
and context logging. Every `input()` call in SSH/container contexts,
destructive confirmations, and interactive menus MUST be wrapped.

Destructive operations (firmware upgrades, reboots, VC conversions,
device command execution — menu items 90-100) MUST require explicit
typed confirmation following the NASA/JPL pattern:
```python
confirmation = safe_input("Type 'UPGRADE' to proceed: ", context="...")
if confirmation != "UPGRADE":
    return  # Early return on validation failure
```

All external inputs MUST be validated before use (reject path traversal,
special characters, etc.). The pattern is: **validate early, return
early** — never proceed with unvalidated data.

Secrets and credentials MUST never appear in logs, outputs, or error
messages. API tokens and passwords MUST be redacted at the logging
boundary.

**Rationale**: MistHelper operates in production NOC environments via
SSH containers. EOF from disconnected sessions, accidental destructive
commands, and credential exposure are real operational risks that MUST
be mitigated at the code level.

### IV. Full Deployment Pipeline (NON-NEGOTIABLE)

After any code change, the complete deployment pipeline MUST be
executed. No steps may be skipped.

1. **Validate syntax** — `python -m py_compile MistHelper.py` MUST
   pass with zero errors before any commit.
2. **Commit** — Message format: `version YY.MM.DD.HH.MM - description`
   (UTC timestamp). All modified files (code + README) MUST be staged.
3. **Push** — `git push origin main` triggers the container build
   workflow (`.github/workflows/container-build.yml`).
4. **Wait for CI** — `gh run watch <run-id>` until the container build
   completes successfully.
5. **Pull image** —
   `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
6. **Restart container** — Stop, remove, and re-run with volume mounts.
7. **Verify** — `podman ps` confirms the container is healthy.

Every changelog update triggers this pipeline. There are no standalone
git operations.

**Rationale**: The user expects the running container to reflect the
latest code after every change. Partial deployments leave the
production environment in an inconsistent state.

### V. Observability & Logging

All log output MUST use ASCII characters only. Unicode characters
(including emoji) MUST be replaced with ASCII substitutions for
cross-platform compatibility.

Logging levels MUST follow these standards:
- **Debug**: Internal state changes, raw API responses
- **Info**: User-facing progress messages
- **Error**: Exception context with full traceback

Structured, machine-parseable log entries (via `structlog` or
equivalent) are required for any new service or module.

Secrets MUST never be logged — this is enforced at the logging
boundary, not at the caller.

**Rationale**: MistHelper runs in heterogeneous environments (Windows
local dev, Linux containers, SSH sessions). ASCII-only logging prevents
encoding failures. Structured logs enable automated monitoring and
incident correlation.

## Technology & Compatibility Constraints

The following technology choices are binding for all MistHelper code:

- **Python**: 3.13 or newer. No code may target older Python versions.
- **mistapi**: 0.59+ (Thomas Munzer's Mist API SDK). This is the sole
  interface to the Juniper Mist Cloud API. Direct HTTP calls to Mist
  endpoints are prohibited when a mistapi method exists.
- **Package Manager**: UV is preferred for speed; `requirements.txt`
  MUST be maintained for pip compatibility.
- **Container Runtime**: Podman is the primary runtime. Docker is
  compatible but all documentation and examples MUST use Podman.
- **File Paths**: MUST use `os.path.join()` or `pathlib.Path()`. Never
  hardcode `/` or `\\` separators. Windows compatibility is required.
- **Output Backends**: All data operations MUST support dual output
  (CSV and SQLite). The `DataExporter.write_with_format_selection()`
  method is the standard entry point.
- **Database Keys**: Natural business keys from the Mist API (not
  artificial IDs). Primary key strategy MUST be defined in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` before implementing any new
  operation.
- **Data Directory**: All outputs MUST go to the `data/` directory,
  enforced at runtime. SSH logs go to `data/per-host-logs/`.
  Database file is `data/mist_data.db`.
- **Container Security**: The container runs as non-root user
  (`misthelper`). The mounted `data/` directory MUST be writable
  (`chmod -R 777 data/` before first run).
- **Zscaler/Proxy**: Local `podman push` behind corporate Zscaler is
  blocked. All container builds and pushes MUST use GitHub Actions CI.

## Development Workflow & Quality Gates

### Adding New Menu Operations

Every new operation MUST follow this sequence:
1. **API Discovery** — Check `mistapi.api.v1.orgs.*` or
   `mistapi.api.v1.sites.*` for available endpoints.
2. **Primary Key Strategy** — Add entry to
   `ENDPOINT_PRIMARY_KEY_STRATEGIES` with the appropriate type
   (natural_pk, composite_pk, or auto_increment_with_unique).
3. **Flatten JSON** — Use existing `flatten_dict()` helpers for nested
   API response structures.
4. **Dual Output** — Call
   `DataExporter.write_with_format_selection(data, filename,
   api_function_name=...)`.
5. **Update README** — Modify the operation count and add the new
   operation to the menu table.
6. **Version Changelog** — Update README with
   `version YY.MM.DD.HH.MM` format (UTC timestamp).
7. **Execute Full Pipeline** — Run the complete deployment pipeline
   (Principle IV).

### Testing

- **Local development**: Windows 11 + venv
  (`python MistHelper.py --test`).
- **Skip list**: Operations 14, 18 (heavy), 63-65 (WIP), 90-100
  (destructive) are excluded from automated tests.
- **Syntax validation**: `python -m py_compile MistHelper.py` MUST
  pass before every commit (enforced by Principle IV).

### Security Findings: Fix Over Suppress (NON-NEGOTIABLE)

Security tool findings (bandit, pip-audit, CodeQL) MUST be
**resolved**, not suppressed:

1. **Fix the root cause** -- Rewrite code to eliminate the vulnerability
   (e.g., validate table names against sqlite_master before use).
2. **Refactor to avoid the pattern** -- Restructure so the flagged
   pattern is not needed (e.g., move a secret default from a dict
   to `os.environ.get()` directly).
3. **`#nosec` only for verified false positives** -- When the tool
   misidentifies safe code (e.g., a logging f-string flagged as SQL
   injection, or an intentional `0.0.0.0` bind gated by
   `is_running_in_container()`). The annotation MUST include a
   justification comment.

Never use `#nosec`, `# type: ignore`, `# noqa`, or similar
suppressions as a shortcut to silence legitimate findings. If a
finding requires more than a trivial fix, create a GitHub issue
and track it.

**Rationale**: Suppressions hide risk. Fixes eliminate it. This
codebase operates in production NOC environments where security
findings left unresolved become real attack surfaces.

### Documentation

- **README.md**: User-facing operations guide. MUST be updated for
  every new operation or behavior change.
- **agents.md**: Internal agent coding guide (~400 lines). MUST be
  consulted before making architectural decisions.
- **Version format**: `YY.MM.DD.HH.MM` (UTC timestamp), consistent
  across changelog entries, commit messages, and container tags.

### Audience Standard

All user-facing text MUST be written for junior NOC engineers. Use
clear, professional language without jargon. The standard is:
"Fred Rogers meets NASA/JPL safety standards."

## Complexity-Driven SpecKit Escalation (NON-NEGOTIABLE)

Not every task needs full ceremony. Use this decision tree:

**Implement directly** (no spec needed):
- Single-file edits with obvious intent (typo, log message, config)
- Lint/format auto-fixes
- Documentation-only changes
- Adding a test for well-understood behavior

**Escalate to SpecKit** (spec required before coding):
- Changes touching 3+ files or 2+ classes
- New menu operations or API integrations
- Architectural changes (new classes, module splits, data flow)
- Bug fixes where root cause is unclear or spans multiple components
- Any change to destructive operations (menu 90-100)
- Performance or concurrency work
- Database schema or primary key strategy changes

**Rationale**: Underpowered models (GPT-5 Mini and similar) lose
track of multi-step implementations without structured artifacts.
The spec anchors intent, the plan decomposes complexity, and tasks
provide checkpoint-by-checkpoint execution any model can follow.
Even capable models benefit from the spec as a contract preventing
scope drift.

Workflow: `speckit.specify` -> `speckit.clarify` (recommended) ->
`speckit.plan` -> `speckit.tasks` -> `speckit.implement` ->
`speckit.analyze`.

If in doubt, escalate. A spec that turns out unnecessary costs
minutes. A botched multi-file change without a spec costs hours.

## Multi-Agent Git Workflow (NON-NEGOTIABLE)

The global coding standards
(`%APPDATA%/Code/User/prompts/coding-standards.instructions.md`)
define the general multi-agent workflow. This section adds
MistHelper-specific enforcement.

### Issue-First Error Pipeline

When any error is detected during development, an issue MUST be
created before attempting a fix:

```powershell
# Ruff violation example
gh issue create --title "Lint: E501 -- line too long in MistHelper.py" \
  --label "lint,MistHelper.py" \
  --body "ruff check output:\n$(ruff check MistHelper.py --select E501)"

# Test failure example
gh issue create --title "Test failure: test_clear_session" \
  --label "bug,test" \
  --body "pytest output:\n$(pytest tests/test_clear_session.py -v)"
```

### Branch Naming for MistHelper

Branches MUST follow this pattern and target `main` directly:
- `fix/<issue-number>-<slug>` -- bug fixes (e.g., `fix/42-clear-session`)
- `feat/<issue-number>-<slug>` -- features (e.g., `feat/50-exports-streaming`)
- `chore/<issue-number>-<slug>` -- maintenance (e.g., `chore/38-ruff-fixes`)

**Never branch from another feature branch.** This caused the
PRs 12-15 stacking mess that required manual conflict resolution.
Every branch starts from `main`.

### Required Labels

Every issue and PR MUST have at least:
1. A **type** label: `bug`, `feature`, `chore`, `lint`, `security`,
   `refactor`
2. A **scope** label: `MistHelper.py`, `tests`, `ci`, `container`,
   `docs`, `web-portal`
3. A **status** label when in progress: `in-progress`

### Fleet Coordination Rules

When multiple agents work on MistHelper simultaneously:

1. **Claim first**: Add `in-progress` label to the issue before
   creating a branch. If another agent already claimed it, pick a
   different issue.
2. **File overlap check**: Run
   `gh pr list --json files --jq '.[].files[].path'`
   to see what files other open PRs touch. Avoid overlapping files.
3. **MistHelper.py is a hot file**: Since most changes touch this
   single file, agents MUST coordinate when multiple PRs modify it.
   Only one agent should have an open PR modifying MistHelper.py at
   a time. Others should wait for merge or work on non-overlapping
   files (tests, docs, CI).
4. **Rebase before push**: Always `git rebase main` before pushing
   to ensure the branch is current.
5. **Squash merge only**: All PRs merge to `main` via squash merge.
   This keeps history linear and readable.

### PR Checklist Enforcement

Every PR MUST include in its description:
- `Closes #<issue-number>` (auto-closes the linked issue)
- CI status confirmation (all quality gates green)
- Files changed summary (to help detect overlap)
- `auto-merge` label added only after all checks pass

## Governance

This constitution is the authoritative source for MistHelper project
rules. It supersedes all other practice documents when conflicts arise.

**Amendment procedure**:
1. Propose the change with rationale in a commit message or discussion.
2. Update this constitution file with the new or modified principle.
3. Increment the version according to semantic versioning:
   - **MAJOR**: Principle removal or backward-incompatible redefinition.
   - **MINOR**: New principle or materially expanded guidance added.
   - **PATCH**: Clarification, wording, or typo fix.
4. Update `LAST_AMENDED_DATE` to the amendment date.
5. Verify that dependent templates (plan, spec, tasks) remain
   consistent with the updated principles.
6. Execute the full deployment pipeline (Principle IV) if code changes
   accompany the amendment.

**Compliance review**: Every PR and code review MUST verify adherence
to all five Core Principles. Complexity that violates a principle MUST
be justified in writing (Complexity Tracking table in plan.md).

**Runtime guidance**: `agents.md` provides detailed implementation
patterns and is the primary reference for day-to-day coding decisions.
The constitution provides the non-negotiable rules; agents.md provides
the how-to.

**Version**: 1.3.0 | **Ratified**: 2026-03-05 | **Last Amended**: 2026-04-06
