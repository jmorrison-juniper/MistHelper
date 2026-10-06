# Feature Specification: Upgrade Portal Session Persistence

**Feature Branch**: `3714-session-persistence`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issue #3714 and assessment comment
[#3714 assessment](https://github.com/jmorrison-juniper/MistHelper/issues/3714#issuecomment-6026814949)

## Problem statement

The upgrade portal stores each authenticated `OperatorSession` in a process-local
dictionary. A Gunicorn worker restart clears that dictionary. The signed browser
cookie remains, but the next protected request returns `401 not_authenticated`.

This is an authentication availability defect. It does not bypass authentication.
It can still interrupt an operator who controls production hardware.

### Operator threat

An attacker who obtains a stale signed cookie cannot enter the portal unless the
server still holds a valid matching session record. The primary threat is an
unlucky operator whose worker restarts during an organization upgrade.

The operator can lose the session that identifies the operator and selected
organization. The portal can then reject pages, forms, status checks, cancel
requests, retry requests, reschedule requests, and stop requests. A running
upgrade can continue without the operator being able to view or control it.

The affected organization is the organization selected in the session. The
affected production resources are the selected sites and their upgrade jobs.
The repaired portal must restore the authenticated session after a worker
replacement without granting access to another operator or organization.

### Evidence and reading method

The previous worker measured revision
`d82f715436f295711ed5ac01ab9242118c03fee0`. It read each committed route blob
with `git show <revision>:<path>`. It found 51
`@identity.require_session` handlers across 13 route files.

The restricted route was read only as the committed blob with:

```text
git show origin/main:src/interfaces/portals/upgrade_portal/app/routes/upgrade.py
```

The working-copy file was not opened. The issue body uses the old
`src/upgrade_portal/` path. The current path is
`src/interfaces/portals/upgrade_portal/`.

## Protected handler groups

The following groups rank the handlers by blast radius. The counts total 51.
The line numbers are decorator lines from the measured assessment revision.

### Group 1: Upgrade execution and control

**Blast radius: Critical.** These handlers can start, monitor, cancel, retry,
reschedule, or stop work that changes production device firmware.

| File | Handlers |
|---|---|
| `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` | `options_page` 1133, `save_options` 1205, `confirm_page` 1299, `submit_upgrade` 2100, `job_page` 2328, `upgrade_status` 2476, `cancel_upgrade` 2553 |
| `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py` | `create_run` 1064, `save_options` 1183, `run_versions` 1647, `start_run` 1758, `run_status` 1812, `run_page` 1950, `options_page` 2007, `confirm_page` 2055, `start_upgrade_via_service` 2177, `upgrade_status_via_service` 2260, `cancel_upgrade_via_service` 2303, `retry_run` 2626, `reschedule_run` 2680, `cancel_run` 2732, `stop_run` 2769 |

**Repair first.** A session loss here can remove operator control of a firmware
upgrade. The repair must restore the session before protected status or control
requests execute.

### Group 2: Organization selection, pre-check, and site locks

**Blast radius: High.** These handlers select the organization and sites that
later upgrade actions can affect. They also coordinate exclusive site access.

| File | Handlers |
|---|---|
| `src/interfaces/portals/upgrade_portal/app/routes/select.py` | `org_page` 1814, `choose_org` 1847, `mode_page` 1881, `choose_mode` 1894, `sites_page` 1920, `choose_sites` 1964, `site_inventory_page` 2050, `list_sites` 2090, `site_inventory` 2140, `take_site_lock` 2673, `beat_site_lock` 2706, `free_site_lock` 2735 |
| `src/interfaces/portals/upgrade_portal/app/routes/org_precheck.py` | `start_org_precheck` 101 |
| `src/interfaces/portals/upgrade_portal/app/routes/org_controls.py` | `open_retry` 153, `clear_retry` 195, `reconcile_operation` 215, `reschedule_operation` 301 |

**Repair second.** The session record must bind the operator to the selected
organization and preserve the site-lock owner identity. A lost heartbeat must
not allow a different session to inherit a lock.

### Group 3: Capture and pre-upgrade evidence

**Blast radius: High.** These handlers collect or expose pre-upgrade evidence
that operators use to decide whether to proceed.

| File | Handlers |
|---|---|
| `src/interfaces/portals/upgrade_portal/app/routes/capture.py` | `capture_pre_upgrade_for_run` 1133, `start_capture` 1241, `capture_status` 1270, `read_capture` 1296, `download_capture` 1339, `capture_page` 1369 |

**Repair third.** The portal must restore the session before it starts a
capture or exposes organization and site evidence.

### Group 4: Comparison and history

**Blast radius: Medium.** These handlers read captures and run history. They
can expose organization data but do not directly start a firmware change.

| File | Handlers |
|---|---|
| `src/interfaces/portals/upgrade_portal/app/routes/review.py` | `compare_captures` 1970, `download_comparison` 1993, `compare_page` 2020, `capture_history` 2044, `run_history` 2064, `history_page` 2114 |

**Repair fourth.** The same ownership and organization checks must protect
historical data and comparison output.

## User stories and acceptance scenarios

### User Story 1: Recover after worker replacement

As an operator, I need a protected request to restore my session after a
Gunicorn worker replacement.

**Acceptance scenarios**

1. Given a valid session and a shared session record, when a replacement
   application receives the signed cookie, then the protected request succeeds.
2. Given a missing, expired, revoked, or undecryptable record, when the cookie
   is presented, then the request returns `401 not_authenticated`.
3. Given a record for another operator, browser, or organization, when the
   cookie is presented, then the request returns `401 not_authenticated`.
4. Given a valid record, when the session expires, then the portal rejects it
   and removes the recoverable record.

### User Story 2: Keep upgrade control safe

As an operator, I need the restored session to keep the original organization,
site selection, and upgrade ownership.

**Acceptance scenarios**

1. Given an active upgrade, when a worker changes, then the operator can view
   status and use the approved control actions.
2. Given a browser with a valid session, when the organization changes, then
   the previous organization binding cannot authorize the new organization.
3. Given a site lock owned by a prior session, when that session expires, then
   the lock does not become owned by a different session without the normal
   lock process.

### User Story 3: Protect recovery data

As an administrator, I need recovery data to resist credential disclosure and
replay.

**Acceptance scenarios**

1. Given a shared store record, when an administrator reads the store, then it
   does not expose plaintext provider credentials or session tokens.
2. Given a log, cookie, response, trace, or error, when it contains session
   data, then it contains no credential or token value.
3. Given a shared-store or key-service failure, when the portal cannot validate
   a session, then it fails closed and reports a safe operator message.

## Defect-asserting test

The issue assessment quotes
`tests/unit/upgrade_portal/test_identity.py:1505-1520` as follows:

```python
def test_current_session_returns_none_after_a_worker_restart(
    flask_app: flask.Flask,
) -> None:
    """Prove that a stale key answers None instead of a server error.

    Why:
        A worker restart empties the registry while the browser still holds a
        valid signed session. The guard must refuse that request calmly.

    Args:
        flask_app: The bare test application.
    """
    stale_key = f"{email_digest(NORMALIZED_EMAIL)}:{FIRST_BROWSER_ID}"
    with flask_app.test_request_context("/", headers=cookie_header(FIRST_BROWSER_ID)):
        flask.session[SESSION_OWNER_KEY] = stale_key  # The store holds no such record
        assert current_session() is None
```

Today, the test asserts that an empty process-local registry returns `None`.
That assertion proves the defect and allows the test to stay green after a
worker restart loses operator control.

After repair, the test must create an approved shared record, clear the
process-local registry, and assert that `current_session()` returns the
original session. The test must also assert `None` for a missing, expired,
revoked, or undecryptable record. A repair that leaves the quoted assertion
unchanged, or that leaves it green without a shared-record recovery assertion,
has not repaired this issue.

## Migration and live-session behavior

**Recommendation: do not force logout of every live operator.** A mass logout
during an upgrade is an operational incident and is not an acceptable security
repair.

Use a staged deployment. The new identity code must write an approved shared
record for every valid local session before the old worker drains. The shared
record must use the existing session owner, browser identifier, organization
scope, expiry, and revocation state. A valid session that reaches the new code
before drain remains usable after worker replacement.

The shared store becomes authoritative after the migration window. A live
session that never reaches the new code before its worker exits cannot be
recovered safely because its record never left process memory. That session
must request a new sign-in. The deployment procedure must drain workers in a
way that gives each active operator a chance to make a protected request before
the worker exits. The procedure must not claim zero logout risk.

The repair must preserve control of a running upgrade when the operator's
session is migrated before worker drain. If a worker exits before migration,
the portal must fail closed rather than restore an unverified session.

## Functional requirements

- **FR-001**: Store approved session recovery data in a shared store available
  to every capture portal worker.
- **FR-002**: Encrypt recovery data before it enters the shared store.
- **FR-003**: Keep the browser cookie limited to a non-secret owner reference.
- **FR-004**: Bind a recovered record to the operator, browser, organization,
  expiry, and revocation state.
- **FR-005**: Restore a valid session after a worker replacement.
- **FR-006**: Reject missing, expired, revoked, mismatched, or undecryptable
  records with `401 not_authenticated`.
- **FR-007**: Delete shared records during sign-out and after expiry.
- **FR-008**: Use the shared store as the authority. Treat a local cache only
  as a short-lived performance optimization.
- **FR-009**: Fail closed when the shared store or encryption key is unavailable.
- **FR-010**: Do not log, return, trace, or place in a cookie any credential,
  provider token, encryption key, or session token.
- **FR-011**: Preserve the current site-lock ownership rules during recovery.
- **FR-012**: Update the defect-asserting test so it proves recovery and failure
  cases instead of proving session loss.
- **FR-013**: Cover all 51 handlers through the approved identity boundary.
- **FR-014**: Do not change the restricted route in this specification branch.
  Its implementation batch must use the committed route blob as its baseline.

## Owner decisions

| Decision | Recommendation | Reason |
|---|---|---|
| Shared store | Use the existing Redis service with a dedicated key prefix and ACL. | Redis already supports portal coordination and avoids a new service. |
| Stored value | Store only the minimum encrypted recovery record. Do not store plaintext credentials. | A smaller record reduces disclosure and replay impact. |
| Encryption | Use authenticated encryption with a deployment-provided key. | Integrity is required before a record can restore access. |
| Key source | Read the key from an environment or secret file. Never commit it or log it. | The repository forbids credentials in source and documentation. |
| Key rotation | Support one active key and one previous key during a bounded rotation window. Re-encrypt on successful recovery, then remove the previous key. | Rotation must not log out every operator or keep an old key forever. |
| Session lifetime | Use an eight-hour absolute lifetime and a 30-minute idle lifetime, capped by the provider session expiry. | The portal serves production operations and must limit replay time. |
| Renewal | Renew only after successful validation and only within the absolute lifetime. | Renewal keeps active work usable without creating an unlimited session. |
| Browser binding | Bind the record to the signed owner reference and browser identifier. Do not bind to IP address. | IP binding breaks operators behind NAT or changing networks. |
| Organization binding | Store the selected organization and reject cross-organization reuse. | A session must not authorize another organization after recovery. |
| Store failure | Fail closed for session creation and recovery. Do not use an unverified local fallback. | A fallback would recreate the authentication defect or permit unsafe access. |
| Existing live sessions | Preserve them during staged migration. Do not force logout. | Logging out an operator during an upgrade can create an outage. |
| Unsupported provider state | Reject recovery when the provider session cannot be restored or validated. | A successful portal cookie must not replace provider authentication. |
| Gunicorn workers | Permit worker replacement after shared persistence is verified. | One worker only hides the defect and does not provide persistence. |
| Protected route changes | Keep route authorization behind the common identity boundary. | The 51 handlers must receive one consistent ownership check. |
| Batch ownership | Create one issue, branch, and pull request for each batch below. | Shared hot files and 51 handlers cannot be safely repaired in one change. |

## Out of scope

- Changes to `src/`, `web_portal/`, or `tests/` in this specification branch.
- A new identity provider or sign-in mode.
- A change to firmware upgrade semantics.
- A bypass for stale cookies.
- A plaintext session database.
- A forced logout of all operators.
- A change to the existing site-lock algorithm.
- A pull request that changes a source file.

## Success criteria

- **SC-001**: A replacement application restores a valid session from the
  shared store with no process-local record.
- **SC-002**: The replacement application rejects missing, expired, revoked,
  mismatched, and undecryptable records.
- **SC-003**: The repaired tests no longer assert that a worker restart must
  return `None` for a valid shared record.
- **SC-004**: All 51 protected handlers use the same recovered identity and
  organization ownership checks.
- **SC-005**: A staged migration preserves active sessions that reach the new
  code before worker drain and does not force a mass logout.
- **SC-006**: Test evidence proves that logs, cookies, responses, traces, and
  shared storage do not expose credentials or session tokens.
- **SC-007**: Each implementation batch has one exact file set and one owner.

## Assumptions

- Redis is already available to the capture portal and can receive a dedicated
  ACL and key prefix.
- The provider session can be represented by approved encrypted recovery data,
  or the provider can issue a safe replacement session after validation.
- The current identity and lock contracts remain the implementation baseline.
- The 51-handler measurement from the assessment comment is authoritative for
  this specification.
- The route moved to
  `src/interfaces/portals/upgrade_portal/` before this specification.
