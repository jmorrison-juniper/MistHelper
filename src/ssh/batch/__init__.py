"""Multi-host SSH batch execution package (T013c).

Concrete collaborators extracted from ``EnhancedSSHRunner``:
- :class:`src.ssh.batch.host_runner.HostRunner`                — single-host worker
- :class:`src.ssh.batch.batch_executor.BatchExecutor`          — non-interactive multi-command
- :class:`src.ssh.batch.interactive_batch_executor.InteractiveBatchExecutor` — interactive multi-step
- :class:`src.ssh.batch.multi_host_runner.MultiHostRunner`     — threaded multi-host orchestrator

NOTE: This package intentionally does NOT re-export the classes at package level
(NO façade directive — callers import the concrete module path directly).
"""
