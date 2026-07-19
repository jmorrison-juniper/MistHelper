#!/usr/bin/env python3
"""
Mist Ideas Scraper - HTTP Receiver Server

Accepts scraped idea data from the VS Code browser and saves it to CSV.
Provides resume capability so interrupted scrapes can continue where they left off.

Usage:
    python scripts/mist_scraper_receiver.py

Endpoints:
    GET  /done        - Returns newline-separated list of already-processed URLs
    GET  /all_urls    - Returns newline-separated list of all known idea URLs
    GET  /status      - Returns JSON progress report
    POST /save_urls   - Accepts JSON array of all idea URLs (Phase 1 output)
    POST /save        - Accepts one complete idea JSON object (Phase 2 per-idea save)
"""

import csv
import json
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

# Boilerplate strings injected by UserVoice around/after descriptions.
# Include both straight-apostrophe and curly-apostrophe (U+2019) variants
# because UserVoice renders the curly form which won't match a straight quote.
BOILERPLATE_LINES = frozenset(
    [
        "Please sign in to leave feedback",
        "We'll send you updates on this idea",
        "We\u2019ll send you updates on this idea",
        "Signing you in. Just a sec...",
        "Thanks for the feedback!",
        "We\u2019ll send you updates on this idea.",
        "We'll send you updates on this idea.",
    ]
)


def extract_idea_id_from_url(url: str) -> str:
    """Extract the real idea numeric ID from the URL path segment."""
    match = re.search(r"/suggestions/(\d+)-", url)
    return match.group(1) if match else ""


def clean_description(text: str) -> str:
    """Strip UserVoice boilerplate lines from description text."""
    lines = text.splitlines()
    cleaned = [line for line in lines if line.strip() not in BOILERPLATE_LINES]
    return "\n".join(cleaned).strip()


DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "mist_ideas.csv"
DONE_URLS_PATH = DATA_DIR / "mist_ideas_done_urls.txt"
ALL_URLS_PATH = DATA_DIR / "mist_ideas_all_urls.txt"
PORT = 8099

CSV_HEADERS = [
    "idea_id",
    "url",
    "title",
    "description_full",
    "votes",
    "comments_count",
    "category",
    "status",
    "submitter",
    "submitter_url",
    "submit_date",
    "tags",
    "comments_json",
]

write_lock = threading.Lock()


def load_done_urls() -> set:
    if not DONE_URLS_PATH.exists():
        return set()
    return set(DONE_URLS_PATH.read_text(encoding="utf-8").strip().split("\n")) - {""}


def append_done_url(url: str) -> None:
    with DONE_URLS_PATH.open("a", encoding="utf-8") as file_handle:
        file_handle.write(url + "\n")


def ensure_csv_headers() -> None:
    if not CSV_PATH.exists():
        # utf-8-sig writes a BOM so Excel opens the file without garbled characters
        with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as file_handle:
            csv.DictWriter(file_handle, fieldnames=CSV_HEADERS).writeheader()


def append_csv_row(row: dict) -> None:
    # utf-8-sig keeps the BOM intact for Excel; append mode is safe after initial header write
    with CSV_PATH.open("a", newline="", encoding="utf-8-sig") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=CSV_HEADERS, extrasaction="ignore")
        writer.writerow(row)


def load_all_urls() -> list:
    if not ALL_URLS_PATH.exists():
        return []
    return [u for u in ALL_URLS_PATH.read_text(encoding="utf-8").strip().split("\n") if u]


class ScraperHandler(BaseHTTPRequestHandler):

    def log_message(self, format_str, *args):
        print(f"[{self.address_string()}] {format_str % args}", flush=True)

    def _add_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(200)
        self._add_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        route_map = {
            "/done": self._handle_get_done,
            "/all_urls": self._handle_get_all_urls,
            "/status": self._handle_get_status,
        }
        handler = route_map.get(parsed.path)
        if handler:
            handler()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_get_done(self):
        content = DONE_URLS_PATH.read_text(encoding="utf-8") if DONE_URLS_PATH.exists() else ""
        self._send_text(content)

    def _handle_get_all_urls(self):
        content = ALL_URLS_PATH.read_text(encoding="utf-8") if ALL_URLS_PATH.exists() else ""
        self._send_text(content)

    def _handle_get_status(self):
        done_count = len(load_done_urls())
        all_urls = load_all_urls()
        total_count = len(all_urls)
        data = json.dumps(
            {
                "done": done_count,
                "total": total_count,
                "pending": max(0, total_count - done_count),
                "csv_path": str(CSV_PATH),
            }
        )
        self._send_text(data, content_type="application/json")

    def _send_text(self, content: str, content_type: str = "text/plain"):
        encoded = content.encode("utf-8")
        self.send_response(200)
        self._add_cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        route_map = {
            "/save_urls": self._handle_save_urls,
            "/save": self._handle_save_idea,
        }
        handler = route_map.get(parsed.path)
        if handler:
            handler(body)
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_save_urls(self, body: bytes):
        try:
            urls = json.loads(body)
            with write_lock:
                with ALL_URLS_PATH.open("w", encoding="utf-8") as file_handle:
                    file_handle.write("\n".join(urls))
            count = len(urls)
            print(f"[SERVER] Saved {count} total idea URLs to {ALL_URLS_PATH}", flush=True)
            self._respond_ok(f"Saved {count} URLs")
        except Exception as exc:
            print(f"[SERVER] Error saving URLs: {exc}", flush=True)
            self._respond_error(str(exc))

    def _handle_save_idea(self, body: bytes):
        try:
            row = json.loads(body)
            url = row.get("url", "")

            # Always derive idea_id from the URL — overrides broken client-side extraction
            row["idea_id"] = extract_idea_id_from_url(url)

            # Strip boilerplate from description
            if "description_full" in row:
                row["description_full"] = clean_description(row["description_full"])

            with write_lock:
                done = load_done_urls()
                if url in done:
                    self._respond_ok("SKIPPED (already done)")
                    return
                append_csv_row(row)
                append_done_url(url)
                done_count = len(load_done_urls())
            total = len(load_all_urls())
            title_short = row.get("title", "")[:60]
            print(f"[SERVER] [{done_count}/{total}] {title_short}", flush=True)
            self._respond_ok(f"Saved row {done_count}")
        except Exception as exc:
            print(f"[SERVER] Error saving idea: {exc}", flush=True)
            self._respond_error(str(exc))

    def _respond_ok(self, msg: str = "OK"):
        encoded = msg.encode("utf-8")
        self.send_response(200)
        self._add_cors_headers()
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _respond_error(self, msg: str):
        encoded = msg.encode("utf-8")
        self.send_response(500)
        self._add_cors_headers()
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main():
    DATA_DIR.mkdir(exist_ok=True)
    ensure_csv_headers()
    server = HTTPServer(("127.0.0.1", PORT), ScraperHandler)
    done_count = len(load_done_urls())
    total_count = len(load_all_urls())
    print(f"[SERVER] Mist Ideas Scraper Receiver starting on http://localhost:{PORT}")
    print(f"[SERVER] CSV output: {CSV_PATH}")
    print(f"[SERVER] Progress: {done_count}/{total_count} ideas already scraped")
    print(f"[SERVER] Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Stopping...", flush=True)
        server.shutdown()


if __name__ == "__main__":
    main()
