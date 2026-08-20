# Site Lock Contract

**Feature**: 1823-upgrade-capture-portal
**Store**: Redis
**Module**: `src/upgrade_portal/runtime/lock.py`

## Why the lock exists

Two operators must not upgrade the same site at the same time. The current portal
keeps its duplicate guard in process memory, so the guard dies with a restart and
does not cross a worker process. This feature needs a lock that survives a restart
and works across every worker.

Reading data never needs the lock. An operator may view a site, a capture, a
comparison, or a history page with no lock and with no typed text.

## Key and value

| Item | Value |
| --- | --- |
| Key | `misthelper:lock:site:{org_id}:{site_id}` |
| Type | Redis string that holds JSON |
| Expiry | 300 seconds, refreshed by a heartbeat |

```json
{
  "actor_email": "person@example.com",
  "browser_id": "b-7f3a1c...",
  "lock_token": "t-9d2e44...",
  "run_id": "run-ab12cd34",
  "acquired_at": "2026-08-19T09:12:03Z",
  "refreshed_at": "2026-08-19T09:16:33Z"
}
```

`lock_token` is a fresh random value for each acquisition. It is not a credential.
It never reaches a log line.

`browser_id` is a random value that the portal sets in a cookie on the first
visit. Two browser windows on one computer share the value. Two computers do not.
The pair of `actor_email` and `browser_id` decides whether a request may resume a
run without typing anything.

## Operations

### Acquire

One atomic command.

```text
SET misthelper:lock:site:{org}:{site} <json> NX EX 300
```

| Result | Meaning | Portal answer |
| --- | --- | --- |
| `OK` | The lock was free and is now held | `200` with the token |
| `nil`, same `actor_email` and same `browser_id` | The same operator returns | `200` with the stored token, state `resume` |
| `nil`, different holder, age under 300 seconds | Another operator is active | `409` `site_locked` |
| `nil`, different holder, age at or over 300 seconds | The holder went quiet | `400` `confirmation_required` |

The portal never uses a read followed by a write to acquire the lock. A read then
a write is not atomic and two operators would both win.

### Refresh

A Lua script that compares and then extends. The compare and the extend run as one
step, so a heartbeat cannot extend a lock that a different operator now holds.

```lua
-- KEYS[1] = lock key, ARGV[1] = lock_token, ARGV[2] = new json, ARGV[3] = ttl
local current = redis.call('GET', KEYS[1])
if not current then return 0 end
local held = cjson.decode(current)
if held['lock_token'] ~= ARGV[1] then return 0 end
redis.call('SET', KEYS[1], ARGV[2], 'EX', tonumber(ARGV[3]))
return 1
```

| Return | Portal answer |
| --- | --- |
| `1` | `200` with `expires_in` |
| `0` | `409` `lock_lost` |

The browser sends a heartbeat every 60 seconds while a run page is open. The run
driver thread also sends a heartbeat every 60 seconds, so a closed browser does not
drop a live upgrade.

### Release

A Lua script with the same compare, followed by `DEL`.

| Return | Portal answer |
| --- | --- |
| `1` | `200` `released` |
| `0` | `409` `lock_lost` |

The portal releases the lock when a run reaches `complete`, `stopped`, or
`failed`. The portal does not release the lock when a browser closes, because the
run continues.

### Takeover

A takeover needs two conditions.

1. The current lock has been quiet for the full 300-second cooldown.
2. The new operator types the exact word `CONFIRM`.

The portal writes an audit record for every takeover. The record holds the old
`actor_email`, the new `actor_email`, and the time. A takeover never cancels a
running upgrade. It transfers who may drive the portal.

## Failure behavior

| Condition | Behavior |
| --- | --- |
| Redis is unreachable at acquire | Refuse the upgrade start with `503` and a plain message. Never fall back to an in-memory lock. |
| Redis is unreachable at heartbeat | Retry for 60 seconds. If the retry fails, move the run to `failed` and say so plainly. |
| Redis is unreachable for a read-only page | Show the page and mark the lock state unknown. Viewing must not need Redis. |

An in-memory fallback is forbidden. A fallback would let two workers each believe
they hold the lock, which is the exact failure the lock prevents.

## What the lock does not do

| Not covered | Reason |
| --- | --- |
| It does not gate a capture for the operator who holds it | The documented journey takes the lock first and the pre-check capture second. A presence-only test would refuse that operator their own capture. |
| It does not gate a comparison or a history page | Reading needs no lock. |
| It does not replace the confirmation words | `CONFIRM` takes the lock and starts the upgrade. `STOP` stops the run. The two acts never share a page, so one word serves both. |

An earlier version of this table said that the lock does not gate a capture at
all. `POST /api/sites/<site_id>/captures` refuses a second operator with `409`
`site_locked`, and section 4 of `contracts/http-api.md` agrees with the code. The
lock gates a capture for every operator except the holder.

An unreachable lock store still lets a capture start. The read above marks the
lock state unknown, and an unknown state names no holder. The fail-closed `503`
stays with the acquire, because only that path leads to a firmware write.
