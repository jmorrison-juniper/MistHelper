# Request contract

Existing routes and status codes remain unchanged.
List and active requests must share the same executor after simultaneous first access.
Operation submission and event delivery occur outside the initialization lock.
Initialization exceptions propagate through existing Flask error handling.
Tests use no authenticated Mist session.
