# Quickstart: Complete ArangoDB Graph Edge Definitions

## Prerequisites

- Python 3.13+
- ArangoDB running (via compose.yml or standalone)
- MistHelper venv activated
- Valid `.env` with Mist API credentials and ArangoDB connection

## Verify Current State

```powershell
# Check existing graph
python -c "from arango import ArangoClient; c=ArangoClient('http://localhost:8529'); db=c.db('misthelper','root','password'); g=db.graph('mist_network_topology'); print('Edge defs:', len(g.edge_definitions())); [print(f'  {e[\"edge_collection\"]}') for e in g.edge_definitions()]"
```

## Run After Implementation

```powershell
# 1. Syntax check
python -m py_compile src/db/arango_writer.py

# 2. Run full org collection (menu 165)
python MistHelper.py --menu 165

# 3. Verify new collections exist
python -c "
from arango import ArangoClient
c = ArangoClient('http://localhost:8529')
db = c.db('misthelper', 'root', 'password')
g = db.graph('mist_network_topology')
print('Vertex collections:', sorted(g.vertex_collections()))
print('Edge collections:', [e['edge_collection'] for e in g.edge_definitions()])
"

# 4. Test graph traversal (org -> sites -> devices -> clients)
python -c "
from arango import ArangoClient
c = ArangoClient('http://localhost:8529')
db = c.db('misthelper', 'root', 'password')
cursor = db.aql.execute('''
  FOR site IN 1..1 OUTBOUND DOCUMENT('orgs', @org_key) OrgContainsSite
    FOR device IN 1..1 OUTBOUND site SiteContainsDevice
      FOR client IN 1..1 INBOUND device ClientConnectedToDevice
        LIMIT 5
        RETURN {site: site.name, device: device.name, client: client.mac}
''', bind_vars={'org_key': '<your-org-id>'})
for doc in cursor:
    print(doc)
"
```

## Key Files

| File | What Changed |
|-|-|
| `src/db/arango_writer.py` | `EDGE_DEFINITIONS`, `COLLECTION_VERTEX_MAP`, `ENTITY_TYPE_TO_VERTEX` expanded |
