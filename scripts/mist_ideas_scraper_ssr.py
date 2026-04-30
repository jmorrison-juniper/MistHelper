"""
SSR-based scraper for ideas.mist.com - no browser needed!

UserVoice does server-side rendering, so we can parse HTML directly
with BeautifulSoup instead of running a headless browser.

Reads URLs from data/mist_ideas_all_urls.txt (3053 URLs).
Writes to data/mist_ideas.csv with resume support.

Usage:
    pip install beautifulsoup4
    python scripts/mist_ideas_scraper_ssr.py
"""
import csv
import json
import logging
import re
import ssl
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Install BeautifulSoup: pip install beautifulsoup4")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ssr_scraper")

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ALL_URLS_FILE = DATA_DIR / "mist_ideas_all_urls.txt"
CSV_FILE = DATA_DIR / "mist_ideas.csv"
DONE_FILE = DATA_DIR / "mist_ideas_done_urls.txt"

# ── CSV headers ───────────────────────────────────────────────
HEADERS = [
    "idea_id", "url", "title", "description_full", "votes",
    "comments_count", "category", "status", "submitter",
    "submitter_url", "submit_date", "tags", "comments_json",
]

# ── SSL context for Zscaler corporate proxy ───────────────────
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE  # nosec B323 — required for Zscaler SSL inspection proxy

# ── Boilerplate lines to strip from descriptions ──────────────
BOILERPLATE_LINES = frozenset([
    "Submitted ideas will be reviewed and responded to by our Product team.",
    "Submitted ideas will be reviewed and responded to by our Product team.",
    "Please do not submit cases here.",
    "Please do not submit support cases here.",
    "All feature requests will be evaluated on the basis of demand (votes), technical feasibility, strategic alignment, and other factors.",
    "All feature requests will be evaluated on the basis of demand (votes), technical feasibility, strategic alignment, and other factors.",
])


class MistIdeasSSRScraper:
    """Scrapes idea pages from ideas.mist.com using HTTP GET + BeautifulSoup."""

    def __init__(self):
        self.saved = 0
        self.errors = 0
        self.skipped = 0
        self.empty_desc = 0

    def load_urls(self):
        """Load all URLs and done URLs, return remaining."""
        all_urls = ALL_URLS_FILE.read_text(encoding="utf-8").strip().splitlines()
        all_urls = [u.strip() for u in all_urls if u.strip()]

        done_set = set()
        if DONE_FILE.exists():
            done_set = set(DONE_FILE.read_text(encoding="utf-8").strip().splitlines())

        remaining = [u for u in all_urls if u not in done_set]
        logger.info("Total: %d, Done: %d, Remaining: %d",
                     len(all_urls), len(done_set), len(remaining))
        return remaining

    def mark_done(self, url):
        """Append URL to done file."""
        with open(DONE_FILE, "a", encoding="utf-8") as file_handle:
            file_handle.write(url + "\n")

    def extract_idea_id(self, url):
        """Extract numeric idea ID from URL."""
        match = re.search(r"/suggestions/(\d+)", url)
        return match.group(1) if match else ""

    def fetch_html(self, url):
        """Fetch raw HTML from URL."""
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
        resp = urlopen(req, context=SSL_CTX, timeout=30)  # nosec B310 — URL is from our curated list
        return resp.read().decode("utf-8")

    def clean_description(self, text):
        """Remove boilerplate lines from description text."""
        if not text:
            return ""
        lines = text.strip().splitlines()
        cleaned = [line for line in lines if line.strip() not in BOILERPLATE_LINES]
        return "\n".join(cleaned).strip()

    def parse_idea(self, html, url):
        """Parse idea data from HTML using BeautifulSoup."""
        soup = BeautifulSoup(html, "html.parser")

        # Title
        title_el = soup.select_one("h1.uvIdeaTitle")
        title = title_el.get_text(strip=True) if title_el else ""

        # Description
        desc_el = soup.select_one(".uvIdeaDescription .typeset")
        raw_desc = desc_el.get_text(strip=True) if desc_el else ""
        description = self.clean_description(raw_desc)

        # Votes
        votes_el = soup.select_one(".uvIdeaVoteCount")
        votes_text = votes_el.get_text(strip=True) if votes_el else "0"
        votes_match = re.search(r"\d+", votes_text)
        votes = int(votes_match.group()) if votes_match else 0

        # Status (specific badge, not the whole section)
        status_el = soup.select_one(".uvStyle-status")
        status = status_el.get_text(strip=True) if status_el else ""

        # Category
        cat_el = soup.select_one('a[href*="category_id"]')
        category = cat_el.get_text(strip=True) if cat_el else ""

        # Submitter
        user_links = soup.select('a[href*="/users/"]')
        submitter = user_links[0].get_text(strip=True) if user_links else ""
        submitter_url = user_links[0].get("href", "") if user_links else ""

        # Submit date
        time_el = soup.select_one("time")
        submit_date = time_el.get_text(strip=True) if time_el else ""

        # Tags
        tag_els = soup.select(".uvTag, .uvIdeaTag")
        tags = "|".join(el.get_text(strip=True) for el in tag_els if el.get_text(strip=True))

        # Comments
        comment_articles = soup.select("article.uvUserAction-comment")
        comments = []
        for article in comment_articles:
            author_el = article.select_one('a[href*="/users/"]')
            date_el = article.select_one("time")
            body_el = article.select_one(".typeset")
            comments.append({
                "author": author_el.get_text(strip=True) if author_el else "",
                "date": date_el.get_text(strip=True) if date_el else "",
                "body": body_el.get_text(strip=True) if body_el else "",
            })

        return {
            "title": title,
            "description": description,
            "votes": votes,
            "status": status,
            "category": category,
            "submitter": submitter,
            "submitter_url": submitter_url,
            "submit_date": submit_date,
            "tags": tags,
            "comments": comments,
        }

    def save_to_csv(self, row):
        """Append a row to CSV."""
        file_exists = CSV_FILE.exists() and CSV_FILE.stat().st_size > 0
        with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as file_handle:
            writer = csv.DictWriter(file_handle, fieldnames=HEADERS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    def scrape_all(self):
        """Main scraping loop."""
        remaining = self.load_urls()
        if not remaining:
            logger.info("All URLs already scraped!")
            return

        for index, idea_url in enumerate(remaining):
            idea_id = self.extract_idea_id(idea_url)
            if not idea_id:
                logger.warning("Skip (no ID): %s", idea_url)
                self.skipped += 1
                continue

            try:
                self.scrape_one(idea_url, idea_id, index, len(remaining))
            except Exception as error:
                self.errors += 1
                logger.error("[%d/%d] ERROR %s: %s",
                             index + 1, len(remaining),
                             idea_url[:60], str(error)[:120])
                self.mark_done(idea_url)

            # Polite delay to avoid rate limiting
            if (index + 1) % 10 == 0:
                time.sleep(0.5)

        logger.info("DONE. Saved=%d Errors=%d Skipped=%d EmptyDesc=%d",
                     self.saved, self.errors, self.skipped, self.empty_desc)

    def scrape_one(self, idea_url, idea_id, index, total):
        """Scrape a single idea page."""
        html = self.fetch_html(idea_url)
        data = self.parse_idea(html, idea_url)

        row = {
            "idea_id": idea_id,
            "url": idea_url,
            "title": data["title"],
            "description_full": data["description"],
            "votes": str(data["votes"]),
            "comments_count": str(len(data["comments"])),
            "category": data["category"],
            "status": data["status"],
            "submitter": data["submitter"],
            "submitter_url": data["submitter_url"],
            "submit_date": data["submit_date"],
            "tags": data["tags"],
            "comments_json": json.dumps(data["comments"], ensure_ascii=False),
        }

        self.save_to_csv(row)
        self.mark_done(idea_url)
        self.saved += 1

        if not data["description"]:
            self.empty_desc += 1

        # Progress logging
        if self.saved % 50 == 0 or self.saved <= 5:
            title_preview = row["title"][:50]
            logger.info("[%d/%d] id=%s votes=%s status=[%s] desc=%dch title=%s",
                        self.saved, total, idea_id, row["votes"],
                        row["status"][:20], len(row["description_full"]),
                        title_preview)


if __name__ == "__main__":
    scraper = MistIdeasSSRScraper()
    scraper.scrape_all()
