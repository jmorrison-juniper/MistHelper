### Fixed

- The fresh container install steps now state measured facts. An audit ran every
  documented step against a Podman host and a clean clone (issue #3465).
  - `Containerfile` and `Dockerfile` pin the `misthelper` account to UID 1000 and
    GID 1000. The account took its number from the base image before, so the
    number moved from 999 to 994 and the documented `chown` target went stale.
  - The install documents no longer tell an operator to run `chmod -R 777 data`.
    Windows and macOS need no command, and a Linux host uses
    `podman unshare chown -R 1000:1000 data`.
  - `podman compose` is the documented start command again. The documents now
    name the `PODMAN_COMPOSE_PROVIDER` setting that corrects the Windows volume
    defect of issue #2184, so a deployment no longer depends on the in-house
    `scripts\compose.ps1` helper.
  - `documentation/wiki/Container-Setup.md` no longer claims that `Containerfile`
    and `Dockerfile` hold two different build strategies. The two files hold the
    same bytes, and a test already proves it.
  - The runtime message for an unwritable data folder names the pinned account
    and a compose command that exists inside the shipped image.
- `tests/guardrails/test_container_account_identifiers.py` holds the documents to
  the account number that `Containerfile` pins.
