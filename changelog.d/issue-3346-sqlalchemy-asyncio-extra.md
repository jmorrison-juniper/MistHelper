### Fixed

- The ops platform installs `greenlet` through `sqlalchemy[asyncio]` (issue #3346). SQLAlchemy 2.1.0 does not install `greenlet` by default. Without `greenlet`, the async engine of the database does not start, and the ops platform tests stop at collection.
