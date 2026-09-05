from src.metrics_gateway.catalog import MetricCatalog, MetricScope

cat = MetricCatalog()
for scope in MetricScope:
    items = cat.for_scope(scope)
    print(f"=== {scope} ({len(items)}) ===")
    for d in items:
        print(f"  col={d.column} name={d.name!r} kind={d.kind} scale={d.snmp_scale}")
