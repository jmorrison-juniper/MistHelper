### Strict entry-point type contracts

- **Fixed**: Correct entry-point collection, callback, session, and module-context types without removing callable declarations. Issue #4758.
- **Changed**: Declare existing externally accessed helper exports and public firmware selectors explicitly. Reject absent policy sessions before client construction. Issue #4758.
