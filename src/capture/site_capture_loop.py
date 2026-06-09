"""Site packet capture loop runner orchestrator."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class SiteCaptureLoopRunner:
    """Run continuous site capture loops by delegating steps to PacketCaptureManager helpers."""

    manager: Any

    def run(self, site_id: str, payload: dict[str, Any]) -> None:
        """Execute loop mode with download-first and start-capture cycle."""
        iteration = 0
        last_capture_time: float | None = None
        min_interval = payload.get("duration", 60)
        download_folder = os.path.join(os.getcwd(), "data")
        self.manager._print_loop_banner(payload)
        try:
            while True:
                iteration += 1
                loop_start = time.time()
                print(f"\n{'=' * 60}\nLoop Iteration #{iteration}\n{'=' * 60}")
                completed = self.manager._fetch_completed_pcaps(site_id, iteration)
                self.manager._download_pending_pcaps(completed, download_folder)
                wait_time = self.manager._check_capture_readiness(last_capture_time, min_interval)
                if wait_time == 0:
                    capture_time = self.manager._attempt_loop_capture(site_id, payload, iteration)
                    if capture_time is not None:
                        last_capture_time = capture_time
                sleep_time = self.manager._calc_loop_sleep(wait_time, time.time() - loop_start)
                print(f"\n{'=' * 60}\nLoop iteration #{iteration} complete")
                print(f"Waiting {sleep_time:.0f} seconds before next check...\n{'=' * 60}\n")
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            print(f"\n\n{'=' * 80}\n LOOP MODE INTERRUPTED BY USER\n{'=' * 80}")
            print(f"  Completed {iteration} loop iteration(s)")
            print("  All available PCAPs have been downloaded\n  Exiting gracefully...")
            self.manager._log_loop_stop(iteration)
