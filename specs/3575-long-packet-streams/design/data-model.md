# Data Model: Long packet streams

## Capture plan

The immutable plan holds the checked request, private channel, duration,
capture body, and scope reservation.
The request supplies the server-owned organization identifier.
The operator cannot supply a host, channel path, or organization.

## Capture events

One event group holds stop, subscription, connection close, wake, and lock state.
The worker and SDK callbacks share that group.
Stop and capture admission use the same lock.

## Capture progress

One progress record holds the accepted capture identifier, deadline,
terminal outcome, cleanup flag, and accepted packet count.
The start response establishes identity before pending events reach the card.
The first terminal outcome wins.

## Capture session

The existing `StreamSession` owns the card state, counters, rate window,
idle tracking, message buffer, and download.
The feature creates no database record or persistent packet store.

## State transitions

`connecting` waits for subscription confirmation and capture acceptance.
`live` receives matching packets.
`stopping` waits for the matching cloud stop result.
`stopped` requires a confirmed stop or cancellation before capture start.
`finished` means the selected interval or a matching capture-end event completed.
`timed_out` means the capture produced no packet record.
`failed` describes a refused or uncertain action, invalid event, or terminal disconnect.

## Resource limits

The existing live-session, message, byte, rate-window, and retention limits remain.
The private pending buffer also has message and byte limits.
One capture owns one worker and one SDK connection.
Each terminal path closes the owned connection and private HTTP transport.
