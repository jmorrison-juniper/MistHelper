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

## Hosted validation and revision review

The review on 2026-11-06 inspected the live PR, completed job logs, run identities, required checks, and branch ownership.
The local branch and live PR head both identified `f5247c68c01cd3badd15f62e23ef14cbdbc3d2b7`.
Only PR #4617 owns these specification records. The worktree was clean before this revision.

| Evaluated head | Web-portal job | Browser installation | Package payload | Full selected result |
| - | - | - | - | - |
| `17ea00e87c767fef956337de6babf9cf9a626b8b` | [127810704470](https://github.com/jmorrison-juniper/MistHelper/actions/runs/42193119980/job/127810704470) | 22 seconds | 21.1 MB in 2 seconds, 9490 kB/s | 453 passed, two warnings, 638.43 seconds |
| `f5247c68c01cd3badd15f62e23ef14cbdbc3d2b7` | [128092020295](https://github.com/jmorrison-juniper/MistHelper/actions/runs/42274893165/job/128092020295) | 22 seconds | 21.1 MB in 1 second, 14.4 MB/s | 453 passed, two warnings, 667.20 seconds |

The rebased run completed successfully with `run_attempt: 1` on the second evaluated head.
Mirror preparation succeeded at `19:02:52Z`. Browser installation ran from `19:02:52Z` through `19:03:14Z`.
The job ran from `19:01:53Z` through `19:14:35Z`, within the unchanged 20-minute limit.
Its log separately records 12.9 MB of package indexes in four seconds.
The required-check query reported 15 passed and zero failed. CodeQL, all E2E shards, and Upgrade portal journeys also passed.

These observations satisfy SC-004 for the evaluated heads. They do not prove future transfer speed or repair the separate #3736 silent interval.
The Azure failure cause remains unknown. No workflow retry produced these measurements.

The user authorized one manual squash merge of the first published head containing this revision.
All required checks and CodeQL must pass on that exact head. The branch must be current with main, and the serial slot must be available.
Retries, auto-merge, check bypasses, and merges of changed heads remain prohibited.
The runtime budget, selected cases, assertions, required statuses, and CI policy remain unchanged.
No workflow or test source changes are part of this revision. PR #4208's upload intent remains unchanged.

At review, live main identified `d29cfd3984bcd00074d7b73c6d786be9edce249c`, beyond this branch's evaluated base.
This revision therefore does not establish current-base merge readiness.
Any later candidate needs applicable local validation and exact-head required checks, including CodeQL.

## Additional existing-run sample

The later review examined both prepared runs and all five completed main runs in the latest 30-run listing.
The listing covered `2026-11-06T18:47Z` through `2026-11-07T00:03Z`. The sample includes the canceled main run.
Every sampled run used attempt one. No new trigger or retry collected these observations.

| Main web-portal job | Browser installation | Apt payload | Selected result |
| - | - | - | - |
| [128117991608](https://github.com/jmorrison-juniper/MistHelper/actions/runs/42282055206/job/128117991608) | 19 seconds | 21.1 MB in 0 seconds, 68.2 MB/s | 453 passed, 721.06 seconds |
| [128135545418](https://github.com/jmorrison-juniper/MistHelper/actions/runs/42288182543/job/128135545418) | 529 seconds | 21.1 MB in 510 seconds, 41.4 kB/s | Canceled, no final summary |
| [128153384917](https://github.com/jmorrison-juniper/MistHelper/actions/runs/42293210843/job/128153384917) | 19 seconds | 21.1 MB in 1 second, 22.5 MB/s | 453 passed, 656.48 seconds |
| [128165880649](https://github.com/jmorrison-juniper/MistHelper/actions/runs/42296900715/job/128165880649) | 19 seconds | 21.1 MB in 1 second, 18.4 MB/s | 453 passed, 676.35 seconds |
| [128229301847](https://github.com/jmorrison-juniper/MistHelper/actions/runs/42315841241/job/128229301847) | 20 seconds | 21.1 MB in 0 seconds, 74.0 MB/s | 453 passed, 717.99 seconds |

These main jobs had no preparation step and downloaded packages through Azure HTTP.
The canceled job's annotation explicitly identifies the 20-minute job limit.
It collected 453 cases after the 529-second installation. Its package indexes transferred in one second.
This independently repeats the setup-budget failure without identifying a stalled test.

All six prepared matrix installations across the two evaluated PR runs completed in 19–23 seconds.
Their payload summaries report 1–3 seconds. Only two jobs ran the web-portal selection.
The other jobs ran different selections and are not additional web-portal samples.

Four main comparisons were as fast as, or faster than, the prepared installations.
Azure therefore shows intermittent behavior, not consistently slow transfers.
This short observational sample uses different commits, runner allocations, and network conditions. Matrix jobs share temporal conditions.
Apt rounds durations. Its `0s` does not mean zero transfer time.
The sample supports no failure probability, universal speed improvement, or future reliability guarantee.
