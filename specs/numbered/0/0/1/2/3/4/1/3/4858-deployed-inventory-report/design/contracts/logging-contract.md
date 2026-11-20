# Logging Contract: Structlog Frontend

## Shared Log Levels

Console threshold:
- `CONSOLE_LOG_LEVEL`
- Valid values: Python logging levels 10, 20, 30, 40, and 50.

File threshold:
- `LOGGING_LOG_LEVEL`
- Valid values: Python logging levels 10, 20, 30, 40, and 50.

## Standard Library Records

The stdlib backend keeps the timestamp, level, logger, message, and exception context.
The root logger uses the lowest needed level so each handler can apply its own threshold.

## Structlog Records

The structlog frontend adds key-value context.
It uses the same stdlib logger factory and the same console and file handlers.
It must not create a separate output stream or file.

## Handler Contract

Console handler:
- Applies `CONSOLE_LOG_LEVEL`.
- Uses the structlog console renderer.
- Enables ANSI color only for an interactive terminal.

File handler:
- Applies `LOGGING_LOG_LEVEL`.
- Uses a plain-text structlog renderer.
- Includes no required ANSI color sequence.

## Redaction Contract

The sensitive-key processor replaces credential-shaped values with `***REDACTED***`.
The existing stdlib redaction filter performs a final message and traceback check.
