# Performance monitoring memory measurement

This file is a standalone artifact for issue #2482. Do not treat it as section
9 of the performance report. The coordinator will fold this table into
`specs\2448-misthelper-performance-monitoring\performance-report.md` after
pull request #2542 merges.

## Sampling method

The harness at `tools\performance_memory.py` ran one bounded scenario for each
memory question. It used `tracemalloc` for traced Python current bytes, traced
Python peak bytes, and the top live allocation sites.

Process memory used the Windows `GetProcessMemoryInfo` API through `ctypes`.
The table keeps Windows working set bytes and private bytes separate from
traced Python bytes. The project did not declare `psutil`, so the harness did
not add or use that dependency.

The memory runs did not measure timing. The harness stopped `tracemalloc`
before any future timing run could execute.

Platform: CPython 3.13.3 at
`C:\Users\jmorrison\mh-mem\.venv\Scripts\python.exe` on Windows 11 AMD64.
The platform string was `Windows-11-10.0.26200-SP0`.

## Measured memory table

| Scenario | Queued events | Traced current bytes | Traced peak bytes | Process working set before | Process working set after | Process private before | Process private after | Bound evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Disabled span, level off | 0 | 4,144 | 4,288 | 32,522,240 | 32,661,504 | 15,929,344 | 15,929,344 | No event reached the sink |
| One minimal enabled span | 1 | 5,024 | 6,682 | 32,665,600 | 32,698,368 | 15,929,344 | 15,929,344 | One queued span |
| One worst case event | 1 | 11,712 | 13,178 | 32,698,368 | 32,727,040 | 15,929,344 | 15,929,344 | One event with 16 labels and 32 measurements |
| Full queue, minimal events | 2,048 | 860,880 | 861,212 | 32,727,040 | 34,656,256 | 15,929,344 | 18,923,520 | Queue reached capacity with no drops |
| Full queue, worst case events | 2,048 | 14,156,856 | 14,157,315 | 34,660,352 | 67,608,576 | 19,136,512 | 52,805,632 | Queue reached capacity with no drops |
| Sustained minimal events | 2,048 | 861,096 | 861,656 | 42,606,592 | 42,356,736 | 26,615,808 | 26,259,456 | 50,000 events emitted and 47,952 dropped |
| Bounded caches | Not applicable | 100,980 | 101,971 | 42,356,736 | 42,778,624 | 27,041,792 | 27,557,888 | Safe cache held 1 entry. LRU caches held 256 and 512 entries. |

## Per-event and plateau values

Per-event traced current bytes from the full queue were 420.35 bytes for the
minimal event and 6,912.53 bytes for the worst case event. The one-event runs
measured 5,024 traced current bytes for a minimal enabled span and 11,712
traced current bytes for one worst case event.

The full queue figure at capacity is 860,880 traced current bytes for minimal
events and 14,156,856 traced current bytes for worst case events.

The sustained minimal run plateaued at 861,096 traced current bytes. That value
is within 216 bytes of the full minimal queue value, although the sustained run
emitted 47,952 additional events.

## Top allocation sites

Top allocation sites for the full worst case queue:

| Site | Live traced bytes |
| --- | ---: |
| `tools\performance_memory.py:163` | 6,860,800 |
| `tools\performance_memory.py:169` | 6,729,656 |
| `tools\performance_memory.py:151` | 213,080 |
| `tools\performance_memory.py:168` | 130,816 |
| `tools\performance_memory.py:162` | 130,752 |

## Remaining unmeasured items

Linux process memory and the native memory split are not measured here. Timing
is not measured here because timing must run without `tracemalloc` active.
