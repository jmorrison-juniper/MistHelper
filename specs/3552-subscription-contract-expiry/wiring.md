# Wiring manifest

## Menu entries

| menu | title | handler import | handler attribute | category | skip_reason | destructive | supports_fast |
| - | - | - | - | - | - | - | - |
| 271 | Export the subscription and contract expiry report | src.reports.subscription_expiry.operation | SubscriptionExpiryReport.run | safe |  | False | False |

## OperationRegistry comment

`# WHY: Menu 271 reads only organization subscription, license usage, and JSI contract data, then writes two local reports. It changes no Mist object, sends no update request, and needs no operator prompt, because it resolves the organization from the cache or the environment.`

## Primary key strategies

```python
"SubscriptionExpiryReport": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "indexes": ["subscription_type", "status", "band"],
    "unique_constraints": [],
    "description": "Subscription expiry score report rows",
},
"ContractExpiryReport": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "indexes": ["serial", "model", "contract_status", "contract_state", "bucket"],
    "unique_constraints": [],
    "description": "Contract expiry score report rows",
},
```

## copilot-instructions category table

The `safe` category row gains menu 271.

## Import line for MistHelper.py

`from src.reports.subscription_expiry.operation import SubscriptionExpiryReport  # Menu 271 (issue #3552) -- subscription and contract expiry report.`

## Deferred integration items

1. Add menu 271 to `MistHelper.py`.
2. Add menu 271 metadata to `OperationRegistry`.
3. Add the primary key strategies above to `src/refactors/endpoint_primary_key_strategies.py`.
4. Update `README.md` operation counts and the menu table.
5. Regenerate the menu wiki with `python scripts\generate_menu_wiki.py`.
6. Regenerate the menu API map with `python -m scripts.menu_api_map`.

## Required run handler

The integration branch must call:

```python
SubscriptionExpiryReport.run()
```

The run handler accepts no positional argument. It must resolve context through
`SourceDependencyResolver`, matching menus 269 and 270.

## Source package boundary

Implementation work belongs under:

```text
src/reports/subscription_expiry/
```

Unit tests belong under:

```text
tests/unit/reports/subscription_expiry/
```

## Integration proof

The wiring branch must prove these outcomes:

1. Menu 271 appears in the operation registry.
2. Menu 271 appears in generated menu references.
3. The README count includes the new operation.
4. The run handler creates both required CSV files.
5. The console summary prints every required band and bucket.
