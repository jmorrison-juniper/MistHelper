### Bootstrap log handler redaction

- **Security**: Filter `mistapi` and `urllib3` records at the bootstrap file and console handlers.
  Keep the existing policy for other logger names. Direct SDK console output remains outside this change.
