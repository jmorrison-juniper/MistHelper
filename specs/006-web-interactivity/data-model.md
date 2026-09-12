# Data Model: Web Portal Interactivity

**Feature**: 006-web-interactivity  
**Date**: 2026-03-04

## Entities

### ParameterDefinition

Describes a single input that an interactive operation requires.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | str | Yes | Machine-readable identifier (e.g., `site_id`, `device_mac`) |
| `label` | str | Yes | Human-readable label for form control |
| `param_type` | str | Yes | One of: `site`, `device`, `client`, `choice`, `text`, `number` |
| `required` | bool | Yes | Whether the field must be filled before execution |
| `depends_on` | str | No | Name of another parameter this depends on (e.g., device depends on site) |
| `device_filter` | str | No | Device type filter when `param_type=device`: `ap`, `switch`, `gateway`, `all` |
| `options` | list[dict] | No | Static options for `choice` type: `[{"value": "1", "label": "Wireless"}]` |
| `default` | str | No | Default value pre-filled in the form |
| `placeholder` | str | No | Placeholder text for text/number inputs |
| `min_value` | int | No | Minimum value for `number` type |
| `max_value` | int | No | Maximum value for `number` type |

**Validation rules**:
- `param_type` must be one of the six defined types
- `depends_on` must reference an existing parameter `name` in the same operation
- `options` required when `param_type=choice`
- `device_filter` only valid when `param_type=device`

### OperationParameterSet

Maps an operation to its required parameters.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `menu_number` | str | Yes | Menu operation number |
| `description` | str | Yes | Human-readable operation description |
| `category` | str | Yes | One of: `non_interactive`, `interactive`, `cli_only` |
| `parameters` | list[ParameterDefinition] | Yes | Ordered list of parameters (may be empty for non-interactive) |
| `cli_only_message` | str | No | Message shown for CLI-only operations |

### InputQueue (Runtime)

Thread-local state for input interception.

| Field | Type | Description |
|-------|------|-------------|
| `input_queue` | deque[str] | Ordered answers to feed to `input()` calls |

**State transitions**: `None` (no queue) → `deque([...])` (queue loaded) → consumed item by item → `None` (cleared in finally)

### PreviewState (Frontend)

Client-side state for the modal preview component.

| Field | Type | Description |
|-------|------|-------------|
| `currentPath` | str | File path being previewed |
| `currentPage` | int | Current pagination page |
| `perPage` | int | Rows per page (default 50) |
| `searchQuery` | str | Active search filter |
| `sortColumn` | int | Column index being sorted (-1 = none) |
| `sortAscending` | bool | Sort direction |
| `fileType` | str | Type of file being previewed (csv/json/log/sqlite) |
| `sqliteTable` | str | Selected SQLite table name (if applicable) |

## Relationships

```
OperationParameterSet 1 ──── * ParameterDefinition
     │
     │ category="interactive"
     │
     └── parameters[].depends_on ──→ parameters[].name
                                      (within same set)
```

**Dependency chain example** (Menu 33 — Site device VC info):
```
site_id (param_type=site, required=true)
  └── device_id (param_type=device, depends_on=site_id, device_filter=switch, required=true)
```

## Parameter Registry Examples

### Simple: Site-only (Menu 31)
```python
"31": {
    "category": "interactive",
    "parameters": [
        {"name": "site_id", "label": "Site", "param_type": "site", "required": True}
    ]
}
```

### Dependent: Site + Device (Menu 72)
```python
"72": {
    "category": "interactive",
    "parameters": [
        {"name": "site_id", "label": "Site", "param_type": "site", "required": True},
        {"name": "device_id", "label": "Device", "param_type": "device",
         "required": True, "depends_on": "site_id", "device_filter": "all"}
    ]
}
```

### Complex: Packet Capture (Menu 9, sub-type 1)
```python
"9": {
    "category": "interactive",
    "parameters": [
        {"name": "capture_type", "label": "Capture Type", "param_type": "choice",
         "required": True, "options": [
             {"value": "1", "label": "Wireless Client"},
             {"value": "2", "label": "Wired Client"},
             {"value": "3", "label": "Gateway"},
             {"value": "4", "label": "Switch"},
             {"value": "5", "label": "New Association"},
             {"value": "6", "label": "Scan Radio"}
         ]},
        {"name": "site_id", "label": "Site", "param_type": "site", "required": True},
        {"name": "device_mac", "label": "Device MAC", "param_type": "device",
         "required": False, "depends_on": "site_id", "device_filter": "ap"},
        {"name": "client_mac", "label": "Client MAC", "param_type": "text",
         "required": False, "placeholder": "e.g., aa:bb:cc:dd:ee:ff"},
        {"name": "duration", "label": "Duration (seconds)", "param_type": "number",
         "required": False, "default": "60", "min_value": 10, "max_value": 300},
        {"name": "num_packets", "label": "Packet Count", "param_type": "number",
         "required": False, "default": "100", "min_value": 1, "max_value": 10000},
        {"name": "max_pkt_len", "label": "Max Packet Length", "param_type": "number",
         "required": False, "default": "128", "min_value": 64, "max_value": 1500},
        {"name": "includes_mcast", "label": "Include Multicast", "param_type": "choice",
         "required": False, "default": "n", "options": [
             {"value": "y", "label": "Yes"},
             {"value": "n", "label": "No"}
         ]}
    ]
}
```

### CLI-Only: Menu 79
```python
"79": {
    "category": "cli_only",
    "parameters": [],
    "cli_only_message": "Interactive CLI shell requires persistent keyboard input. Use SSH access on port 2200."
}
```
