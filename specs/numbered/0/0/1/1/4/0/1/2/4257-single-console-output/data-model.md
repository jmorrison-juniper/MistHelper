# Console routing data model

No persistent data model changes.

The existing log record retains its logger name, level, message template, and arguments.
The console handler rejects the helper's logger name.
The file handler receives the unchanged record when its level permits INFO.
