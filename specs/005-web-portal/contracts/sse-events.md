# SSE Event Contracts: Web Portal

**Feature**: 005-web-portal | **Date**: 2026-03-04

## Overview

The web portal uses **Server-Sent Events (SSE)** for real-time server-to-client communication. SSE was chosen over WebSocket based on research findings (see [research.md](../research.md#r1-real-time-communication--websocket-vs-sse-vs-polling)).

**Endpoint**: `GET /api/operations/stream`

**Content-Type**: `text/event-stream`

**Client connection**:
```javascript
const source = new EventSource('/api/operations/stream?run_id=<optional>');
source.addEventListener('status', (event) => { /* handle */ });
source.addEventListener('log', (event) => { /* handle */ });
source.addEventListener('complete', (event) => { /* handle */ });
source.addEventListener('error', (event) => { /* handle */ });
```

---

## Event Types

### 1. status

Emitted when an operation's progress or status changes.

**Frequency**: On each progress increment (throttled to max 1 per second)

```
event: status
data: {"run_id": "550e8400-e29b-41d4-a716-446655440000", "status": "running", "progress_pct": 45, "menu_number": "11", "description": "List Organization Sites"}
```

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | UUID of the operation run |
| `status` | string | `pending`, `running`, `completed`, `failed` |
| `progress_pct` | integer | 0-100 completion percentage |
| `menu_number` | string | Menu operation number |
| `description` | string | Human-readable operation name |

---

### 2. log

Emitted for each log line captured during operation execution.

**Frequency**: Per log line (throttled: batched every 500ms if high volume)

```
event: log
data: {"run_id": "550e8400-...", "message": "Processing site 5 of 42...", "level": "info", "timestamp": "2026-03-04T12:35:15Z"}
```

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | UUID of the operation run |
| `message` | string | Log message text (ASCII only — no Unicode) |
| `level` | string | `debug`, `info`, `warning`, `error` |
| `timestamp` | string | ISO 8601 timestamp |

---

### 3. complete

Emitted once when an operation finishes successfully.

**Frequency**: Once per operation run

```
event: complete
data: {"run_id": "550e8400-...", "status": "completed", "output_files": ["site_inventory.csv"], "duration_seconds": 12.5, "row_count": 42}
```

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | UUID of the operation run |
| `status` | string | Always `completed` |
| `output_files` | array[string] | Relative paths of output files created |
| `duration_seconds` | float | Total execution time |
| `row_count` | integer | Number of data rows exported (if applicable) |

---

### 4. error

Emitted once when an operation fails.

**Frequency**: Once per operation run

```
event: error
data: {"run_id": "550e8400-...", "status": "failed", "error_message": "API token expired - please check .env credentials", "duration_seconds": 3.2}
```

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | UUID of the operation run |
| `status` | string | Always `failed` |
| `error_message` | string | Human-readable error description |
| `duration_seconds` | float | Time elapsed before failure |

---

### 5. heartbeat

Keep-alive signal to prevent proxy/load balancer timeout.

**Frequency**: Every 30 seconds

```
event: heartbeat
data: {"timestamp": "2026-03-04T12:35:30Z", "active_operations": 2}
```

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 current server time |
| `active_operations` | integer | Number of currently running operations |

---

## Connection Behavior

### Client-Side

- **Auto-reconnect**: Built into the `EventSource` specification. Browser automatically reconnects on disconnect with exponential backoff.
- **Last-Event-ID**: Not used. Client re-fetches current state via `GET /api/operations/active` on reconnect.
- **Filtering**: Optional `?run_id=` query parameter limits events to a specific operation.

### Server-Side

- **Thread model**: Each SSE connection is served by a Gunicorn gthread worker thread. The thread loops, checking a shared queue for new events, yielding `data:` lines.
- **Backpressure**: If client stops consuming events, the thread drops events older than 10 seconds to prevent memory buildup.
- **Connection limit**: Max 10 concurrent SSE connections (configurable). Additional connections receive HTTP 503.
- **Cleanup**: When client disconnects (detected via write failure), the thread exits and resources are freed.

### Event Queue Architecture

```
OperationExecutor (background thread)
    │
    ├── Writes event to shared queue (threading.Queue)
    │
SSE Handler Thread (per connection)
    │
    ├── Reads from shared queue (with timeout)
    ├── Formats as SSE text
    └── Yields to client via Flask streaming response
```

The shared queue uses a publish-subscribe pattern:
- `OperationExecutor` publishes events to a `PortalEventBus`
- Each SSE connection subscribes and gets its own `Queue`
- Events are copied to all subscriber queues on publish
- Subscriber queues are bounded (max 100 events) to prevent memory leaks
