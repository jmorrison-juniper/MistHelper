# Entry-point contract

Import remains passive.
The entry point retains every existing module-level declaration.
Dynamic dispatch resolves current attributes so monkeypatches and injected dependencies remain effective.
Unknown module attributes raise `AttributeError`.
Context attribute assignment and deletion retain their existing behavior.
Optional packages retain their existing availability signals.
No test sends a production Mist request or changes a device.
Tests invoke handlers only with mocked dependencies or an absent session.
