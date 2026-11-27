# Implementation Plan: Upgrade Portal Session Recovery

**Branch**: `fix/3714-upgrade-portal-session-recovery` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record route `specs/numbered/0/0/1/0/4/3/2/4/` and feature folder `3714-upgrade-portal-session-recovery`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Supporting artifacts sit under `design/`.

## Summary

Recover an environment token operator session after a worker replacement. The portal writes one encrypted, non-credential store record at each environment token sign-in. A replacement process reads that record on a registry miss. It rebuilds the cloud session from the process environment and validates it through `APISession.login` and `getSelf`. Browser token and provider login sessions stay out of the store. They need a new sign-in after a worker replacement, unless decision D-1 changes.

The plan uses three implementation groups. Group A adds the store and settings. Group B changes the identity guard and the sign-in route. Group C edits the existing tests and documents the behavior. No route module changes. The 51 protected handlers keep their decorator (`identity.py:886`).

## Technical Context

- **Language/Version**: Python 3.15 or newer (`.github/copilot-instructions.md:18`).
- **Primary Dependencies**: Flask 3.1.3 (`requirements.txt:49`), Gunicorn 27.0.1 (`requirements.txt:58`), mistapi 0.64.1 (`requirements.txt:129`), redis 8.1.0 (`requirements.txt:215`), cryptography 50.0.2 (`requirements.txt:37`). The feature adds no package.
- **Storage**: Redis already holds site locks and run heartbeats (`src/interfaces/portals/upgrade_portal/app/config.py:156`). This feature adds one key family for environment token store records.
- **Testing**: pytest with Flask test clients. An in-memory fake store replaces Redis in tests. The repository has no `fakeredis` pin (`requirements-dev.txt`, local search without a match).
- **Target Platform**: Linux container under Podman. Windows 11 and macOS for local runs.
- **Project Type**: Flask web portal (upgrade capture portal), served by Gunicorn.
- **Performance Goals**: A registry hit adds no Redis call. A sign-in adds one Redis write. An idle refresh writes at most once each 60 seconds for each session.
- **Constraints**: Fail closed. No credential persistence (D-1). One Gunicorn worker (D-11). Five-item rule (Principle I). No route module edits (D-18).
- **Scale/Scope**: Up to 10 operators at one time (`identity.py:474`). 51 protected handlers in 7 route files (RC-23 to RC-29).

## Constitution Check

Each rule has a result and a reason. "PASS as planned" means the task list enforces the rule during implementation.

| Rule | Result | Reason |
| - | - | - |
| Principle I: five-item rule, placement | PASS with recorded debt | The new module enters `persistence/`, which holds 3 children (RC-21). It becomes 4. No new child enters `runtime/` (10 children, RC-20), `app/` (10), `app/routes/` (13), or the test folders. Existing debt is recorded in analysis.md item A-15. |
| Principle I: function limits | PASS as planned | T-LOCAL-GATES runs `radon` with `--max 10` and `pylint`. Each new function keeps five parameters or fewer and 25 lines or fewer. |
| Principle II: class-based architecture | PASS | The store is `SessionRecordStore`, a class. No wrapper function delegates to a class method. |
| Principle III: safety-first | PASS | The feature reads environment variable names only. It validates each setting before use. It adds no destructive operation. |
| Principle III: secrets never logged | PASS as planned | Test TP-22 searches logs, responses, cookies, and store payloads for synthetic values (FR-014). |
| Principle IV: full deployment pipeline | PASS as planned | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE follow this order. |
| Principle V: ASCII logs and structured fields | PASS as planned | Log text stays ASCII. Identifiers in logs use digest prefixes only (contracts/store-record.md). |
| Principle VI: inline comments | PASS as planned | Each task acceptance statement requires a comment on each executable line. |
| Principle VII: action logging | PASS as planned | T005 and T009 require an info line before and a debug line after each store action. |
| Technology: Python version | PASS | Python 3.15 or newer (`.github/copilot-instructions.md:18`). |
| Technology: mistapi sole Mist interface | PASS | The feature calls only the constructor, `login`, and `getSelf` (spec.md, Mist Cloud Transport Requirements). |
| Technology: owned WebSocket transport | Not applicable | The feature adds no owned transport. |
| Technology: package manager | PASS | `requirements.txt` stays unchanged. |
| Technology: container runtime | PASS | The change edits compose and the environment template only. |
| Technology: test containers | PASS | No test container starts. T-LOCAL-GATES uses local commands. |
| Technology: file paths | PASS as planned | New code builds paths with `pathlib` only. |
| Technology: output backends | Not applicable | The feature adds no export. |
| Technology: operational store | PASS as planned | Fail closed (D-9). Backup and recovery: not required, because a lost record forces one sign-in. Retention: the absolute deadline, at most 28800 seconds. Verified persistence: sign-in succeeds only when the write returns true. |
| Technology: database keys | Not applicable | The feature adds no Mist data table. |
| Technology: data directory | PASS | The feature writes no product output under `data/`. |
| Technology: container security | PASS | The non-root user and UID stay unchanged. |
| Development: menu operations | Not applicable | No menu operation changes. |
| Development: README | PASS | README has no sign-in behavior text. It links the operator guide (`README.md:42`). The operator guide changes (D-16). |
| Development: documentation in the same change | PASS as planned | Task T016 updates `documentation/upgrade_capture_portal.md`. |
| Development: release note | PASS as planned | Task T017 adds one Security fragment. |
| Security findings: fix over suppress | PASS | The feature adds no suppression. The existing `nosec` comments in `config.py` stay unchanged. |
| Multi-agent: issue first and labels | PASS | Issue #3714 exists. The labels action appears in STATUS.json. |
| Multi-agent: branch name | PASS | `fix/3714-upgrade-portal-session-recovery`. |
| Multi-agent: file overlap | PASS with condition | Draft PR #4208 changes `deploy/.env.example`. Task T003 coordinates before the edit. |
| Multi-agent: reserved test file | PASS with condition | Issue #2708 reserves `test_no_credential_leak.py` (RC-32). FR-023 forbids an edit before the handoff. |
| SpecKit escalation | PASS | The change touches more than three files and more than two classes. This spec exists. |
| Test-quality ratchet | PASS as planned | T-LOCAL-GATES runs the analyzer with the repository baseline (`.github/copilot-instructions.md:95`). |

## Architecture

The change has five parts.

1. **Store boundary** (`persistence/session_store.py`): `SessionRecordStore` maps an owner key to a store key. It encrypts and decrypts one payload with `MultiFernet`. It writes with a TTL. It reads and deletes one key. Each failure raises a typed error.
2. **Settings** (`app/config.py`): Four settings are read and validated: the encryption key, the previous key, the absolute lifetime, and the idle lifetime. Container startup refuses a missing key and, when D-2 is approved, the default Redis password.
3. **Factory wiring** (`app/factory.py`): `create_app` builds one store for each application. The factory injects the recovery builder (`auth.default_token_session`) and a clock. Teardown closes the store client.
4. **Identity guard** (`runtime/identity.py`): `sign_in` writes the store record before the registry registration. `current_session` reads the store only on a registry miss. `sign_out` deletes the store record. Deadline checks and idle refresh occur in the guard.
5. **Sign-in route** (`app/routes/auth.py`): The environment token path asks for a store write. Other credential modes skip the write. A store failure returns `503 session_store_unavailable`.

Sign-in flow: `submit_signin` (`auth.py:1181`) dispatches the environment token branch (`auth.py:1203`) to `start_token_session` (`auth.py:1027`). The flow then calls `finish_token_session` (`auth.py:1050`) and `sign_in_with_environment_token` (`identity.py:732`). That call writes the store record, then calls `SESSION_REGISTRY.register` (`identity.py:725`), then sets the owner key in the signed session (`identity.py:727`).

Protected request flow: `require_session` (`identity.py:886`) calls `current_session` (`identity.py:764`). A registry hit validates the local deadlines. A registry miss reads the store, decrypts the record, validates it, rebuilds the cloud session, checks the token name, registers the session, and continues. Each failure returns the response in `design/contracts/http-responses.md`.

Sign-out flow: `sign_out` (`identity.py:800`) pops the owner key (`identity.py:821`), clears the browser session, drops the registry record (`identity.py:826`), and deletes the store record. A failed delete logs an error. The browser session still clears.

## File-by-File Change Map

| Path | Action | Task | Reason |
| - | - | - | - |
| `src/interfaces/portals/upgrade_portal/persistence/session_store.py` | Add | T005 | Store class: key digest, `MultiFernet` envelope, TTL write, read, delete, typed errors. |
| `src/interfaces/portals/upgrade_portal/app/config.py` | Modify | T006 | Four settings, validation, container refusals. |
| `src/interfaces/portals/upgrade_portal/app/factory.py` | Modify | T007 | Build the store in `create_app`, inject builder and clock, close at teardown. |
| `src/interfaces/portals/upgrade_portal/runtime/identity.py` | Modify | T009 | Registry-miss recovery, deadline checks, idle refresh, sign-out delete, 503 mapping. |
| `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | Modify | T010 | Environment token sign-in writes a record. Other modes do not. Store failure refuses sign-in. |
| `compose.yml` | Modify | T008 | Required key variable and optional lifetime variables in the `misthelper` environment block (lines 96 to 112). |
| `deploy/.env.example` | Modify | T008 | Document each variable without a value. Coordinate first (T003). |
| `tests/unit/upgrade_portal/test_identity.py` | Modify | T012 | Replace the checks at lines 1505 to 1520 and 1647. Add TP-01 to TP-14 and TP-25. |
| `tests/unit/upgrade_portal/test_config.py` | Modify | T006 | Add TP-15 to TP-17 and TP-26. |
| `tests/contract/upgrade_portal/test_auth.py` | Modify | T013 | Add TP-18 to TP-21. |
| `tests/contract/upgrade_portal/test_security.py` | Modify | T014 and T015 | Add TP-22 to TP-24 and TP-27. |
| `documentation/upgrade_capture_portal.md` | Modify | T016 | Environment table (line 132) and credential mode statements (lines 181 to 192). |
| `changelog.d/issue-3714-portal-session-recovery.md` | Add | T017 | One Security fragment that names issue 3714. |
| `specs/numbered/0/0/1/0/4/3/2/4/3714-upgrade-portal-session-recovery/` | Add | Record | This record, moved by the orchestrator. |

Files that stay unchanged: every module under `src/interfaces/portals/upgrade_portal/app/routes/` except `auth.py`, `container/scripts/start.sh`, `requirements.txt`, `src/foundation/support/utils/logger_utils.py`, `src/interfaces/portals/upgrade_portal/upgrade/driver.py`, and `tests/contract/upgrade_portal/test_no_credential_leak.py`.

## Dependencies

- **Runtime**: `cryptography.fernet.MultiFernet` (`.venv\Lib\site-packages\cryptography\fernet.py:172`), the Redis client (`src/interfaces/portals/upgrade_portal/runtime/lock.py:1055`), and Flask. All three are pinned.
- **Build**: none.
- **Process**: decisions D-1 and D-2 (task T001), the handoff for `test_no_credential_leak.py` (task T002), and the overlap check for `deploy/.env.example` (task T003).

## Risks and Mitigations

| ID | Risk | Mitigation | Residual |
| - | - | - | - |
| R-1 | Warning: A writer with Redis access changes a store record. | `MultiFernet` authenticates each record (FR-004). A writer without the key cannot create a valid record. D-2 requires a non-default Redis password. | A holder of the encryption key can create records. The key stays in the container environment only. |
| R-2 | Caution: Operators authenticate again once, at the deployment that adds the store. | Deploy when no upgrade run is active. The operator guide states the one-time sign-in (T016). | One planned sign-in per operator. |
| R-3 | Caution: A cloud outage during recovery forces a sign-in. | The portal deletes the record on a failed validation (FR-024). The operator authenticates again. | Conservative failure. |
| R-4 | Caution: A lost encryption key makes every record unreadable. | Store records expire within 8 hours. The previous-key setting supports rotation (FR-004). | Operators authenticate again. |
| R-5 | Caution: The idle refresh write fails. | The local session continues. The stored deadline stays earlier than the local deadline. | A later recovery expires sooner. |
| R-6 | Caution: Sign-out cannot delete the store record. | The browser session clears. The record expires within the absolute deadline. The error log names the exception class. | A record remains for at most 28800 seconds. |
| R-7 | Warning: The pattern-based log filter misses an unlabeled secret (`logger_utils.py:216`). | Test TP-22 searches the output for the synthetic values. No new log line prints a token. | The filter limit stays for other code. |
| R-8 | Caution: Existing sign-in tests fail without a store. | T012 and T013 inject an in-memory store double. | Test setup grows. |
| R-9 | Caution: A worker replacement stops a running upgrade driver thread (`driver.py:1386`). | Out of scope. D-12 requires a separate issue. | Runs can stop after a replacement. |
| R-10 | Principle I debt grows. | The new module enters `persistence/` only. Tests edit existing files only. | None added. |
| R-11 | The local checkout differs from main in `logger_utils.py`. | The branch starts from remote main. Do not commit the local change (analysis.md item A-11). | None. |
| R-12 | Warning: The compose default Redis password stays in use. | D-2 requires a change before the store activates (FR-022). | Depends on approval. |

## Rollback Steps

1. Revert the squash commit through a new pull request. Do not force-push `main`.
2. Redeploy the previous image through the `container-build.yml` workflow.
3. Delete store keys that match the prefix `misthelper:capture:session:` one at a time.
4. Remove the `CAPTURE_SESSION_*` variables after the previous image starts.
5. Expect one sign-in for each operator whose session used the new version.

Warning: `FLUSHDB` and `FLUSHALL` delete the site locks and run heartbeats. Do not run either command during rollback.

Warning: removing the volume `misthelper-redis-data` deletes every capture and upgrade run. The volume cannot be recovered after removal.

Caution: removing `CAPTURE_SESSION_ENCRYPTION_KEY` before the revert makes the container refuse to start.

## Validation Plan

The commands appear in `design/quickstart.md`. Each task names one command. T-LOCAL-GATES runs every applicable gate from the local gates table in `.github/copilot-instructions.md:50`.
