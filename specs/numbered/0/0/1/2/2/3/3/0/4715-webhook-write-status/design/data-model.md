# Existing data contract

The repair adds no field, entity, table, or key strategy.
Delivery rows retain their current normalization.
The writer retains `searchOrgWebhooksDeliveries` as its operation identifier.
The writer returns `True` for success and `False` for failure.
Both `_persist` and `deliveries` retain their `None` return contract.
