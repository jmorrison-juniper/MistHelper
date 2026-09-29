# Deferred Wiring: Subscription Contract Expiry Report

This file records integration work that is intentionally deferred. Do not
implement these items in the report package branch.

## Deferred integration items

1. Add menu 271 to `MistHelper.py`.
2. Add menu 271 metadata to `OperationRegistry`.
3. Update `README.md` operation counts and the menu table.
4. Regenerate the menu wiki with `python scripts\generate_menu_wiki.py`.
5. Regenerate the menu API map with `python -m scripts.menu_api_map`.
6. Add primary key strategies for the new output sources when the integration
   branch adds the new operation.
7. Add the release note fragment for the user-visible menu operation.

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
