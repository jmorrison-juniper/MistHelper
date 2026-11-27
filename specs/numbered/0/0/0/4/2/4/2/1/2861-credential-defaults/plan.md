# Implementation Plan: Credential default audit

**Branch**: `chore/2861-credential-defaults` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record route `specs/numbered/0/0/0/4/2/4/2/1/2861-credential-defaults`.

## Summary

Repair the remaining wrong-identity sites first. Refuse a missing credential with a typed error or a terminal prompt. Keep intentional defaults with reasons in a ratchet baseline. Three decisions need the owner before their tasks start.

## Technical Context

- **Language and version**: Python 3.15 (`pyproject.toml:23`).
- **Primary dependencies**: `mistapi==0.64.1` (`requirements.txt:129`). Standard library modules `getpass`, `ast`, `hashlib`, `json`, and `subprocess`.
- **Storage**: One baseline JSON file. No database or schema change.
- **Testing**: pytest. Guard tests run without network access. Tests use fake values.
- **Target platform**: Windows 11 first. macOS and Linux must still run.
- **Project type**: Command-line tool, Flask portals, and the `mist-ops-platform` backend.
- **Scale**: 64 baseline candidates in 40 files. 59 lines are present, 4 are partial, and 1 is absent (see research.md).

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass with condition | The guard enters a new nested package. A direct path would add a child to `tests/guardrails/`, which already exceeds five children. |
| II. Class-based architecture | Pass | The scanner is class `CredentialDefaultScanner`. No wrapper function is added. |
| III. Safety-first | Pass | Prompts use hidden input and end-of-file handling. Logs omit every value. |
| IV. Full deployment pipeline | Pass with condition | T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 9. Steps 10 to 12 run after T-MERGE. |
| V. Observability | Pass | Guard output and new messages use ASCII only. |
| VI. Inline comments | Pass with condition | Each new executable line needs an inline comment. |
| VII. Action logging | Pass with condition | Each new action needs an info line before and a debug line after. |
| Mist SDK rule | Pass | No REST request is added. The constructor path appears below. |
| Podman rule | Pass with condition | No container starts in this record. Decision D-7 controls compose changes. |
| File paths | Pass | The scanner uses `pathlib`. |

## Mist Cloud Transport Requirements

- **SDK path**: The `mistapi.APISession` constructor with `apitoken` and `host` (`.venv\Lib\site-packages\mistapi\__api_session.py:55-59`).
- **Call site**: `mist-ops-platform/src/shared/mist/session.py:51`.
- **Token header**: The SDK builds the `Token` header (`__api_session.py:199-201`). The OpenAPI file lists `apiToken` as a security requirement (`documentation/mist-api-openapi31yaml.yaml:85`).
- **New REST endpoints**: None.
- **Contract test**: `tests/integration/test_mistapi_sdk_compatibility.py` runs unchanged.
- **Failure safety**: The factory must not build a session without a usable token.
- **Redaction**: Tests use fake values and assert that no value reaches logs.

## Architecture

1. **Ratchet**: A nested guard package. The scanner lists tracked Python files with `git ls-files`. It walks each syntax tree and reports defaults on credential-bearing names. Each candidate gets a fingerprint.
2. **Database**: `DatabaseConfig` credential fields default to empty values. `__post_init__` rejects sample credential values.
3. **Portal**: A helper reads `ARANGO_USERNAME`. Container runtime requires it. Other runtimes use the image account name and log the variable name.
4. **Command-line token**: A helper asks for a hidden token only when both streams are terminals. It stores the token in `MainEntrypoint.context` for this process. `_parse_api_tokens` returns it when both environment lists are empty.
5. **Integration tests**: The helper reads `MIST_API_TOKEN` first. It fails the session on a conflict.

## File-by-File Change Map

| Path | Action | Batch | Requirements |
| - | - | - | - |
| `tests/guardrails/credential_default_ratchet/__init__.py` | Add | 0 | FR-014 |
| `tests/guardrails/credential_default_ratchet/test_credential_default_ratchet.py` | Add | 0 and 4 | FR-014, FR-015, FR-017 |
| `tests/guardrails/credential_default_ratchet/credential_default_baseline.json` | Add | 0 and 3 | FR-015, FR-016 |
| `src/foundation/persistence/db/__init__.py` | Modify lines 44, 45, and 48, and add `__post_init__` | 1 | FR-001, FR-002, FR-003 |
| `tests/unit/test_standalone.py` | Modify | 1 | FR-001, FR-002, FR-003 |
| `src/interfaces/portals/upgrade_portal/app/config.py` | Modify line 276 | 1 | FR-004, FR-005 |
| `tests/unit/upgrade_portal/test_config.py` | Modify | 1 | FR-004, FR-005 |
| `tests/integration/conftest.py` | Modify lines 36 and 93 | 1 | FR-011 |
| `MistHelper.py` | Modify lines 2809-2832, 2847-2866, and 2891-2905 | 2 | FR-006, FR-007, FR-008 |
| `src/foundation/support/refactors/initialize_mist_session.py` | Modify only if the stored token needs a new read path | 2 | FR-008 |
| `tests/unit/test_credential_preflight.py` | Modify | 2 | FR-006 to FR-010 |
| `mist-ops-platform/src/shared/mist/session.py` | Modify line 90 after D-6 | 1, blocked | FR-013 |
| `compose.yml` and `container/scripts/start.sh` | Modify after D-7 | 4, blocked | FR-018 |
| `MistHelper.py` lines 2819-2827 and 2873-2881, `README.md`, `documentation/development-setup.md`, `documentation/sample.env`, and `deploy/.env.example` | Modify after D-5 | 4, blocked | FR-009 |
| `README.md` line 63 and `documentation/development-setup.md` line 154 | Modify after the prompt exists | 2 | FR-006 |
| `changelog.d/issue-2861-credential-default-ratchet.md` | Add | 0 | SC-005 |
| `changelog.d/issue-2861-database-sample-credentials.md` | Add | 1 | SC-005 |
| `changelog.d/issue-2861-token-variable-precedence.md` | Add | 1 | SC-005 |
| `changelog.d/issue-2861-interactive-token-prompt.md` | Add | 2 | SC-005 |

No file is deleted in batches 0 to 3.

## Dependencies

No package is added. The standard library `getpass` module reads the hidden token. `mistapi` stays at 0.64.1.

## Batch Order

Batch 0 adds the guard first. Batch 1 repairs the database, portal, and integration helper. Batch 2 adds the command-line prompt. Batch 3 records accepted entries and reduces the baseline. Batch 4 adds the SDK allowlist test and waits for decisions D-5 and D-7.

## Risks and Mitigations

- **A prompt blocks automation.** The terminal check runs first. No prompt occurs without both streams.
- **Direct test construction changes.** Existing tests pass explicit values or use standalone mode. Each batch runs its test modules.
- **Container start fails without `ARANGO_USERNAME`.** `compose.yml:145` sets the variable. The refusal names the variable.
- **Hot-file conflicts.** One open pull request may change `MistHelper.py` at a time (`.github/copilot-instructions.md`, Hot files section).
- **Fingerprint duplicates.** The fingerprint includes the enclosing scope and the occurrence order.

Caution: The guard can fail unrelated pull requests when a baseline entry becomes stale. Update the baseline in the same change.

## Rollback

Revert the batch commit. The revert restores the previous baseline file. No data migrates and no schema changes.

Warning: Do not revert batch 1 without restoring the database field defaults. The database then selects a default account again.

## Complexity Tracking

No constitution exception is required. The existing `tests/guardrails` debt remains. Its remediation needs a separate issue.
