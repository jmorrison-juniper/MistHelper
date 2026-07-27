"""Frozen dataclass that groups thread-pool batch-worker configuration parameters.

The original ``_pool_process_batch_wait_loop`` function in ``MistHelper.py`` took 7
positional parameters which exceeded the 5-Item Rule's max-5 limit. The 4 fields
here are the configuration values that stay constant across batch iterations
(worker function, connection semaphore, thread count, batch description); the
remaining per-batch values (batch payload, batch number, total batches) stay as
direct parameters because they change every loop iteration.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/431
"""

from __future__ import annotations  # Enable PEP 604 union syntax everywhere.

import threading  # Imported for the Semaphore type used by the connection_semaphore field.
from collections.abc import Callable  # Modern home for the Callable type alias (replaces typing.Callable).
from dataclasses import dataclass  # The standard library dataclass decorator.
from typing import Any  # Type alias for the worker callable's payload items.


@dataclass(frozen=True, slots=True)
class BatchWorkerConfig:
    """Configuration values that stay constant across batches in a thread-pool batch loop."""

    worker_function: Callable[..., Any]  # Callable that processes a single batch item; takes (item, semaphore).
    connection_semaphore: threading.Semaphore  # Bound on concurrent network connections across all batches.
    max_threads: int  # Upper bound on threads the pool may spawn; passed to ThreadPoolExecutor.
    batch_description: str  # Human-readable label (for example "devices") used in tqdm + log messages.
