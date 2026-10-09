### The container web portal starts again after a launch quoting fault

- **Fixed**: The container no longer restarts in a loop. The launch script passed the access log format without quotes, so Gunicorn stopped at start. Refs #4157.
