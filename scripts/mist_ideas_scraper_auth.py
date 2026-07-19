"""
Authenticated Playwright scraper for ideas.mist.com.

The forum is PRIVATE — requires Mist SSO login. This script:
  1. Opens a headed browser for manual SSO login (one-time)
  2. Saves cookies to data/mist_ideas_auth.json
  3. Scrapes all 3053 idea pages using stored auth

Reads URLs from data/mist_ideas_all_urls.txt.
Writes to data/mist_ideas.csv with resume support.

Usage:
    # First time (login):
    python scripts/mist_ideas_scraper_auth.py --login

    # Scrape (uses saved cookies):
    python scripts/mist_ideas_scraper_auth.py
"""

import argparse
import csv
import json
import logging
import re
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("auth_scraper")

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ALL_URLS_FILE = DATA_DIR / "mist_ideas_all_urls.txt"
CSV_FILE = DATA_DIR / "mist_ideas.csv"
DONE_FILE = DATA_DIR / "mist_ideas_done_urls.txt"
AUTH_FILE = DATA_DIR / "mist_ideas_auth.json"

FORUM_URL = "https://ideas.mist.com/forums/912934-product-features"

# ── CSV headers ───────────────────────────────────────────────
HEADERS = [
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

# ── Boilerplate to strip ─────────────────────────────────────
BOILERPLATE_LINES = frozenset(
    [
        "Submitted ideas will be reviewed and responded to by our Product team.",
        "Submitted ideas will be reviewed and responded to by our Product team.\u2019",
        "Please do not submit cases here.",
        "Please do not submit support cases here.",
        "All feature requests will be evaluated on the basis of demand (votes), technical feasibility, strategic alignment, and other factors.",
        "All feature requests will be evaluated on the basis of demand (votes), technical feasibility, strategic alignment, and other factors.\u2019",
    ]
)


def do_login():
    """Open headed browser for manual Mist SSO login, save cookies."""
    from playwright.sync_api import sync_playwright

    logger.info("Opening browser for login...")
    logger.info("1. Click the 'Mist' SSO button")
    logger.info("2. Log in with your Mist credentials")
    logger.info("3. Wait until the forum page loads with ideas")
    logger.info("4. The script will auto-detect login success")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.goto(FORUM_URL, wait_until="load", timeout=60000)

        logger.info("Browser open. Log in now...")
        logger.info("Waiting for successful login (detecting idea content)...")

        # Poll for login success: body class changes from access-denied
        max_wait_seconds = 300
        for elapsed in range(max_wait_seconds):
            time.sleep(1)
            try:
                body_class = page.evaluate("() => document.body.className")
                if "access-denied" not in body_class:
                    # Check for actual idea content
                    has_content = page.evaluate(
                        "() => document.querySelectorAll('.uvIdeaTitle, .uvIdeaList, .uvIdeaListItem').length > 0"
                    )
                    if has_content:
                        logger.info("Login detected! Forum content visible.")
                        break
            except Exception:
                pass  # Page may be navigating

            if elapsed % 30 == 0 and elapsed > 0:
                logger.info("Still waiting for login... (%ds)", elapsed)
        else:
            logger.warning("Timeout waiting for login. Saving cookies anyway.")

        # Give extra time for all cookies to settle
        time.sleep(2)

        # Save auth state
        context.storage_state(path=str(AUTH_FILE))
        logger.info("Auth saved to %s", AUTH_FILE)
        browser.close()

    logger.info("Login complete. Now run without --login to scrape.")


class AuthenticatedScraper:
    """Scrapes ideas.mist.com with saved authentication cookies."""

    def __init__(self):
        self.saved = 0
        self.errors = 0
        self.skipped = 0
        self.empty_desc = 0

    def load_urls(self):
        """Load all URLs and done URLs, return remaining."""
        all_urls = ALL_URLS_FILE.read_text(encoding="utf-8").strip().splitlines()
        all_urls = [url.strip() for url in all_urls if url.strip()]

        done_set = set()
        if DONE_FILE.exists():
            done_set = set(DONE_FILE.read_text(encoding="utf-8").strip().splitlines())

        remaining = [url for url in all_urls if url not in done_set]
        logger.info("Total: %d, Done: %d, Remaining: %d", len(all_urls), len(done_set), len(remaining))
        return remaining

    def mark_done(self, url):
        """Append URL to done file."""
        with open(DONE_FILE, "a", encoding="utf-8") as fh:
            fh.write(url + "\n")

    def extract_idea_id(self, url):
        """Extract numeric idea ID from URL."""
        match = re.search(r"/suggestions/(\d+)", url)
        return match.group(1) if match else ""

    def clean_description(self, text):
        """Remove boilerplate from description."""
        if not text:
            return ""
        lines = text.strip().splitlines()
        cleaned = [line for line in lines if line.strip() not in BOILERPLATE_LINES]
        return "\n".join(cleaned).strip()

    def extract_data(self, page):
        """Extract all idea data from the current page via JS."""
        return page.evaluate(
            """() => {
            const title_element = document.querySelector('h1.uvIdeaTitle');
            const title = title_element ? title_element.textContent.trim() : '';

            const desc_element = document.querySelector('.uvIdeaDescription .typeset');
            const description = desc_element ? desc_element.textContent.trim() : '';

            const votes_text = document.querySelector('.uvIdeaVoteCount')?.textContent || '';
            const votes_match = votes_text.match(/\\d+/);
            const votes = votes_match ? parseInt(votes_match[0]) : 0;

            const status_span = document.querySelector('.uvStyle-status');
            const status = status_span ? status_span.textContent.trim() : '';

            const cat_link = document.querySelector('a[href*="category_id"]');
            const category = cat_link ? cat_link.textContent.trim() : '';

            const first_user = document.querySelector('a[href*="/users/"]');
            const submitter = first_user ? first_user.textContent.trim() : '';
            const submitter_url = first_user ? first_user.href : '';

            const submit_date = (document.querySelector('time')?.textContent || '').trim();

            const tag_elements = document.querySelectorAll('.uvTag, .uvIdeaTag');
            const tags = Array.from(tag_elements)
                .map(element => element.textContent.trim())
                .filter(Boolean)
                .join('|');

            const comment_articles = document.querySelectorAll('article.uvUserAction-comment');
            const comments = Array.from(comment_articles).map(article => ({
                author: (article.querySelector('a[href*="/users/"]')?.textContent || '').trim(),
                date: (article.querySelector('time')?.textContent || '').trim(),
                body: (article.querySelector('.typeset')?.textContent || '').trim(),
            }));

            return {
                title, description, votes, status, category,
                submitter, submitter_url, submit_date, tags, comments,
                current_url: window.location.href,
            };
        }"""
        )

    def save_to_csv(self, row):
        """Append a row to CSV."""
        file_exists = CSV_FILE.exists() and CSV_FILE.stat().st_size > 0
        with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=HEADERS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    def scrape_all(self):
        """Main scraping loop with auth cookies."""
        from playwright.sync_api import sync_playwright

        if not AUTH_FILE.exists():
            logger.error("No auth file found! Run with --login first.")
            sys.exit(1)

        remaining = self.load_urls()
        if not remaining:
            logger.info("All URLs already scraped!")
            return

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                storage_state=str(AUTH_FILE),
                ignore_https_errors=True,
            )
            page = context.new_page()

            # Verify auth works
            if not self.verify_auth(page):
                browser.close()
                sys.exit(1)

            for index, url in enumerate(remaining):
                idea_id = self.extract_idea_id(url)
                if not idea_id:
                    logger.warning("Skip (no ID): %s", url)
                    self.skipped += 1
                    continue

                try:
                    self.scrape_one(page, url, idea_id, index, len(remaining))
                except Exception as error:
                    self.errors += 1
                    logger.error("[%d/%d] ERROR %s: %s", index + 1, len(remaining), url[:60], str(error)[:120])
                    self.mark_done(url)

                # Polite delay
                if (index + 1) % 20 == 0:
                    time.sleep(1)

            browser.close()

        logger.info(
            "DONE. Saved=%d Errors=%d Skipped=%d EmptyDesc=%d", self.saved, self.errors, self.skipped, self.empty_desc
        )

    def verify_auth(self, page):
        """Verify auth cookies work by loading the forum page."""
        logger.info("Verifying authentication...")
        page.goto(FORUM_URL, wait_until="load", timeout=30000)
        page.wait_for_timeout(3000)

        # Check if we see the access-denied page
        body_class = page.evaluate("() => document.body.className")
        if "access-denied" in body_class:
            logger.error("Auth FAILED - access denied. Re-run with --login")
            return False

        # Check for idea list content
        has_ideas = page.evaluate("() => document.querySelectorAll('.uvIdeaTitle, .uvIdeaList').length > 0")
        if has_ideas:
            logger.info("Auth verified - forum content visible!")
            return True

        logger.warning("Auth uncertain - no idea content found, but no access-denied either. Proceeding...")
        return True

    def scrape_one(self, page, url, idea_id, index, total):
        """Scrape a single idea page."""
        # Navigate
        page.goto(url, wait_until="load", timeout=20000)

        # Wait for title to render (proof content loaded)
        try:
            page.wait_for_selector("h1.uvIdeaTitle", timeout=10000)
        except Exception:
            # Fallback: wait a bit more
            page.wait_for_timeout(3000)

        # Validate URL matches
        current_id = self.extract_idea_id(page.url)
        if current_id != idea_id:
            logger.warning("[%d/%d] URL mismatch: expected %s, got %s", index + 1, total, idea_id, current_id)
            self.skipped += 1
            self.mark_done(url)
            return

        # Extract data
        data = self.extract_data(page)
        description = self.clean_description(data.get("description", ""))

        row = {
            "idea_id": idea_id,
            "url": url,
            "title": data.get("title", ""),
            "description_full": description,
            "votes": str(data.get("votes", 0)),
            "comments_count": str(len(data.get("comments", []))),
            "category": data.get("category", ""),
            "status": data.get("status", ""),
            "submitter": data.get("submitter", ""),
            "submitter_url": data.get("submitter_url", ""),
            "submit_date": data.get("submit_date", ""),
            "tags": data.get("tags", ""),
            "comments_json": json.dumps(data.get("comments", []), ensure_ascii=False),
        }

        self.save_to_csv(row)
        self.mark_done(url)
        self.saved += 1

        if not description:
            self.empty_desc += 1

        # Progress logging
        if self.saved % 50 == 0 or self.saved <= 5:
            title_preview = row["title"][:50]
            logger.info(
                "[%d/%d] id=%s votes=%s status=[%s] desc=%dch title=%s",
                self.saved,
                total,
                idea_id,
                row["votes"],
                row["status"][:20],
                len(description),
                title_preview,
            )


def main():
    parser = argparse.ArgumentParser(description="Scrape ideas.mist.com with auth")
    parser.add_argument("--login", action="store_true", help="Open browser for manual SSO login")
    args = parser.parse_args()

    if args.login:
        do_login()
    else:
        scraper = AuthenticatedScraper()
        scraper.scrape_all()


if __name__ == "__main__":
    main()
