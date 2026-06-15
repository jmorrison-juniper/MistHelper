# Feature Specification: Vault & OS Keyring Credential Backends

**Feature Branch**: `201-vault-keyring-secrets`
**Created**: 2026-06-11
**Status**: Draft
**Input**: User description: "Adopt HashiCorp Vault and/or OS keyring for MistHelper credential storage. Optional Vault backend for enterprise NOC; optional OS keyring for local dev; .env remains default fallback. Upstream mistapi >=0.59 already supports both."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enterprise NOC operator uses Vault for all credentials (Priority: P1)

A NOC operator running MistHelper from a hardened jump host or container in an enterprise environment configures MistHelper to read every secret (Mist API token, ArangoDB password, Redis password, SSH device passwords) from HashiCorp Vault. No plaintext secrets land on disk or in process environment dumps. Vault leases and audit logs cover all credential reads.

**Why this priority**: This is the primary motivator for the feature. Enterprise security teams currently block or restrict MistHelper deployments because of plaintext `.env` files. Vault support unblocks production rollout in HPE/Juniper enterprise environments and satisfies SOC2/ISO27001 controls. Without P1, the feature delivers no enterprise value.

**Independent Test**: Stand up a Vault dev server (or use HCP Vault), populate the four secret paths, set `MIST_CREDENTIAL_BACKEND=vault` plus `VAULT_ADDR` and `VAULT_TOKEN`, launch MistHelper, and confirm it reads each credential from Vault and never falls back to `.env`. Verify in Vault audit log that each secret was fetched exactly once at startup.

**Acceptance Scenarios**:

1. **Given** Vault contains valid Mist/Arango/Redis/SSH secrets at the configured paths and `MIST_CREDENTIAL_BACKEND=vault`, **When** MistHelper starts, **Then** all four credential types load successfully and no `.env` file is required.
2. **Given** `MIST_CREDENTIAL_BACKEND=vault` but `VAULT_TOKEN` is missing or invalid, **When** MistHelper starts, **Then** it fails fast with a clear error naming the backend and the missing/invalid variable — it does NOT silently fall back to `.env`.
3. **Given** Vault is reachable but a specific secret path returns 404, **When** MistHelper tries to load that credential, **Then** it raises an actionable error naming the missing path and the credential type.
4. **Given** Vault is configured and a Mist token retrieved from Vault expires mid-session, **When** the next API call returns 401, **Then** MistHelper surfaces the auth failure with a hint to refresh the Vault-stored token (rotation logic itself is out of scope).

---

### User Story 2 - Local developer uses OS keyring instead of plaintext .env (Priority: P2)

A developer on Windows/macOS/Linux running MistHelper locally stores Mist API tokens, ArangoDB/Redis passwords, and SSH device passwords in their OS keyring (Windows Credential Manager, macOS Keychain, Secret Service / kwallet). They run MistHelper without a `.env` file present. A first-run interactive prompt offers to migrate existing `.env` entries into the keyring and then suggests deleting the `.env` file.

**Why this priority**: Eliminates plaintext credential files on developer laptops — the most common audit finding for individual contributors. Lower priority than Vault because it serves single users, not the production NOC, and developers can already use `.env` safely-ish behind git-ignore. Strong adoption driver for security-conscious individuals.

**Independent Test**: On a clean machine with no `.env` file, store the four credential types in the OS keyring under documented service names, set `MIST_CREDENTIAL_BACKEND=keyring`, launch MistHelper, and confirm all operations work. Separately, with an existing `.env`, run the migration prompt and verify secrets move into the keyring and the `.env` is offered for deletion.

**Acceptance Scenarios**:

1. **Given** the four credentials are stored in the OS keyring and `MIST_CREDENTIAL_BACKEND=keyring`, **When** MistHelper starts, **Then** all credentials load and no `.env` is read.
2. **Given** `MIST_CREDENTIAL_BACKEND=keyring` is set but the `keyring` Python package is not installed, **When** MistHelper starts, **Then** it raises an actionable error explaining how to install keyring support (`pip install mistapi[keyring]` or equivalent).
3. **Given** a populated `.env` exists and `MIST_CREDENTIAL_BACKEND` is unset on first run, **When** MistHelper detects keyring is available, **Then** it prompts the user once to migrate `.env` values into the keyring; on accept, secrets are written to keyring and the user is asked whether to delete the `.env` file.
4. **Given** the keyring is locked (e.g., Linux Secret Service requires unlock), **When** MistHelper tries to read a credential, **Then** it surfaces the OS-level unlock error verbatim plus a hint to unlock the keyring.

---

### User Story 3 - Existing .env deployments continue to work unchanged (Priority: P1)

An existing NOC engineer who already runs MistHelper with `.env` (host install or container with `-v .env:/app/.env:ro`) upgrades to the new MistHelper version. They make no configuration changes. MistHelper behaves identically to before: reads `.env`, loads credentials, runs all 194 menu operations.

**Why this priority**: Backward compatibility is non-negotiable. Breaking the default deployment path would block every existing user from upgrading. This is co-P1 with US1 because the feature is dead-on-arrival if upgrading users hit credential failures.

**Independent Test**: Take a working pre-feature MistHelper deployment with a populated `.env`, swap in the new binary/image with no other changes, and run a representative set of menu operations (read-only org export, site device list, SSH runner). Every operation must succeed exactly as before.

**Acceptance Scenarios**:

1. **Given** an existing `.env` with all four credential types and `MIST_CREDENTIAL_BACKEND` is unset, **When** MistHelper starts, **Then** it loads credentials from `.env` and logs which backend resolved each credential at INFO level.
2. **Given** an existing `.env` and the `keyring` package is not installed, **When** MistHelper starts, **Then** it does NOT prompt for migration and does NOT raise warnings about keyring being unavailable.
3. **Given** a container started with `podman run ... -v ./.env:/app/.env:ro ghcr.io/jmorrison-juniper/misthelper:latest`, **When** the container boots, **Then** behavior is identical to the pre-feature release.

---

### User Story 4 - CLI flag overrides environment-configured backend (Priority: P3)

An operator wants to test Vault temporarily without modifying their `.env`-based deployment. They launch MistHelper with `--credential-backend vault` and it takes precedence over any `MIST_CREDENTIAL_BACKEND` environment variable, the OS keyring, and the `.env` file for the duration of that invocation.

**Why this priority**: Quality-of-life feature for testing and one-off operations. Not required for the security wins of US1/US2, but valuable for migration validation and CI/CD pipelines that want to force a specific backend.

**Independent Test**: With `.env` present and `MIST_CREDENTIAL_BACKEND=env` exported, run `MistHelper.py --credential-backend vault --menu 11` and confirm Vault is used; without the flag, confirm `.env` is used.

**Acceptance Scenarios**:

1. **Given** `MIST_CREDENTIAL_BACKEND=env` is set and `.env` is present, **When** MistHelper is launched with `--credential-backend vault`, **Then** Vault is used for all credential reads and `.env` is ignored.
2. **Given** `--credential-backend` is set to an unknown value, **When** MistHelper starts, **Then** it fails fast with an error listing the valid values (`env`, `keyring`, `vault`).

---

### Edge Cases

- **Vault unreachable at startup**: Backend selection is explicit (`vault`), but the Vault server is down or the network is partitioned. Behavior: fail fast with the connection error and a hint to verify `VAULT_ADDR` and network connectivity. Do not fall back silently.
- **Partial credential coverage in chosen backend**: User sets backend to `vault` but only stores the Mist token there; ArangoDB password is missing. Behavior: fail fast naming the missing credential and backend path; do not look elsewhere unless the user explicitly opts into a fallback chain.
- **Resolution order with no backend set**: When `MIST_CREDENTIAL_BACKEND` and `--credential-backend` are both absent, fall back chain runs: explicit env vars (e.g., `MIST_TOKEN` already exported) → keyring (only if package present and a sentinel entry exists) → `.env`. If none yield credentials, run the existing first-run setup wizard.
- **First-run migration declined**: User says "no" to migrating `.env` into keyring. Behavior: remember the decline for that machine (write a sentinel in user config dir) and never prompt again unless the user explicitly runs a `--migrate-credentials` command.
- **Credential rotation mid-run**: Vault token used to authenticate to Vault expires during a long-running operation. Behavior: out of scope — surface the error and document the limitation.
- **Container with no .env mounted and no backend configured**: Behavior: fail fast at startup with a clear error explaining the three supported backends and how to configure each.
- **Conflicting env vars (`MIST_TOKEN` exported AND `MIST_CREDENTIAL_BACKEND=vault`)**: Backend selection wins — Vault is queried, the exported `MIST_TOKEN` is ignored, and a WARNING is logged noting the override.
- **Logging redaction**: Credentials retrieved from any backend must never appear in logs. The existing log sanitizer must be re-validated against new code paths.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support three credential backends: `env` (current `.env`/`os.environ` behavior, default), `keyring` (OS-native credential store via the `keyring` Python package), and `vault` (HashiCorp Vault KV v2 secrets engine).
- **FR-002**: System MUST select the backend in this priority order: (1) `--credential-backend` CLI flag, (2) `MIST_CREDENTIAL_BACKEND` environment variable, (3) auto-detect: pre-exported env vars → keyring (if package present and sentinel exists) → `.env` file, (4) first-run setup wizard if no credentials are discoverable.
- **FR-003**: System MUST load all four credential types — Mist API token (`MIST_TOKEN`), ArangoDB password (`ARANGO_PASSWORD`), Redis password (`REDIS_PASSWORD`), and SSH device passwords (the existing `SSH_COMMANDS.CSV`-driven set) — from the selected backend.
- **FR-004**: System MUST NOT silently fall back to a different backend when the explicitly selected backend is configured but fails (missing secret, auth error, network error). It MUST fail fast with an actionable error naming the backend, the credential, and the most likely fix.
- **FR-005**: System MUST preserve full backward compatibility for existing `.env`-only deployments. When no backend is explicitly selected and `.env` is present, behavior MUST be identical to the pre-feature release (no new prompts, no new warnings, no behavioral changes).
- **FR-006**: System MUST accept Vault configuration via standard Vault env vars: `VAULT_ADDR` (required for Vault backend), `VAULT_TOKEN` (required unless an alternate auth method is configured), `VAULT_NAMESPACE` (optional, for Vault Enterprise), and a MistHelper-specific `VAULT_PATH` (default `secret/data/misthelper`) identifying the KV v2 secret path containing the four credential keys.
- **FR-007**: System MUST document the expected key names within the Vault secret payload (`mist_token`, `arango_password`, `redis_password`, plus SSH password key naming convention) and within the OS keyring (service name `misthelper`, account names matching the env-var names).
- **FR-008**: System MUST offer an interactive first-run migration prompt when (a) `.env` exists with credentials AND (b) keyring is available AND (c) no `MIST_CREDENTIAL_BACKEND` is set AND (d) the user has not previously declined migration. The prompt MUST be skippable (default = No) and the decision MUST be remembered.
- **FR-009**: System MUST provide a `--migrate-credentials <target-backend>` CLI subcommand (or equivalent menu operation) for explicit on-demand migration between any two backends.
- **FR-010**: System MUST log at INFO level which backend resolved each credential type at startup (e.g., `Loaded MIST_TOKEN from vault`). It MUST NOT log credential values, even partially.
- **FR-011**: System MUST treat the `keyring` and `hvac` Python packages as optional dependencies. Missing packages MUST raise actionable errors only when their respective backends are explicitly requested.
- **FR-012**: System MUST work inside the container distribution. The container image MUST include `keyring` and `hvac` so any backend works out of the box; container documentation MUST cover how to inject `VAULT_TOKEN` securely (e.g., file mount, runtime secret).
- **FR-013**: System MUST validate that Vault `VAULT_ADDR` uses `https://` in non-development environments. A `http://` Vault address MUST trigger a WARNING unless an explicit `VAULT_ALLOW_HTTP=true` is set.
- **FR-014**: System MUST extend the existing log sanitizer to redact credentials sourced from Vault and keyring, not just `.env`. Adding a new backend MUST NOT regress sanitization.
- **FR-015**: System MUST expose the active backend in the existing diagnostic/health output (e.g., menu item that already prints config) so operators can confirm at a glance which backend is in use.

### Key Entities

- **Credential Backend**: An abstraction over a secret source. Has a name (`env`/`keyring`/`vault`), an `is_available()` capability check, a `get(credential_name)` accessor that raises an actionable exception on failure, and an optional `put(credential_name, value)` for migration support.
- **Credential**: One of four logical secrets — Mist API token, ArangoDB password, Redis password, SSH device password set. Each has a canonical name used as the env-var name, keyring account name, and Vault payload key.
- **Migration Decision Sentinel**: A small per-user state file (location: user config dir, e.g., `%APPDATA%\MistHelper\migration.json` on Windows) recording whether the first-run migration prompt has been answered, so it is shown at most once per machine.
- **Vault Secret Payload**: A KV v2 secret at a single configurable path containing all four credentials as keys in one JSON object.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An enterprise NOC operator can deploy MistHelper with zero plaintext credentials on disk by configuring Vault — verified by `find / -name .env` returning no MistHelper-related results post-deploy and all 194 menu operations functioning.
- **SC-002**: A developer can move their local credentials from `.env` to the OS keyring in under 5 minutes by accepting the first-run migration prompt — measured end-to-end from launching MistHelper to deleting the `.env` file.
- **SC-003**: Existing `.env`-based deployments upgrade to the new release with zero configuration changes and zero behavioral differences — verified by running the full menu-coverage smoke test suite (operations 1-89, excluding 14/18/63-65/90+) against a pre-feature `.env` deployment and confirming identical outputs.
- **SC-004**: 100% of credential reads from any backend are redacted in script logs, validated by an automated log-scanning test that fails the build if any stored credential value appears in `data/script.log`.
- **SC-005**: Test coverage for the new credential subsystem is ≥70% (statement coverage) measured by `pytest-cov`, with at least one happy-path and one failure-path test per backend.
- **SC-006**: An operator can switch between backends with a single CLI flag for the duration of one MistHelper invocation, verified by `--credential-backend vault` overriding both `MIST_CREDENTIAL_BACKEND=env` and a present `.env` file.
- **SC-007**: Failure modes (missing credential, unreachable Vault, locked keyring, missing optional package) produce error messages that name the backend, the credential, and the recommended fix in a single line, validated by snapshot tests against the error output.

## Assumptions

- **Vault deployment is the operator's responsibility**: MistHelper consumes Vault; it does not provision, seal/unseal, or configure Vault policies. Operators are expected to create the secret path and an appropriate access policy/token.
- **KV v2 only for v1**: Only the Vault KV v2 secrets engine is supported initially. KV v1, AWS Secrets Engine, dynamic database creds, and other engines are out of scope.
- **`VAULT_TOKEN` auth for v1**: Only Vault token auth is supported initially. AppRole, Kubernetes auth, JWT/OIDC, and AWS IAM auth are out of scope for this spec (can be added in follow-up specs without breaking the contract).
- **Single Vault path for all four credentials**: All four credential types live as keys in one KV v2 secret. Splitting across multiple paths is out of scope for v1.
- **Keyring scope per OS user**: OS keyring entries are scoped to the OS user account running MistHelper. Multi-user shared-machine setups are not in scope.
- **Upstream mistapi >=0.59 keyring helper available**: Where upstream `mistapi` already exposes a keyring helper for the Mist token, MistHelper SHOULD reuse it rather than reimplementing. For the other three credential types (ArangoDB/Redis/SSH), MistHelper implements its own keyring wrapper using the same `keyring` library.
- **No secrets rotation UI**: This spec covers reading credentials. Rotating or refreshing credentials (Vault leases, token TTLs, automatic re-auth) is explicitly out of scope.
- **SSH device password set**: "SSH device passwords" refers to the existing credential set MistHelper already manages via `SSH_COMMANDS.CSV` and related config — this spec changes the storage backend, not the per-device password model.
- **First-run migration is interactive only**: Migration runs only when MistHelper is launched interactively (stdin is a TTY). Container/systemd non-interactive runs never prompt.
- **No removal of `.env` support**: The `.env` backend remains a first-class option and the default for unconfigured deployments. This spec adds backends; it does not remove or deprecate any.
- **Reference doc context**: The upstream-change rationale documented in `docs/UPSTREAM_mistapi_changes.md` is the source of truth for what mistapi 0.59 already provides.
