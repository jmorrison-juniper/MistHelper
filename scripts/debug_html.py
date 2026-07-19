"""Dump the raw HTML of a single idea page to diagnose what we're getting."""

import ssl
import sys
from pathlib import Path
from urllib.request import Request, urlopen

url = "https://ideas.mist.com/forums/912934-product-features/suggestions/50598263-modify-port-configuration-button"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    },
)

resp = urlopen(req, context=ctx, timeout=30)
html = resp.read().decode("utf-8")

outfile = Path(__file__).resolve().parent.parent / "data" / "debug_raw_html.html"
outfile.write_text(html, encoding="utf-8")
print(f"Saved {len(html)} chars to {outfile}")

# Check for key markers
print(f"\nuvIdeaTitle in HTML: {'uvIdeaTitle' in html}")
print(f"uvIdeaDescription in HTML: {'uvIdeaDescription' in html}")
print(f"Modify Port in HTML: {'Modify Port' in html}")
print(f"modify-port in HTML: {'modify-port' in html}")

# Show what the page actually contains
print(f"\nFinal URL (check for redirect): {resp.url}")
print(f"Status: {resp.status}")
print(f"Content-Type: {resp.headers.get('Content-Type')}")

# Print a sample around uvIdeaTitle if found
if "uvIdeaTitle" in html:
    idx = html.index("uvIdeaTitle")
    start = max(0, idx - 50)
    end = min(len(html), idx + 500)
    print(f"\n=== Around uvIdeaTitle ===\n{html[start:end]}")
else:
    print("\n=== FIRST 5000 CHARS ===")
    print(html[:5000])
