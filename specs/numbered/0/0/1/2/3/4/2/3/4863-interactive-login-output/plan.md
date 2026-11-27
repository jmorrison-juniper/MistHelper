# Implementation Plan: Interactive Login Output

**Branch**: `fix/4863-interactive-login-output` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/3/4/2/3/4863-interactive-login-output/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

Route each interactive login line to the channel that matches its meaning. Banners, menus, success lines, and result lines use direct output through `echo`. Progress lines write info records only. Failure lines keep their warning or error records. The SDK console level for the interactive login becomes 30, so the SDK stops printing its own success lines. A new 2FA success line confirms an accepted code. The MSP picker and the switch cancel record follow the same rules. No new module, class, or method is added.

## Technical Context

**Language/Version**: Python 3.15 or newer, as stated in the `Language and environment` section of `.github/copilot-instructions.md`.

**Primary Dependencies**: `mistapi==0.64.1` (`requirements.txt` line 129). `pyproject.toml` line 29 allows `mistapi>=0.64.1,<0.65`. The standard library `logging` module. No new dependency.

**Storage**: No new storage. The existing file handler writes `data/script.log`, unchanged.

**Testing**: pytest with fake SDK sessions, `capsys`, `caplog`, and one real-SDK test with a patched HTTP session. The commands are listed in the local gates table of `.github/copilot-instructions.md`.

**Target Platform**: Windows 11, macOS, Linux, and the Podman container. No change.

**Project Type**: Existing command-line and menu tool in one repository.

**Performance Goals**: No change. The login sends the same requests in the same order.

**Constraints**: Each function has at most 25 lines, 5 parameters, and 5 logical blocks. Printed text and log text use ASCII only. Secrets never reach output or logs.

**Scale/Scope**: Four source files, one entry-point line, four updated test modules, one new test module, one operator guide section, and one changelog fragment.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes, with one recorded debt item.*

| Principle or rule | Gate | Evidence in this plan |
|-------------------|------|-----------------------|
| I. Five-item rule | Pass with recorded debt | No directory gains a child. `src/mist/access/auth/interactive/` keeps five tracked files. `LoginOrchestrator` holds 22 methods and `MspOrgSelector` holds 13 methods. Both counts predate this change, and this change adds no method. See Complexity Tracking. |
| II. Class-based design | Pass | Each edit stays inside an existing class. No wrapper function is added. |
| III. Safety first | Pass | Prompt input paths do not change. Passwords and 2FA codes stay out of output and logs (FR-016, SC-004). |
| IV. Full deployment pipeline | Pass | The tasks follow the order of T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. The agent does not merge or deploy. |
| V. Observability and logging | Pass | Each new printed line is ASCII (FR-018). Info and warning records keep their logger names. |
| VI. Inline comments | Pass with task | Each changed line gets an inline comment that states its channel and reason (FR-017). T-LOCAL-GATES checks each changed line. |
| VII. Action logging | Pass | Each removed progress line duplicates an info record that stays. The 2FA success line follows an existing debug record. |
| Mist Cloud gate | Pass | Every REST call still goes through `mistapi`. The change adds no HTTP call and no owned transport. |
| Output backends | Not applicable | No collected data is exported. |
| Data directory | Pass | No product output moves. The file log stays at `data/script.log`. |
| Database keys | Not applicable | No table or endpoint strategy changes. |
| Container security | Not applicable | No container file changes. |
| Zscaler and proxy | Not applicable | No container build or push. |
| Documentation | Pass | The operator guide gets the 2FA line (T013). The changelog fragment is added (T014). |
| Audience standard | Pass | Each printed line keeps its wording or uses plain words. |
| SpecKit escalation | Pass | The change touches four source files and two or more classes, so a specification is required. This record is that specification. |
| Multi-agent workflow | Pass | Issue #4863 has type label `bug`, scope label `MistHelper.py`, and status label `in-progress`. A check of seven open pull requests found no file overlap. |

For repository structure and generated files:

- The commit subject and the pull request title use the Conventional Commit form, for example `fix(login): route interactive login messages to direct output`.
- The record adds one folder under the managed route `specs/numbered/0/0/1/2/3/4/2/3/`. Remote check RC-52 confirms the route formula. The route folder does not exist on `main` (remote tree query, 2026-11-26), so the record creates it with one child.
- The change adds one fragment under `changelog.d/`.
- Product output stays under `data/`. Test output uses `tmp_path`.

For a feature that uses Juniper Mist Cloud:

- REST methods, all through `mistapi`:
  - The `APISession` constructor (`mistapi.__api_session`, `__init__` at line 55, default level at line 67).
  - `APISession.login_with_return` (`mistapi.__api_session`, line 804). It calls `_process_login` (line 740 posts to `/api/v1/login`), `_two_factor_authentication` (line 1100 posts to `/api/v1/login/two_factor`), and `mist_get` (line 892 reads `/api/v1/self`).
- No owned WebSocket transport. The feature needs none.
- Contract tests: `test_two_factor_login_resends_credentials_with_installed_sdk` and `test_http_503_login_clears_session_and_reports_server_failure` keep the SDK path. The constructor assertion changes to level 30 (T005). The new real-SDK test `test_sdk_success_line_stays_off_console` (T006) proves the SDK success line does not reach the terminal.
- Redaction tests: `test_sentinel_password_and_2fa_code_stay_out_of_output` (T006) searches output and log records.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/4/2/3/4863-interactive-login-output/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      operator-output.md
      sdk-login.md
    checklists/
      requirements.md
      output.md
      redaction.md
```

### Source Code (repository root)

File-by-file change map. No file is added to a source package. One test module and one changelog fragment are added.

| Path | Action | Change | Requirements |
|------|--------|--------|--------------|
| `MistHelper.py` | Modify | Line 2702: the cancel record becomes `logger.info`. The line keeps its comment, updated to name the channel. | FR-015, FR-017 |
| `src/mist/access/auth/interactive/clouds.py` | Modify | Line 59 spacer becomes `echo("")`. Lines 66 to 81 (the banner, the divider lines, the explainer, and the cloud rows) become `echo`. | FR-001, FR-002, FR-017 |
| `src/mist/access/auth/interactive/login_orchestrator.py` | Modify | Delete lines 85 and 86 (spacer and progress). Delete lines 136, 169, 197, and 236 (progress). Line 142 changes `console_log_level` from 20 to 30. Lines 191 and 192 (spacer and banner) become `echo`. Insert the 2FA success line after line 204. Lines 229 and 230 (spacer and success) become `echo`. Lines 242 to 249 (MSP summary and spacer) become `echo`. Add the `echo` import with a comment. | FR-004 to FR-009, FR-014, FR-017 |
| `src/mist/access/auth/interactive/msp_org_selector.py` | Modify | Lines 45 to 49 (banner), 55 (MSP auto-selection), 72 (skip), 88 and 92 and 93 (MSP menu), 100 (selected MSP), 133 (no organizations), 137 and 138 (organization count and spacer), 185 to 195 (organization menu and page hint), 206 (skip), and 227 to 229 (selected organization) become `echo`. Line 101 becomes `logger.info`. Add the `echo` import with a comment. | FR-012, FR-013, FR-017 |
| `src/mist/access/auth/interactive/credential_prompter.py` | Unchanged | Lines 28, 44, 47, and 62 are failure or validation lines. They keep their warning records. | FR-011 |
| `tests/unit/marvis/mist/access/auth/interactive/test_clouds.py` | Add | Three tests for the cloud menu and the default choice. | FR-001, FR-002 |
| `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py` | Modify | Update five tests (lines 183, 368, 446, 583, 598). Add five tests. | FR-004 to FR-010, FR-014, FR-016 |
| `tests/unit/marvis/mist/access/auth/interactive/test_msp_org_selector.py` | Modify | Update five tests (lines 49, 226, 277, 328, 343). Add one test. | FR-012, FR-013 |
| `tests/unit/config/foundation/support/refactors/runtime/session/test_switch_to_interactive_login.py` | Modify | Add one test for the cancel record. | FR-015 |
| `documentation/operator-guide.md` | Modify | Add one sentence before the paragraph at line 591 about the 2FA success line. | FR-019 |
| `changelog.d/issue-4863-interactive-login-output.md` | Add | One fragment with one `Fixed` bullet. | FR-019 |

Import placement: the `echo` import goes in the existing import block of each module. It uses the path `src.foundation.support.utils.console`, the same path that `clouds.py` already uses.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
|-----------|------------|--------------------------------------|
| `LoginOrchestrator` holds 22 methods. The limit is 5. The count predates this change. | The class holds the complete login sequence. This change edits existing methods only. | A new helper method would raise the count and break the no-new-method rule. Splitting the class is remediation R-1. |
| `MspOrgSelector` holds 13 methods. The limit is 5. The count predates this change. | The class holds the MSP picker. This change edits existing methods only. | A new helper method would raise the count. Splitting the class is remediation R-2. |
| The `_handle_two_factor` body grows by two lines and stays within 25 lines. | The 2FA success line needs an `if` block and one `echo` call. | A helper would be a new method (see the first row). |

Remediation items, recorded for separate tracking:

- R-1: split `LoginOrchestrator` into a prompt class, a session class, and a reporting class.
- R-2: split `MspOrgSelector` into a menu class and a selection class.

The pull request body names R-1 and R-2. The repository owner opens the tracking issues.

## Dependencies

No package dependency changes. `requirements.txt` keeps `mistapi==0.64.1`. The `echo` helper and the stdlib `logging` module are already used by the affected modules.

## Risks and Mitigations

- **Process-wide SDK console level.** Setting 30 in the interactive login affects every later SDK print until another SDK session sets the level. Mitigation: the spec records this as a Caution. The next SDK session construction resets the level. T006 verifies the level behavior.
- **Symbol gate and the added import.** The `symbol-diff` gate detects lost declarations. An added import is not a lost declaration, but the gate may still report a changed module-level name. Mitigation: the gate runs as written. The pull request states the exact result. No suppression is added.
- **Hidden progress at a higher threshold.** At `CONSOLE_LOG_LEVEL=30`, progress records stay in `data/script.log` but do not reach the terminal. Mitigation: FR-005 and the spec require this. Operators use threshold 20 to see progress.
- **Existing assertions on warning records.** Thirteen assertions check warning records for lines that become direct output. Mitigation: T005 and T009 convert them. Failure assertions stay unchanged.
- **Line drift.** Another merge can move the cited lines. Mitigation: T001 rebases onto `origin/main` and rechecks each cited line before editing.
- **Hot file.** `MistHelper.py` takes one open pull request at a time. Mitigation: T-PR checks `gh pr list` for overlap before the push.

## Rollback

Revert the squash commit of the pull request with `git revert <commit>` on a new branch from `main`. The change moves log channels and adds one fragment, one test module, and one documentation sentence. No data migration and no configuration change are needed. The revert restores the previous warning records and the previous SDK console level.
