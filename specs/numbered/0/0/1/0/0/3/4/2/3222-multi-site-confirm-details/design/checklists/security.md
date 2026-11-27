# Security Checklist: Multi-Site Confirm Page Plan Detail

**Purpose**: Check the safety and security controls of the confirm page and of the submit refusal.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Write Control

- [x] The typed word `CONFIRM` stays required. The submit route checks it before any write (research R-23).
- [x] The submit route refuses an incomplete plan before any record change, site lock, pre-check read, or cloud call (FR-009, contract C3).
- [x] The browser control stays disabled for an incomplete plan (FR-008, contract C2). The server check does not depend on the browser control (decision D-2).
- [x] The write gate and the pre-check gate keep their current order and their current messages (FR-010).

## Output Encoding

- [x] Site names, device names, and models reach the page through autoescape (research R-62). The template marks no value as safe (FR-011).
- [x] A test renders a name that contains markup and checks the escaped text (contract C4).

## Cloud Access

- [x] The change adds no Mist cloud request (FR-013). The existing reads of `selected_rows` stay unchanged (research R-21, R-55).
- [x] The change adds no mistapi method and no direct REST request (`spec.md`, Mist Cloud Transport Requirements).
- [x] A contract test counts the cloud calls of the confirm GET and compares the count with the baseline (contract C6).

## Secrets and Logging

- [x] The change reads no credential, prints no credential, and stores no credential.
- [x] The new log lines carry counts only. No line prints a MAC address, a site identifier, or a token.
- [x] The new log lines use ASCII only (Principle V).

## Access Control

- [x] The confirm route keeps its session requirement at `org_upgrade.py` line 1338 (`@identity.require_session`).
- [x] The change adds no route and no public endpoint.

## Data Integrity

- [x] The plan record keeps its stored shape. No migration runs (data model, "Stored Shape Compatibility").
- [x] Each new value comes from the stored record only (decision D-3).

## Residual Risks

- [ ] A reviewer must confirm the rendered page with a stand-in cloud before the merge. The residual risk is a rendering fault that the tests do not catch. The human safety review named by `needs-human-review` covers this check (decision D-11).
- [ ] The family defect of issue #3394 remains open. A family that the stored plan omits stays invisible on the page. This change does not fix it (out of scope).
