# Credential default resolution security specification

**Feature Branch**: `2861-credential-defaults`  
**Feature Path**: `specs/numbered/0/0/0/4/2/4/2/1/2861-credential-defaults/`  
**Issue**: #2861  
**Status**: Draft

## Summary

Credential defaults and provider fallbacks can select an unintended identity.
They can also hide a missing credential and make an operation appear successful.

The current-tree review measured **64 candidates in 40 files**. It identified
**10 wrong-identity sites**. The other **54 candidates** either fail closed,
degrade a message, or preserve an intentional optional value.

The route uses eight base-5 digits. The route for issue 2861 is
`0/0/0/4/2/4/2/1`, because 2861 converts to base 5 as `00042421`.

## Threat model

An attacker or an operator mistake can place a valid Mist token, database
credential, or process variable in a wider scope than the active operation.
The code can then use that value after the intended session or scope has no
credential.

The result is an action under the wrong identity. The action can read or change
Mist data, connect to the wrong database account, or use the wrong cache account.
The operator may not see an error because the fallback returns a valid value.

The review parsed 2,295 tracked Python files. It found zero parse failures.
The review found 64 candidates in 40 files. It found 10 wrong-identity sites.
The review excluded the four prohibited source files from direct inspection.

## Wrong-identity sites

Each site below must reject a missing identity instead of selecting a wider
identity. The listed identity is the unintended identity that the current
fallback can select.

| Site | Unintended identity | Consequence |
| --- | --- | --- |
| `MistHelper.py:2901` | The account represented by the legacy token environment variable | A Mist request can run as the legacy variable account instead of the active variable account. |
| `mist-ops-platform/src/shared/mist/session.py:87` | The global configured Mist account | An organization-scoped session can read or change data with a token that belongs to another organization or account. |
| `src/foundation/persistence/db/__init__.py:58` | The database user in the direct-construction default | A direct database client can connect as a local or shared default user instead of the operator-selected user. |
| `src/foundation/persistence/db/__init__.py:59` | The database password paired with the direct-construction default | A client can authenticate to the wrong database account when the caller omitted the password. |
| `src/foundation/persistence/db/__init__.py:62` | The Redis account represented by the default password | A writer can authenticate to the wrong Redis instance or account and read or change unrelated cache data. |
| `src/interfaces/portals/upgrade_portal/app/config.py:276` | The default Arango username | The upgrade portal can access a database as a default user instead of the configured service identity. |
| `src/mist/networking/network/_routing_utils_payload.py:262` | The process-wide Mist token | A request built for one session can run as the account in the process environment. |
| `src/mist/realtime/websocket/manager.py:79` | The process-wide Mist token | A WebSocket subscription can receive data under the process account instead of the session account. |
| `src/mist/realtime/websocket/manager.py:166` | The process-wide Mist token | A later WebSocket action can use the process account after the session token is absent. |
| `src/mist/resources/device/arp_command_manager.py:62` | The process-wide Mist token | An ARP request can read device data under the process account instead of the selected session account. |

The database username and password are separate sites because each field can
complete a different authentication tuple. The Redis password is separate
because it selects the authentication identity for a different service.

## Severity split

### Security priority: wrong identity

The 10 sites above have the highest priority. They can produce a valid request
under an unintended identity. The repair must remove the fallback or require an
explicit, validated identity boundary.

### Review priority: other 54 candidates

The other 54 candidates are not one defect class.

* Some return an empty value and reject the operation.
* Some make an optional analyzer or webhook backend unavailable.
* Some provide a display label, refusal message, test fixture, or lock value.
* Some preserve an explicit optional setting, such as an absent SMTP account.
* Some use a disabled feature flag or a local-only generated key.

The implementation must review all 54 candidates. It must change only a
candidate that can select an identity or violates the rule below. It must
preserve intentional optional and test defaults.

The output fallback at
`src/mist/resources/device/_utility_commands_action.py:371` requires a separate
output-safety review. It must not expose a complete response as a password.

## Security rule

**If a required credential is absent, blank, or not a string, return a typed
refusal before SDK, database, cache, or remote-service construction.**

The refusal must identify the required credential class without printing its
value. It must not prompt in unattended execution. It must not select a
process-wide, global, legacy, local, or placeholder value.

The rule applies at the identity boundary:

1. A session token belongs to the session that makes the request.
2. An organization token belongs to the organization-scoped session.
3. A database credential belongs to the database configuration object.
4. A cache credential belongs to the cache configuration object.
5. A portal service credential belongs to the portal service configuration.

The caller must pass a validated credential object or receive the typed refusal.
The implementation must remove the old fallback path. It must not add an alias,
adapter, compatibility shim, prompt, or second fallback.

The token environment variables need one documented rule. Until the owner
selects the final rule, the specification recommends this behavior:

* Use one canonical environment variable.
* If only the legacy variable exists, return a typed refusal.
* If both variables exist with different values, return a typed refusal.
* If both variables exist with the same value, accept the value only during the
  migration batch that removes the legacy variable.

## Scope

### In scope

* Credential, token, password, secret, username, and authentication defaults.
* Credential provider precedence and identity boundaries.
* Direct construction of credential-bearing configuration objects.
* Structural prevention of new empty credential defaults.
* Tests for refusal, precedence, scope, and intentional optional defaults.
* Documentation of the 64-candidate review and the 10-site priority repair.

### Out of scope

* Mist resource identifiers owned by #2863.
* Generic non-credential defaults owned by #2753.
* Production source changes in this specification pull request.
* The separate output-safety repair for the device password display fallback.
* Credential rotation, secret storage migration, and access policy changes.

## User scenarios and tests

### Scenario 1: Reject a missing session token

As an operator, I want a Mist request to stop when its session token is absent.

**Independent test**: Build a session without a token and assert the typed
refusal before the SDK receives a request.

### Scenario 2: Reject a wider-scope token

As an operator, I want an organization session to reject a global token.

**Independent test**: Miss the organization providers while setting a process
token and assert that the session refuses the request.

### Scenario 3: Reject direct database defaults

As an operator, I want direct database configuration to require explicit
credentials.

**Independent test**: Construct the database configuration without credentials
and assert a refusal before Arango or Redis construction.

### Scenario 4: Preserve intentional optional values

As a maintainer, I want optional SMTP, test, fixture, and disabled-feature
values to keep their documented behavior.

**Independent test**: Run focused tests for each preserved candidate group and
assert the optional path or fail-closed result.

### Scenario 5: Prevent new credential defaults

As a maintainer, I want a guard to stop new empty credential defaults.

**Independent test**: Run the guard on the repository and on a negative fixture.
The negative fixture must produce one environment default and one dataclass
credential default, then fail the guard.

## Functional requirements

* **FR-001**: The implementation MUST reject a required missing, blank, or
  non-string credential before the dependent client is constructed.
* **FR-002**: The implementation MUST keep each credential inside its
  session, organization, database, cache, or portal identity boundary.
* **FR-003**: The implementation MUST remove process-wide and global fallbacks
  from the 10 wrong-identity sites.
* **FR-004**: The implementation MUST define one token environment precedence
  rule and test both variables set to different values.
* **FR-005**: The implementation MUST preserve intentional optional defaults
  only when they cannot select an identity.
* **FR-006**: The implementation MUST not print a credential or a credential
  value in a refusal, log, test report, or generated document.
* **FR-007**: The guard MUST parse Python with `ast`.
* **FR-008**: The guard MUST print the number of files scanned and findings.
* **FR-009**: The guard MUST fail when the scanned file count is zero.
* **FR-010**: The guard MUST report parse failures instead of treating them as
  a successful scan.
* **FR-011**: The guard MUST use a ratchet baseline while the 64 candidates
  are repaired in batches.
* **FR-012**: The guard tests MUST prove that the negative fixture fails.
* **FR-013**: Each implementation batch MUST include focused unit tests.
* **FR-014**: The specification pull request MUST change no source or portal
  file.

## Guard design

Add a guard under `tests/guardrails/` in the first implementation batch.
Follow the structure of `test_blind_exception_handler_ratchet.py`.

The guard must:

1. List tracked Python files with Git.
2. Parse each selected file with `ast`.
3. Record read and parse failures.
4. Detect empty credential defaults, credential-bearing dataclass defaults,
   environment defaults, value-selection fallbacks, and reviewed provider-chain
   fallbacks.
5. Print a stable ASCII line with files scanned, parse failures, and findings.
6. Fail when no files are scanned.
7. Compare findings with a checked-in baseline.
8. Fail when a new finding appears outside the baseline.
9. Test a zero-input report.
10. Test a negative fixture with one environment default and one dataclass
    credential default.

Recommended proof line:

```text
credential-default-scan files=2295 parse_failures=0 candidates=64
```

The guard must calculate the values. It must not hard-code the line.

## Acceptance criteria

* The current-tree review records 64 candidates in 40 files and 10
  wrong-identity sites.
* The 10 wrong-identity sites have named identities and named consequences.
* A required missing credential produces a typed refusal before client creation.
* A session never uses a process-wide token as a silent replacement.
* Direct database construction cannot use placeholder credentials.
* Token precedence is explicit, tested, and rejects conflicting values.
* Intentional optional defaults remain unchanged or have a documented,
  operator-visible validation path.
* The guard reports files, parse failures, and findings.
* The guard fails on zero input and on the deliberate negative fixture.
* Each batch has focused tests and does not edit a shared hot file held by
  another open pull request.
* No credential, token, password, or real secret appears in a document.
* The smallest test boundary passes for each completed batch.

## Smallest test boundary

The implementation worker must run the smallest applicable tests after each
batch. The combined boundary is:

```text
python -m pytest tests/unit/test_credential_preflight.py tests/unit/refactors/test_initialize_mist_session.py tests/unit/websocket/test_manager.py tests/unit/websocket/test_commands.py tests/unit/device/test_arp_command_manager.py tests/unit/db_discovery/test_config.py tests/unit/test_standalone.py
python -m pytest mist-ops-platform/tests/unit/mist/token_resolution
python -m pytest tests/guardrails/test_credential_default_ratchet.py
python -m py_compile MistHelper.py src/foundation/persistence/db/__init__.py src/mist/networking/network/_routing_utils_payload.py src/mist/realtime/websocket/manager.py src/mist/resources/device/arp_command_manager.py mist-ops-platform/src/shared/mist/session.py
```

Do not run the full test suite for this issue campaign.

## Owner decisions

1. **What must happen when a required credential is absent?**
   * Raise a typed exception.
   * Return a typed refusal result.
   * Prompt the operator.
   * **Recommendation**: Return a typed refusal result at the boundary.
     Do not prompt because unattended runs must stop safely.

2. **What token variable rule should replace the legacy precedence?**
   * Use the newer variable and ignore the legacy variable.
   * Use the legacy variable until a migration date.
   * Reject conflicting values and accept equal values during migration.
   * **Recommendation**: Reject conflicts, accept equal values only during the
     migration batch, then remove the legacy path.

3. **Should standalone database mode remain available?**
   * Remove standalone mode.
   * Require a validated credential object for standalone mode.
   * Keep direct construction with documented placeholder values.
   * **Recommendation**: Require a validated credential object. Do not keep
     placeholder values.

4. **Should the guard baseline cover all 64 candidates at once?**
   * Baseline only the 10 wrong-identity sites.
   * Baseline all 64 candidates and reduce the baseline per batch.
   * Do not use a baseline and repair all candidates in one pull request.
   * **Recommendation**: Baseline all 64 candidates and reduce it per batch.

5. **Should this specification close issue #2861?**
   * Close the issue because the threat is documented.
   * Keep the issue open for the implementation batches.
   * **Recommendation**: Keep it open and use `Refs #2861`.
