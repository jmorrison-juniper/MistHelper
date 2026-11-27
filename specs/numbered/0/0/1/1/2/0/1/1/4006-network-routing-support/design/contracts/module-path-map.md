# Contract: Routing Support Import Paths

This contract defines the import paths of the three moved modules. Active code and tests use these paths. No old path works after the change.

## Path Map

| Old module path | Canonical module path | Names that active code imports |
| - | - | - |
| `src.mist.networking.network._routing_utils_display` | `src.mist.networking.network.support._routing_utils_display` | `_RoutingUtilsDisplay` (imported by `routing_utils.py` line 22) |
| `src.mist.networking.network._routing_utils_parsing` | `src.mist.networking.network.support._routing_utils_parsing` | `_RoutingUtilsParsing` (imported by `routing_utils.py` line 26) |
| `src.mist.networking.network._routing_utils_payload` | `src.mist.networking.network.support._routing_utils_payload` | `_RoutingUtilsPayload` (imported by `routing_utils.py` line 27) and `RoutingPayloadQuery` (imported by `_routing_utils_routing.py` line 25) |

The unparseable-response guard imports from the payload path at line 16. Its import list stays unchanged.

## Canonical Import Statements

```python
from src.mist.networking.network.support._routing_utils_display import _RoutingUtilsDisplay
from src.mist.networking.network.support._routing_utils_parsing import _RoutingUtilsParsing
from src.mist.networking.network.support._routing_utils_payload import _RoutingUtilsPayload
from src.mist.networking.network.support._routing_utils_payload import RoutingPayloadQuery
```

## Mock and Logger Targets

```python
patch("src.mist.networking.network.support._routing_utils_payload.requests")
patch("src.mist.networking.network.support._routing_utils_display.PrettyTable")
caplog.at_level(logging.WARNING, logger="src.mist.networking.network.support._routing_utils_payload")
```

## Rules

1. A canonical path imports the module. An old path raises `ModuleNotFoundError`.
2. Module-level names stay the same. `symbol-diff` reports no change for each moved module.
3. Logger names come from `__name__`. The payload logger becomes `src.mist.networking.network.support._routing_utils_payload`.
4. The contract has no alias and no re-export at an old path.

Caution: a consumer that uses an old path fails at import time. Search each consumer before the merge. Old paths remain only in historical records and in the approved catalog move map (`tests/guardrails/test_performance_hook_catalog.py`).
