### Strict entry-point type contracts

- **Fixed**: Correct entry-point collection, callback, session, and module-context types without removing callable declarations. Issue #4758.
- **Changed**: Give verified host helpers public names and update their callers. Preserve existing explicit exports. Use public firmware selectors and reject absent policy sessions before client construction. Issue #4758.
