# Specification: the bootstrap browser download trusts the system certificate store

- Issue: #3302
- Branch: `chore/3302-bootstrap-system-ca`
- Scope: the local developer setup only

## Problem

`scripts/bootstrap_worktree.py` downloads the Playwright browser for the tests
under `tests/e2e/`. Playwright downloads the browser with its own Node runtime.
That runtime trusts only its own certificate list by default.

A proxy that inspects TLS, such as Zscaler, signs each certificate with its own
root. Only the Windows certificate store holds that root. The download then
fails with `UNABLE_TO_GET_ISSUER_CERT_LOCALLY`, and every browser test fails at
setup.

The repair line that the bootstrap prints fails in the same way, because it
sets no certificate option.

## Measurements

A probe on 2026-09-23 sent one HEAD request from the Playwright Node runtime,
version 24.21.0, to the root path of the browser download server.

| Setting | Result |
| - | - |
| No option | `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` |
| `NODE_OPTIONS=--use-system-ca`, request from a forked child | HTTP 400 from the server, so the TLS handshake passed |

Playwright downloads each browser in a forked child. The child reads
`NODE_OPTIONS` from the environment of its parent.

A second probe on 2026-09-24 ran the real `python -m playwright install chromium`
into a temporary browser folder.

| Environment | Result |
| - | - |
| The old download environment | Exit code 1 after 8.1 seconds, with `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` |
| The new download environment | Exit code 0 after 62.3 seconds, with 4 packages |

## Functional requirements

- FR-001: The browser download subprocess gets `--use-system-ca` in
  `NODE_OPTIONS`.
- FR-002: The browser download keeps each Node option that the caller set. The
  bootstrap adds the new option after the caller options.
- FR-003: If the caller options already hold `--use-system-ca`, the bootstrap
  does not add it a second time.
- FR-004: The pip subprocess gets no new Node option. The rest of the
  environment of the browser download stays the same.
- FR-005: If the download fails, the warning line and the final report print a
  repair command that sets `--use-system-ca`.
- FR-006: The repair command fits the shell of the platform. Windows gets a
  PowerShell command. Linux gets a POSIX shell command.
- FR-007: The download command, the return value, and the report on success
  stay the same.

## Success criteria

- SC-001: A unit test reads the environment of the download subprocess and
  finds the option. The test needs no network.
- SC-002: The existing tests of the browser download stay green.

## Out of scope

- The CI Playwright job. The GitHub runners are not behind Zscaler.
- The cause of the missing Chromium build 1243 in the shared browser cache.
- The pip certificate settings. pip reads its own configuration.

## Assumptions

- The pinned Playwright release, 1.63.0, bundles Node 24.21.0. That runtime
  accepts `--use-system-ca` in `NODE_OPTIONS`.
- The option adds the system store to the certificate list of Node. It removes
  no certificate, so a machine without a proxy sees no change.
