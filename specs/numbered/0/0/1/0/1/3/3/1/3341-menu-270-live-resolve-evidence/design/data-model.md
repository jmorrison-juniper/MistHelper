# Data Model: Menu 270 Live Resolve Acceptance Evidence

This model describes the data that the live check reads and writes. It adds no schema. Each value cites a row of the remote verification table in `research.md`.

## Entities

### Marvis Action (Mist object)

- **Natural key**: `uuid`. The results row copies it (row 11).
- **Addressing key**: `row_key`. The resolve body names the action by this key (row 16).
- **Open statuses**: `open`, `inprogress`, and `reoccured` (row 18).
- **Status names**: `open`, `inprogress`, `resolved`, `validated`, `marvis_self_driven`, `reoccured`, and `expired action` (row 19).
- **Topic**: a pair key such as `switch/sw_offline`. The results row copies `topic` (row 11). The example comes from issue comment IC_kwDOQltU8c8AAAABWysfYQ.

### Resolve request (one per run)

- **Run fields**: the resolution code, the comment, and `resolve_time` in epoch milliseconds (row 15).
- **Body per action**: `row_key`, `status` with the fixed value `resolved` (row 16), `label` with the code key, `comment`, and `resolve_time`.
- **Run time**: one `resolve_time` value serves every request of one run (row 15).

### Results row (one per target action)

- **Natural key**: `result_id`. The results file key follows the strategy `resolveOrgMarvisActions` (row 24).
- **Columns**: 26 fields in the order of the results class (row 11). The contract `contracts\results-csv.md` lists them.
- **Outcome**: one of `resolved`, `sent_unverified`, `error`, `not_sent`, or `skipped` (row 10). The interim value `sent` (row 9) is replaced by the verify step (row 12).
- **HTTP status**: an integer, or an empty value when no request went out (row 11).
- **Verified status**: the status from the verify read (row 11).

### Owner evidence record (issue comment)

The owner evidence record is one comment on issue #3341. It is not a file in the repository. Its format appears in `contracts\live-evidence-record.md`.

## State Transitions

### Mist action status

```text
open, inprogress, or reoccured --(resolve request accepted, closed verified status)--> resolved
resolved --(set to Open in the Mist UI)--> open
open --(Mist closes the action without MistHelper)--> validated
```

- The Mist UI can set a resolved action back to Open. The confirmation prompt names this option (row 17).
- Mist closed the action `swoff-292` as `validated` without a MistHelper request (issue comment IC_kwDOQltU8c8AAAABWysfYQ).

### Results outcome

```text
(start) --send--> sent
sent --verify read, closed status--> resolved
sent --verify read, open status or no status or failed read--> sent_unverified
sent --HTTP status outside 2xx, or no HTTP answer--> error
(start) --stop signal before send--> not_sent
(start) --no row_key--> skipped
```

- The verdict rules follow row 12.
- Only `resolved` supports acceptance (FR-007).

## Keys and Units

- Epoch times use milliseconds (row 15). The results file also stores a readable time (row 11).
- A natural key identifies each action. The results row adds the run time to make one key for each action and each run.
- Blank cells mean that no value exists. A blank cell is not a zero value.
