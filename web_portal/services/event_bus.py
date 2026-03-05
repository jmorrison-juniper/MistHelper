"""SSE event bus for the MistHelper web portal.

Implements a publish-subscribe pattern for server-sent events.
OperationExecutor publishes events, SSE handler threads consume
via per-subscriber bounded queues.
"""

import json
import logging
import threading
import time
import uuid
from queue import Empty, Full, Queue


class PortalEventBus:
    """Publish-subscribe event bus for SSE streaming.

    Each SSE connection subscribes and receives its own Queue.
    Events are copied to all subscriber queues on publish.
    Subscriber queues are bounded to prevent memory leaks.
    """

    MAX_SUBSCRIBERS = 10
    QUEUE_MAX_SIZE = 100

    def __init__(self):
        """Initialize the event bus with empty subscriber registry."""
        self._subscribers = {}
        self._lock = threading.Lock()
        self._heartbeat_thread = None
        self._running = False

    def start(self) -> None:
        """Start the heartbeat timer thread."""
        self._running = True
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="portal-heartbeat",
        )
        self._heartbeat_thread.start()

    def stop(self) -> None:
        """Stop the heartbeat timer and clean up."""
        self._running = False
        with self._lock:
            self._subscribers.clear()

    def subscribe(self, run_id: str = None) -> str:
        """Create a new subscriber and return its unique ID."""
        with self._lock:
            if len(self._subscribers) >= self.MAX_SUBSCRIBERS:
                raise ConnectionError("Maximum SSE connections reached")
            subscriber_id = str(uuid.uuid4())
            self._subscribers[subscriber_id] = {
                "queue": Queue(maxsize=self.QUEUE_MAX_SIZE),
                "run_id": run_id,
                "created_at": time.time(),
            }
            return subscriber_id

    def unsubscribe(self, subscriber_id: str) -> None:
        """Remove a subscriber and free its queue."""
        with self._lock:
            self._subscribers.pop(subscriber_id, None)

    def publish(self, event_type: str, data: dict) -> None:
        """Publish an event to all matching subscribers."""
        event = {"type": event_type, "data": data}
        run_id = data.get("run_id")
        with self._lock:
            for sub_info in self._subscribers.values():
                if not self._matches_filter(sub_info, run_id):
                    continue
                self._enqueue_event(sub_info["queue"], event)

    def poll(self, subscriber_id: str, timeout: float = 35) -> dict:
        """Block until an event is available or timeout expires."""
        with self._lock:
            sub_info = self._subscribers.get(subscriber_id)
        if sub_info is None:
            return None
        try:
            return sub_info["queue"].get(timeout=timeout)
        except Empty:
            return None

    def _matches_filter(self, sub_info: dict, run_id: str) -> bool:
        """Check if a subscriber's filter matches the event."""
        filter_id = sub_info.get("run_id")
        if filter_id is None:
            return True
        return filter_id == run_id

    def _enqueue_event(self, queue: Queue, event: dict) -> None:
        """Add event to queue, dropping oldest if full."""
        try:
            queue.put_nowait(event)
        except Full:
            try:
                queue.get_nowait()
            except Empty:
                pass
            try:
                queue.put_nowait(event)
            except Full:
                pass

    def _heartbeat_loop(self) -> None:
        """Send heartbeat events every 30 seconds."""
        while self._running:
            time.sleep(30)
            if not self._running:
                break
            active_count = self._count_active()
            self.publish("heartbeat", {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "active_operations": active_count,
            })
            self._cleanup_stale_subscribers()

    def _count_active(self) -> int:
        """Count currently active subscribers."""
        with self._lock:
            return len(self._subscribers)

    def _cleanup_stale_subscribers(self) -> None:
        """Remove subscribers older than 1 hour."""
        cutoff = time.time() - 3600
        with self._lock:
            stale = [
                sid for sid, info in self._subscribers.items()
                if info["created_at"] < cutoff
            ]
            for sid in stale:
                del self._subscribers[sid]
                logging.info("Cleaned up stale SSE subscriber %s", sid[:8])
