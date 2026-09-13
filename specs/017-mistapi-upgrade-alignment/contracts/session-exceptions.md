# Contract: Session Exception Handling

**Purpose**: Define the error handling pattern for `mistapi.APISession` initialization after v0.59.5 exception changes.

## Current Pattern

```python
# No explicit exception handling; mistapi used sys.exit() on errors
apisession = mistapi.APISession(env_file=env_path)
# If token invalid or connection failed, process would exit
```

## Target Pattern

```python
try:
    apisession = mistapi.APISession(env_file=env_path)
except ConnectionError as error:
    logging.error("Cannot connect to Mist API: %s", error)
    print("ERROR: Cannot connect to the Mist Cloud API.")
    print("Please check your network connection and proxy settings.")
    sys.exit(1)
except ValueError as error:
    logging.error("Invalid API credentials: %s", error)
    print("ERROR: Your Mist API token is invalid or expired.")
    print("Please update your .env file with a valid token.")
    sys.exit(1)
```

## Rules

1. Always catch `ConnectionError` and `ValueError` separately for clear error messages
2. Log the technical error details at ERROR level
3. Print user-facing message (NOC engineer audience — clear, jargon-free)
4. Exit with non-zero code after logging
5. Never log the actual token value in error context
