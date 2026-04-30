"""
Standalone Playwright scraper for ideas.mist.com.

Reads URLs from data/mist_ideas_all_urls.txt (3053 URLs).
Writes CSV via the receiver server at localhost:8099.
Supports resume via done_urls tracking.

Usage:
    1. Start server: python scripts/mist_scraper_receiver.py
    2. Run scraper:  python scripts/mist_ideas_scraper_standalone.py
"""
import csv
import json
import logging
import re
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scraper")

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ALL_URLS_FILE = DATA_DIR / "mist_ideas_all_urls.txt"
CSV_FILE = DATA_DIR / "mist_ideas.csv"
DONE_FILE = DATA_DIR / "mist_ideas_done_urls.txt"

SERVER = "http://localhost:8099"

# ── CSV headers (match server) ────────────────────────────────
HEADERS = [
    "idea_id", "url", "title", "description_full", "votes",
    "comments_count", "category", "status", "submitter",
    "submitter_url", "submit_date", "tags", "comments_json",
]


class MistIdeasScraper:
    """Scrapes idea pages from ideas.mist.com using Playwright."""

    def __init__(self):
        self.saved = 0
        self.errors = 0
        self.skipped = 0
        self.empty_desc = 0

    # ── URL management ────────────────────────────────────────
    def load_urls(self):
        """Load all URLs and done URLs, return remaining."""
        all_urls = ALL_URLS_FILE.read_text(encoding="utf-8").strip().splitlines()
        all_urls = [u.strip() for u in all_urls if u.strip()]

        done_set = set()
        if DONE_FILE.exists():
            done_set = set(DONE_FILE.read_text(encoding="utf-8").strip().splitlines())

        remaining = [u for u in all_urls if u not in done_set]
        logger.info("Total: %d, Done: %d, Remaining: %d", len(all_urls), len(done_set), len(remaining))
        return remaining

    def mark_done(self, url):
        """Append URL to done file."""
        with open(DONE_FILE, "a", encoding="utf-8") as file_handle:
            file_handle.write(url + "\n")

    # ── Extraction ────────────────────────────────────────────
    def extract_idea_id(self, url):
        """Extract numeric idea ID from URL."""
        match = re.search(r"/suggestions/(\d+)", url)
        return match.group(1) if match else ""

    def extract_data(self, page, url):
        """Extract all idea data from the current page."""
        return page.evaluate("""() => {
            const titleEl = document.querySelector('h1.uvIdeaTitle');
            const title = titleEl ? titleEl.textContent.trim() : '';

            const descEl = document.querySelector('.uvIdeaDescription .typeset');
            const description = descEl ? descEl.textContent.trim() : '';

            const votesText = document.querySelector('.uvIdeaVoteCount')?.textContent || '';
            const votes = parseInt(votesText.match(/\\d+/)?.[0] || '0');

            // Status: use the specific badge span, not the whole section
            const statusSpan = document.querySelector('.uvStyle-status');
            const status = statusSpan ? statusSpan.textContent.trim() : '';

            // Category: first category_id link text
            const catLink = document.querySelector('a[href*="category_id"]');
            const category = catLink ? catLink.textContent.trim() : '';

            const firstUser = document.querySelector('a[href*="/users/"]');
            const submitter = firstUser ? firstUser.textContent.trim() : '';
            const submitterUrl = firstUser ? firstUser.href : '';

            const submitDate = (document.querySelector('time')?.textContent || '').trim();

            const tagEls = document.querySelectorAll('.uvTag, .uvIdeaTag, [class*="tag"]');
            const tags = Array.from(tagEls).map(el => el.textContent.trim()).filter(Boolean).join('|');

            const commentArticles = document.querySelectorAll('article.uvUserAction-comment');
            const comments = Array.from(commentArticles).map(article => ({
                author: (article.querySelector('a[href*="/users/"]')?.textContent || '').trim(),
                date: (article.querySelector('time')?.textContent || '').trim(),
                body: (article.querySelector('.typeset')?.textContent || '').trim(),
            }));

            return {
                title, description, votes, status, category,
                submitter, submitterUrl, submitDate, tags, comments,
                currentUrl: window.location.href,
            };
        }""")

    def validate_page(self, page, expected_id):
        """Check that the loaded page matches the expected idea ID."""
        current_url = page.url
        current_id_match = re.search(r"/suggestions/(\d+)", current_url)
        current_id = current_id_match.group(1) if current_id_match else ""
        return current_id == expected_id

    # ── Save data ─────────────────────────────────────────────
    def save_to_csv(self, row):
        """Append a row directly to CSV (no server needed)."""
        file_exists = CSV_FILE.exists() and CSV_FILE.stat().st_size > 0
        with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as file_handle:
            writer = csv.DictWriter(file_handle, fieldnames=HEADERS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    # ── Main scrape loop ──────────────────────────────────────
    def scrape_all(self):
        """Main scraping loop using Playwright."""
        from playwright.sync_api import sync_playwright

        remaining = self.load_urls()
        if not remaining:
            logger.info("All URLs already scraped!")
            return

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                ignore_https_errors=True,
            )
            page = context.new_page()

            for index, idea_url in enumerate(remaining):
                idea_id = self.extract_idea_id(idea_url)
                if not idea_id:
                    logger.warning("Skip (no ID): %s", idea_url)
                    self.skipped += 1
                    continue

                try:
                    self.scrape_one(page, idea_url, idea_id, index, len(remaining))
                except Exception as error:
                    self.errors += 1
                    logger.error("[%d/%d] ERROR %s: %s", index + 1, len(remaining), idea_url[:60], str(error)[:100])

                # Brief delay to avoid rate limiting
                if (index + 1) % 50 == 0:
                    time.sleep(2)

            browser.close()

        logger.info("DONE. Saved=%d, Errors=%d, Skipped=%d, EmptyDesc=%d",
                     self.saved, self.errors, self.skipped, self.empty_desc)

    def scrape_one(self, page, idea_url, idea_id, index, total):
        """Scrape a single idea page with URL validation."""
        # Navigate with retry
        for attempt in range(3):
            try:
                page.goto(idea_url, wait_until="load", timeout=20000)
            except Exception:
                page.wait_for_timeout(2000)

            # Wait for votes to render (signals content loaded)
            try:
                page.wait_for_function(
                    r"() => /\d/.test(document.querySelector('.uvIdeaVoteCount')?.textContent || '')",
                    timeout=8000,
                )
            except Exception:
                page.wait_for_timeout(2000)

            # Validate URL matches expected idea
            if self.validate_page(page, idea_id):
                break
            elif attempt < 2:
                logger.warning("URL mismatch attempt %d for %s, retrying...", attempt + 1, idea_id)
                page.goto("about:blank", wait_until="commit", timeout=5000)
                page.wait_for_timeout(500)
        else:
            # After 3 attempts, check one more time
            if not self.validate_page(page, idea_id):
                logger.warning("SKIP (URL mismatch after 3 tries): %s", idea_id)
                self.skipped += 1
                self.mark_done(idea_url)
                return

        # Extract data
        data = self.extract_data(page, idea_url)

        # Build CSV row
        row = {
            "idea_id": idea_id,
            "url": idea_url,
            "title": data.get("title", ""),
            "description_full": data.get("description", ""),
            "votes": str(data.get("votes", 0)),
            "comments_count": str(len(data.get("comments", []))),
            "category": data.get("category", ""),
            "status": data.get("status", ""),
            "submitter": data.get("submitter", ""),
            "submitter_url": data.get("submitterUrl", ""),
            "submit_date": data.get("submitDate", ""),
            "tags": data.get("tags", ""),
            "comments_json": json.dumps(data.get("comments", []), ensure_ascii=False),
        }

        self.save_to_csv(row)
        self.mark_done(idea_url)
        self.saved += 1

        if not data.get("description", "").strip():
            self.empty_desc += 1

        # Log progress
        if self.saved % 25 == 0 or self.saved <= 5:
            title_preview = row["title"][:50]
            logger.info("[%d/%d] id=%s votes=%s desc=%dch title=%s",
                        self.saved, total, idea_id, row["votes"],
                        len(row["description_full"]), title_preview)


if __name__ == "__main__":
    scraper = MistIdeasScraper()
    scraper.scrape_all()
