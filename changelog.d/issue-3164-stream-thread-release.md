### Fixed

- The portal event stream now closes itself after a fixed time, and it refuses
  an unknown run identifier. One open stream held one Gunicorn worker thread
  for the whole life of a browser tab. Four open tabs took every thread, and
  the portal stopped answering. The thread pool also grew from 4 to 24, and
  `PORTAL_THREADS` and `PORTAL_STREAM_MAX_SECONDS` now tune both limits.
  Issue #3164.
