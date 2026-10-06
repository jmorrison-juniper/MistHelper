# Request dependency contract

## Startup

The default factory stores one provider. The provider holds settings only.
Startup opens no external connection.

## Authentication

The provider reads the existing operator registry before storage access. A
missing operator or unusable Mist session causes HTTP 401.

## Construction

One authenticated request receives:

- Its borrowed Mist session
- One owned ArangoDB client
- One database gateway
- The existing audit and portal services
- One durable action repository

Flask `g` holds the graph until request teardown.

## Cleanup

Teardown closes the owned database client. It does not close the borrowed Mist
session. A partial construction failure closes the client before refusal.

## Failure

An unavailable database or service module causes HTTP 503. The response does
not contain a credential or dependency exception.

## Overrides

A configured route service wins over the provider. A complete E2E override set
returns before production provider installation.
