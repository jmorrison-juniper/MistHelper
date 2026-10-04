"""Multi-host SSH batch execution package (T013c).

Concrete collaborators extracted from ``EnhancedSSHRunner``:
- :class:`src.operations.execution.ssh.batch.host_runner.HostRunner`                — single-host worker
- :class:`src.operations.execution.ssh.batch.batch_executor.BatchExecutor`          — non-interactive multi-command
- :class:`src.operations.execution.ssh.batch.interactive_batch_executor.InteractiveBatchExecutor`
  provides interactive multi-step execution.
- :class:`src.operations.execution.ssh.batch.multi_host_runner.MultiHostRunner`     — threaded multi-host orchestrator

NOTE: This package intentionally does NOT re-export the classes at package level
(NO façade directive — callers import the concrete module path directly).
"""
