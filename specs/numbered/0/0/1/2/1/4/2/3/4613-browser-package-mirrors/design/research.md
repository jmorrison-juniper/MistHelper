# Browser dependency evidence

## Measured failure

[Run 42180836919](https://github.com/jmorrison-juniper/MistHelper/actions/runs/42180836919) used source `91c64e872`.

| Job | Browser setup | Apt package transfer | Completed calls |
| - | - | - | - |
| Web portal 127772055565 | 07:37:15Z to 07:47:44Z, 629 seconds | 18.2 MB in 609 seconds, 29.8 kB/s | 221 passed, zero failed |
| Web portal 127783738558 | 08:06:33Z to 08:16:06Z, 573 seconds | 21.1 MB in 554 seconds, 38.1 kB/s | 298 passed, zero failed |
| Websockets 127772055522 | 07:36:34Z to 07:36:59Z, 25 seconds | 21.1 MB in 5 seconds, 4113 kB/s | Successful shard |
| Upgrade portal 127772055434 | 07:33:51Z to 07:41:17Z, 446 seconds | 21.1 MB in 427 seconds, 49.4 kB/s | Successful shard |

Both web-portal attempts collected 453 cases and stopped at the unchanged 20-minute job limit.
Neither has a final pytest summary.
The repeat artifact contains 298 passed calls, not the 297 visible in the earlier issue comment.
Its final passed call is the small-phone responsive-layout case at `08:25:43.441215Z`.
Its next setup passed at `08:25:43.544655Z`.
The original artifact ends with the blank-site map test setup at `07:56:23.060588Z`.
The available evidence shows continuing progress, not an identified test stall.

The original font download received `Ign:6`, then requested `fonts-wqy-zenhei` again.
Package indexes transferred at approximately 10 MB/s in both attempts.
The delay occurred in package payload transfers from `http://azure.archive.ubuntu.com/ubuntu`.
Chromium installation completed after apt.

## Prior issue

[Issue #3736](https://github.com/jmorrison-juniper/MistHelper/issues/3736) describes several different incomplete browser runs.
Its original job `111057821335` fetched 32.1 MB in two seconds.
It then stopped reporting results for more than seven minutes before cancellation.
That earlier silent interval does not establish a connection to this package-transfer delay.
The later #4408 comment records another repeated slow apt transfer, but does not explain the earlier stall.

## Decision

Remove only the slow Azure entry from the existing runner mirror list.
Keep the official HTTPS archive and security alternatives already configured by GitHub.
Keep `python -m playwright install --with-deps chromium` unchanged.
Do not manually maintain a smaller package list or bypass browser availability checks.

[Runner configuration](https://github.com/actions/runner-images/blob/main/images/ubuntu/scripts/build/configure-apt-sources.sh)
defines Azure at priority 1, the HTTPS archive at priority 2, and the HTTPS security archive at priority 3.
It points Ubuntu sources to `mirror+file:/etc/apt/apt-mirrors.txt`.
The repair changes routing only, not suites, components, keys, or package verification.

On 2026-11-06, both HTTPS endpoints returned identical Noble `InRelease` bytes.
The SHA-256 digest was `cdb2f31d809f589719a53c6ad15f255b27569c4059542ada282aaa21b8e164b0`.
This proves archive metadata equivalence for that request, not hosted-runner transfer speed.
The underlying Azure network or server cause remains unknown.

## Alternatives considered

- A browser cache does not supply missing system packages and does not repair a cache miss.
- A reduced package list can change fonts and rendering, so it is not equivalent.
- A prebuilt container changes the runner environment and needs separate Python, services, and browser-version validation.
- More retries or a larger timeout conflict with the explicit task constraints.
- Switching mirrors cannot guarantee network speed. A later normal CI run must measure completion.

## Ownership

Open-PR inspection found only #4208 overlapping `.github/workflows/ci.yml`.
Its diff adds only the WAN Performance evidence upload in that file.
The user granted the handover, and this session notified its owner before editing.
Keep that upload unchanged during reconciliation.
The issue artifact list returned no artifacts. Both diagnostic ZIP artifacts and all issue comments were read.
