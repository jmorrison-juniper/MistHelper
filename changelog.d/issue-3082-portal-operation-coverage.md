### The operations dashboard lists every safe operation

- **Fixed**: The operations dashboard listed 86 operations while
  `OperationRegistry` called 165 of them safe to run. A second gate compared the
  menu number against 90, and a menu number states when an operation was added,
  not what the operation does. That bound hid 79 operations, and a new safe
  operation above it never appeared. The registry verdict now decides alone, and
  a guard fails when a numeric bound returns. Issue #3082.
- **Fixed**: The site dropdown, the device dropdown, and the client dropdown
  listed their entries in the order the Mist API returned them. Each list now
  reads in the order of the label the page shows, without regard to letter case.
  An entry with no label sorts last and stays reachable. The wireless clients
  and the wired clients interleave by name instead of forming two blocks. Issue
  #3083.
- **Added**: `scripts/generate_portal_menu_registry.py` rewrites the static
  description map from the menu titles and the registry, so the fallback list
  cannot drift again. Issue #3082.
