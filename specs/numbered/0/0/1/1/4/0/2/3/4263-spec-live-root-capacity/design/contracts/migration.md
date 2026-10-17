# Contract: Approved record relocation

## Preconditions

Read current open PR paths before preparing the move.
Obtain a handover for every overlapping record and affected reference.
Use the [manifest fields](../data-model.md) to record content and ownership.
Do not treat this planning issue as approval to change another owner's record.

Add discovery and guard tests before moving any record.
Publish the shared task-audit update before accepting its coverage result.
Keep the process-folder baseline unchanged.

## Relocation

Build a complete source-to-destination map before writing.
Verify destination capacity and uniqueness for the whole map.
Move only approved records.
Keep each record independent and retain its basename.
Verify every file against the original manifest.

Update approved references in the same implementation change.
Preserve original hashes and review the exact reference-only patches.
Reject any unrelated narrative change.
Do not add aliases, duplicate records, exclusion entries, or feature nesting.

If verification fails, stop and preserve both evidence and the recoverable source.
Do not overwrite a source or destination to conceal a conflict.
Resolve the failing manifest entry before another move.

## Completion

The guard must pass with the same five-child threshold.
Each moved file must have a verified destination.
Every affected selector must return the same feature identity.
Every affected link must resolve.
Search tracked text for each old slash path and Windows path form.
Only explicit historical evidence may retain an old path.
Review each remaining occurrence rather than suppressing the search.

## Redis Planning Dependency

PR [#4223](https://github.com/jmorrison-juniper/MistHelper/pull/4223) remains blocked until the process implementation merges.
Its owner then rebases, relocates the Redis record, and updates its references.
Run the strengthened guard on that rebased branch.
Do not merge based on an earlier passing result or this planning PR.

## Proposed Move Requiring Owner Review

**State**: Moved and verified after the coordinator relayed the user's scoped authorization.

**Owner**: `jmorrison-juniper`, author of merged PR [#4202](https://github.com/jmorrison-juniper/MistHelper/pull/4202).

**Source**: `specs/live/20261013-182828-fix-generated-control-labels/`

**Destination**: `specs/live/0/0/0/1/2/1/3/2/2/1/2/3/0/3/4/1/3/20261013-182828-fix-generated-control-labels/`

The original commit is `58a786c59`.
The record has nine files and five direct children.
Its design and checklist directories also remain bounded.
No open PR path overlaps this source.
Recheck ownership before any approved move.

The proposed move replaces one live-root child with group `0`.
It retains five root children and gives the Redis timestamp a shared structural prefix.
The source `plan.md` contains two absolute repository-path references that require approved updates.
The tracked-text search found no external reference to this source path.
Historical references in this issue's evidence remain explicitly historical.

| Original relative file | Bytes | SHA-256 |
| --- | --- | --- |
| `checklists/requirements.md` | 1069 | `7823f63fe0549c72bbc4aeac0f664bd68823a62bb4a33868c442403a3db2ec93` |
| `design/analysis.md` | 3155 | `7381387632eb8ea5d8b7cc9d526bb870d70e45e92bc123b65af4666ac459024a` |
| `design/contracts/labels.md` | 502 | `3cedbc0d11c64db3264f5ef26376077f9be70392f8626436fd8f7753341517cb` |
| `design/data-model.md` | 607 | `cc166460ff5e44b95927ac68233efca75092444e06b9b851388b8a7421af4035` |
| `design/quickstart.md` | 970 | `1d95e1b839dd45060de4f169931237f8045f6903d276d95ef840f252c2ad4ba8` |
| `design/research.md` | 794 | `600168a14c35eb3604b625596c0134c662dc4405f725445b96d7dea980a78d65` |
| `plan.md` | 2761 | `8eb63c8736c993a1c1a8090e1045f406c6b5e71a1441fa0de948235ab9399056` |
| `spec.md` | 2744 | `09174506609175549af8388e057d749d3d237dc09fcbeda8f2fa981d6c2f793f` |
| `tasks.md` | 1626 | `d2686b3e6ae68e1cf1a0836bff99bd83ac635bcb49d1ee27f92bddd046b8c474` |

The coordinator relayed explicit authorization for this record and its two reference-only edits.
The move first preserved the record in session artifacts, outside the full live root.
It then created the bounded groups and returned the record to its final destination.
The live root never required a sixth child.

Before reference updates, all nine destination hashes matched the original inventory.
After reference updates, eight files remain byte-identical.
The only changed file is `plan.md`, with exactly the two approved path replacements.
Its final SHA-256 is `6d882df48a8911eb8077596a86fd4947a953fe3b9d7ec022e722c8ecce18dc48`.
The record identity, original branch metadata, and ownership text remain unchanged.
No other feature record moved.
The shared task-audit dependency remains separate.
