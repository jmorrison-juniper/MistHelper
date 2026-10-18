# Research: Guest Authorization Migration

**Issue**: [#4231](https://github.com/jmorrison-juniper/MistHelper/issues/4231) | **Reviewed**: 2026-10-18

## Provenance and Prior Work

**Decision**: Refresh the existing `4231-mist-guest-authorizations` identity. Do not allocate another feature number.
**Rationale**: Issue #4278 already names this managed path, and Git checkpoint `20cf234e2` preserves the prior nine-file record.
**Alternatives**: A new record would duplicate the migration and obscure its prior gates.

Current `main` at `1e9b280dd` contains no tracked #4231 planning artifacts.
The checkpoint has a complete specification, plan, tasks, research, model, quickstart, two contracts, and a checklist.
This refresh preserves their subject and checklist location while grouping supporting artifacts below `design/`.

[PR #4279](https://github.com/jmorrison-juniper/MistHelper/pull/4279) is merged.
It added `GuestAuthorizationReadModel` and 22 offline projection cases.
Its Flask serialization case does not prove portal identity, access control, live reads, or write safety.
The class emits only `masked_mac`, `authorized`, and `expires_at`.
Missing authorization and expiry remain unknown.

The PR records a user statement of source authorship and permission.
It does not record an approved compatible distribution path for protected expression.
The PR also states that it copied or adapted no source material.
Do not reinterpret that statement as approval for this migration's reuse.
Issues #4231 and #4278 remain open.

## Source Evidence

The inspected source default branch remains at commit `0213240cb9edfa237f763acd156b90a6049363cb`.
GitHub metadata reports `NOASSERTION`, but the [LICENSE](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/LICENSE) declares CC BY-NC-SA 4.0.
It names Joseph Morrison as the copyright holder.
The actual license text controls this planning boundary, not the metadata classification.

**Decision**: Use independently recorded functional requirements. Do not copy or adapt source code, templates, tests, screenshots, or assets without compatible rights.
**Rationale**: Attribution alone does not resolve noncommercial and share-alike compatibility.
**Alternatives**: Direct source or visual reuse remains blocked by G1.

The [README](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/README.md)
and [guide](https://github.com/jmorrison-juniper/MistGuestAuthorizations/blob/0213240cb9edfa237f763acd156b90a6049363cb/docs/guide.md) describe:

- A dashboard with site and guest WLAN selection, filtering, and status counts.
- Add, supported edit, extension, and revocation journeys.
- Connected-client search by MAC address, hostname, or IP address.
- CSV bulk import and per-device access changes.
- A standalone Flask service on port 5000, token configuration, and a logs mount.

The screenshots use fictional offline data. They do not prove cloud behavior or grant asset reuse rights.
The source dependency file pins Mist SDK `0.64.0`, Flask `3.1.3`, and python-dotenv `1.2.4`.
Its Compose file defines one separate `mistguestauth` application, not a required guest database.
Do not migrate its service, port, credentials, secret-key setting, or logs mount.
The source permission guide requests organization/site read and WLAN/guest read-write permissions.
Those claims do not establish MistHelper's least-privilege operator policy.

## Contract and Architecture Decisions

**Decision**: Use the existing application, authenticated session, database services, and Compose group.
**Rationale**: A second deployment conflicts with the requested migration.
**Alternatives**: A standalone application, new guest database, and shadow authorization cache are rejected.

MistHelper's Redis service supports existing webhook ingestion and backend checks.
No reviewed requirement needs guest authorization caching.
Do not treat Redis availability as authorization or audit durability evidence.
Audit storage, retention, and attribution require G4 approval.

**Decision**: Keep site and organization operations distinct.
**Rationale**: An organization operation can affect more than the selected site.
**Alternatives**: Automatic scope fallback after failure is prohibited.

**Decision**: Verify pinned requests and responses before routes exist.
**Rationale**: SDK signatures accept a generic body and cannot establish writable fields or cloud semantics.
**Alternatives**: Direct HTTP fallback and trusting source behavior are prohibited.

Local inspection found `mistapi==0.64.1`, not the source's `0.64.0`.
The checked-in schema defines `guest.minutes` and `guest_org.minutes` from 0 through 259200.
The descriptions name a 180-day maximum. This does not establish a grant minimum or revoke semantics.
The site `guest.name` field is read-only. The organization schema differs and must be verified separately.
The source guide claims durations up to five years and revocation through an update with `minutes=0`.
It also claims DELETE can return success without ending access. These remain source claims, not verified cloud guarantees.
The previous specification's one-hour grant minimum is not an approved product policy.

**Decision**: Imports are bounded, reviewed, sequential individual writes, not atomic transactions.
**Rationale**: An uncertain write cannot safely be repeated.
**Alternatives**: Unbounded parsing, automatic retry, and batch rollback claims are rejected.

## Unresolved Approval and Evidence Gates

All five gates block every guest-data route and grant, edit, extend, revoke, search, or import workflow.
Approval requires a dated maintainer decision linked here. Verification requires reproducible evidence, not a checked box alone.

| Gate | Required decision or evidence | Responsible role | Current state |
| --- | --- | --- | --- |
| G1 Rights | Approve independently authored integration or a compatible reuse path, including distribution obligations | Maintainer and rights holder | Unresolved |
| G2 Access | Approve shared-token/no-login access or an operator identity design, permitted scopes/actions, and cross-scope denial tests | Maintainer responsible for access | Unresolved |
| G3 Bounds | Approve maximum CSV bytes, rows, encoding, header/cell limits, and bounded request budget | Maintainer responsible for operations | Unresolved |
| G4 Audit | Approve operator attribution, existing durable sink, retention, pre-write failure, post-write failure, and recovery behavior | Maintainer responsible for audit | Unresolved |
| G5 Contracts | Pin SDK/API revisions and verify requests, responses, writable fields, grant/extension durations, revocation, and scope mapping | Implementer and reviewing maintainer | Signatures inspected only |

G2 must cover reads as well as writes. Existing IP restrictions and CSRF controls do not establish accountable operator permissions.
G4 must distinguish a confirmed cloud change from an audit failure.
The minimum safety constraint is a visible incomplete outcome, no success claim, and no automatic write retry.
The recovery procedure and durable audit mechanism remain unapproved.
G5 must explain API documentation conflicts without sending production-changing requests during routine tests.

## Safe Work Boundary

This refresh permits documentation, offline signature inspection, and validation of the existing independently authored projection.
It does not authorize new product work.
A later issue may propose an offline pure transformation with fictional inputs and no route, session, persistence, or write behavior.
Such a proposal needs independent requirements and must not duplicate the already merged projection.
No additional offline implementation is needed to complete issue #4231's planning request.
