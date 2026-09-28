# Feature Specification: Plain words for each cancel result of a multi-site operation

**Issue**: #3538
**Feature Branch**: `fix/3538-cancel-result-words`
**Status**: Draft
**Found by**: the browser run of 2026-09-28 for issue #3518

## Problem

The progress page of a multi-site operation shows one "Cancellation result" card for each child job.
Each card shows the word that the portal stored for the cancel of that child job.
The site table shows the same word at the start of its Cancellation cell.

The stored words are internal words.

| Stored word | Where the portal writes it | Meaning |
| - | - | - |
| `cancel_claimed` | The claim step before the cancel call | The cancel call has no answer yet. |
| `requested` | The site cancel and the organization cancel | The portal sent the cancel request, and the cloud answered. |
| `failed` | The organization cancel | The cloud refused the cancel, or its answer is damaged. |
| `unavailable` | The cancel of a child job with no upgrade identifier | The portal cannot send a cancel request. |
| `unknown` | The cancel call that raised an error | The result of the cancel request is not known. |
| `cancel_unknown` | The recovery of an expired claim | The result of the cancel request is not known. |
| `already_ended` | The cancel of a child job in a final state | The portal sent no cancel request. |

An operator can read `requested` as "the cancel still waits".
The word stays after the operation reaches the final state `cancelled`.
A junior NOC engineer must know the internal words to read the card.

The single-site stop page shows no stored word.
It shows the message and the three device lists only.

## User Scenarios & Testing

### User Story 1 (P1): The card names the cancel result in plain words

An operator cancels a multi-site operation, and then reads each "Cancellation result" card.

**Independent test**: Cancel an operation in the browser.
Read each card after the operation is final.

**Acceptance scenarios**:

1. **Given** a child job that took the cancel request.
   **When** the operation is final.
   **Then** the card shows "Cancel request: Sent", and it shows no stored word.
2. **Given** a child job that ended before the cancel.
   **When** the page shows the card.
   **Then** the card shows "Cancel request: Not sent".
3. **Given** each of the seven stored words.
   **When** the page shows the card.
   **Then** the card shows the plain label of that word.
4. **Given** a stored word that the portal does not know.
   **When** the page shows the card.
   **Then** the card shows "Not recognized", and it does not show the stored word.

### User Story 2 (P1): The site table uses the same words

An operator reads the Cancellation cell of the site table.

**Independent test**: Load the progress page after a cancel, and wait for one poll.

**Acceptance scenarios**:

1. **Given** a child job with a cancel result.
   **When** the page loads.
   **Then** the Cancellation cell starts with the same label as the card.
2. **Given** the same child job.
   **When** the poll paints the site table.
   **Then** the Cancellation cell keeps the same text.

### User Story 3 (P2): A test and a tool can still read the stored word

**Acceptance scenarios**:

1. **Given** a card.
   **When** a test reads the status element of the card.
   **Then** the attribute `data-cancel-status` holds the stored word.
2. **Given** the JSON answer of the status call.
   **When** a tool reads `cancellation.status`.
   **Then** the value is the stored word, with no change.

## Edge Cases

- A cancel result with no stored word shows "Not recorded" on the card.
  The Cancellation cell then shows no label, as before.
- A stored word that is not a text shows "Not recognized".
- The page load after a new cancel result still follows the stored words.
  The labels do not change the reload rule.
- The stored words of the record do not change.
  So an operation that an earlier release stored shows the new labels.

## Requirements

### Functional Requirements

- **FR-001**: The card must show one plain label for each stored word.
  The label must follow the text "Cancel request:".
- **FR-002**: The seven labels must be these words.

  | Stored word | Label |
  | - | - |
  | `cancel_claimed` | In progress |
  | `requested` | Sent |
  | `failed` | Failed |
  | `unavailable` | Not possible |
  | `unknown` | Result not known |
  | `cancel_unknown` | Result not known |
  | `already_ended` | Not sent |

- **FR-003**: A stored word outside the table must show "Not recognized".
  An empty stored word must show "Not recorded" on the card.
- **FR-004**: The Cancellation cell of the site table must use the same label.
  The first render and each poll must show the same text.
- **FR-005**: The status element of the card must keep its test identifier.
  It must carry the stored word in the attribute `data-cancel-status`.
- **FR-006**: The change must not change a stored word, the JSON answer of a call, or the reload rule of the page.
- **FR-007**: One class must hold the label table.
  The card and the cell must read the same table.
- **FR-008**: The operator guide must name each label and its meaning.

### Key Entities

- **Cancel result**: The stored result of the cancel of one child job.
  It holds the stored word, the message, and the three device lists.
- **Label**: The plain words that the page shows for one stored word.

## Success Criteria

- **SC-001**: In a browser run, 0 cancellation cards show a stored word as the visible text.
- **SC-002**: For each of the seven stored words, a direct test proves the label.
- **SC-003**: The card and the Cancellation cell show the same label for 100 percent of the child jobs.
- **SC-004**: Each browser journey that reads a card passes in Microsoft Edge.

## Assumptions

- The operation status words, such as `partial` and `attention_required`, are out of scope.
  The status card of the operation shows them, not the cancellation card.
- The single-site stop page needs no change, because it shows no stored word.
- The label "Sent" is true for each child job that stores `requested`.
  Each child job of a multi-site operation has a site scope or an organization scope.
  So the portal always has a cancel call for it.
- The message of each card keeps the exact words of the cancel result.
