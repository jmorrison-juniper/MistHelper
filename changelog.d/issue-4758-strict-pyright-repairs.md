### Strict entry-point type contracts

- **Fixed**: Correct entry-point collection, callback, session, and module-context types while preserving live calls and exports. Issue #4758.
- **Changed**: Give verified host helpers public names and update their callers, including the approved authentication-status interface. Preserve existing explicit exports. Use public firmware selectors and reject absent policy sessions before client construction. Issue #4758.
- **Removed**: Delete unused private startup helpers after caller verification. Test help, session validation, and deferred imports through their production boundaries. Issue #4758.
