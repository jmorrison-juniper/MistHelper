# Data model

The application retains `OPERATION_EXECUTOR` in its existing configuration.
Its state changes from absent to one complete executor.
An exception leaves it absent and permits a later retry.
Separate applications retain separate values.
No persistent data or schema changes.
