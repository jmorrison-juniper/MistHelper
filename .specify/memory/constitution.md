<!--
  Sync Impact Report
  ==================
  Version change: 1.7.1 -> 1.7.2 (PATCH)
  Bump rationale: PATCH, because the amendment corrects stale references and
    stale menu numbers. No principle is added, removed, or redefined. The
    operation registry already enforced the corrected destructive set.
  Modified principles:
    - III. Safety-First: replaced the stale destructive range with the
      destructive set of the operation registry.
  Modified sections:
    - Development Workflow > Testing: replaced the stale skip list with the
      registry categories.
    - Development Workflow > Documentation: replaced the retired lowercase agent
      guide entry with `AGENTS.md` and `.github/copilot-instructions.md`.
    - Complexity-Driven SpecKit Escalation: corrected the destructive set.
    - Multi-Agent Git Workflow: replaced the retired user-profile
      standards file reference with `AGENTS.md`.
    - Governance > Runtime guidance: replaced the retired lowercase agent guide
      with `AGENTS.md` and `.github/copilot-instructions.md`.
    - Header comment: replaced the user-profile standards file with
      `AGENTS.md`.
  Added sections: None.
  Removed sections: None.
  Templates requiring updates:
    - .specify/templates/plan-template.md: no update required.
    - .specify/templates/spec-template.md: no update required.
    - .specify/templates/tasks-template.md: no update required.
    - .specify/templates/checklist-template.md: no update required.
    - .specify/templates/agent-file-template.md: no update required.
    - .specify/templates/constitution-template.md: no update required.
  Related files updated simultaneously: None.
  Follow-up actions: None.
-->

<!-- Generic coding standards (5-Item Rule, class-based architecture,
     safety-first input, logging, quality gates) live in `AGENTS.md` at the
     repository root. `.github/copilot-instructions.md` holds the rules
     that apply to MistHelper only.
     This constitution extends those standards with
     MistHelper-specific principles and constraints. -->

# MistHelper Constitution

## Core Principles

### I. Five-Item Rule (Structural Discipline)

Every new hierarchy level MUST contain no more than five children.

Existing tracked violations are grandfathered technical debt. A feature MUST
NOT add a direct child to a noncompliant parent. New feature code MUST enter a
compliant nested package.

Required unique process records MAY be direct children of an established
process folder, such as `specs/` or `changelog.d/`, when the repository
workflow requires direct children. Each change MUST add only its own unique
record. The plan MUST record the existing folder debt and MUST track a
separate incremental remediation action. This exception does not permit other
new direct children in a noncompliant parent.

A change MAY edit an existing child when the edit is narrow and necessary.
The change MUST NOT increase the number of children at that hierarchy level.
The change does not need to restructure unrelated existing children.

New functions, methods, classes, constants, and expressions remain subject to
the limits below. The plan MUST record each touched existing violation. The
plan MUST also record a separate incremental remediation action.

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
device command execution, and other changes to the Mist cloud) MUST require
explicit typed confirmation following the NASA/JPL pattern. The
`destructive` category of `src/foundation/support/utils/operation_registry.py`
is the source of truth. It holds menus 154-187, 189-191, 194, 206-208, 239, 281, 286-287, and 291-293:
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

After any code change, the complete deployment pipeline MUST run. No step may
be skipped.

1. **Run local gates** — Run every existing gate that applies to the changed
   files.
2. **Build the manifest** — Include committed branch changes, staged changes,
   unstaged changes, and feature-owned untracked files.
3. **Stage the feature** — Stage every file in the explicit feature manifest.
   Do not stage unrelated files.
4. **Commit** — Use a Conventional Commit subject that the pull request title
   guard accepts. Use `type: description`, `type(scope): description`,
   `type!: description`, or `type(scope)!: description`. Use one of these
   types: `fix`, `feat`, `chore`, `refactor`, `test`, `docs`, `ci`, `style`,
   or `perf`.
5. **Rebase** — Fetch and rebase the committed feature branch onto
   `origin/main`. Rerun affected local gates after the rebase.
6. **Push the feature branch** — Push the rebased branch to its remote branch.
7. **Open the pull request** — Target `main` and include the issue closure,
   changed-file summary, local gate results, and deployment notes.
8. **Pass CI** — All required pull request checks MUST pass.
9. **Squash merge** — Merge the approved pull request with one squash commit.
10. **Wait for the main build** — Wait for
    `.github/workflows/container-build.yml` on the merged `main` revision.
11. **Verify the revision** — The image revision label MUST equal the merged
    commit SHA.
12. **Deploy and check health** — Pull the approved image, deploy it, and
    confirm the container and portal health checks.

No feature workflow may push directly to `main`.

Every release-note fragment triggers this pipeline. There are no standalone
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

### VI. Inline Comments (NON-NEGOTIABLE)

Every line of AI-generated code MUST have an inline comment on the
same line explaining what it does and why. This is not optional and
MUST NOT be skipped under any circumstances.

Comments MUST explain *why* and *what for*, not just restate the code.
Blank lines, closing braces/parens, and decorators are exempt.

When modifying existing code, inline comments MUST be added to the
changed lines AND to any adjacent uncommented lines in the same block.
When existing code is found lacking inline comments during any edit,
comments MUST be added to the entire function or block being touched.

```python
# WRONG: No comments or restating the code
result = api.get_sites(org_id)  # get sites

# CORRECT: Explaining intent and context
result = api.get_sites(org_id)  # Fetch all sites for this org from Mist API
sites = [s for s in result if s.get("name")]  # Exclude unnamed/placeholder sites
```

Code without inline comments is considered incomplete and MUST NOT
be committed, merged, or deployed.

**Rationale**: Junior NOC engineers are the primary maintainers of
this codebase. Every line must be self-explanatory without external
context. Inline comments eliminate guesswork and reduce onboarding
time from days to hours.

### VII. Action Logging (NON-NEGOTIABLE)

Every meaningful action in AI-generated code MUST have a logging
statement BEFORE and AFTER execution. This enables operators to trace
exactly what happened during any run.

- Log an `info` message BEFORE every action (API call, file write,
  database operation, data transformation, user prompt).
- Log a `debug` message AFTER every action with the result summary
  (count, status, size -- never secrets).
- Log `error` with full context on any exception.
- Use `%s` style formatting in logging calls (not f-strings) for
  performance and security.

When modifying existing code, if the function or block being touched
lacks action logging, logging MUST be added to the entire function or
block.

```python
# WRONG: No logging around actions
result = api.list_devices(site_id)
processed = flatten_response(result)

# CORRECT: Log before and after every action
logging.info("Fetching device list for site %s", site_id)
result = api.list_devices(site_id)  # Call Mist API for all devices at this site
logging.debug("Received %d devices from API", len(result))
logging.info("Flattening device response data")
processed = flatten_response(result)  # Normalize nested JSON to flat structure
logging.debug("Flattened %d device records", len(processed))
```

Code without action logging is considered incomplete and MUST NOT be
committed, merged, or deployed.

**Rationale**: When a NOC engineer reports "it broke at step 3," the
logs must show exactly what happened before, during, and after step 3.
Code without logging is code without observability.

## Technology & Compatibility Constraints

The following technology choices are binding for all MistHelper code:

- **Python**: 3.13 or newer. No code may target older Python versions.
- **mistapi**: 0.59+ (Thomas Munzer's Mist API SDK). This is the sole
  interface for Juniper Mist Cloud REST APIs. Code MUST NOT send direct
  HTTP requests to a Mist REST endpoint when a working mistapi method exists.
- **Owned WebSocket Transport**: Code MAY own a Mist Cloud WebSocket transport.
  This permission applies only when the matching mistapi WebSocket path is
  broken, incomplete, or cannot preserve required output. The specification and plan
  MUST name the SDK path and the failed contract. Contract tests MUST prove
  that the SDK path is insufficient before implementation can pass review.
  The owned transport MUST preserve the SDK authentication and endpoint
  contracts. It MUST follow every safety rule and every secret-redaction rule
  in this constitution. Its tests MUST verify authentication, endpoint,
  output, failure, and redaction contracts. This exception does not permit
  direct HTTP requests to Mist REST endpoints.
- **Package Manager**: UV is preferred for speed; `requirements.txt`
  MUST be maintained for pip compatibility.
- **Container Runtime**: Podman is the primary runtime. Docker is
  compatible but all documentation and examples MUST use Podman.
- **Test Containers**: Every container started for a test, a debug
  session, or an end-to-end run MUST join the compose group. A bare
  `podman run` outside the group is prohibited. An ephemeral container
  MUST carry the issue number or the pull request number in its name
  (`misthelper-tmp-<issue|pr><number>-<slug>`). It MUST NOT publish a
  production local port. Read `compose.yml` for the current set. It
  MUST be removed when the test ends. See
  `documentation/container-deployment.md` § "Test and debug containers".
- **File Paths**: MUST use `os.path.join()` or `pathlib.Path()`. Never
  hardcode `/` or `\\` separators. Windows compatibility is required.
- **Output Backends**: API export and data collection operations MUST support
  the configured output backends through
  `DataExporter.write_with_format_selection()`.
- **Operational Store**: Internal coordination records MAY use the declared
  operational store when they need transactions, locks, idempotency, or
  compare-and-swap. The specification MUST define fail-closed behavior,
  backup and recovery, retention, and verified persistence. The application
  MUST NOT report success until it verifies the required durable write.
- **Export Boundary**: The operational-store exception MUST NOT weaken the
  multi-backend rule for API exports or collected API data.
- **Database Keys**: Natural business keys from the Mist API (not
  artificial IDs). Primary key strategy MUST be defined in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` before implementing any new
  operation.
- **Data Directory**: All product outputs MUST go to the `data/` directory,
  enforced at runtime. Generated test evidence MAY go to the established,
  git-ignored `test-artifacts/` folder. SSH logs go to
  `data/per-host-logs/`. Database file is `data/mist_data.db`.
- **Container Security**: The container runs as the non-root user
  `misthelper` with UID 1000. The mounted `data/` directory MUST accept a
  write from that identifier. On Linux, use
  `podman unshare chown -R 1000:1000 data`. Never use `chmod -R 777 data`.
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
4. **Multi-Backend Output** — Call
   `DataExporter.write_with_format_selection(data, filename,
   api_function_name=...)`.
5. **Update README** — Modify the operation count and add the new
   operation to the menu table.
6. **Release Note** — Add one new fragment under `changelog.d/`. Name
   it `pr-<number>.md`, `issue-<number>-<slug>.md`, or
   `<YYYY-MM-DD>-<slug>.md`. Never edit `CHANGELOG.md` on a feature
   branch.
7. **Execute Full Pipeline** — Run the complete deployment pipeline
   (Principle IV).

### Testing

- **Local development**: Windows 11 + venv
  (`python MistHelper.py --test`).
- **Skip list**: `OperationRegistry` decides. `--test` runs only the
  `safe` category, and `--testinteractive` adds `interactive_safe`. The
  automated tests skip every other category: `resource_intensive`
  (14, 18-19, 59, 97-101, 153), `destructive` (154-187, 189-191, 194, 206-208, 239, 281, 286-287, and 291-293),
  `interactive`, `websocket`, and `continuous_loop`.
- **Syntax validation**: `python -m py_compile MistHelper.py` MUST
  pass before every commit (enforced by Principle IV).

### Security Findings: Fix Over Suppress (NON-NEGOTIABLE)

Security tool findings (bandit, pip-audit, CodeQL) MUST be
**resolved**, not suppressed:

1. **Fix the root cause** -- Rewrite code to eliminate the vulnerability
   (e.g., validate table names against sqlite_master before use).
2. **Refactor to avoid the pattern.** Restructure the code so it does not
   need the flagged pattern. For example, move a secret default out of a dict.
   Use `os.environ.get()` to read it directly.
3. **`#nosec` only for verified false positives** -- Use this option only
   when the tool misidentifies safe code. Examples include a logging
   f-string flagged as SQL injection and an intentional `0.0.0.0` bind
   gated by `is_running_in_container()`. The annotation MUST include a
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
- **AGENTS.md** and **.github/copilot-instructions.md**: The agent
  guides. `AGENTS.md` holds the generic rules, and
  `.github/copilot-instructions.md` holds the rules for MistHelper only.
  Both MUST be consulted before making architectural decisions.
- **Version format**: `YY.MM.DD.HH.MM` (UTC timestamp), consistent
  across released changelog entries, commit messages, and container
  tags. The release coordinator writes that stamp.
- **Release notes**: Each change MUST add one unique fragment under
  `changelog.d/`. A feature branch MUST NOT edit `CHANGELOG.md`,
  because a shared file conflicts on every parallel rebase. See
  `changelog.d/README.md`.

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
- Changes touching 3+ files or 2+ classes.
- New menu operations or API integrations.
- Architectural changes (new classes, module splits, data flow).
- Bug fixes where root cause is unclear or spans multiple components.
- Any change to destructive operations (menus 154-187, 189-191, 194, 206-208, 239, 281, 286-287, and 291-293).
- Performance or concurrency work.
- Database schema or primary key strategy changes.

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

`AGENTS.md` at the repository root defines the general multi-agent
workflow. This section adds
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
4. **Rebase before push**: Always `git rebase origin/main` before pushing
   to ensure the branch is current.
5. **Squash merge only**: All PRs merge to `main` via squash merge.
   This keeps history linear and readable.

### PR Checklist Enforcement

Every PR MUST include in its description:
- `Closes #<issue-number>` (auto-closes the linked issue).
- CI status confirmation (all quality gates green).
- Files changed summary (to help detect overlap).
- Local gate results.
- Deployment and rollback notes.
- `auto-merge` label added only after all checks pass.

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

A MINOR amendment MAY reconcile established repository practice with these
rules. It MUST preserve safety, MUST prevent new debt, and MUST record existing
debt for separate incremental remediation.

**Compliance review**: Every PR and code review MUST verify adherence
to all seven Core Principles. Complexity that violates a principle MUST
be justified in writing (Complexity Tracking table in plan.md). The table MUST
separate grandfathered debt from new design. A feature MUST NOT use
grandfathered debt as permission to add another violation.
Principles VI (Inline Comments) and VII (Action Logging) are
non-negotiable quality gates -- code lacking either MUST NOT pass
review, regardless of other merits.

**Runtime guidance**: `AGENTS.md` and `.github/copilot-instructions.md`
provide detailed implementation patterns and are the primary references for
day-to-day coding decisions. The constitution provides the non-negotiable
rules. The two guides provide the how-to.

**Version**: 1.7.2 | **Ratified**: 2026-03-05 | **Last Amended**: 2026-10-05
