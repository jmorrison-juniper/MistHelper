### Observium starts on first boot

- **Fixed**: Observium starts on first boot in the `monitoring` profile, with no restart loop. The sensor script runs after the first-run setup creates the Observium configuration. The sensor block also tolerates a database with no schema yet. Issue #4912.
