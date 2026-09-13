# Data Model: Quality Gate Exception Remediation

**Date**: 2026-05-07
**Purpose**: Config dataclass designs for PLR0913 refactors (Phase 2, FR-008)

No new database tables, API entities, or persistent data structures are introduced.
All entities below are in-memory Python dataclasses that replace long positional
parameter lists.

---

## Config Dataclasses

### 1. `SiteDataFetcherConfig`

**File**: `MistHelper.py` (co-located with `SiteDataFetcher` class)
**Replaces**: 6-parameter `SiteDataFetcher.__init__` at line 5626

```python
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class SiteDataFetcherConfig:
    """Configuration for a SiteDataFetcher operation."""
    fetch_function: Callable  # type: ignore[type-arg]
    filename: str
    description: str
    device_type: str = "all"
    site_id: str | None = None
    device_id: str | None = None
```

**Validation rules**: `fetch_function` must be callable; `filename` must be non-empty.
**State transitions**: Immutable after creation (dataclass, not mutated).
**Usage pattern**:
```python
config = SiteDataFetcherConfig(
    fetch_function=api.get_site_devices,
    filename="site_devices",
    description="All site devices",
)
fetcher = SiteDataFetcher(config)
```

---

### 2. `ComparisonItemConfig`

**File**: `src/inventory/csv_comparator.py` (co-located with the class)
**Replaces**: 8-parameter signatures of `_build_mismatch_item` (line 1085)
and `_build_diff_item` (line 1128) -- these functions share identical parameters.

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class ComparisonItemConfig:
    """Parameters for building a mismatch or diff report item."""
    device: dict[str, Any]
    device_serial: str
    mist_address: dict[str, str]
    comparison_address: dict[str, str]
    comparison_result: dict[str, Any]
    week_key: str
    mismatch_type: str
    validation_result: dict[str, Any] | None
```

**Validation rules**: `device_serial` must be non-empty; `week_key` must be non-empty.
**State transitions**: Immutable after creation.
**Usage pattern**:
```python
config = ComparisonItemConfig(
    device=device,
    device_serial=serial,
    mist_address=mist_addr,
    comparison_address=comp_addr,
    comparison_result=result,
    week_key=week,
    mismatch_type="address",
    validation_result=None,
)
item = self._build_mismatch_item(config)
```

---

### 3. `RoutingTableContext`

**File**: `src/network/routing_utils.py` (co-located with the class)
**Replaces**: 6-parameter signatures of `_process_routing_table_results` (line 1451)
and `_display_routing_table_output` (line 1480).

> **Implementer note on `result`**: `_display_routing_table_output` takes a `result`
> parameter (the response dict from `_process_routing_table_results`). Keep `result`
> as an explicit separate argument rather than embedding it in the context. This keeps
> the dataclass a pure input context and preserves the single-responsibility boundary
> between the two methods.

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class RoutingTableContext:
    """Shared context for routing table WebSocket operations."""
    websocket_manager: Any
    session_id: str
    device_id: str
    device_info: dict[str, Any] | None
    payload: dict[str, Any]
    debug_mode: bool
```

**State transitions**: Immutable after creation.
**Usage pattern**:
```python
context = RoutingTableContext(
    websocket_manager=ws_mgr,
    session_id=session_id,
    device_id=device_id,
    device_info=device_info,
    payload=payload,
    debug_mode=debug,
)
self._process_routing_table_results(context)
result = ...  # captured from process step
self._display_routing_table_output(context, result)
```

---

### 4. `SsrRouteQuery`

**File**: `src/network/routing_utils.py` (co-located with the class)
**Replaces**: 8-parameter signature of `_build_ssr_payload` (line 1656).

```python
from dataclasses import dataclass

@dataclass
class SsrRouteQuery:
    """User-supplied filter parameters for an SSR/SRX route query."""
    protocol_input: str
    prefix_input: str
    vrf_input: str
    neighbor_input: str
    route_direction: str
    node_input: str
    interval_input: str
    duration_input: str
```

**Validation rules**: All fields are strings; empty string is valid (means "no filter").
**State transitions**: Immutable after creation.
**Usage pattern**:
```python
query = SsrRouteQuery(
    protocol_input=protocol,
    prefix_input=prefix,
    vrf_input=vrf,
    neighbor_input=neighbor,
    route_direction=direction,
    node_input=node,
    interval_input=interval,
    duration_input=duration,
)
payload = self._build_ssr_payload(query)
```

---

### 5. `SsrRouteContext`

**File**: `src/network/routing_utils.py`
**Replaces**: Shared parameters of `_process_ssr_route_results` (line 1779)
and `_display_ssr_route_output` (line 1811).

> **Implementer note**: Read both function signatures at lines 1779 and 1811 before
> coding. Define fields to match the shared parameter subset. If the two functions
> diverge significantly, create `SsrProcessContext` and `SsrDisplayContext` as
> separate dataclasses rather than one combined type with unused fields.

```python
# Placeholder -- fields to be determined at implementation time
@dataclass
class SsrRouteContext:
    """Context for SSR route result processing and display operations."""
    # Fields: inspect lines 1779/1811 signatures before finalizing
    ...
```

---

## Unchanged Entities

The following are NOT new dataclasses -- they exist in the codebase and are referenced
for context only:

- `SiteDataFetcher` (MistHelper.py) -- the class whose `__init__` is refactored
- `CsvComparator` (csv_comparator.py) -- the class containing `_build_mismatch_item`
- `RoutingTableManager` or equivalent (routing_utils.py) -- the class containing the routing functions

No database schema changes, no new API endpoints, no new SQLite tables.
