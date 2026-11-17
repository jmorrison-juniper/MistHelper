# Entry-point contract

Import remains passive.
The entry point retains all 196 existing explicit exports.
Verified host helpers use public names, and every owned caller uses those names without aliases.
The mode dispatcher binds direct handlers on each invocation and retains first-match evaluation.
The previous module-level string table moves into that dispatcher.
No callable implementation is removed.
Unknown module attributes raise `AttributeError`.
Context attribute assignment and deletion retain their existing behavior.
Optional packages retain their existing availability signals.
No test sends a production Mist request or changes a device.
Tests invoke handlers only with mocked dependencies or an absent session.
