### Observium starts on first boot

- **Fixed**: The `monitoring` profile starts Observium without a restart loop. The sensor script runs after the first-run setup creates the Observium configuration, and the sensor block tolerates a database that has no schema yet. Issue #4912.
