# Data Model: WebSocket Operation Form Cancellation

This feature adds no server-side persistence or API resource. These are
client-side concepts represented by the existing page state and picker
controls.

## Pending operation selection

The unsubmitted catalog entry and its form values.

| Field | Meaning | Validation / invariant |
|---|---|---|
| `entry` | Selected catalog operation (currently `state.selectedEntry`) | Null when no pending selection exists. |
| `generation` | Monotonically changing selection lifetime token | Changes on every new selection and on cancellation; an old picker response cannot match it. |
| `values` | Target and parameter inputs, including repeatable values and confirmation | Belong only to the current entry; discard on Cancel. |
| `presentation` | Title, description, selected catalog styling, safety notice, start error and confirmation visibility | Must describe the same current entry; reset with selection state. |
| `submitted` | Whether the current pending selection has been submitted | Cancel applies only before submission. Existing session controls handle the resulting live session. |

### State transitions

```text
unselected --select(entry)--> selected(generation n)
selected(n) --select(other)--> selected(generation n+1)
selected(n) --cancel--> unselected(generation n+1)
selected(n) --submit--> submitted/session lifecycle
```

Repeated Cancel from `unselected` is a no-op. Cancel never transitions or
mutates a live session.

## Picker result

An asynchronous list response requested by a field in a pending selection.

| Field | Meaning | Validation / invariant |
|---|---|---|
| `selectionGeneration` | Generation captured when the read starts | Must equal the active selection generation before response handling. |
| `entryIdentity` | Identity/key of the operation that requested the list | Must equal the active selected entry. |
| `controlSerial` | Existing per-select newest-request marker | Must equal the active control's request serial. |
| `rows` / `reason` | Picker options or empty/error text | May update the current control only after all identity checks pass. |
| `sharedLabels` | Label entries added from usable picker rows | Must not be changed by canceled/superseded responses. |

The response is discarded before `fillPicker`, option construction, or any
shared label mutation if it is stale. The existing serial remains necessary
for repeated dependent-picker reads within one current selection.

## Live session card

The display state of a submitted session.

| Field | Meaning | Cancellation invariant |
|---|---|---|
| `sessionIdentity` | Existing session identifier | Unchanged by pending form cancellation. |
| `sessionState` | Existing live/stopped/finished state | Unchanged by pending form cancellation. |
| `cardPresentation` | Existing card content and controls | Remains present and unchanged when another form is canceled. |

The live session model is existing behavior, not an entity modified by this
feature.
