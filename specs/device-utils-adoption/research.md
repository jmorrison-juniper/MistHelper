# Research: device_utils Adoption

**Date**: 2026-06-11 | **Plan**: [plan.md](plan.md)

## R1: mistapi.device_utils API Surface

### Decision
Use `mistapi.device_utils` submodules (`ex`, `ssr`, `srx`, `ap`) which provide typed helper functions for each device type + command combination. Each function accepts `(mist_session, site_id, device_id, **params)` and returns a `UtilResponse` object.

### Rationale
- Eliminates ~100 lines of boilerplate per command (WebSocket connect, subscribe, POST, poll, parse)
- SDK handles WebSocket lifecycle internally — no more `WebSocketManager` for device commands
- Typed function signatures provide IDE autocompletion and catch parameter errors at call time

### Alternatives Considered
- **Keep raw API + WebSocket**: Rejected — maintaining custom WebSocket polling is the #1 source of complexity and bugs in device command code
- **Partial adoption (show commands only)**: Rejected as final state — but accepted as phased migration strategy

## R2: UtilResponse Structure

### Decision
`UtilResponse` wraps the API response and provides:
- `.data` — parsed response dict (equivalent to current WebSocket message `data` field)
- `.status_code` — HTTP status from the initial POST
- `.raw` — raw response for debugging
- `.session_id` — WebSocket session identifier (replaces manual channel tracking)

The `.data` field contains the same JSON structure as current WebSocket messages, so normalization is straightforward: extract `.data` and flatten using existing `flatten_dict()`.

### Rationale
Direct `.data` access means the adapter's primary job is: call `device_utils.*()` → extract `.data` → flatten → return. Minimal transformation needed.

### Alternatives Considered
- **Custom response wrapper**: Rejected — adds unnecessary abstraction over SDK's own response type

## R3: Version Detection

### Decision
Use try/except import at module load time:

```python
try:
    import mistapi.device_utils as device_utils
    DEVICE_UTILS_AVAILABLE = True
except ImportError:
    DEVICE_UTILS_AVAILABLE = False
```

Check `DEVICE_UTILS_AVAILABLE` before any device_utils call. Log a clear warning at startup if unavailable. Fall back to raw API for all operations when unavailable.

### Rationale
- Import-time detection is standard Python practice
- Graceful degradation means existing deployments with older mistapi continue working
- Single boolean flag simplifies all conditional logic

### Alternatives Considered
- **Version string parsing** (`mistapi.__version__`): Rejected — fragile, version string format may change
- **Hard fail at startup**: Rejected — breaks existing deployments during gradual rollout

## R4: Fallback Strategy

### Decision
When `DEVICE_UTILS_AVAILABLE` is `False`, or when a specific `device_utils.*` function raises `AttributeError` (missing function for a device type + command combo), fall back to existing raw API + WebSocket code path. Log the fallback at `info` level.

The adapter method signature: `execute(command, device_type, site_id, device_id, **params) -> dict`. Internally dispatches to device_utils or falls back to raw API.

### Rationale
- Not all device type + command combinations may be covered in device_utils v0.61.0
- Fallback ensures zero regression risk per command
- Logging fallbacks helps track which commands still need SDK coverage

### Alternatives Considered
- **No fallback (hard fail on missing)**: Rejected — too risky for production NOC tool
- **Per-command feature flags**: Rejected — over-engineering; import check + AttributeError catch is sufficient

## R5: Rate Limiting Interaction

### Decision
`UtilResponse`'s internal WebSocket polling does NOT interact with MistHelper's adaptive delay system because:
- The initial POST request goes through mistapi's own HTTP session (which has its own retry logic)
- WebSocket polling is internal to the SDK and doesn't make additional REST API calls
- MistHelper's delay system only governs REST API pagination calls, not WebSocket streams

No changes needed to the adaptive delay system.

### Rationale
Separation of concerns — REST rate limiting and WebSocket streaming operate on different channels.

### Alternatives Considered
- **Integrate device_utils with adaptive delay**: Rejected — SDK handles its own HTTP retries, double-managing would cause conflicts
