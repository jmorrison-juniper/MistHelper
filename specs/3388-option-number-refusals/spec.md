# Option number refusals

The authoritative issue is #3388. Comment 5967924631 grants exactly 13 paths.
The accepted commit is `18127a874259732e9e6770de027e9485388b7592`.
Its tree is `203ead4ef7c0a9e51f53b459193c6b410c811732`.

## Acceptance criteria

- Each number control accepts the ASCII digits `0` through `9` only.
- A value with more digits than the largest accepted value refuses before `int()` runs.
- Each refusal is a `BadOptionError` that names the control, in both modes.
- No refusal text and no log line repeats the typed value.
- A unit test covers a superscript digit and a 5000-digit value for each number reader.

## Preservation requirements

Preserve absent and empty controls, defaults, units, field ranges, phase order,
list cardinality, stored seconds, and stored epoch replay.
Use the actual imported readers, routes, renderer, and unchanged native browser harness.
Refusals must produce zero plan persistence, worker, cloud-write, and firmware calls.
Use synthetic records and isolated loopback resources only.

## Range decisions

Percentages use 0 through 100. Peer sizes use 0 through 1000.
Phase shares use 1 through 100. Durations use the existing site lock horizon.
The organization failure-count schema uses 0 through `2**31 - 1`.
The single-site failure-count reader currently has no upper bound.
Epoch replay with `now=None` currently has no upper bound.
The shared numeric helper requires a finite maximum.
Comment 5967972624 explicitly preserves both unbounded business ranges.
Use the active Python representation limit for these two readers.
If Python disables that limit, preserve unbounded conversion in these readers.
Do not change the global limit or assign an artificial cloud maximum.
Finite fields use their existing maximum to determine the raw token width.

## Coupled read-only boundary

`OrgOptionRefusal.whole_number` is defined in `src/upgrade_portal/app/routes/org_upgrade.py`.
`_base_request_options` calls it for the failure percentage.
`_phase_values` calls it for every phase share.
This method converts text before the mapper sees it.
The coordinator received its definition, callers, and smallest required boundary.
Comment 5968086205 releases only `OrgOptionRefusal.whole_number(text, field)`.
The cumulative grant contains 14 paths.
The method uses the existing percentage maximum of 100 for its two production callers.
Module-level imports, callers, sibling methods, and reporting regions remain byte-identical.
The reporting owner retains its frozen commit and position 41.
The mapper owner retains position 55.

## Publication boundary

Prepare locally only. Publication remains held at position 55.
Do not push, create a pull request, request Actions, merge, deploy, or release another owner.
